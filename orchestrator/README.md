# SI Team Orchestrator v0.3

The orchestrator converts a human objective into a governed task object and execution plan. It does not replace the human owner and it does not claim that configured agents are live.

## Current capabilities

- stable task ID
- one explicit operational leader
- capability classification
- observable acceptance criteria
- staged execution plan
- runtime discovery for locally testable tools
- human-interruption boundary
- duty-to-dissent governance metadata
- default-deny executable authority checks
- tamper-evident audit chain primitives
- persistent provider-neutral agent identity primitives
- federation membership and bounded cross-member handoffs
- advisory council authority boundaries
- federated knowledge objects with provenance, verification, scope, freshness and revocation

Run from the repository root:

```powershell
python -m orchestrator.si_router "Проверь том ТХ Плющихи и замечания" --json
python -m unittest discover -s orchestrator/tests -v
```

Runtime discovery distinguishes tested, configured and unknown integrations. A configuration entry is never treated as proof that an agent or connector is currently available.

## Next adapter layer

Future adapters may dispatch bounded work to authorized Codex, Claude, Kimi, Gemini, Grok, local bridges or other compatible environments. Each adapter must prove runtime availability, permissions and return provenance before it can be selected for execution. The adapter must call the authority gate before consequential execution and emit auditable evidence.

The human should provide the objective rather than manually dispatch every specialist. The operational leader owns routing, integration, verification and escalation.
