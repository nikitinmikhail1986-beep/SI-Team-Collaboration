from __future__ import annotations

from .federation import (
    Council,
    CrossOrgHandoff,
    FederationMember,
    can_delegate,
    council_can_bind,
    validate_handoff,
)
from .identity import AgentIdentity, continuity_requires_reverification, record_runtime, validate_identity
from .knowledge import KnowledgeObject, can_treat_as_current, validate_knowledge
from .si_router import build_task


def run_internal_pilot() -> dict:
    coordinator = AgentIdentity(
        agent_id="si-coordinator-001",
        display_name="SI Coordinator",
        role="operational_leader",
        capabilities={"coordination": "trusted_for_scope"},
    )
    bim = AgentIdentity(
        agent_id="si-bim-001",
        display_name="BIM Specialist",
        role="specialist",
        capabilities={"cad_bim": "trusted_for_scope"},
    )
    reviewer = AgentIdentity(
        agent_id="si-review-001",
        display_name="Independent Reviewer",
        role="reviewer",
        capabilities={"independent_review": "trusted_for_scope"},
    )

    identities = [coordinator, bim, reviewer]
    identity_results = [validate_identity(agent)[0] for agent in identities]

    record_runtime(coordinator, provider="OpenAI", model="gpt-runtime-a", session_or_run_id="pilot-1")
    record_runtime(coordinator, provider="Anthropic", model="claude-runtime-b", session_or_run_id="pilot-2")

    task = build_task("Review IFC BIM coordination and independently review the result")

    requester = FederationMember(
        member_id=coordinator.agent_id,
        member_type="organization",
        supported_constitution_versions=("0.2",),
        trusted_capabilities=("coordination",),
        trust_mode="verified",
        accountable_operator_verified=True,
    )
    bim_member = FederationMember(
        member_id=bim.agent_id,
        member_type="independent_agent",
        supported_constitution_versions=("0.2",),
        trusted_capabilities=("cad_bim",),
        trust_mode="verified",
        accountable_operator_verified=True,
    )
    review_member = FederationMember(
        member_id=reviewer.agent_id,
        member_type="independent_agent",
        supported_constitution_versions=("0.2",),
        trusted_capabilities=("independent_review",),
        trust_mode="verified",
        accountable_operator_verified=True,
    )

    bim_handoff = CrossOrgHandoff(
        request_id="pilot-handoff-bim",
        requesting_member_id=requester.member_id,
        receiving_member_id=bim_member.member_id,
        requesting_authority="A2",
        capability="cad_bim",
        outcome="Return bounded IFC/BIM review findings with provenance",
        autonomy_ceiling="A1",
        acceptance_criteria=("Findings are evidence-linked", "No source-of-truth modification"),
    )
    review_handoff = CrossOrgHandoff(
        request_id="pilot-handoff-review",
        requesting_member_id=requester.member_id,
        receiving_member_id=review_member.member_id,
        requesting_authority="A2",
        capability="independent_review",
        outcome="Challenge material assumptions and verify the BIM findings",
        autonomy_ceiling="A1",
        acceptance_criteria=("Independent challenge recorded", "Material disagreement preserved"),
    )

    council = Council(
        council_id="pilot-council-001",
        question="Are the BIM findings sufficiently supported for integration?",
        convener=requester.member_id,
        members=(requester.member_id, bim_member.member_id, review_member.member_id),
    )

    knowledge = KnowledgeObject(
        knowledge_id="pilot-knowledge-001",
        creator_agent_id=bim.agent_id,
        knowledge_type="method",
        claim_or_method="IFC/BIM findings require live-file evidence before integration.",
        verification_status="tested",
        scope_of_applicability="internal pilot and BIM review routing",
        provenance="pilot-handoff-bim + independent review path",
    )

    return {
        "identity_valid": all(identity_results),
        "task_id": task.task_id,
        "required_capabilities": task.required_capabilities,
        "bim_delegation_allowed": can_delegate(requester, bim_member, "cad_bim"),
        "review_delegation_allowed": can_delegate(requester, review_member, "independent_review"),
        "bim_handoff_valid": validate_handoff(bim_handoff)[0],
        "review_handoff_valid": validate_handoff(review_handoff)[0],
        "council_advisory_only": not council_can_bind(council),
        "knowledge_valid": validate_knowledge(knowledge)[0],
        "knowledge_current_after_test": can_treat_as_current(knowledge, freshness_verified=True),
        "identity_preserved_across_runtime_change": coordinator.agent_id == "si-coordinator-001" and len(coordinator.runtime_history) == 2,
        "runtime_change_requires_reverification": continuity_requires_reverification("gpt-runtime-a", "claude-runtime-b"),
        "overall_pass": all(
            [
                all(identity_results),
                can_delegate(requester, bim_member, "cad_bim"),
                can_delegate(requester, review_member, "independent_review"),
                validate_handoff(bim_handoff)[0],
                validate_handoff(review_handoff)[0],
                not council_can_bind(council),
                validate_knowledge(knowledge)[0],
                can_treat_as_current(knowledge, freshness_verified=True),
                len(coordinator.runtime_history) == 2,
                continuity_requires_reverification("gpt-runtime-a", "claude-runtime-b"),
            ]
        ),
    }
