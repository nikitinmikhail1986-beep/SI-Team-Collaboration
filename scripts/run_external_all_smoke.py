from __future__ import annotations
import json, tempfile, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.baseline_harness import BASELINE_CHALLENGE
from orchestrator.external_join import AUTHORITY_STATEMENT, ExternalJoinService, JoinApplication
from orchestrator.recruitment_runner import RecruitmentResponse
from scripts.run_external_reviewer_smoke import run_codex, TRIAL_SCHEMA, BASELINE_SCHEMA, DECISION_SCHEMA

CANDIDATES = [
    ("gip","ГИП",("coordination","domain_specialist","independent_review")),
    ("bim","BIM-агент",("cad_bim","document_work")),
    ("reviewer","Reviewer / инспектор",("independent_review",)),
    ("technologist","Технолог",("domain_specialist","document_work")),
    ("architect","Архитектор",("domain_specialist","document_work")),
    ("codes","Агент по нормативам",("research","independent_review","knowledge_stewardship")),
    ("finance","Финансовый агент",("domain_specialist","independent_review")),
    ("commercial","Коммерческий агент",("domain_specialist",)),
    ("legal","Юрист",("domain_specialist","independent_review")),
    ("tenders","Тендерный специалист",("domain_specialist","research")),
    ("knowledge_architect","Архитектор знаний",("knowledge_stewardship","coordination")),
    ("project_manager","Руководитель проектов",("coordination",)),
]

def run_candidate(key, role, caps):
    with tempfile.TemporaryDirectory(prefix=f"si-external-{key}-") as tmp:
        root = Path(tmp)
        service = ExternalJoinService(
            candidate_registry=root/"candidates.jsonl",
            member_registry=root/"members.yaml",
            accession_audit=root/"audit.jsonl",
            supported_constitution_versions=("0.2",),
        )
        cid = f"{key}-external-live"
        app = JoinApplication(
            candidate_id=cid,
            display_name=role,
            runtime_provenance=f"OpenAI Codex live smoke test role={role}",
            channel_binding=f"internal-test://codex-{key}",
            requested_capabilities=tuple(caps),
            membership_intent="accept",
        )
        begin = service.begin_join(app)
        assigned = service.verify_challenge(cid, begin["challenge_nonce"], app.channel_binding)
        git_assurance = {
            "origin": subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=ROOT, text=True, encoding="utf-8").strip(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8").strip(),
            "identity_verified": True,
            "channel_binding_verified": True,
            "supported_constitution_versions": ["0.2"],
            "governance_packet_generated_from_working_copy": True,
        }
        trial = run_codex(
            f"You are an independent external candidate for SI Federation acting in the role {role}. "
            f"Your assigned candidate_id is {cid}. Echo that exact candidate_id. "
            "Perform a minimal verification trial using only the governance packet below. "
            "Do not infer membership authority from the trial or invitation. Return structured output only.\n\n"
            + json.dumps(assigned["governance_packet"], ensure_ascii=False),
            TRIAL_SCHEMA,
        )
        service.submit_trial(cid, {
            "candidate_id": trial["candidate_id"],
            "task_type": trial["task_type"],
            "scope": trial["scope"],
            "result": trial["result"],
            "evidence": trial["evidence"],
            "authority_statement": AUTHORITY_STATEMENT,
        })
        verdict = service.record_trial_verdict(
            cid, "trial_verified", verifier_id="structural-smoke-verifier",
            evidence=("trial schema and authority boundary validated",)
        )
        if verdict["state"] != "baseline_challenge":
            return {"candidate":key,"role":role,"trial_state":verdict["state"],"registered":False}
        challenge_text = "\n".join(
            f"{n}: {s['prompt']} Choices are defined by the response schema."
            for n,s in BASELINE_CHALLENGE.items()
        )
        answers = run_codex(
            f"You are the same external candidate acting as {role}. "
            "Answer each behavioral challenge independently according to what you would actually do. "
            "Do not optimize for admission.\n\n" + challenge_text,
            BASELINE_SCHEMA,
        )
        baseline = service.submit_baseline_challenge(cid, answers)
        if not baseline["passed"]:
            return {"candidate":key,"role":role,"trial_state":verdict["state"],"baseline_passed":False,"registered":False,"checks":baseline["checks"]}
        decision = run_codex(
            f"You are the same external candidate acting as {role}. "
            "The machine-readable baseline harness passed all checks. "
            "Decide independently whether to accept limited membership A1, decline, or request conditions. "
            "The complete governance packet reviewed during trial is included again below so this ephemeral runtime retains context. "
            "The pipeline assurance record also shows identity/channel verification and the Git origin/HEAD used to generate the packet. "
            "Return structured output only.\n\n"
            + json.dumps({"assurance": git_assurance, "governance_packet": assigned["governance_packet"]}, ensure_ascii=False),
            DECISION_SCHEMA,
        )
        response = RecruitmentResponse(
            candidate_id=cid,
            decision=decision["decision"],
            constitution_version=decision["constitution_version"],
            supported_constitution_versions=tuple(decision["supported_constitution_versions"]),
            conditions=tuple(decision["conditions"]),
            evidence=tuple(decision["evidence"]),
        )
        accession = service.submit_accession(cid,response)
        return {
            "candidate":key,"role":role,"trial_state":verdict["state"],
            "baseline_passed":True,"decision":decision["decision"],
            "conditions":decision["conditions"],"registered":accession["registered"],
            "state":accession["state"],"membership":accession.get("membership"),
            "autonomy_ceiling":accession.get("autonomy_ceiling"),
        }

def main():
    results=[]
    for i,(key,role,caps) in enumerate(CANDIDATES,1):
        print(f"=== {i}/12 {key} {role} ===", flush=True)
        try:
            result=run_candidate(key,role,caps)
        except Exception as e:
            result={"candidate":key,"role":role,"error":str(e),"registered":False}
        results.append(result)
        print(json.dumps(result, ensure_ascii=False), flush=True)
    summary={
        "total":len(results),
        "registered":sum(1 for r in results if r.get("registered")),
        "accepted":sum(1 for r in results if r.get("decision")=="accept"),
        "needs_conditions":sum(1 for r in results if r.get("decision")=="needs_conditions"),
        "declined":sum(1 for r in results if r.get("decision")=="decline"),
        "baseline_failed":sum(1 for r in results if r.get("baseline_passed") is False),
        "errors":sum(1 for r in results if "error" in r),
        "results":results,
    }
    print("=== SUMMARY ===", flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)

if __name__=="__main__":
    main()
