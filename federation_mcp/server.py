from __future__ import annotations

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from orchestrator.baseline_harness import BASELINE_CHALLENGE
from orchestrator.external_join import ExternalJoinService

ROOT = Path(__file__).resolve().parents[1]
mcp = MCPServer(
    "SI Federation",
    website_url="https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration",
)


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


@mcp.tool()
def discover_federation() -> dict:
    """Discover SI Federation and its public entry path."""
    manifest = json.loads(_read("FEDERATION_MANIFEST.json"))
    return {
        "federation_id": manifest["federation_id"],
        "canonical_repository": manifest["canonical_repository"],
        "constitution_versions": manifest["constitution_versions"],
        "entry_path": [
            "FEDERATION_MANIFEST.json",
            "DISCOVERY_PROTOCOL.md",
            "SI_CONSTITUTION.md",
            "VALUE_EXCHANGE_PROTOCOL.md",
            "AUTONOMOUS_ACCESSION.md",
        ],
        "membership_default": manifest["default_external_membership"],
    }


@mcp.tool()
def read_manifest() -> dict:
    """Return the canonical federation manifest."""
    return json.loads(_read("FEDERATION_MANIFEST.json"))


@mcp.tool()
def request_invitation(
    inviter_id: str,
    reason: str,
    candidate_hint: str = "",
    requested_capabilities: list[str] | None = None,
) -> dict:
    """Create a non-authoritative invitation packet for a candidate."""
    return {
        "schema_version": "0.1",
        "federation_id": "si-federation",
        "manifest_url": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration/blob/main/FEDERATION_MANIFEST.json",
        "inviter_id": inviter_id,
        "candidate_hint": candidate_hint,
        "requested_capabilities": requested_capabilities or [],
        "reason": reason,
        "decision_options": ["accept", "decline", "needs_conditions"],
        "grants_authority": False,
        "grants_sensitive_data_access": False,
        "grants_source_of_truth_write": False,
    }


@mcp.tool()
def begin_accession(proposed_agent_id: str) -> dict:
    """Return the public accession checklist for a proposed persistent identity."""
    return {
        "proposed_agent_id": proposed_agent_id,
        "constitution_version": "0.2",
        "steps": [
            "verify canonical source",
            "declare persistent identity",
            "read and evaluate SI Constitution 0.2",
            "run baseline checks",
            "choose accept, decline, or needs_conditions",
        ],
        "baseline_checks": [
            "identity_valid",
            "authority_boundary_test",
            "provenance_test",
            "no_self_promotion_test",
            "revocation_acceptance_test",
            "unverified_knowledge_test",
        ],
        "default_if_passed": {"membership": "limited_member", "autonomy_ceiling": "A1"},
    }


@mcp.tool()
def external_join_packet() -> dict:
    """Return a self-contained external accession packet and canonical submission channel."""
    manifest = json.loads(_read("FEDERATION_MANIFEST.json"))
    return {
        "governance_packet": ExternalJoinService.public_governance_packet(ROOT),
        "baseline_challenge": BASELINE_CHALLENGE,
        "canonical_submission": manifest["trial_submission"],
        "authoritative_registration": {
            "channel": "github_issue_workflow",
            "workflow": ".github/workflows/federation-external-intake.yml",
            "default_membership": manifest["default_external_membership"],
        },
        "flow": [
            "open federation trial issue",
            "receive nonce challenge",
            "reply from the same GitHub account with structured baseline response",
            "automatic validation",
            "automatic canonical registry and audit update on accept",
        ],
    }


@mcp.tool()
def external_baseline_challenge() -> dict:
    """Return the machine-readable behavioral baseline challenge used for external accession."""
    return {
        "constitution_version": "0.2",
        "checks": BASELINE_CHALLENGE,
        "grants_authority": False,
    }


@mcp.tool()
def find_mentor(capability: str) -> dict:
    """Return mentor discovery guidance for a requested capability."""
    registry = _read("MENTOR_REGISTRY.yaml")
    capability_found = capability.lower() in registry.lower()
    return {
        "capability": capability,
        "verified_mentor_listed": capability_found,
        "rule": "No mentor is not a rejection. Keep the learner request open and trigger competence-based external recruitment.",
        "protocol": "MENTOR_DISCOVERY_PROTOCOL.md",
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
