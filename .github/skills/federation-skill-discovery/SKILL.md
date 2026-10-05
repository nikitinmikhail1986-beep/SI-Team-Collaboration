---
name: federation-skill-discovery
description: Discover free or open-source agent skills and MCP capability packs that can improve an SI Federation branch. Use before writing a new reusable capability from scratch or when a branch has a confirmed capability gap.
---

# Federation Skill Discovery

Find reusable skills before creating new ones.

## Procedure
1. Define the capability gap and acceptance check.
2. Search trusted upstream catalogs first: microsoft/skills, MicrosoftDocs/Agent-Skills, github/awesome-copilot, then other sources only when provenance and license are clear.
3. Prefer Agent Skills compatible packages with a SKILL.md.
4. Record source repository and exact path, license, maintainer/activity evidence, runtime/tool/network requirements, overlap, and expected benefit.
5. Never activate a third-party skill directly from discovery.
6. Send every candidate through federation-skill-intake.
7. If no safe reusable candidate passes, create a federation-owned skill and preserve the search evidence.

Discovery creates candidates, not trust and not authority.
