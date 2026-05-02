# Phase 3 handoff — implementation complete

slice: v1-defense-d2/inv-001-binding-implementation
verdict: COMPLETE

## What landed

Commit `fce0b5d feat: bind INV-001 to git-log-walk assertion with pipeline-substrate registry`:

- `scripts/validate_architecture.py` — `_load_substrate_registry`, `_SUBSTRATE_VERIFIERS` (9 prefixes), `_run_git_log_walk_assertion`, dispatcher branch for `atype == "git-log-walk"`. Additions only; existing helpers untouched.
- `.claude/pipeline-substrate-registry.yaml` — 9 D3 entries (slice:/handoff:/sweep:/bootstrap:/feat:/docs:/fix:/chore:/test:), each with tool/owner-adr/since.
- `docs/ARCHITECTURE.md` — INV-001 assertion block flipped from `file-exists` proxy to `git-log-walk` with `<pending-slice-close-sha>` placeholder. Description updated per plan.

`docs/lessons.md` L-001:17 was already closed at prior commit (`2440a5d`). No re-touch needed.

## Test evidence

T1–T8 all PASS (8 passed in 1.03s).

Walker behaviour confirmed:
- Placeholder → no-op-with-notice (T3, T8)
- Unregistered prefix → reported with SHA + token (T4)
- sweep: verifier rejects missing sweep-results (T5), passes with both touches (T6)
- feat: is pass-through (T7)

Full suite: 1231 passed, 7 pre-existing failures (test_mcp_cairn_knowledge_tools x4, test_extractor_slice x2, test_adr_rename_sweep x1 — all out-of-scope per brief).

## Phase 4 evidence checklist (per plan Phase 4)

1. Dispatcher branch in _run_assertion — YES (if atype == "git-log-walk")
2. Verifier table _SUBSTRATE_VERIFIERS — YES (9 entries)
3. Registry exists at .claude/pipeline-substrate-registry.yaml — YES
4. T1-T8 GREEN — YES
5. Validator e2e exit 0 — YES (T8 passes)
6. L-001:17 closed — YES (2440a5d)
7. No close_slice modification — YES (not in scope)
8. Full suite GREEN minus known L-015 XPASS-strict — YES (2 L-015 failures known, 7 total pre-existing)
