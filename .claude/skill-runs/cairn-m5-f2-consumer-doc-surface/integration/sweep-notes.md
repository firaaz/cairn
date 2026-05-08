---
feature: cairn-m5-f2-consumer-doc-surface
phase: 4 (Auditor)
snapshot-sha: b4eb5b74630f050ec3b6c6acd452979f443723bb
head-sha: e3d088d
audited-commits:
  - 4e3cb0b  # P1 — intent.md
  - 2518dd1  # P2 — 13 RED tests
  - 2583bbe  # P3 — implementation (Risk Surface materialized)
  - e3d088d  # operator-approved fixup (Option A)
invariants-touched: [INV-003]
---

## Summary

F2 closes the consumer-doc surface gap (ADR `m5-plugin-distribution-and-symlink-retire` D6+D7, portfolio-eval Findings 1–5). The slice closes **4 commits**, not 3: Phase 3 RAISE_ISSUE on materialized Risk Surface → triager ESCALATE_TO_USER → operator chose **Option A (fixup-on-this-dispatch)** → fixup `e3d088d` rebinds `validate_phase_topology` to `docs/phase-skill-mapping.md`. All gates green at HEAD.

**First-dogfood signal of the new 8-section intent schema is positive**: the Risk Surface authored in Phase 1 (`intent.md:40-42`) predicted *exactly* the validator-binding break that materialized in Phase 3 — the schema's structural prompt to enumerate "domain wrongness pytest greens cannot catch" caught what the test envelope structurally could not. The schema earned its first commit; recommend keeping for future features.

## Tests

Command: `uv run pytest -q`

| Metric | Baseline (snapshot SHA, `/tmp/m5-f2-baseline-failures.txt`) | HEAD | Delta |
|---|---|---|---|
| Passed | 400 | 414 | +14 |
| Failed | 3 | 2 | −1 |
| xfailed | 2 | 2 | 0 |

**Failures at HEAD (both pre-existing, baseline-attributed):**
- `tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_no_extra_assertion_blocks` — pre-existing (baseline file line 9).
- `tests/unit/test_invariant_assertions.py::TestSlice011AssertionCoverage::test_invariant_count_unchanged` — pre-existing (baseline file line 10). Asserts the firm-invariant set excludes INV-011; cairn currently carries 11 invariants. Out-of-scope for F2 (touches INV-003 only).

**Incidental green:** `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget` (baseline line 8) now passes — likely the F2.4 promotion (lifting Phase Skill Guide out of `operational-reference.md`) shrunk a context surface back into INV-004's turn-1 token budget. Not claimed as F2 victory; documented as incidental.

**New tests added by Phase 2 (all green at HEAD):**
- `tests/unit/test_consumer_doc_surface.py` — 5 sub-tests covering CLAUDE.md `[both]/[maintainer]` tagging, CONSUMER.md anchor resolution, `phase-skill-mapping.md` existence, `operational-reference.md` Phase Skill Guide pointer (FLI-4), `adoptable-disciplines.md` four-discipline coverage.
- `tests/unit/test_template_extraction.py` — 5 sub-tests (one per template).
- `tests/unit/test_readme_reading_order.py` — 1 test for the four-step reading order.

Net: +13 target tests green; +14 total passes (the +1 is the incidental INV-004 budget recovery).

## Validator

Command: `uv run python scripts/validate_architecture.py`

```
ALL CHECKS PASSED
  Invariants verified: 11
  ADR files checked: 28
```

`validate_phase_topology` returns `[]` (no failures) on the live tree (validator exit 0 confirms). The Risk-Surface-predicted break is fully resolved by the rebind in `e3d088d`.

Known stderr noise (out-of-scope): `[structural-parser] INV-002: token budget warning: 436 tokens (warn-at 360) in .claude/handoff.md` — pre-existing per handoff Pending list ("INV-002 budget on this file"); not gated.

## Smoketest hooks

Command: `bash scripts/smoketest_hooks.sh`

```
PASS role_guard.py
```

Exit 0. No hook changes in F2; regression-safety only — confirmed unchanged.

## Word budget (FLI-6)

Command: `wc -w CONSUMER.md`

```
838 CONSUMER.md
```

838 ≤ 1500. PASS.

## Invariants

| ID | Statement | Status | Evidence |
|---|---|---|---|
| INV-003 | Three-way phase-topology binding: `(phase_ordinal, role_slug)` agreed across `.claude/agents/role-topology.yaml` (authoritative), Phase Skill Guide, and `.claude/agents/phase-{1..4}-tdd.md` filenames. `validate_phase_topology()` is the binding entry point. | PASS | (1) `scripts/validate_architecture.py:590` — `phase_skill_mapping_path = project_root / "docs" / "phase-skill-mapping.md"` (rebound from `operational-reference.md`); (2) `scripts/validate_architecture.py:495,516,573,607` — all four hard-coded references rebound; (3) `docs/phase-skill-mapping.md:13-16,24-27` — table rows preserve all four `phase-N-tdd` slugs co-occurring with `Reader`/`Skeptic`/`Builder`/`Auditor` (FLI-3 anchors intact); (4) `docs/phase-skill-mapping.md:3,20` — literal `Superpowers` token preserved (FLI-3); (5) validator exit 0 + `[]` returned by `validate_phase_topology` (live-tree confirmation). |

### Adjacent-code regression check (FLI-3 + Risk Surface follow-up)

Grep evidence that no stale Phase-Skill-Guide-source references to `operational-reference.md` remain in the validator or its tests:

```
grep -rn "operational-reference.*Phase Skill Guide\|Phase Skill Guide.*operational-reference" \
  scripts/ tests/unit/test_inv_003* tests/unit/test_consumer_doc*
```

Hits in **production code (scripts/)**: 0. PASS.

Hits in **tests**:
- `tests/unit/test_inv_003_phase_topology.py:10,246` — comment/docstring strings; do **not** drive the validator binding (validator binding is in `scripts/validate_architecture.py`). These are stale comment-strings inside the test file. Non-load-bearing for INV-003 enforcement; flagged as cleanup follow-up (cosmetic only — see Out-of-scope).
- `tests/unit/test_consumer_doc_surface.py:282,287,300,320` — these are F2's *new* FLI-4 tests asserting the pointer-replacement contract (operational-reference.md keeps a ≤5-line pointer linking to phase-skill-mapping.md). Correct, expected, load-bearing for FLI-4.

No stale binding references remain in the validator or fixtures it consumes. INV-003 is fully reanchored.

## Schema dogfood (intent-system v1)

The 8-section `intent.md` schema was committed in `39f5e9f` and first-dogfooded by F2's `intent.md` (Phase 1 commit `4e3cb0b`). The Risk Surface section (intent-system's headline addition) authored at `intent.md:40-42` predicted that T4's relocation would silently break INV-003's regex anchor; it explicitly named `scripts/validate_architecture.py` as outside-envelope and flagged `Phase 4 must RAISE_ISSUE if binding broke`. That exact failure materialized in Phase 3, was caught by the Auditor-class instinct surfaced via the schema, and was resolved by an operator-approved fixup. **Schema dogfood: confirmed positive (n=1).**

## Out-of-scope / follow-ups

- **Cosmetic cleanup:** `tests/unit/test_inv_003_phase_topology.py:10,246` comment-strings still reference `operational-reference.md` as Phase Skill Guide source. Non-load-bearing (test logic reads `phase-skill-mapping.md` correctly). Cleanup-only.
- **INV-002 budget on `.claude/handoff.md`** (handoff Pending list) — pre-existing.
- **`TestSlice011AssertionCoverage` pair** — pre-existing INV-011 admission lag.
- **F1 placeholders** (marketplace URL, validator stdout) — F1-followup.
- **F3 symlink-instruction removal** in README — F3-followup.
