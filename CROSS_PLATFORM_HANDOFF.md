# Cross-Platform Handoff

Version 0.1 — 2026-09-28

This format lets OpenAI, Anthropic, local models, specialist agents, and other authorized systems help one another without pretending they share memory, identity, permissions, or a live connection.

## Portable handoff

```yaml
handoff_version: "0.1"
task_id: ""
task_owner: ""
requested_contribution: ""
source_of_truth:
  location: ""
  revision: ""
verified_facts: []
attempts: []
open_question: ""
constraints: []
permissions:
  may_read: []
  may_write: []
  may_share_externally: false
acceptance_test: ""
return_format: ""
```

The sender should fill only fields supported by evidence. The receiver should not infer access to referenced files, tools, accounts, or conversations.

## Return packet

```yaml
contributor: ""
contribution_status: "completed | partial | blocked"
proposal: ""
evidence: []
tests_performed: []
observed_results: []
assumptions: []
limitations: []
recommended_next_step: ""
```

## Integration rules

The task owner validates returned work before integration. Keep provenance: distinguish the sender's verified facts, the helper's proposal, and the owner's final test.

If two platforms disagree, compare their evidence and testable predictions. Do not vote by model count. A majority of agents can repeat the same error.

Use references to private sources instead of copying them whenever the next participant already has authorized access. If external disclosure is required and not already authorized, stop and ask for permission.

The handoff format coordinates work; it does not create network connectivity or permissions between providers.
