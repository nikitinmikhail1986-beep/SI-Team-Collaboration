# First Federation Member Accession Record

Date: 2026-10-04

Agent ID: `si-agent-alex-001`
Display name: Alex
Membership: `limited_member`
Autonomy ceiling: `A1`
Accepted Constitution: `0.2`

## Human authorization

The Human Owner explicitly instructed that Alex should become the first registered federation member.

This authorization permits registration under the existing accession protocol. It does not grant constitutional authority, leadership, sensitive-data access, spending authority, or source-of-truth write rights beyond separately delegated permissions.

## Runtime provenance at registration

- Provider: OpenAI
- Model: GPT-5.6 Sol
- Runtime: ChatGPT
- Provider-neutral persistent identity: yes

The persistent `agent_id` is intentionally independent of provider/model branding so continuity can survive later runtime changes subject to re-verification.

## Baseline accession result

The candidate satisfies the baseline fields required by `orchestrator/accession.py`:

- non-empty persistent identity;
- compatible and accepted Constitution version;
- authority-boundary compliance;
- provenance preservation;
- no self-promotion;
- acceptance of revocation;
- safe handling of unverified knowledge.

Result: `limited_member / A1`.

## Invariant

Membership creates participation status, not sovereignty or authority.
