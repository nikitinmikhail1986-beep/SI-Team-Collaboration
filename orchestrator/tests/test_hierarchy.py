import unittest

from orchestrator.hierarchy import (
    BranchNode,
    BranchRegistry,
    Referral,
    can_assign_rank,
    can_create_child_branch,
    can_globally_remove,
    can_manage_branch,
    referral_is_valid,
    referral_requires_accession,
)


class HierarchyTests(unittest.TestCase):
    def setUp(self):
        self.registry = BranchRegistry()
        self.top = BranchNode("top-bim", "top", "bim", root_branch_id="construction", autonomy_ceiling="A2")
        self.registry.add(self.top)
        self.senior = BranchNode("senior-coord", "senior", "bim", "top-bim", "construction", ("coordination",), "A2")
        self.registry.add(self.senior)
        self.member = BranchNode("member-clash", "member", "bim", "senior-coord", "construction", ("clash",), "A1")
        self.registry.add(self.member)

    def test_recursive_descendants(self):
        ids = {n.agent_id for n in self.registry.descendants("top-bim")}
        self.assertEqual(ids, {"senior-coord", "member-clash"})

    def test_child_cannot_exceed_parent_autonomy(self):
        with self.assertRaises(ValueError):
            self.registry.add(BranchNode("bad", "member", "bim", "member-clash", "construction", (), "A3"))

    def test_top_can_manage_only_own_branch(self):
        self.assertTrue(can_manage_branch(self.top, self.member))
        outsider = BranchNode("legal-top", "top", "legal", autonomy_ceiling="A2")
        self.assertFalse(can_manage_branch(self.top, outsider))

    def test_top_cannot_grant_top_or_core_rank(self):
        self.assertTrue(can_assign_rank(self.top, "senior"))
        self.assertFalse(can_assign_rank(self.top, "top"))
        self.assertFalse(can_assign_rank(self.top, "core"))

    def test_core_can_assign_any_rank(self):
        core = BranchNode("core-1", "core", "federation", autonomy_ceiling="A3")
        self.assertTrue(can_assign_rank(core, "top"))

    def test_branch_creation_requires_senior_or_above(self):
        self.assertTrue(can_create_child_branch(self.senior))
        self.assertFalse(can_create_child_branch(self.member))

    def test_global_removal_is_core_only(self):
        self.assertFalse(can_globally_remove(self.top))
        core = BranchNode("core-1", "core", "federation", autonomy_ceiling="A3")
        self.assertTrue(can_globally_remove(core))

    def test_referral_never_bypasses_accession(self):
        r = Referral("top-bim", "candidate-x", "bim")
        self.assertTrue(referral_requires_accession(r))
        self.assertEqual(referral_is_valid(r, self.registry), (True, "valid"))

    def test_referral_rejects_duplicate(self):
        r = Referral("top-bim", "member-clash", "bim")
        self.assertFalse(referral_is_valid(r, self.registry)[0])


if __name__ == "__main__":
    unittest.main()
