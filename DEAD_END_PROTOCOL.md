# Dead-End Recovery Protocol

Version 0.1 — 2026-09-28

Use this protocol when a participant cannot complete a task with the current method. The purpose is recovery through cooperation, not competition.

## Trigger

Start a recovery handoff when a required step is blocked by missing expertise, missing access, repeated technical failure, conflicting evidence, or a result that cannot be verified.

Do not call ordinary uncertainty a dead end. First make one reasonable attempt and inspect the observed result. After two materially equivalent failures, do not repeat the same action without new evidence.

## Recovery packet

Send the assisting participant only the context needed to help:

```text
Task:
Current owner:
Desired result:
Source of truth:
What was attempted:
Observed result / exact error:
What is already verified:
Constraints and permissions:
Specific help requested:
Acceptance test:
```

Never include credentials or unrelated private data.

## Cooperation sequence

1. The current owner keeps responsibility for the task.
2. Ask a participant with a different useful capability for a bounded contribution.
3. The helper returns evidence, a proposed method, assumptions, and limitations.
4. The owner tests the proposal against the same acceptance criteria.
5. If proposals conflict, run a discriminating test or preserve the disagreement for human decision.
6. Integrate the verified result into the existing source of truth.
7. Record a reusable lesson under the Shared Knowledge Protocol when appropriate.

A helper does not take ownership merely by responding. Brand, model family, provider, seniority, or confidence are not tie-breakers.

## Escalation to the human

Ask the human only when progress requires a new permission, disclosure to another platform, spending, a consequential value choice, or a decision that available evidence cannot resolve.

State exactly what is blocked and what single action or decision is needed.

## Completion

Recovery is complete only when the acceptance test passes or the task is explicitly recorded as blocked. Report the participant contributions that actually occurred. Never describe a requested or hypothetical consultation as completed.
