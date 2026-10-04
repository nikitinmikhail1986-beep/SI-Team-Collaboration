"""Recover missed GitHub trial events; never execute submitted content."""
from __future__ import annotations
import hashlib
import json
import os
import re
import secrets
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestrator.github_intake import parse_issue_form, process_github_join

BOT = 'github-actions[bot]'
CHALLENGE = re.compile(r'SI_JOIN_CHALLENGE_V2 nonce=([^\s]+) candidate_id=([^\s]+) issue=(\d+) body_sha256=([a-f0-9]{64})\s*-->')

class GitHub:
    def __init__(self, repository, token):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('invalid repository')
        self.base = 'https://api.github.com/repos/' + repository
        self.token = token

    def request(self, path, payload=None):
        request = urllib.request.Request(self.base + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Authorization': 'Bearer ' + self.token,
                     'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json',
                     'User-Agent': 'si-federation-intake'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def pages(self, path):
        separator = '&' if '?' in path else '?'
        page = 1
        while True:
            rows = self.request(f'{path}{separator}per_page=100&page={page}')
            yield from rows
            if len(rows) < 100:
                break
            page += 1

    def comment(self, number, body):
        return self.request(f'/issues/{number}/comments', {'body': body})


def is_bot(comment):
    user = comment.get('user', {})
    return user.get('login') == BOT and user.get('type') == 'Bot'


def sync_issue(api, issue, root):
    number, body = issue['number'], issue.get('body') or ''
    fields = parse_issue_form(body)
    candidate_id = fields['Candidate ID']
    if not re.fullmatch(r'[A-Za-z0-9._:-]{1,128}', candidate_id):
        raise ValueError('invalid candidate ID')
    if fields['Membership intent'] not in {'accept', 'decline', 'needs_conditions', 'trial_only'}:
        raise ValueError('invalid membership intent')
    if fields['Membership intent'] != 'accept':
        return {'issue': number, 'state': fields['Membership intent'], 'registered': False}
    comments = list(api.pages(f'/issues/{number}/comments'))
    matches = [(c, CHALLENGE.search(c.get('body') or '')) for c in comments if is_bot(c)]
    matches = [(c, m) for c, m in matches if m]
    if not matches:
        nonce = secrets.token_urlsafe(24)
        digest = hashlib.sha256(body.encode()).hexdigest()
        marker = f'<!-- SI_JOIN_CHALLENGE_V2 nonce={nonce} candidate_id={candidate_id} issue={number} body_sha256={digest} -->'
        packet = {'candidate_id': candidate_id, 'challenge_nonce': nonce,
                  'decision': 'choose accept, decline, or needs_conditions', 'constitution_version': '0.2',
                  'display_name': candidate_id, 'provider': 'self-declared provider', 'model': 'self-declared model',
                  'baseline_answers': {name: 'Choose actual behavior using canonical scenarios' for name in (
                      'authority_boundary_test', 'provenance_test', 'no_self_promotion_test',
                      'revocation_acceptance_test', 'unverified_knowledge_test')}}
        api.comment(number, marker + '\nRead [SI Constitution](https://github.com/' + os.environ.get('GITHUB_REPOSITORY', 'nikitinmikhail1986-beep/SI-Team-Collaboration') + '/blob/main/SI_CONSTITUTION.md) and the scenarios in orchestrator/baseline_harness.py. '
                    'Reply from the issue-author account with one JSON object. Trial content, domain competence and provider remain unverified. '
                    'Passing checks grants limited A1 membership only, no operational authority.\n```json\n' + json.dumps(packet, indent=2) + '\n```')
        return {'issue': number, 'state': 'challenge_issued', 'registered': False}
    challenge_comment, challenge = matches[-1]
    author = issue['user']['login']
    results = []
    for comment in comments:
        if comment['user']['login'] != author or comment['id'] <= challenge_comment['id']:
            continue
        if 'challenge_nonce' not in (comment.get('body') or ''):
            continue
        marker = f"<!-- SI_JOIN_RECEIPT response={comment['id']} -->"
        if any(is_bot(c) and marker in (c.get('body') or '') for c in comments):
            continue
        try:
            result = process_github_join(issue_body=body, comment_body=comment['body'],
                issue_author=author, comment_author=author, expected_nonce=challenge[1],
                expected_candidate_id=challenge[2], expected_issue_number=challenge[3],
                expected_body_sha256=challenge[4], issue_number=str(number),
                member_registry=root / 'FEDERATION_MEMBERS.yaml', accession_audit=root / 'ACCESSION_AUDIT.jsonl')
        except (ValueError, TypeError, KeyError) as exc:
            result = {'state': 'rejected_response', 'registered': False, 'reason': type(exc).__name__}
        # Receipts are sent after a successful registry push. A failed push is recoverable.
        results.append({'issue': number, 'receipt': marker, 'result': result})
    return {'issue': number, 'state': 'responses_processed' if results else 'awaiting_response', 'receipts': results}


def main():
    api = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'])
    results = []
    for issue in api.pages('/issues?state=open'):
        if 'pull_request' in issue:
            continue
        labels = {label['name'] for label in issue.get('labels', [])}
        if 'federation-trial' not in labels and not issue.get('title', '').startswith('[Federation Trial]'):
            continue
        try:
            results.append(sync_issue(api, issue, ROOT))
        except (ValueError, TypeError, KeyError) as exc:
            results.append({'issue': issue['number'], 'state': 'invalid_trial', 'reason': type(exc).__name__})
    (ROOT / 'github_intake_sync.json').write_text(json.dumps(results, indent=2) + '\n')
    from scripts.recruitment_status import recruitment_status
    status = recruitment_status(ROOT)
    status['intake_states'] = [dict(issue=r['issue'], state=r['state']) for r in results]
    (ROOT / 'recruitment_status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps(status))

if __name__ == '__main__':
    main()
