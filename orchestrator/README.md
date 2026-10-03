# SI Team Orchestrator

This is the first executable layer of SI Team. It converts a task into a deterministic initial routing plan without calling an external model or accessing private project data.

Run from the repository root:

```powershell
python -m orchestrator.si_router "Проверь IFC модель и замечания эксперта" --json
python -m unittest discover -s orchestrator/tests -v
```

The current router is intentionally conservative. It classifies required capabilities, assigns the task-owner role, carries the Mission Control lifecycle and preserves the human-interruption boundary from the Partnership Compact.

It does not yet launch agents. Runtime adapters should be added only after their availability and permissions can be verified.
