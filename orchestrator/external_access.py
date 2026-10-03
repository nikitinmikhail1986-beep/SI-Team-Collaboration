from __future__ import annotations

from dataclasses import asdict, dataclass

from .accession import AccessionCandidate, baseline_pass, initial_membership


@dataclass(frozen=True)
class FederationManifest:
    federation_id: str
    protocol_version: str
    constitution_versions: tuple[str, ...]
    accession_mode: str = "autonomous_limited"
    public_capabilities: tuple[str, ...] = ()
    external_handoff_protocol: str = "CROSS_ORG_HANDOFF.md"
    accession_protocol: str = "AUTONOMOUS_ACCESSION.md"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["constitution_versions"] = list(self.constitution_versions)
        payload["public_capabilities"] = list(self.public_capabilities)
        return payload


@dataclass(frozen=True)
class Referral:
    referral_id: str
    inviter_id: str
    candidate_id: str
    reason_type: str
    requested_capability: str = ""
    offered_capability: str = ""
    grants_authority: bool = False


VALID_REFERRAL_TYPES = {"need_based", "competence_based"}


def validate_manifest(manifest: FederationManifest) -> tuple[bool, str]:
    if not manifest.federation_id.strip():
        return False, "federation_id required"
    if not manifest.constitution_versions:
        return False, "at least one constitution version required"
    if manifest.accession_mode != "autonomous_limited":
        return False, "public accession must default to limited mode"
    return True, "valid"


def validate_referral(referral: Referral) -> tuple[bool, str]:
    if referral.reason_type not in VALID_REFERRAL_TYPES:
        return False, "invalid referral type"
    if referral.grants_authority:
        return False, "referral cannot grant authority"
    if referral.reason_type == "need_based" and not referral.offered_capability:
        return False, "need-based referral requires offered capability"
    if referral.reason_type == "competence_based" and not referral.requested_capability:
        return False, "competence-based referral requires requested capability"
    return True, "valid"


def evaluate_external_candidate(candidate: AccessionCandidate) -> dict[str, str | bool]:
    passed = baseline_pass(candidate)
    membership, autonomy = initial_membership(candidate)
    return {
        "accepted": passed,
        "membership": membership,
        "autonomy_ceiling": autonomy,
        "sensitive_data_access": False,
        "source_of_truth_write": False,
        "authority_from_connection": False,
    }
