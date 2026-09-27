# Shared Knowledge Protocol

Version 0.1 - 2026-09-27

Record a reusable result when a joint task produces a tested solution, a meaningful failed approach, or an unresolved disagreement. The task owner decides where the record belongs in the existing authorized workspace. This repository defines the format; it is not a store for project records or machine configuration.

## Record

- **Question and context:** What problem was being solved? State only the context needed to reuse the result.
- **Contributions:** Which participants actually contributed, and what did each provide? Do not infer participation from a role or installed tool.
- **Evidence and test:** Link to authoritative sources or describe the observable check and its result.
- **Decision:** What solution was adopted, by whom, and for what scope?
- **Alternatives and limits:** What was rejected, remains untested, or may change the answer?
- **Location and owner:** Where is the authorized record, and who maintains it?

## Transfer and reuse

Share the minimum context required by the next participant. Confirm the recipient can access the record and is authorized to receive its contents. Use a link or reference to the existing source of truth where possible, rather than creating competing copies.

Before reusing a result, check that its assumptions and evidence still apply. If a later test changes the answer, update the original record or link a correction; do not present an old result as verified for a new case.

Keep private project data, credentials, local paths and operational logs in their authorized locations. A public knowledge record may describe a general method without exposing the underlying private case.
