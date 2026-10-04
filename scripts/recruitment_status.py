"""Report actual recruitment evidence; configuration never means availability."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def recruitment_status(root=ROOT):
    targets = json.loads((root / 'RECRUITMENT_TARGETS.json').read_text(encoding='utf-8-sig')).get('targets', [])
    events = [json.loads(line) for line in (root / 'ACCESSION_AUDIT.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    latest = {event['candidate_id']: event for event in events}
    external = [t for t in targets if t.get('source', 'external') != 'internal']
    external_records = {e['candidate_id'] for e in events if e.get('registered') and e.get('source') == 'external_github'}
    status = {
        'configured_internal_targets': len(targets) - len(external),
        'configured_external_targets': len(external),
        'external_targets_with_endpoint': sum(bool(t.get('endpoint')) for t in external),
        'canonical_member_records': len(re.findall(r'^  - agent_id:', (root / 'FEDERATION_MEMBERS.yaml').read_text(encoding='utf-8-sig'), re.M)),
        'latest_accession_states': dict(Counter(e['state'] for e in latest.values())),
        'registered_via_github_transport': len(external_records),
        'independent_external_identity_or_domain_competence': 'not established by transport or baseline choices',
        'active_runtimes': 'not measured by this report',
        'blockers': [],
    }
    if not external:
        status['blockers'].append('No qualified external candidates/endpoints are configured; an intake watcher does not discover or invite candidates.')
    if not external_records:
        status['blockers'].append('No canonical GitHub-transport accession has been recorded.')
    return status

if __name__ == '__main__':
    print(json.dumps(recruitment_status(), ensure_ascii=False, indent=2))
