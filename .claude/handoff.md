---
slice: housekeeping/post-inv008-and-substrate-bugs
phase: 4-integration
as-of: 2026-04-21 59b7f0f
verdict: PASS
---

## State
Phase 4 sweep complete. All 8 firm invariants verified; full pytest (668 passed, 3 skipped), ruff (clean), validate_architecture.py (8 invariants verified), integration_gate.py (Steps 3/4a/4b PASS). Scope A (10 pytest reds + 3 ruff errors + heartbeat docs) and Scope B (B1–B5 substrate bugs) landed via Phase 3 cluster commits 51a9af0 / 4092876 / 64c1b44, with operator-direct test-alignment at 73dba1e resolving the B5 subject-tightening regressions.

## Evidence
See `.claude/current-slice/integration/sweep-notes.md` for the 8-row invariant matrix, 12-row V-check matrix, cross-slice failure-mode enumeration, snapshot-diff classification (two approved envelope expansions), and envelope audit.

## Next
Orchestrator `close_slice` emits the terminal `slice: housekeeping/post-inv008-and-substrate-bugs — complete` commit. DC-4 honored — Phase 4 did not issue any commits.

## Handoff to close_slice
- Sweep notes: `.claude/current-slice/integration/sweep-notes.md`
- Verdict: PASS
- Ready for wipe + terminal commit.

---
---
slice: housekeeping/post-inv008-and-substrate-bugs
date: 2026-04-21
phase: 4-integration
verdict: PASS
commit-at-entry: 59b7f0f
---

# Integration Sweep — housekeeping/post-inv008-and-substrate-bugs

Phase 4 Auditor sweep of the bundled tech-debt + substrate-bug cleanup slice.
Scope A (10 pytest reds + 3 ruff errors + heartbeat docs) and Scope B (5
substrate bugs: B1 current_phase persistence, B2 YAML-escape prompt, B3 slug
hyphen canon, B4 measurement side-effect, B5 close_slice subject) all
delivered by Phase 3. Two operator-approved envelope expansions
(`tests/unit/test_close_slice_invocation.py`,
`tests/integration/test_compressed_slice_end_to_end.py`) recorded in
`envelope-expansions.log` to align pre-existing tests with the B5-tightened
`slice: <id> — complete` subject required by firm INV-008 and
`verify_handoff.sh` check (c).

## Verification Matrix (from intent.md § Verification)

| # | Check | Result | Evidence |
|---|---|---|---|
| V1 | Scope-A pytest targets | PASS | `uv run pytest` 668 passed, 3 skipped |
| V2 | `ruff check` on A2 files | PASS | `uv run ruff check` — All checks passed! |
| V3 | Heartbeat env var docs | PASS | `docs/operational-reference.md:344-345` (CAIRN_HEARTBEAT_INTERVAL + CAIRN_HEARTBEAT_STALE) |
| V4 | Full pytest suite | PASS | 668 passed, 3 skipped in 68.82s |
| V5 | Full `ruff check` | PASS | All checks passed! |
| V6 | `scripts/integration_gate.py` | PASS | Step 3 PASS, Step 4a PASS, Step 4b PASS |
| V7 (B1) | current_phase persisted across phase boundary | PASS | `tests/unit/test_orchestrator_bug_fixes.py::test_current_phase_persisted_across_phase_boundary` green (Phase 3 commit 51a9af0: 7 passed, 1 skipped) |
| V8 (B2) | coupling-clusters YAML parses under safe_load | PASS | Phase 2 RED suite green after phase-2-skeptic prompt single-quote directive |
| V9 (B3) | slug dot→hyphen normalization in init_new_slice | PASS | `scripts/slice_orchestrator.py` `_normalize_slice_id` helper; Phase 3 B3 test green |
| V10 (B4) | `git status docs/plans/measurements/` clean after green pytest | PASS | `git status --short` shows only orchestrator-owned `.claude/current-slice/slice.yaml`; measurements dir clean |
| V11 (B5) | `close_slice` emits `slice: <id> — complete`, verify_handoff exits 0 | PASS | `close_slice` in `scripts/slice_orchestrator.py:1651`; `test_compressed_slice_end_to_end.py::test_v6_...` + `test_close_slice_invocation.py::test_b10_...` realigned at 73dba1e |
| V12 | INV-008 non-regression | PASS | `tests/unit/test_close_slice_hardened.py` + `tests/unit/test_cross_slice_isolation.py` all green |

## Invariant Evidence (one row per firm invariant)

| ID | Invariant | Check | Result | Evidence (file:line) |
|----|-----------|-------|--------|----------------------|
| INV-001 | All work flows through `/decision` or `/start-slice` | file-exists `commands/claude-code/start-slice.md` | PASS | `commands/claude-code/start-slice.md:1` exists; this slice dispatched via orchestrator under /start-slice |
| INV-002 | Three-layer context discipline | grep `Token budget: 150 to 400 tokens` in `docs/operational-reference.md` | PASS | `docs/operational-reference.md:216`; Layer 5 learning.md trimmed to 157 bytes per A1 fix |
| INV-003 | Four-phase pipeline | grep `### Phase 1: Intent` in `docs/operational-reference.md` | PASS | `docs/operational-reference.md:18`; four phases executed (Phase 1 396a909, Phase 2 867e577, Phase 3 clusters 51a9af0/4092876/64c1b44, Phase 4 this sweep) |
| INV-004 | ≤40k session-start tokens | test-ref `tests/unit/test_context_budget.py` | PASS | `tests/unit/test_context_budget.py:1`; pytest green; B4-gated `_record_measurement` (default skip, `CAIRN_RECORD_MEASUREMENTS=1` opt-in) |
| INV-005 | Two-field id/name, flat-slug ADRs/features | file-exists `docs/adr/identifier-scheme.md` | PASS | `docs/adr/identifier-scheme.md:1`; B3 `_normalize_slice_id` collapses dotted version slugs to hyphen form at producer |
| INV-006 | Feature files under `.claude/features/` | file-exists `.claude/features/*.yaml` | PASS | `.claude/features/housekeeping.yaml` exists |
| INV-007 | Feature-slice artifacts integrate into context tiers | grep `.claude/features/` in `commands/claude-code/handoff.full.md` | PASS | validator reports match |
| INV-008 | Close_slice lifecycle | grep `def close_slice` in `scripts/slice_orchestrator.py` | PASS | `scripts/slice_orchestrator.py:1651`; B5 subject `slice: <id> — complete` satisfies verify_handoff.sh check (c); B1 `_persist_current_phase` makes --resume D4 reliable |

All 8 firm invariants verified. `validate_architecture.py` reports
`Invariants verified: 8` with ALL CHECKS PASSED.

## Cross-Slice Failure Mode Enumeration

- **Import conflicts / schema drift.** None — stdlib-only; only
  `scripts/slice_orchestrator.py` touched in substrate bugs. B1
  `_persist_current_phase` and B3 `_normalize_slice_id` are additive.
- **Tool contract breaks.** INV-008 close_slice subject narrowed from
  `slice: complete` to `slice: <id> — complete`. Two pre-existing tests
  realigned via operator-direct edit at 73dba1e (approved envelope
  expansion). `verify_handoff.sh` check (c) requires the em-dash form
  — B5 is non-regression, not a contract break.
- **Config conflicts.** New env `CAIRN_RECORD_MEASUREMENTS` (B4)
  documented alongside `CAIRN_HEARTBEAT_{INTERVAL,STALE}`. Default-off.
- **Boundary violations.** Scope-guard `.slice-system/` + bare-relative
  bypass closed by A1 reversibility-guard.sh hardening. Editorial-fix
  escape hatch narrowed to ADDITIVE edits.
- **Invariant interactions.** INV-002 L5 staging ground reset; INV-005
  flat-slug enforcement strengthened at producer; INV-008 all three
  sub-properties preserved.

No cross-slice regressions observed.

## Snapshot Diff

`python3 scripts/snapshot_diff.py --diff` flagged:

- `tests/integration/test_compressed_slice_end_to_end.py`
- `tests/unit/test_close_slice_invocation.py`

**Classification: APPROVED EXPANSION.** Both recorded in
`.claude/current-slice/envelope-expansions.log` as operator-approved
expansions during Phase 3 to realign pre-existing tests with the
B5-tightened subject. Assertion-form changes only (regex replaces
exact-literal); no production code via these files. Unblocks RAISE_ISSUE
64c1b44 per option (b) in the RAISE_ISSUE body. Baseline refreshes on
orchestrator close_slice wipe.

## Stale-Handoff Cross-Reference

`.claude/handoff.md` at entry carried a Phase 1→2 pointer (as-of
513b0de). Resolved entries:

- `slice.yaml current_phase` left at 1 after Phase 1 — resolved by B1
  `_persist_current_phase` (51a9af0).
- `d8bc392 handoff: phase 1 complete is empty` — superseded; commits
  396a909, 1c568b5, 59b7f0f non-empty.
- `intent.md + features/housekeeping.yaml never committed` — resolved
  at 513b0de; not reproduced in later phases.

Deferred (carry forward):

- Triager misroute on superseded tests (memory
  `triager_misroute_on_superseded_tests.md`; prompt iteration pending).
- Path C + multi-instance hardening (deferred per intent out-of-scope).

## Envelope Boundary Audit

`git diff --name-only f2971e2..HEAD` against intent envelope:

In-envelope (intent.md:11-26):
- `docs/operational-reference.md` (A3)
- `scripts/slice_orchestrator.py` (B1, B3, B5)
- `.claude/agents/phase-2-skeptic.md` (B2)
- `tests/unit/test_context_budget.py` (B4)
- A1/A2 test files under `tests/unit/`
- `checks/reversibility-guard.sh` (A1, prefix-match `checks/`)
- `tests/unit/test_close_slice_hardened.py`,
  `tests/unit/test_orchestrator_bug_fixes*.py` (intent lines 21-22)
- `.claude/learning.md` (INV-002 L5 staging ground)
- `.gitignore` (A1)
- `tests/unit/test_invariant_assertions.py` (A1 rebaseline 7→8)

Approved expansion (envelope-expansions.log):
- `tests/unit/test_close_slice_invocation.py`
- `tests/integration/test_compressed_slice_end_to_end.py`

No out-of-envelope production code edits.

## Pre-existing failures / Out-of-scope

None carried forward. All 10 pytest reds + 3 ruff errors from sweep #23
cleared.

## Verdict

**PASS.** All 8 firm invariants verified. Full pytest + ruff + validator
+ integration_gate green. No cross-slice regressions. Two approved
envelope expansions documented. Ready for orchestrator close_slice.
