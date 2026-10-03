# ADR-001 — Preserve Existing Sources of Truth

Status: Accepted
Date: 2026-10-03

## Context
Creating a new copy for every agent produces divergence, unclear ownership and privacy risk.

## Decision
The collaboration repository defines operating protocols but does not become a copy of private project knowledge. Participants use the existing authorized source of truth whenever possible.

## Reasons
This reduces conflicting copies, preserves provenance and limits unnecessary disclosure.

## Consequences
Participants without access receive bounded handoffs rather than entire private stores.

## Verification
Repository protocols must not instruct agents to copy entire private vaults or project folders here.

## Revisit
Revisit if an authorized shared knowledge service becomes the designated source of truth.
