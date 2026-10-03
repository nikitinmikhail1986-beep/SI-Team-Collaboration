# ADR-002 — Route by Capability, Not Provider Brand

Status: Accepted
Date: 2026-10-03

## Context
Participants differ in tools, context, domain roles and runtime availability. A permanent global model ranking does not reliably describe task fitness.

## Decision
Route bounded work according to required capability, actual availability, authorization and verification needs. Provider or model identity is not a tie-breaker.

## Consequences
The capability registry describes functions and evidence requirements rather than scores.

## Verification
TASK_ROUTING.md and AGENT_REGISTRY.yaml must not contain global best/worst rankings of participants.
