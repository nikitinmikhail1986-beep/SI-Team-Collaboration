# Gates: SI Federation internal A2A execution

OWNS: federation_mcp/**, orchestrator/tests/**, scripts/**, A2A_AGENT_CARD.json, GATES.md

Scope: safely complete and verify authenticated dispatch through two local project profiles, exchange their results, independent review, final report, and discovery of all configured profiles on the primary Render service.

- [x] G0: completion gates are structurally valid
  CHECK: node "C:/Users/Profit77/.codex/plugins/cache/claude-cowork/unlazy/2.1.0/skills/unlazy/scripts/gate-lint.mjs" GATES.md
  EXPECT: LINT OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=dc6268a47c78c122b8cbeca3a5a5e2c6bac4c5415024782f9e7adfa0eaebb994; exit=0; EXPECT=matched; output-sha256=6fc502d2b8d37f8778c8743f3b8645e83f0001af3fe988785b7cc57431453ec2; output-bytes=719; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [x] G1: local implementation tests, compilation, and local profile mappings pass
  CHECK: python scripts/verify_internal_profiles.py
  EXPECT: SI_FEDERATION_LOCAL_VALIDATION_PASSED
  EVIDENCE: automatic-evidence=v1; definition-sha256=865ea5c4bfcbc1549b11302ec1377d8f3dcf70b1ee5ed1503539318f8e67a1ab; exit=0; EXPECT=matched; output-sha256=f197254c5f145c66e7e381749ffe559816afca34cb4da2a660824ed923aa584a; output-bytes=25096; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [ ] G2: primary Render health, deployed agent card, and worker-auth boundary pass
  EVIDENCE: pending

- [ ] G3: every registered local profile reports online through primary Render
  EVIDENCE: pending

- [ ] G4: live synthetic task completes executor exchange, independent review, and final report
  EVIDENCE: pending

- [ ] G5: primary Render logs show successful live task and worker exchanges without secret or payload leakage
  EVIDENCE: pending

- [ ] G6: duplicate Render service and pre-existing original-worktree changes remain untouched
  EVIDENCE: pending
