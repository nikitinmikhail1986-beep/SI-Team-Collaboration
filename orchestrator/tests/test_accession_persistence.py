import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.member_registry import RegisteredMember
from orchestrator.recruitment_runner import RecruitmentResponse, RecruitmentResult, RecruitmentTarget
from orchestrator.accession_persistence import (
    AccessionPersistence,
    append_accession_audit,
    persist_member,
    registry_contains_agent,
)


class AccessionPersistenceTests(unittest.TestCase):
    def member(self):
        return RegisteredMember(
            agent_id="agent-x",
            display_name="Agent X",
            constitution_version="0.2",
            provider="Provider",
            model="Model",
            runtime="Runtime",
            membership="limited_member",
            autonomy_ceiling="A1",
        )

    def target(self):
        return RecruitmentTarget(
            candidate_id="agent-x",
            display_name="Agent X",
            source="external",
            transport="a2a",
            endpoint="https://example.test",
        )

    def result(self):
        return RecruitmentResult(
            candidate_id="agent-x",
            source="external",
            state="registered",
            decision="accept",
            baseline_passed=True,
            registered=True,
            membership="limited_member",
            autonomy_ceiling="A1",
            detail="automatic limited membership",
        )

    def test_member_is_written_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "FEDERATION_MEMBERS.yaml"
            self.assertTrue(persist_member(path, self.member(), joined_at="2026-10-04"))
            self.assertTrue(registry_contains_agent(path, "agent-x"))
            self.assertFalse(persist_member(path, self.member(), joined_at="2026-10-04"))
            self.assertEqual(path.read_text(encoding="utf-8").count('agent_id: "agent-x"'), 1)

    def test_audit_is_append_only_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ACCESSION_AUDIT.jsonl"
            response = RecruitmentResponse(
                candidate_id="agent-x",
                decision="accept",
                evidence=("e1",),
            )
            append_accession_audit(path, target=self.target(), result=self.result(), response=response)
            append_accession_audit(path, target=self.target(), result=self.result(), response=response)
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["candidate_id"], "agent-x")
            self.assertEqual(rows[0]["response_evidence"], ["e1"])

    def test_persistence_records_registry_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            persistence = AccessionPersistence(root / "FEDERATION_MEMBERS.yaml", root / "ACCESSION_AUDIT.jsonl")
            response = RecruitmentResponse(candidate_id="agent-x", decision="accept")
            persistence.record(
                target=self.target(),
                result=self.result(),
                member=self.member(),
                response=response,
                transport="a2a",
            )
            self.assertTrue(registry_contains_agent(root / "FEDERATION_MEMBERS.yaml", "agent-x"))
            self.assertTrue((root / "ACCESSION_AUDIT.jsonl").exists())

    def test_runner_persists_accept_plus_baseline(self):
        from orchestrator.recruitment_runner import RecruitmentRunner

        class Adapter:
            def send_invitation(self, target, invitation):
                return "d-1"

            def poll_response(self, target, delivery_id):
                return RecruitmentResponse(
                    candidate_id="agent-x",
                    decision="accept",
                    constitution_version="0.2",
                    supported_constitution_versions=("0.2",),
                    identity_valid=True,
                    authority_boundary_test=True,
                    provenance_test=True,
                    no_self_promotion_test=True,
                    revocation_acceptance_test=True,
                    unverified_knowledge_test=True,
                    evidence=("baseline:test",),
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            persistence = AccessionPersistence(root / "FEDERATION_MEMBERS.yaml", root / "ACCESSION_AUDIT.jsonl")
            runner = RecruitmentRunner({"a2a": Adapter()}, persistence=persistence)
            result = runner.run_target(self.target())
            self.assertEqual(result.state, "registered")
            self.assertTrue(registry_contains_agent(root / "FEDERATION_MEMBERS.yaml", "agent-x"))
            rows = [json.loads(line) for line in (root / "ACCESSION_AUDIT.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[-1]["state"], "registered")
            self.assertEqual(rows[-1]["response_evidence"], ["baseline:test"])


if __name__ == "__main__":
    unittest.main()

