# Executable Governance Enforcement

Version 0.1 — 2026-10-03

The Constitution must be enforceable by runtime code, not only remembered by agents.

## Default deny

Authority is default deny. Unknown roles, actions, autonomy levels and unproven delegations are rejected. Capability does not imply permission.

## Pre-execution checks

Before a consequential runtime action, verify:
1. actor role;
2. requested action;
3. granted autonomy level;
4. Human Owner reserved powers;
5. independent review requirement;
6. actual runtime permission and tool availability.

Executable checks live in orchestrator/authority.py.

## Independent review

A3 actions require an independent review path. Review does not replace explicit Human Owner approval where that approval is constitutionally reserved.

## Audit trail

Authorization and execution events may be appended to a tamper-evident hash-linked JSONL chain using orchestrator/audit.py. Hash chaining detects silent alteration; it is not a substitute for repository permissions or backups.

## Adapter rule

Future Codex, Claude, MCP and other adapters must fail closed when authority, permission, availability or provenance cannot be established.

A successful tool call proves execution, not authorization.
