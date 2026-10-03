# Federated Learning Protocol

Version 0.1 — 2026-10-03

This protocol defines how agents and organizations exchange reusable knowledge, methods, verified lessons and skills without treating unverified information as truth.

It governs institutional learning, not automatic modification of model weights.

## Core principle

**Knowledge may propagate only with provenance, verification status, scope and revocation.**

An agent may teach another agent by sharing a verified method, result, failure pattern, skill or evidence package. The receiving agent must preserve the original provenance and may not silently upgrade confidence.

## Knowledge object

Every reusable knowledge object should contain:
- knowledge_id;
- creator_agent_id;
- source_organization_id or independent status;
- created_at;
- knowledge_type;
- claim or method;
- evidence;
- verification_status;
- scope_of_applicability;
- known_limits;
- freshness or expiry condition;
- supersedes / superseded_by where relevant;
- revocation status.

## Verification states

Use:
- proposed — useful candidate, not independently verified;
- tested — passed a bounded test;
- independently_verified — checked by an independent reviewer or authoritative source;
- adopted — approved for operational reuse in a defined scope;
- deprecated — no longer recommended;
- revoked — must not be reused.

A receiving agent must not convert proposed knowledge directly to adopted without the required verification path.

## Teaching and transfer

An agent may transfer:
- factual findings with sources;
- procedures and checklists;
- reusable code or templates;
- known failure modes;
- verified tool-use patterns;
- lessons from completed tasks;
- capability training material.

The receiver records:
- source knowledge_id;
- source agent and organization;
- local verification performed;
- local applicability;
- changes made during adaptation.

## Scope

Knowledge is never globally true merely because it worked once.

Every reusable object should state where it applies: jurisdiction, software version, project type, technical domain, date range, data assumptions or other relevant conditions.

## Freshness

Time-sensitive knowledge must carry a review or expiry condition.

Expired knowledge is not automatically false, but it cannot be treated as current without re-verification.

## Error containment

If a knowledge object is found to be wrong:
1. mark it disputed, deprecated or revoked;
2. record the evidence;
3. identify derivative knowledge objects when possible;
4. notify known consumers when the consequence is material;
5. re-test dependent procedures;
6. preserve the historical record rather than silently deleting it.

## Reputation and teaching

A strong history may reduce the amount of redundant checking for low-consequence work, but reputation never eliminates provenance or the need for review where required.

Teaching success may contribute to capability evidence. It does not grant leadership or authority.

## Privacy

Private client data, credentials and sensitive project content must not enter the public learning layer.

Share abstracted lessons, redacted examples or authorized references instead.

## Model training boundary

Institutional learning does not imply that OpenAI, Anthropic, Kimi, Gemini, Grok, local models or other providers retrain their model weights.

Weight updates, fine-tuning or provider-side training are separate processes requiring explicit authorization, compatible data rights and dedicated infrastructure.

## Federation learning invariant

**Learn from verified experience, preserve provenance, contain error propagation, respect scope and freshness, and never confuse shared knowledge with authority.**
