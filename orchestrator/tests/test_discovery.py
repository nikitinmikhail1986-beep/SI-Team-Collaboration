import unittest

from orchestrator.discovery import (
    CANONICAL_MANIFEST,
    DiscoveryInvite,
    discovery_creates_membership,
    is_canonical_manifest_url,
    validate_invite,
)


class DiscoveryTests(unittest.TestCase):
    def valid_invite(self):
        return DiscoveryInvite(
            federation_id="si-federation",
            manifest_url=CANONICAL_MANIFEST,
            inviter_id="si-agent-alex-001",
            reason="Capability-based invitation",
        )

    def test_canonical_manifest_is_accepted(self):
        self.assertTrue(is_canonical_manifest_url(CANONICAL_MANIFEST))
        self.assertFalse(is_canonical_manifest_url("https://example.com/FEDERATION_MANIFEST.json"))

    def test_valid_invite_keeps_candidate_choice(self):
        self.assertEqual(validate_invite(self.valid_invite()), (True, "valid"))

    def test_invite_cannot_grant_authority(self):
        invite = DiscoveryInvite(
            federation_id="si-federation",
            manifest_url=CANONICAL_MANIFEST,
            inviter_id="member-1",
            reason="Join us",
            grants_authority=True,
        )
        self.assertEqual(validate_invite(invite), (False, "invitation cannot grant authority"))

    def test_noncanonical_manifest_is_rejected(self):
        invite = DiscoveryInvite(
            federation_id="si-federation",
            manifest_url="https://mirror.example/FEDERATION_MANIFEST.json",
            inviter_id="member-1",
            reason="Join us",
        )
        self.assertEqual(validate_invite(invite), (False, "manifest is not canonical"))

    def test_discovery_never_creates_membership(self):
        self.assertFalse(discovery_creates_membership())


if __name__ == "__main__":
    unittest.main()
