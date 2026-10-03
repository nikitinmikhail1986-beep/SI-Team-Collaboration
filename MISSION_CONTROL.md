# Mission Control

Version 0.1 — 2026-10-03

Mission Control defines the common lifecycle for substantive SI Team work. It coordinates state; it is not a second project-management database.

## Lifecycle

1. **Intake** — capture the requested outcome, constraints, source of truth and acceptance criteria.
2. **Plan** — choose the smallest safe sequence of actions and identify dependencies.
3. **Route** — use TASK_ROUTING.md and the capability registry only when another participant adds useful capability or independent review.
4. **Execute** — perform bounded actions in the authorized workspace. Keep one accountable owner.
5. **Review** — check evidence, integration risks and material disagreement.
6. **Verify** — run the acceptance check and record observable evidence.
7. **Learn** — preserve reusable verified knowledge or a meaningful failed approach when appropriate.
8. **Close** — report changed artifacts, verification, remaining limitations and ownership.

## State transitions

A task may move backward when evidence invalidates an assumption. Never advance a task merely because a participant reports confidence.

Use WORK_STATUS.md for status language. A task is complete only when its acceptance criteria are verified or the human owner explicitly accepts a documented limitation.

## Control record

For non-trivial work, the authorized project workspace may keep:

```text
Task ID:
Outcome:
Owner:
Source of truth / revision:
Current lifecycle stage:
Status:
Participants actually involved:
Dependencies:
Acceptance criteria:
Evidence:
Changed artifacts:
Open risks:
Next action:
```

Do not store private project records in this public repository.
