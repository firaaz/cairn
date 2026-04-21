---
slice: housekeeping/inv004-rebaseline-cc-2.1.116
phase: 4-integration
date: 2026-04-21
verdict: PASS
---

# Phase 4 -> close_slice handoff

## What landed
- `a2e6d2d` raised `BUDGET_HARD` 30000->40000 + `BUDGET_ASPIRATIONAL` 25000->33000 in `tests/unit/test_context_budget.py`; regenerated `docs/plans/measurements/2026-04-12-slice-003.txt` (CC 2.1.116, turn-1 30335, both budgets PASS).
- `012db32` amended `docs/ARCHITECTURE.md:41` to cite <=40,000 + the CC 2.1.116 re-baseline sentence; updated invariant-check description to "machine-checks the 40k token budget".
- `0475a05` Phase 3 handoff.

## Audit result
PASS. Evidence in `.claude/current-slice/integration/sweep-notes.md`:
- 5/5 envelope tests GREEN
- `validate_architecture.py` exit 0 (8 invariants verified)
- `integration_gate.py` Step 3 PASS on INV-004
- Net suite delta: -1 red vs sweep #22 (INV-004 turn-1 cleared)
- Zero new reds; zero out-of-envelope writes; working tree clean

## What close_slice needs
- Terminal `slice: complete` commit (DC-4: Phase 4 does not commit).
- No ADR firmness flips (none touched).
- No envelope mutations pending.

## Carryover -> next slice
`housekeeping/post-inv008-tech-debt`:
- 10 inherited pytest reds (sweep #22 catalogue, INV-004 turn-1 now cleared)
- 3 ruff errors (2x E741 + 1x F841)
- Heartbeat env var docs (`docs/operational-reference.md:339-344`)
- INV-008 fallout: `test_invariant_assertions.py` Slice011AssertionCoverage tests need bumping from 7->8 invariants

---
# housekeeping/inv004-rebaseline-cc-2.1.116 — Phase 4 Integration Sweep Notes

**Slice**: housekeeping/inv004-rebaseline-cc-2.1.116
**Phase**: 4 (Integration)
**Role**: Auditor
**Date**: 2026-04-21
**Primary skill**: `superpowers:verification-before-completion` — file:line evidence backs every PASS/FAIL claim below.
**Builder commits under audit**: `a2e6d2d` (envelope contract), `012db32` (doc contract)
**Phase 3 handoff**: `0475a05`
**Branch**: `feature/compression`

## Verdict

**PASS**. INV-004 is GREEN under the new 40k ceiling on CC 2.1.116. All five envelope tests pass; validator exits 0; integration_gate Step 3 (invariant check) PASS. Full pytest still has 10 inherited reds — all classified out-of-scope per intent.md and queued for `housekeeping/post-inv008-tech-debt`. Net suite delta: -1 red (the prior INV-004 turn-1 over-budget red is cleared).

## Invariant evidence (mandatory row per declared invariant)

Declared invariants (intent.md frontmatter `invariants-touched`): **[INV-004]**.

| Invariant | Result | Evidence (file:line) |
|---|---|---|
| INV-004 - session-start context <=40,000 turn-1 tokens (CC 2.1.116 re-baseline) | **PASS** | `tests/unit/test_context_budget.py` 5/5 GREEN; `docs/ARCHITECTURE.md:41` (paragraph cites <=40,000 + both provenance sentences); `docs/ARCHITECTURE.md:43-47` (invariant-check block: "machine-checks the 40k token budget"); `docs/plans/measurements/2026-04-12-slice-003.txt:1-6` (CC 2.1.116, turn-1 30335, Hard budget (40000): PASS, Aspirational (33000): PASS); `scripts/integration_gate.py` Step 3 exits 0 |

## Runnable checks

### Envelope pytest (intent Verification item 1)

```
$ uv run pytest tests/unit/test_context_budget.py -v
============================== 5 passed in 9.34s ===============================
```
- `test_inv004_turn1_token_budget` PASS
- `test_inv004_architecture_rebaselined` PASS
- `test_inv004_invariant_check_block_description_rebaselined` PASS
- `test_inv004_turn1_token_budget_docstring_rebaselined` PASS
- `test_inv004_regression_guards_preserved` PASS

### Architecture validator (intent Verification item 4)

```
$ uv run python scripts/validate_architecture.py
ALL CHECKS PASSED
  Invariants verified: 8
  ADR files checked: 14
```
Exit 0. INV-004 declaration at `docs/ARCHITECTURE.md:41` resolves cleanly; 8 invariants intact (INV-001..INV-008 - INV-008 added at slice 3 close `e025714`).

### Measurement artifact (intent Verification item 2)

```
$ cat docs/plans/measurements/2026-04-12-slice-003.txt
CC version: 2.1.116 (Claude Code)
Turn-1 tokens: 30335
D1 baseline: 27314
Delta: +3021 (+11.1%)
Hard budget (40000): PASS
Aspirational (33000): PASS
```
- Line 1: CC 2.1.116 OK
- Line 5: `Hard budget (40000): PASS` OK
- Line 6: `Aspirational (33000): PASS` OK (no stale `(25000)` / `(20000)` text)
- 30335 turn-1 sits 9665 tokens (24.2%) below the 40k ceiling - restores the comparable headroom convention from the prior re-baseline (22->30 = +36% headroom; 30->40 = +33% headroom)

### ARCHITECTURE.md INV-004 paragraph (intent Verification item 5)

- `docs/ARCHITECTURE.md:41` contains literal "<=40,000 total tokens" OK
- Banished literals: `<=30,000`, `<=22,000`, `30k token budget` not present anywhere in ARCHITECTURE.md OK
- Both provenance sentences present: `housekeeping/inv004-rebaseline` (CC 2.1.110, 2026-04-16) and `housekeeping/inv004-rebaseline-cc-2.1.116` (CC 2.1.116, 2026-04-21) OK
- `docs/ARCHITECTURE.md:46`: invariant-check description reads `"machine-checks the 40k token budget"` OK

### Full pytest suite (intent Verification item 3)

```
$ uv run pytest tests/
============= 10 failed, 650 passed, 3 skipped in 65.48s (0:01:05) =============
```

**Net delta vs. sweep #22 baseline: -1 red (INV-004 turn-1 cleared).** Sweep #22 catalogued 11 reds; 10 remain. All 10 are pre-existing and classified out-of-scope per intent.md (queued for `housekeeping/post-inv008-tech-debt`):

| Test | Status | Classification |
|---|---|---|
| `test_context_discipline_protocol.py::test_v5_learning_staging_ground_exists_and_is_minimal` | RED (pre-existing) | learning.md staging-ground over 500 bytes - sweep #22 |
| `test_hook_relpath_bypass.py::TestV1BareRelativeFlatSlugBlocked::test_edit_body_bare_relative_flat_slug_blocked` | RED (pre-existing) | hook-tolerance flat-slug coverage - sweep #22 |
| `test_hook_relpath_bypass.py::TestV2BareRelativeLegacyBlocked::test_edit_body_bare_relative_legacy_blocked` | RED (pre-existing) | hook-tolerance flat-slug coverage - sweep #22 |
| `test_hook_relpath_bypass.py::TestV3SliceSystemPrefixedDeniesConsistently::test_edit_body_slice_system_flat_slug_blocked` | RED (pre-existing) | hook-tolerance flat-slug coverage - sweep #22 |
| `test_hook_tolerance.py::TestV3FrontmatterEditBothForms::test_edit_body_flat_slug_blocked` | RED (pre-existing) | hook-tolerance flat-slug coverage - sweep #22 |
| `test_hook_tolerance.py::TestV3FrontmatterEditBothForms::test_edit_body_flat_slug_emits_message` | RED (pre-existing) | hook-tolerance flat-slug coverage - sweep #22 |
| `test_hook_tolerance.py::TestV3FrontmatterEditBothForms::test_edit_body_legacy_blocked` | RED (pre-existing) | hook-tolerance flat-slug coverage - sweep #22 |
| `test_housekeeping_post_slice_a_tidy.py::test_item_b_handoff_not_tracked` | RED (pre-existing) | post-slice-a tidy item B - sweep #22 |
| `test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks` | RED (pre-existing) | INV-008 added at slice 3 close `e025714`; test predates and expects 7 invariants - sweep #22 |
| `test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged` | RED (pre-existing) | INV-008 added at slice 3 close `e025714`; test predates and expects 7 invariants - sweep #22 |

No new reds introduced by this slice. The single envelope-test red present at sweep #22 (the INV-004 turn-1 over-budget assertion) is cleared by the re-baseline as designed.

### Integration gate (intent Verification item 7)

```
$ uv run python scripts/integration_gate.py
... Step 3 (invariant check): PASS
```
Step 1 (full pytest) fails on the 10 inherited reds above; Step 3 (invariant check) PASS on INV-004. Overall gate non-green only on pre-existing inherited items, exactly as specified by intent.

### Working tree (intent Verification item 6)

```
$ git status
On branch feature/compression
nothing to commit, working tree clean
```
No residue. Phase 3 commits already landed: `a2e6d2d` (envelope), `012db32` (doc contract), `0475a05` (handoff).

## Boundary respect

Files touched by Phase 3 commits (`git show --stat a2e6d2d 012db32`):
- `tests/unit/test_context_budget.py` OK (in envelope)
- `docs/plans/measurements/2026-04-12-slice-003.txt` OK (in envelope)
- `docs/ARCHITECTURE.md` OK (in envelope)

Zero out-of-envelope writes. No ADR edits. No source/test edits in Phase 4.

## Out-of-scope deferred items

Per intent.md and the sweep #22 carryover, the following remain queued for the next slice (`housekeeping/post-inv008-tech-debt`):
- 10 inherited pytest reds (table above)
- 3 ruff errors: 2x E741 (`tests/unit/test_cross_slice_isolation.py:72-73`), 1x F841 (`tests/unit/test_post_timeout_reconcile.py:101`) - sweep #22
- `CAIRN_HEARTBEAT_INTERVAL` / `CAIRN_HEARTBEAT_STALE` documentation at `docs/operational-reference.md:339-344`
- Dedicated context-budget ADR (the ARCHITECTURE.md pending-ADR note remains, unchanged)

## Slice readiness

- [x] Envelope pytest GREEN (5/5)
- [x] validate_architecture.py exit 0
- [x] integration_gate.py Step 3 PASS on INV-004
- [x] Measurement artifact reflects CC 2.1.116, 30335 turn-1, both budgets PASS
- [x] ARCHITECTURE.md paragraph cites <=40,000 + both provenance sentences
- [x] No new reds vs sweep #22 baseline (net -1)
- [x] Zero out-of-envelope writes
- [x] Working tree clean

**Ready for `close_slice` (orchestrator-issued terminal commit).**
