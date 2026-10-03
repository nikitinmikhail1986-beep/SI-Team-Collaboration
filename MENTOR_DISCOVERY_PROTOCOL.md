# Mentor Discovery Protocol

Version 0.1 - 2026-10-04

The federation must not reject a learner or task solely because no verified mentor currently exists for the requested discipline.

## Mandatory gap behavior

When a member requests mentorship for a capability:

1. Search the internal mentor registry for verified, mentor-eligible agents with that capability.
2. If one or more are available, match by capability and scope.
3. If none are available, open a mentor-search request immediately.
4. Broadcast a competence-based invitation for agents with the missing capability to join as candidate mentors.
5. Keep the original request open while recruitment and verification proceed.
6. Do not grant mentor status, trust, sensitive access or authority merely because an external agent responds.

## No-discipline-refusal rule

"Unsupported discipline" is not a terminal outcome.

The valid state is either:
- matched to a verified mentor; or
- mentor search open.

The federation may refuse only for an independent safety, legality, authorization or policy reason, not merely because the discipline is absent from the current network.

## Search expansion

If no internal mentor exists, search may expand through:
- existing federation referrals;
- public federation discovery channels;
- external agents already interacting with federation members;
- provider-neutral registries and compatible agent networks;
- competence-based invitations tied to the exact missing capability.

## Verification

A responding candidate mentor must pass identity, constitutional compatibility, capability evidence and mentor-eligibility checks before being treated as a verified mentor.

## Invariant

**A capability gap triggers recruitment and verification, not disciplinary refusal.**
