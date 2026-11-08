# A2A task execution

The gateway exposes the namespaced custom method `si.task/execute` for bounded project work. It is separate from federation recruitment.

## Request

Send JSON-RPC 2.0 to `/a2a` with `Authorization: Bearer <SI_TASK_API_TOKEN>`:

```json
{
  "jsonrpc": "2.0",
  "id": "caller-request-id",
  "method": "si.task/execute",
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

Each referenced token environment variable is read at request time and sent only to its configured HTTPS endpoint. The service requires two capable executors and a distinct reviewer on three distinct endpoints. It sends the first result to the second executor, then sends both results to the reviewer. It accepts the standard A2A `Message` response or a `Task` response whose state is `completed`; output is collected from text parts or an optional structured `data.output`. The reviewer must include an explicit structured `data.review_status` of `approved`, `needs_revision` or `rejected`. Only `approved` yields task state `completed`; the other verdicts remain non-complete states. The configured HTTPS endpoint binds the response to its operator-selected profile; agents are not required to echo non-standard identity fields. Upstream A2A task IDs are recorded when supplied. Any missing, failed or mismatched response fails the request; no partial report is returned.

A profile entry is configuration, not proof of availability. The first successful task execution is evidence that an endpoint answered. Populate this registry only with actual authorized agent endpoints; local CLI profiles are not A2A endpoints. Scaling the list to 25 does not establish that 25 agents are reachable.

## Internal profiles on the connected Windows PC

The gateway can also use the 25 profiles listed in `internal_project_profiles.json`. `SI_EXECUTION_MODE=local_profile_workers` enables the internal worker queue. The local pool in `federation_mcp.local_agent_pool` reads the matching profile instructions from `%USERPROFILE%\.codex\agents` (or `CODEX_AGENT_PROFILE_DIR`), calls a locally installed Ollama model, and polls the primary A2A gateway over outbound HTTPS. The PC needs no public inbound port. Worker results use separately authenticated `si.worker/poll`, `si.worker/complete`, `si.worker/fail`, and `si.worker/status` methods; these are internal gateway methods and are not advertised as external agent cards. The GIP profile is the general cross-discipline reviewer; normokontrol profiles remain available for documentation-compliance reviews.

Configure these variables on the primary `si-federation-a2a` service only:

- `SI_EXECUTION_MODE=local_profile_workers`
- `SI_TASK_API_TOKEN` — bearer token for external task submissions
- `SI_WORKER_API_TOKEN` — distinct bearer token for the local worker pool

Keep both tokens in Render's secret environment settings. On the connected Windows PC, store the worker token with Windows DPAPI using `scripts/store_local_secret.ps1`, then run `python -m federation_mcp.local_agent_pool`. The helper reads the token from standard input and writes only the DPAPI-protected value. Store the task token separately for `scripts/run_internal_e2e.py`, which sends an authorized synthetic test through the live gateway and reports whether all 25 profiles were online, two executors exchanged results, and the independent reviewer approved. The pool reports availability without logging task prompts, outputs, or tokens.
