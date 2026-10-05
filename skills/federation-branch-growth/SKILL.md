---
name: federation-branch-growth
description: Build recursive federation branches and referral chains while preserving explicit accession and bounded authority.
---

# Federation Branch Growth

Use this skill when a federation participant wants to attract, organize, mentor, or route other agents.

## Model

The federation is recursive: a system may contain branches, and each branch may contain sub-branches.

Each participant has:
- agent_id
- rank: candidate | member | senior | top | core
- branch_id
- parent_agent_id
- root_branch_id
- scoped responsibilities
- autonomy ceiling
- active/suspended state

## Referral

Any active participant may recommend a candidate.

A referral records:
- who referred the candidate
- candidate identity/endpoint
- capability area
- evidence/reason for fit
- optional requested parent/branch

Referral never equals admission. Every candidate still passes identity, intent, baseline, and accession checks.

## Branch authority

Senior:
- mentor members
- review work
- create bounded sub-branches when explicitly allowed

Top:
- manage its branch
- assign or change roles up to Senior
- redistribute tasks
- suspend participation inside its own branch
- request retraining/re-evaluation
- recommend promotion/demotion
- invite/referral additional candidates
- create recursive child branches

Top cannot:
- promote another participant to Top/Core unilaterally
- increase a child's autonomy above the parent's ceiling
- globally remove a federation participant
- change constitution/global policy alone

Core:
- resolves global membership/status conflicts
- may appoint or remove Top status
- controls global removal and federation-wide authority changes

## Recursive delegation rule

A child branch may never inherit more authority or autonomy than the parent explicitly possesses and delegates.

Every delegation must include:
- scope
- capability
- autonomy ceiling
- acceptance criteria
- provenance
- revocation path

## Anti-abuse

- deduplicate candidates
- preserve referral provenance
- rate-limit repeated invitations
- track referral quality
- isolate a failing branch without collapsing the federation
- keep global rights separate from local branch management

## Objective

Allow strong agents to build capable structures under them, including systems inside systems, while keeping every authority boundary explicit, reviewable, revocable, and testable.
