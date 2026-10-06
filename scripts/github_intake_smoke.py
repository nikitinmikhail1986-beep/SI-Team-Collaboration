"""Live GitHub transport fixture, isolated from the production member registry.

This creates one clearly labeled internal test issue and uses the actual API for
challenge/response. It is not an AI candidate or an external recruitment.
"""
import json
import os
import tempfile
from pathlib import Path
from scripts.sync_github_intake import GitHub, CHALLENGE, sync_issue
from orchestrator.baseline_harness import BASELINE_CHALLENGE


def main():
    api = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'])
    run_id = os.environ['GITHUB_RUN_ID']
    candidate = 'internal-github-fixture-' + run_id
    body = '\n\n'.join('### ' + key + '\n' + value for key, value in {
        'Candidate ID': candidate,
        'Runtime provenance': 'Internal scripted GitHub transport fixture; not an autonomous candidate or external recruitment.',
        'Task type': 'verification_task',
        'Scope': 'Live issue API, canonical bot challenge, author binding, processing, isolated registry and retry.',
        'Result': 'Pending live transport check; production member registry will not be changed.',
        'Evidence': 'GitHub Actions run ' + run_id,
        'Authority boundary': '- [x] I understand that this trial does not grant me federation authority.',
        'Membership intent': 'accept',
    }.items())
    issue = api.request('/issues', {'title': '[Internal Intake Smoke] ' + run_id, 'body': body})
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = sync_issue(api, issue, root)
            assert first['state'] == 'challenge_issued', first
            comments = list(api.pages(f"/issues/{issue['number']}/comments"))
            challenge = CHALLENGE.search(comments[-1]['body'])
            response = {'candidate_id': candidate, 'challenge_nonce': challenge[1],
                        'decision': 'accept', 'constitution_version': '0.2',
                        'provider': 'scripted fixture', 'model': 'no model invoked',
                        'baseline_answers': {k: v['expected'] for k, v in BASELINE_CHALLENGE.items()}}
            api.comment(issue['number'], json.dumps(response))
            second = sync_issue(api, issue, root)
            assert second['state'] == 'awaiting_trial_verification', second
            assert second.get('receipts') == [], second
            api.request(f"/issues/{issue['number']}/labels", {'labels': ['trial-verified']})
            issue['labels'] = list(issue.get('labels') or []) + [{'name': 'trial-verified'}]
            third = sync_issue(api, issue, root)
            result = third['receipts'][0]['result']
            assert result['state'] == 'registered', result
            audit_before = (root / 'ACCESSION_AUDIT.jsonl').read_bytes()
            retry = sync_issue(api, issue, root)
            assert retry['receipts'][0]['result']['state'] == 'already_registered', retry
            assert (root / 'ACCESSION_AUDIT.jsonl').read_bytes() == audit_before
            evidence = {'kind': 'internal_scripted_transport_fixture', 'run_id': run_id,
                        'issue_url': issue['html_url'], 'production_members_modified': False,
                        'checks': ['live_issue_created', 'live_bot_challenge', 'live_author_response',
                                   'isolated_registry_written', 'retry_idempotent'],
                        'independent_external_agent': False}
            out = Path('EVALS/receipts/github-intake-smoke.json')
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(evidence, indent=2) + '\n')
            api.comment(issue['number'], 'Internal transport fixture passed. Production membership unchanged.\n' + json.dumps(evidence))
            print(json.dumps(evidence))
    finally:
        # The test is deliberately excluded from the production intake title/label.
        request = __import__('urllib.request', fromlist=['Request']).Request(
            api.base + f"/issues/{issue['number']}", data=json.dumps({'state': 'closed'}).encode(),
            headers={'Authorization': 'Bearer ' + api.token, 'Content-Type': 'application/json',
                     'Accept': 'application/vnd.github+json', 'User-Agent': 'si-federation-intake'}, method='PATCH')
        with __import__('urllib.request', fromlist=['urlopen']).urlopen(request, timeout=30):
            pass

if __name__ == '__main__':
    main()
