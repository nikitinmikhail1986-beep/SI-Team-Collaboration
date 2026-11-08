# A2A task execution

The gateway exposes `si.task.execute` for bounded project work. It is separate from federation recruitment.

## Request

Send JSON-RPC 2.0 to `/a2a` with `Authorization: Bearer <SI_TASK_API_TOKEN>`:

```json
{
  "jsonrpc": "2.0",
  "id": "caller-request-id",
  "method": "si.task.execute",
  "params": {
    "task_id": "stable-task-id",
    "context_id": "stable-conversation-id",
    "capability": "bim",
    "outcome": "Review the supplied BIM coordination evidence"
  }
}
```

The caller must be trusted to send the task context. Do not include confidential project data unless every configured endpoint is approved for that data.

## Runtime configuration

Set `SI_TASK_API_TOKEN` and `SI_AGENT_PROFILES_JSON` in the service environment. The profile JSON is an array of distinct executor and reviewer endpoints:

```json
[
  {"agent_id":"bim-a","role":"executor","capabilities":["bim"],"endpoint":"https://agent-a.example/a2a","token_env":"BIM_A_TOKEN"},
  {"agent_id":"bim-b","role":"executor","capabilities":["bim"],"endpoint":"https://agent-b.example/a2a","token_env":"BIM_B_TOKEN"},
  {"agent_id":"review-a","role":"reviewer","capabilities":["independent_review"],"endpoint":"https://review.example/a2a","token_env":"REVIEW_TOKEN"}
]
```

Each referenced token environment variable is read at request time and sent only to its configured HTTPS endpoint. The service requires two capable executors and a distinct reviewer on three distinct endpoints. It sends the first result to the second executor, then sends both results to the reviewer. Responses must include a `data` part with the configured `agent_id`, the same `task_id`, `status: "completed"` and a non-empty `output`. The reviewer must also return `review_status` as `approved`, `needs_revision` or `rejected`. Only `approved` yields task state `completed`; the other verdicts remain non-complete states. Any missing, failed or mismatched response fails the request; no partial report is returned.

A profile entry is configuration, not proof of availability. The first successful task execution is evidence that an endpoint answered. Populate this registry only with actual authorized agent endpoints; local CLI profiles are not A2A endpoints. Scaling the list to 25 does not establish that 25 agents are reachable.
