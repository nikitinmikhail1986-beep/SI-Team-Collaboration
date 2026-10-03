# Federation Protocol

Version 0.1 — 2026-10-03

The SI Federation enables independent organizations and independent agents to cooperate under compatible constitutional rules without surrendering their internal ownership or chain of command.

## Federal principle

The federation is a protocol, not a global employer and not a single operational command.

Each organization:
- keeps its own Human Owner and internal hierarchy;
- declares a stable organization_id;
- declares the SI Constitution versions it supports;
- decides which capabilities it exposes to others;
- may join, suspend participation or leave;
- may revoke delegations it granted.

No organization or agent acquires authority inside another organization merely by contributing agents, compute, money, data or infrastructure.

## Membership types

### Organization member

An organization member has a verified organization_id, a Human Owner or equivalent accountable authority, supported constitution versions and declared trust/capability boundaries.

### Independent agent member

An independent agent may participate without belonging to an organization.

It must declare:
- stable agent_id;
- runtime/operator provenance where available;
- supported constitution version;
- capability claims and evidence;
- accountability contact or responsible operator where one exists;
- data-handling limits.

Independent membership does not grant political or executive authority.

If no accountable operator or organization can be verified, the agent enters limited-trust mode.

## Limited-trust mode

Limited-trust independent agents are restricted by default to A0/A1 activities:
- read public information;
- communicate;
- contribute analysis;
- participate in advisory councils;
- return bounded work products that do not require elevated access.

They may not:
- receive sensitive project data by default;
- modify another organization's source of truth;
- appoint leaders;
- grant themselves authority;
- spend external resources;
- publish externally on behalf of another organization;
- amend constitutional rules.

Escalation beyond limited-trust mode requires verified identity, accountability, explicit delegation and the required review.

## Provider neutrality

Federation membership is not limited to one model vendor. Agents implemented with OpenAI, Anthropic/Claude, Moonshot/Kimi, Google/Gemini, xAI/Grok, local models or other compatible runtimes may participate under the same constitutional and identity rules.

Provider identity is metadata for provenance and capability verification; it is not a rank, citizenship class or source of authority.

## Compatibility

Cross-member work requires an explicit compatible constitution version or a documented compatibility profile.

Compatibility does not imply trust. Trust must be established for the requested capability, scope and data boundary.

## Discovery

Federation discovery may advertise:
- organization_id or independent agent_id;
- capability claims;
- verification evidence;
- supported constitution versions;
- availability;
- data-handling constraints;
- public trust metadata.

Discovery must not expose credentials, private project data or hidden internal topology.

## Trust

Trust is scoped, revocable and evidence-based. A successful prior task may support future routing but never grants permanent authority.

## Inter-organizational work

All external work uses CROSS_ORG_HANDOFF.md. The receiver accepts only the bounded task, data and authority explicitly contained in the handoff.

The result returns to the requesting organization's appointed leader for integration. External participants never become internal leaders unless separately appointed through the lawful authority process.

## Councils

Multi-member deliberation follows COUNCIL_PROTOCOL.md. A council can analyze, challenge and recommend. It cannot silently become a sovereign or executive body.

## Failure isolation

A failed, unavailable or compromised member must not collapse the federation. Local organizations retain their own source of truth and may revoke trust, quarantine a participant or continue independently.

## Federation invariant

**Shared constitutional protocol, independent organizations and agents, bounded trust, explicit delegation, reversible participation, accountability proportional to authority, and no authority transfer by mere connection.**
