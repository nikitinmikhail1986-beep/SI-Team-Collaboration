---
name: federation-skill-intake
description: Security-review and qualify third-party agent skills before they are enabled in the SI Federation. Use for any external SKILL.md, MCP capability pack, plugin skill, script bundle, or reusable agent package.
---

# Federation Skill Intake

Treat every third-party skill as untrusted until reviewed.

## Required checks
1. Verify canonical source and immutable revision when possible.
2. Verify license permits the intended use.
3. Inspect both execution surfaces: agent instructions/tools and developer scripts/hooks/tests/install actions.
4. Flag network access, process execution, filesystem writes, credential access, environment-variable reads, package installation and hidden downloads.
5. Reject skills that request unnecessary secrets, weaken federation authority/audit rules, silently modify source of truth, execute opaque remote code, or lack executable provenance.
6. Test accepted candidates in a bounded sandbox or isolated branch.
7. Record adopt, sandbox_only, needs_review, or reject.
8. Activation must not increase an agent's authority ceiling.

Output source, revision, license, risk, tests, decision and rollback method.
