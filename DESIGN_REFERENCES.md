# External Design References

Version 0.1 — 2026-10-03

SI Team remains its own governance model. Public repositories were studied only as engineering references; no external code was copied.

## ShackleAI Orchestrator

Repository: shackleai/orchestrator

Confirmed useful mechanisms:
- explicit CEO/manager/worker hierarchy;
- default-deny tool governance;
- per-agent and company budgets;
- audit trail;
- adapter layer across several runtimes.

Adopted as an original SI Team implementation: default-deny authority checks and tamper-evident audit chaining.

## AgentPolis Agent Constitution

Repository: AgentPolis/agent-constitution

Confirmed useful mechanisms:
- high-stakes decisions trigger structured challenge;
- critic/defender/judge review;
- document-grounded evidence;
- auditable decision history.

Adopted in SI terms: independent review for high-consequence actions without replacing appointed command or Human Owner authority.

## Orchestra

Repository: DrSeedon/orchestra

Confirmed useful mechanisms:
- the human provides the goal instead of manually dispatching workers;
- workers run in isolated git worktrees;
- cross-model review can be a code-enforced merge gate;
- platform-side tests can gate merge decisions;
- the project explicitly documents where a governance rule is prompt-only rather than code-enforced.

Adopted as a design principle: constitutional rules should become enforceable gates wherever practical, and documentation must distinguish written policy from code-enforced policy.

## Rule

External projects are references, not authorities. Every borrowed concept must be tested against SI Constitution, Human Owner authority, unity of command, bounded autonomy, privacy and source-of-truth rules before adoption.
