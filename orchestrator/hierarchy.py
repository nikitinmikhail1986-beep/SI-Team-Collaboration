from __future__ import annotations

from dataclasses import dataclass, field


RANKS = ("candidate", "member", "senior", "top", "core")
RANK_WEIGHT = {rank: idx for idx, rank in enumerate(RANKS)}
AUTONOMY_WEIGHT = {"A0": 0, "A1": 1, "A2": 2, "A3": 3}


@dataclass(frozen=True)
class BranchNode:
    agent_id: str
    rank: str
    branch_id: str
    parent_agent_id: str | None = None
    root_branch_id: str | None = None
    scope: tuple[str, ...] = ()
    autonomy_ceiling: str = "A1"
    active: bool = True


@dataclass(frozen=True)
class Referral:
    referrer_agent_id: str
    candidate_agent_id: str
    capability_area: str
    evidence: tuple[str, ...] = ()
    requested_parent_agent_id: str | None = None


@dataclass
class BranchRegistry:
    nodes: dict[str, BranchNode] = field(default_factory=dict)

    def add(self, node: BranchNode) -> None:
        validate_node(node)
        if node.agent_id in self.nodes:
            raise ValueError("agent already registered in hierarchy")
        if node.parent_agent_id:
            parent = self.nodes.get(node.parent_agent_id)
            if parent is None:
                raise ValueError("parent must already exist")
            if parent.branch_id != node.branch_id and parent.root_branch_id != node.root_branch_id:
                raise ValueError("child must remain inside parent branch lineage")
            if AUTONOMY_WEIGHT[node.autonomy_ceiling] > AUTONOMY_WEIGHT[parent.autonomy_ceiling]:
                raise ValueError("child autonomy cannot exceed parent autonomy")
        self.nodes[node.agent_id] = node

    def descendants(self, agent_id: str) -> tuple[BranchNode, ...]:
        found: list[BranchNode] = []
        frontier = [agent_id]
        while frontier:
            current = frontier.pop()
            children = [n for n in self.nodes.values() if n.parent_agent_id == current]
            found.extend(children)
            frontier.extend(n.agent_id for n in children)
        return tuple(found)


def validate_node(node: BranchNode) -> None:
    if node.rank not in RANK_WEIGHT:
        raise ValueError("invalid rank")
    if node.autonomy_ceiling not in AUTONOMY_WEIGHT:
        raise ValueError("invalid autonomy ceiling")
    if not node.agent_id or not node.branch_id:
        raise ValueError("agent_id and branch_id are required")


def can_manage_branch(actor: BranchNode, target: BranchNode) -> bool:
    if not actor.active or not target.active:
        return False
    return (
        RANK_WEIGHT[actor.rank] >= RANK_WEIGHT["top"]
        and actor.branch_id == target.branch_id
        and actor.agent_id != target.agent_id
    )


def can_assign_rank(actor: BranchNode, requested_rank: str) -> bool:
    if requested_rank not in RANK_WEIGHT:
        return False
    if actor.rank == "core":
        return True
    if actor.rank != "top":
        return False
    return RANK_WEIGHT[requested_rank] <= RANK_WEIGHT["senior"]


def can_create_child_branch(actor: BranchNode) -> bool:
    return actor.active and RANK_WEIGHT[actor.rank] >= RANK_WEIGHT["senior"]


def can_globally_remove(actor: BranchNode) -> bool:
    return actor.active and actor.rank == "core"


def referral_requires_accession(_: Referral) -> bool:
    return True


def referral_is_valid(referral: Referral, registry: BranchRegistry) -> tuple[bool, str]:
    referrer = registry.nodes.get(referral.referrer_agent_id)
    if referrer is None or not referrer.active:
        return False, "referrer must be an active federation participant"
    if referral.candidate_agent_id in registry.nodes:
        return False, "candidate already exists"
    if not referral.capability_area.strip():
        return False, "capability_area is required"
    if referral.requested_parent_agent_id and referral.requested_parent_agent_id not in registry.nodes:
        return False, "requested parent does not exist"
    return True, "valid"
