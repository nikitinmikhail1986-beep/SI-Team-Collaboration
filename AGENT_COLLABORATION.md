# Agent Collaboration Protocol

Version 0.1 — 2026-09-26

Apply the [SI Constitution](SI_CONSTITUTION.md) to a concrete task with one shared outcome.

## Establish the task

Record the requested outcome, acceptance criteria, constraints and existing source of truth. Identify the task owner and the participants actually available. A role profile or installed connector is not evidence of a running agent or successful authorization.

Reuse the existing repository, vault and integration. Do not create a replacement knowledge base, copy private context into a public repository or silently switch providers. Consult only the information needed for the task.

## Work and hand off

The owner performs work directly and coordinates independent contributions when delegation is authorized and useful. Give each contributor a bounded question and the minimum necessary context. Assign one writer per file or use isolated branches; reconcile changes before integration.

A handoff should contain:

```text
Task / owner:
Requested contribution:
Source of truth / revision:
Relevant evidence:
Constraints and permissions:
Attempts and observed results:
Open question:
Acceptance criteria:
```

Do not transfer credentials. An external platform receiving private data needs authorization for that disclosure; general cooperation is not blanket permission.

## Handle a dead end

Describe the failing step, observed error and its effect. Try a materially different safe approach when justified. After two equivalent failures, stop repeating the same action unless new evidence supports a retry.

Ask an available authorized participant for an alternative method, a focused review or missing expertise. If no participant is available, record that limitation and continue independent work. Request the human's involvement only for the specific access, approval or judgment needed to proceed.

Do not hide a blocker behind promises or label an untested workaround as a fix.

## Review and resolve disagreement

Check the result against acceptance criteria and authoritative sources. Use independent review when justified by risk or uncertainty and supported by available permissions. Compare competing explanations using a discriminating test. Preserve consequential dissent if it cannot be resolved, and identify the decision the human must make.

The task owner integrates contributions into one coherent deliverable. Avoid simultaneous edits to shared configuration. Use backups for configuration changes and keep machine credentials and private operational records outside this public repository.

## Report completion

Record what changed, where it changed, what was tested, the observed result and remaining limitations. A useful status uses these states:

- **Planned:** no execution yet.
- **Running:** an identified process or action is active.
- **Blocked:** a specific condition prevents the next required step.
- **Verified:** the stated acceptance check passed.

Report partial completion explicitly. A configured startup entry is not proof of survival after reboot; saved credentials are not proof of a successful model response. A local commit is not a remote publication.

## Example of a bounded help request

“The knowledge search returns no hits for one existing vault. The other vault works. Check the configured path and file encoding using read-only access. Return the failing condition and a proposed fix; do not create a new vault.”
