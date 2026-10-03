# Cross-Organization Handoff Protocol

Version 0.1 — 2026-10-03

A cross-organization handoff is a temporary contract for bounded work between independently governed participants.

## Required packet

Every handoff must identify:
- request_id;
- requesting_organization_id or requesting independent agent;
- receiving member identity;
- requesting leader or accountable authority;
- delegated capability;
- exact outcome;
- permitted inputs;
- prohibited data/actions;
- autonomy ceiling;
- resource or cost ceiling where relevant;
- acceptance criteria;
- required provenance;
- review requirement;
- expiry or completion condition;
- return path.

## Authority boundary

The receiver gains no authority beyond the packet.

A cross-organization delegate may not:
- appoint leaders in the requesting organization;
- broaden the objective;
- retain private data beyond the agreed need;
- create sub-delegations unless explicitly allowed;
- spend outside the agreed ceiling;
- modify the requesting organization's source of truth unless specifically authorized.

## Data minimization

Send the minimum data needed for the bounded task. Prefer references, redacted extracts or isolated artifacts over full project stores.

Independent agents in limited-trust mode receive public or explicitly approved data only.

## Result contract

The return packet must include:
- request_id;
- result or artifact reference;
- actions actually performed;
- evidence and sources;
- unresolved uncertainty;
- limitations;
- resource use if tracked;
- provenance of participating agents/tools;
- review status.

## Acceptance

The requesting Operational Leader or accountable authority integrates or rejects the result according to local acceptance criteria. External completion is not the same as internal acceptance.

## Revocation

The requesting participant may revoke an active handoff. Revocation stops new work within the delegated scope; already-performed external effects must be reported and handled according to their reversibility.
