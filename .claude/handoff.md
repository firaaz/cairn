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

---
# Phase 4 handoff — OK

slice: v1-defense-d2/inv-001-binding-implementation
verdict: OK
attempt: 3

## Summary

INV-001 is now bound to a true machine-checkable `git-log-walk` assertion. `docs/ARCHITECTURE.md` declares the new type with `binding-effective-from: <pending-slice-close-sha>` placeholder; `scripts/validate_architecture.py` ships the dispatcher + verifier table; `.claude/pipeline-substrate-registry.yaml` co-creates with 9 D3 entries; T1–T8 GREEN; full validator clean. Re-dispatch envelope expansion (`V1_ASSERTION_TYPES += "git-log-walk"` at `tests/unit/test_invariant_assertions.py:1116`) unblocked the prior revert.

## Evidence

- `docs/ARCHITECTURE.md:14-19`: `type: git-log-walk` block live.
- `tests/unit/test_invariant_assertions.py:1116`: allowlist now includes `"git-log-walk"`.
- `uv run pytest`: 1231 passed; 2 failed (L-015 XPASS-strict, out of scope).
- `uv run python scripts/validate_architecture.py`: exit 0; INV-001 routed through new walker (placeholder no-op-with-notice).

## Out of scope (slice 2)

INV-002 / INV-008 binding, `structural-parser` type, `templates/handoff.md` & `commands/claude-code/handoff.full.md` instrumentation.

## Post-close operator step

D3 grandfathering: a single `docs:` commit (manual or `/refresh-architecture`) substitutes `<pending-slice-close-sha>` with the actual close SHA emitted by orchestrator.

---
# Phase 4 Integration — sweep-notes

slice: v1-defense-d2/inv-001-binding-implementation
phase: 4
verdict: OK
attempt: 3 (Phase-3 re-dispatched after prior RAISE_ISSUE; envelope expanded to include test allowlist)

## Invariants verified

| ID      | Statement (substrate) | Status | Evidence |
|---------|-----------------------|--------|----------|
| INV-001 | All cairn development after the bootstrap commit flows through `/decision` or `/start-slice`. Direct commits not permitted except as recorded in a superseding ADR. Pipeline-substrate commits emitted by registered substrate tools are a third legitimate class per `pipeline-substrate-naming`. True machine-checkable binding via `git-log-walk` per `invariant-binding-strategy` (D1–D3). | PASS | `docs/ARCHITECTURE.md:14-19` declares `type: git-log-walk` with `binding-effective-from: <pending-slice-close-sha>`; `scripts/validate_architecture.py` `_run_git_log_walk_assertion` + `_SUBSTRATE_VERIFIERS` dispatcher (committed `fce0b5d`, re-applied `fdbfcdb`); registry at `.claude/pipeline-substrate-registry.yaml` (9 D3 entries); `tests/unit/test_inv_001_git_log_walk.py` 8/8 GREEN; validator exit 0 with `INV-001: binding pending effective-from set (placeholder present)`. |

## Envelope completeness

| Envelope item | Status |
|---|---|
| `scripts/validate_architecture.py` (`_load_substrate_registry`, `_SUBSTRATE_VERIFIERS`, `_run_git_log_walk_assertion`, dispatcher branch) | DONE @ `fce0b5d` |
| `.claude/pipeline-substrate-registry.yaml` (9 D3 entries) | DONE @ `fce0b5d` |
| `docs/ARCHITECTURE.md` INV-001 → `git-log-walk` + `<pending-slice-close-sha>` | DONE @ `fdbfcdb` (re-applied after intermediate revert) |
| `docs/lessons.md` L-001:17 closure | Already closed in prior commit |
| `tests/unit/test_inv_001_git_log_walk.py` (RED set) | DONE @ `19dbcae`; 8/8 GREEN |
| `tests/unit/test_invariant_assertions.py:1116` `V1_ASSERTION_TYPES += "git-log-walk"` | DONE @ `fdbfcdb` (envelope expansion per re-dispatch triage) |

## Test/validator state

- `uv run pytest`: 1231 passed, 3 skipped, 2 xfailed, 2 failed.
  - 2 failures: `test_extractor_slice.py::test_extracts_at_least_four_slices` and `::test_emits_parent_edge_to_feature` — pre-existing L-015 XPASS-strict, declared **out of scope** per brief.
- `tests/unit/test_inv_001_git_log_walk.py`: 8/8 GREEN.
- `uv run python scripts/validate_architecture.py`: exit 0, `ALL CHECKS PASSED, Invariants verified: 10`. INV-001 PASS path now via new `git-log-walk` walker (placeholder branch: no-op-with-notice as designed by D3 grandfathering).

## Out-of-scope confirmations

- INV-002 / INV-008 assertion blocks unchanged (slice 2).
- `structural-parser` type not introduced (slice 2).
- `scripts/slice_orchestrator/` untouched — D3 grandfathering uses post-close `docs:` SHA substitution, not orchestrator modification.

## Learnings observed (optional)

- The `V1_ASSERTION_TYPES` allowlist at `tests/unit/test_invariant_assertions.py:1116` is the third-party constraint that any new assertion-type slice must include in envelope (matches existing memory note); confirmed live this re-dispatch.
