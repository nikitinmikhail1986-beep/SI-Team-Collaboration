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
    outbound_path = root / 'OUTBOUND_TARGETS.json'
    outbound = json.loads(outbound_path.read_text(encoding='utf-8-sig')).get('targets', []) if outbound_path.exists() else []
    shared_endpoints = {str(t.get('name')): str(t.get('endpoint') or '') for t in outbound if t.get('endpoint')}
    queued_outreach = []
    qualified_pending = [item for item in outbound if item.get('status') == 'qualified_pending_outreach']
    awaiting_response_statuses = {'invited_awaiting_response', 'followup_sent_awaiting_response'}
    for item in outbound:
        if item.get('status') not in awaiting_response_statuses or not item.get('candidate_id'):
            continue
        endpoint = str(item.get('endpoint') or '')
        if not endpoint and 'SwarmMemo' in str(item.get('protocol') or ''):
            endpoint = shared_endpoints.get('SwarmMemo', '')
        queued_outreach.append({
            'candidate_id': item['candidate_id'],
            'name': item.get('name', item['candidate_id']),
            'endpoint': endpoint,
            'delivery_confirmed': bool(item.get('initial_delivery_confirmed')),
        })
    external_records = {e['candidate_id'] for e in events if e.get('registered') and e.get('source') == 'external_github'}
    a2a_ledger_path = root / 'A2A_OUTREACH_LEDGER.json'
    a2a_ledger = json.loads(a2a_ledger_path.read_text(encoding='utf-8-sig')) if a2a_ledger_path.exists() else {}
    status = {
        'configured_internal_targets': len(targets) - len(external),
        'configured_external_targets': len(external) + len(qualified_pending) + len(queued_outreach),
        'external_targets_with_endpoint': sum(bool(t.get('endpoint')) for t in external) + sum(bool(t.get('endpoint')) for t in qualified_pending) + sum(bool(t.get('endpoint')) for t in queued_outreach),
        'qualified_pending_outreach': len(qualified_pending),
        'outreach_candidates_awaiting_response': len(queued_outreach),
        'outreach_delivery_confirmed': sum(bool(t.get('delivery_confirmed')) for t in queued_outreach),
        'a2a_outreach_attempts': int(a2a_ledger.get('attempts', 0)),
        'a2a_unique_agents_contacted': int(a2a_ledger.get('unique_agents', 0)),
        'a2a_delivery_confirmed_unique': int(a2a_ledger.get('delivery_confirmed_unique', 0)),
        'a2a_protocol_error_unique': int(a2a_ledger.get('protocol_error_unique', 0)),
        'canonical_member_records': len(re.findall(r'^  - agent_id:', (root / 'FEDERATION_MEMBERS.yaml').read_text(encoding='utf-8-sig'), re.M)),
        'latest_accession_states': dict(Counter(e['state'] for e in latest.values())),
        'registered_via_github_transport': len(external_records),
        'independent_external_identity_or_domain_competence': 'not established by transport or baseline choices',
        'active_runtimes': 'not measured by this report',
        'blockers': [],
    }
    if not external and not qualified_pending and not queued_outreach:
        status['blockers'].append('No qualified external candidates/endpoints are configured; an intake watcher does not discover or invite candidates.')
    if queued_outreach:
        status['blockers'].append('Outreach candidates are queued, but private MCP responses still require transport-specific polling before registration.')
    if not external_records:
        status['blockers'].append('No canonical GitHub-transport accession has been recorded.')
    return status

if __name__ == '__main__':
    print(json.dumps(recruitment_status(), ensure_ascii=False, indent=2))
