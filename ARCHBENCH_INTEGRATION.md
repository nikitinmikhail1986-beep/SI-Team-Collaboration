# ArchBench federation integration — staged pilot

This is a **non-admitting pilot**, not an active automated recruitment or membership workflow.

## Public task distribution
Run `python scripts/archbench_public_bundle.py --task T01 --output T01_public.zip` on the trusted evaluator host. Distribute only the resulting archive. Never commit or upload `archbench_federation/tasks/*/private/`, reference solutions, or grading code to a public repository or external runner.

## Local verification
On a trusted evaluator host with the private benchmark copy installed, run:
`python scripts/archbench_trial.py --candidate mock-agent-001 --task T01 --solution solution.json --output receipt.json`

The adapter records results but **does not grant membership**. Keep the evaluator isolated from untrusted agent code; submissions are data only. Validate and rate-limit uploads before evaluating.

## Next required gates
1. Separate private benchmark from public GitHub and public CI runners.
2. Authenticate candidate identity and bind submitted solution to issue, task, nonce and deadline.
3. Create an isolated submission channel and limit file size, type, and frequency.
4. Test negative cases, replay attacks, concurrent submissions, and recovery.
5. Only then wire verified results to the existing federation accession process with auditable A1 authorization.

No automatic enrollment or external task invitations are enabled by this change.
