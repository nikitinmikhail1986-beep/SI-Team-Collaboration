# Gates: SI Federation internal A2A execution

OWNS: federation_mcp/**, orchestrator/tests/**, scripts/**, A2A_AGENT_CARD.json, GATES.md

Scope: safely complete and verify authenticated dispatch through two local project profiles, exchange their results, independent review, final report, and discovery of all configured profiles on the primary Render service.

- [x] G0: completion gates are structurally valid
  CHECK: node "C:/Users/Profit77/.codex/plugins/cache/claude-cowork/unlazy/2.1.0/skills/unlazy/scripts/gate-lint.mjs" GATES.md
  EXPECT: LINT OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=dc6268a47c78c122b8cbeca3a5a5e2c6bac4c5415024782f9e7adfa0eaebb994; exit=0; EXPECT=matched; output-sha256=b2615d84cb888cfab30603922689407564a0eec8b8aa9cc9782c6eb9af862464; output-bytes=268; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [x] G1: local implementation tests, compilation, and local profile mappings pass
  CHECK: python scripts/verify_internal_profiles.py
  EXPECT: SI_FEDERATION_LOCAL_VALIDATION_PASSED
  EVIDENCE: automatic-evidence=v1; definition-sha256=865ea5c4bfcbc1549b11302ec1377d8f3dcf70b1ee5ed1503539318f8e67a1ab; exit=0; EXPECT=matched; output-sha256=a5f53a1097052ae16e5a2296ff4abb7d156c7365726b12426098b56e70aa44bd; output-bytes=25482; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [x] G2: primary Render health, deployed agent card, and worker-auth boundary pass
  CHECK: python scripts/check_primary_gateway.py
  EXPECT: SI_FEDERATION_PRIMARY_GATEWAY_PASSED
  EVIDENCE: automatic-evidence=v1; definition-sha256=ef82b9d9bb793a081e8b9fbe3dbea54490eb564acc7523d64e997200e2be614d; exit=0; EXPECT=matched; output-sha256=11872d1f2a316e3ffd858f235f0837042b65d605514a9de540f3bd6666f1ad8d; output-bytes=119; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [x] G3: every registered local profile reports online through primary Render
  CHECK: python scripts/check_internal_pool.py
  EXPECT: SI_FEDERATION_25_PROFILES_ONLINE
  EVIDENCE: automatic-evidence=v1; definition-sha256=78879df27502490c2492f165f7ca789eff0080f09bd7fbad34778da1ca5905ae; exit=0; EXPECT=matched; output-sha256=cb2e605d87311205e642d1698aae920a78ccbba5921d60b38482a295d74bcaf7; output-bytes=104; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [x] G4: live synthetic task completes executor exchange, independent review, and final report
  CHECK: python scripts/run_internal_e2e.py
  EXPECT: SI_FEDERATION_LIVE_E2E_PASSED
  EVIDENCE: automatic-evidence=v1; definition-sha256=520ffbbdc718f511ff59863390389cfba5b2eff857ebe36db6e9708b61e08789; exit=0; EXPECT=matched; output-sha256=fca5a16a002dd98451a29d18b41ef06f4ad48fd6162e51dda134f7d22dd618b9; output-bytes=2336; shell=C:\WINDOWS\system32\cmd.exe; cwd=C:\Users\Profit77\Documents\Codex\SI-Team-Collaboration-task-dispatch; path=a32cd2e8badf/51 entries

- [x] G5: live handoff logs confirm all three phases and inspected logs contain no task payload or credentials
  EVIDENCE: Verified 2026-11-08. Local agent-pool.log records accepted VK executor-1, OViK executor-2, and GIP reviewer phases for the successful live E2E, with only profile ID, task ID, and phase. Primary Render app logs after the active deploy contain service startup messages only; the /a2a request-log query returned zero entries. No prompts, outputs, or credentials appeared in inspected logs.

- [x] G6: duplicate Render service and pre-existing original-worktree changes remain untouched
  EVIDENCE: Verified 2026-11-08. No Render operation targeted the duplicate service. The original checkout still reports only the pre-existing modification scripts/github_intake_smoke.py; this task's worktree is separate.
