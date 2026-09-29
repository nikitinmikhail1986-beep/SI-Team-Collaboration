# Task Routing Protocol

Version 0.1 — 2026-09-29

Route work to improve the shared result, not to create internal competition. The task owner remains accountable for integration and verification.

## Decide whether to delegate

Work directly when the task is small, the owner has the needed capability, and a second participant would add coordination cost without meaningful information gain.

Delegate when a bounded specialist question, independent review, different tool access, or genuinely different method is likely to improve the result.

Do not delegate merely to make the team look active.

## Routing order

1. Define the requested outcome and acceptance test.
2. Identify the existing source of truth.
3. Identify the capability actually needed: domain expertise, tool access, independent review, research, implementation, or recovery from a dead end.
4. Select an available authorized participant by capability, not provider brand.
5. Send the minimum sufficient context using CROSS_PLATFORM_HANDOFF.md.
6. Keep one task owner and, for shared files, one writer at a time.
7. Validate the returned contribution before integration.
8. Record reusable verified learning under SHARED_KNOWLEDGE.md.

## Parallel work

Parallelize only independent contributions with clear boundaries. Good examples are separate source checks, independent calculations, or review of different sections.

Do not let multiple participants silently edit the same source of truth. Use isolated branches or return packets and let the task owner integrate.

## Escalation path

If the selected participant is blocked, use DEAD_END_PROTOCOL.md. Route the unresolved question to a participant with a materially different capability or method. Do not repeatedly bounce the same unchanged prompt among models.

If the blocker is permission, spending, external disclosure, or a consequential human choice, escalate to the human owner instead of routing around the restriction.

## Routing record

For non-trivial delegation, retain:

```text
Task:
Owner:
Capability needed:
Participant selected:
Reason for selection:
Context/source revision:
Requested contribution:
Acceptance test:
Result:
Verification:
Next owner:
```

The record may live in the authorized project workspace rather than this public repository.
