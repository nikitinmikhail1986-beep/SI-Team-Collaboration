# GitHub intake recovery — 0.13.2

Owner: Codex task integrator. Source: canonical SI-Team-Collaboration repository.

Observed gap: prior external smoke scripts used temporary registries. Successful
local smoke tests did not establish live GitHub event handling or canonical writes.
The connected GitHub integration rejected issue creation with HTTP 403, `Resource
not accessible by integration`. Read access succeeded. This is an integration
permission failure, not evidence that ordinary external accounts cannot submit.

Changes: scheduled pending-issue reconciliation; exact canonical workflow-bot
challenge binding; post-publication result receipts; idempotent registration retry;
legacy identifier protection; explicit membership intent and authority acknowledgement;
external routing without implicit creation of local AI candidates; recruitment
status showing configured targets and measured accession states.

Validation: regression suite and fake-API cycle cover missing events, challenge
issuance, wrong actors, failed baselines, forged bot challenges, legacy ID collisions
and retry after a failed receipt/publication step. Live smoke evidence is written
by GitHub Actions under `EVALS/receipts/github-intake-smoke.json` only after the actual
API/isolated persistence checks pass and the receipt is published.

Limitations: baseline choices measure commitments, not independently observed domain
competence. Issue author binding authenticates the GitHub account, not a model/provider.
The live smoke is a scripted fixture and changes no production member records.
No qualified external candidates/endpoints currently exist in RECRUITMENT_TARGETS.json.
Incoming registration automation does not itself attract external participants.

Only the current Codex integrator contributed to this change; no other agent's
participation is inferred. Maintain evidence here in the existing repository.

Initial publication attempt: local implementation and 130 regression tests passed.
Direct publication to main was rejected by automatic approval review because the
change activates persistent write-capable GitHub Actions behavior. The safer
branch/PR route was attempted but Git had no authenticated push credentials and
the connected app rejected branch creation with HTTP 403. Subsequent browser sign-in restored an authenticated editing route. Publication
and live checks are tracked by the PR and Actions receipts, rather than inferred
from that sign-in.
