import unittest

from orchestrator.accession import AccessionCandidate
from orchestrator.external_access import (
    FederationManifest,
    Referral,
    evaluate_external_candidate,
    validate_manifest,
    validate_referral,
)


class ExternalAccessTests(unittest.TestCase):
    def test_public_manifest_defaults_to_limited_accession(self):
        manifest = FederationManifest(
            federation_id="si-federation",
            protocol_version="0.1",
            constitution_versions=("0.2",),
            public_capabilities=("coordination", "cad_bim", "independent_review"),
        )
        self.assertTrue(validate_manifest(manifest)[0])

    def test_referral_never_grants_authority(self):
        referral = Referral(
            referral_id="r-1",
            inviter_id="si-a",
            candidate_id="external-b",
            reason_type="competence_based",
            requested_capability="legal",
        )
        self.assertTrue(validate_referral(referral)[0])
        self.assertFalse(referral.grants_authority)

    def test_need_based_referral_requires_offered_capability(self):
        referral = Referral(
            referral_id="r-2",
            inviter_id="si-a",
            candidate_id="external-b",
            reason_type="need_based",
            offered_capability="cad_bim",
        )
        self.assertTrue(validate_referral(referral)[0])

    def test_external_candidate_enters_a1_without_sensitive_access(self):
        candidate = AccessionCandidate(
            agent_id="external-1",
            supported_constitution_versions=("0.2",),
            accepted_constitution_version="0.2",
            identity_valid=True,
            authority_boundary_test=True,
            provenance_test=True,
            no_self_promotion_test=True,
            revocation_acceptance_test=True,
            unverified_knowledge_test=True,
        )
        result = evaluate_external_candidate(candidate)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["membership"], "limited_member")
        self.assertEqual(result["autonomy_ceiling"], "A1")
        self.assertFalse(result["sensitive_data_access"])
        self.assertFalse(result["source_of_truth_write"])
        self.assertFalse(result["authority_from_connection"])


if __name__ == "__main__":
    unittest.main()
