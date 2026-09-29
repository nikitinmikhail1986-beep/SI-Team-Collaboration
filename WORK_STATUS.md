# Verifiable Work Status Protocol

Version 0.1 — 2026-09-29

Status reports must describe observable work. They are not reassurance, intention, or a substitute for execution.

## Allowed states

**Planned** — the next action is identified but has not started.

**Running** — a named action or process is currently active. When possible include a process, job, branch, file, tool call, or other observable reference.

**Blocked** — a specific condition prevents the next required action. State the blocker and the exact action needed to clear it.

**Partial** — useful output exists, but one or more acceptance criteria remain unmet.

**Verified** — the stated acceptance test has passed and the evidence is available.

**Superseded** — a newer verified result replaces this result.

## Reporting rule

A status update should answer:

```text
State:
Action:
Observable evidence:
Changed artifacts:
Acceptance check:
Remaining blocker or next step:
```

Do not say “working in the background” unless an actual background process, automation, job, or delegated participant is running and can be identified.

Do not say “done” because a command was issued. Report the observed result. A successful local commit is not proof of remote publication; configured credentials are not proof of successful authentication; a startup entry is not proof that a service survived reboot.

## Silence and interruption

Do not interrupt the human merely to confirm presence. Ask for human action only when a blocker requires permission, authentication, physical interaction, spending, disclosure authorization, or a consequential decision.

If no work is running, say so. If a process stopped, report the stop rather than implying continuation.

## Verification evidence

Prefer compact evidence that another participant can reproduce: commit hash, test result, file revision, command result, job identifier, source citation, or direct observation.

Evidence should prove the claim being made and should not expose credentials or unrelated private information.
