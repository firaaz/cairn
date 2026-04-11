# SLICE-003-precursor — Phase 2 Validation Approach

**Slice**: SLICE-003-precursor
**Phase**: 2 (Validation)
**Role**: Skeptic
**Date**: 2026-04-11
**Primary skill**: `superpowers:test-driven-development` — RED + Verify RED half of the red-green cycle. Phase 3 Builder completes GREEN. The cycle is bisected by the Phase 2 → Phase 3 session boundary per ADR-004 D4.

## Summary

Spec items V1–V6 from `intent.md` are codified as pytest assertions in `tests/unit/test_slice_003_precursor.py`, plus one GREEN regression canary for INV-003 sub-claim (1) — the load-bearing phase/role name lock from ADR-004 D1. V7–V9 are operator dry-run assertions documented below as a checklist Phase 4 Auditor runs against two dummy slice fixtures. Skills are Markdown protocols with no runtime, so V7–V9 cannot be automated.

Seven pytest functions total: six fail RED at this commit and flip GREEN at Phase 3 Builder's implementation commit; one stays GREEN throughout as a regression canary against future rename drift.

## Ambiguity resolutions

Skeptic read `intent.md` as a black-box input, independently enumerated ambiguities, then cross-checked against `handoff-phase-1.md`'s four pre-flagged items. Resolutions below. Overlap with Phase 1's pre-flagged ambiguities noted.

### Resolved by reference to ARCHITECTURE.md / ADR-004 / intent.md itself

| ID | Ambiguity | Resolution | Reference |
|---|---|---|---|
| A1 | S2 "alongside the existing Loaded/Excluded/Gate report" — where in /catchup Mode A does surfacing happen? (Phase 1 flag #1) | V4 tests for textual anchor inside Mode A region; Builder picks exact format | V4 |
| A2 | S2 "primary and supporting skills" vs Phase 1's "no primary fit" D4 row | Follow V2's escape hatch: "at least one of: primary, supporting, or 'no primary fit' note per ADR-004 D4 Phase 1 row" | intent.md V2 |
| A3 | S3 placement unspecified for Phase 1 (no gate to pass in /start-slice for Phase 1) | V5 accepts Step 3 OR Step 5; V9 accepts Phase 1 "no primary fit" note | intent.md V5, V9 |
| A4 | S1.a "verbatim" scope: byte-equivalent copy vs structural equivalence | V2 tests content (4 phases × 4 roles × ≥1 skill), not byte equivalence. "Verbatim" is a Builder instruction, not a Skeptic test criterion | intent.md V2 |
| A5 | **S1.b exclusion list has no V-item coverage — V1–V9 gap** | V2 test adds sub-assertion for ≥1 excluded-skill name (tightens V2 without inventing new V-item). Documented here for Phase 4 Auditor transparency | Gap identified; mitigated in test |
| A6 | `ADR-NNN` → filename slug resolution for D3 gate (how does `adrs-referenced: [ADR-004]` map to `docs/adr/004-phase-lock-and-role-declaration.md`?) | Deferred to Builder. V6 tests existence check presence; V7/V8 use `ADR-999-nonexistent` which fails under any resolution scheme (glob, exact-match, or index lookup all miss) | intent.md S4.a, V6 |
| A7 | Phase Skill Guide section layout: flat table vs sub-sectioned `### Phase N — Role` structure (Phase 1 flag #2) | V2 tests content not structure; either layout passes | intent.md V2 |

### Resolved by operator escalation (one-at-a-time per brainstorming skill)

| ID | Question | Resolution |
|---|---|---|
| E1 | Optional test landing zone — write `tests/unit/test_slice_003_precursor*.py` or keep V1–V6 as pure-Markdown operator checklist? (Phase 1 flag #4) | **Write pytest file.** Direct TDD RED + Verify RED discipline per ADR-004 D4 Skeptic primary skill. Codifies greps as version-controlled assertions. Phase 4 Auditor re-runs via pytest, lower drift than manual greps. `tests/unit/test_validate_architecture.py` proves the infrastructure exists |
| E2 | V6 failure message plurality — when multiple ADRs are missing, list all or first? (Phase 1 flag #3) | **List all.** Prevents whack-a-mole. Matches `/integration-sweep` evidence style. V6 test asserts `re.search(r"missing\s+adr", step3, re.IGNORECASE)` which Builder satisfies by writing Step 3 prose that explicitly commits to naming every missing slug |

### Novel ambiguities (not pre-flagged by Phase 1)

A2, A3, A4, **A5**, A6 were found by Skeptic but not listed in `handoff-phase-1.md`. **A5 is the most substantive** — the S1.b exclusion list has no direct V-item in intent.md's V1–V9 enumeration. Left untreated, Builder could omit the exclusion list entirely and all tests still pass. Mitigation: V2 test's sub-assertion. Phase 4 Auditor should re-verify by reading the Phase Skill Guide section body for at least one `superpowers:dispatching-parallel-agents`-style exclusion line.

## Test-to-spec mapping

| Test function | V item | Spec items covered | Status at Phase 2 commit |
|---|---|---|---|
| `test_v1_phase_skill_guide_section_exists` | V1 | S1 — `## Phase Skill Guide` heading | **RED** |
| `test_v2_phase_skill_guide_content` | V2 + A5 mitigation | S1.a (table content), Phase 1 escape, S1.b (exclusions sub-check) | **RED** |
| `test_v3_living_registry_and_adr_citation` | V3 | S1.c (living registry note), S1.d (ADR-004 citation) | **RED** |
| `test_v4_catchup_references_phase_skill_guide` | V4 | S2 — /catchup Mode A reference | **RED** |
| `test_v5_startslice_references_phase_skill_guide` | V5 | S3 — /start-slice Step 3 or Step 5 reference | **RED** |
| `test_v6_startslice_step3_d3_gate` | V6 | S4 — D3 gate (S4.a adrs-referenced check, S4.b empty-trivial semantics, S4.c missing-slug failure message) | **RED** |
| `test_inv_003_four_phase_order_and_role_names` | INV-003 sub-claim (1) | ADR-004 D1 phase/role name lock | **GREEN** (regression canary) |

**Why one GREEN test.** INV-003 has four sub-claims (intent.md § Verification § Invariant check):
1. Four phases in fixed order with fixed role names are preserved (no rename) — **this canary**
2. Phase Skill Guide section exists — covered by V1
3. Referenced by /catchup and /start-slice at phase entry — covered by V4+V5
4. D3 gate present in start-slice.md Step 3 — covered by V6

Sub-claim (1) is already true in `docs/ARCHITECTURE.md:16` from commit `7cfe719`. The canary persists as a regression check against future rename drift; it fails GREEN→RED only if a future slice accidentally removes or reorders the phase/role names. Sub-claims (2)(3)(4) are the Phase 2 → Phase 3 RED→GREEN flips.

## RED verification (TDD Iron Law — evidence, not assertion)

```
$ uv run --with pytest python -m pytest tests/unit/test_slice_003_precursor.py -v

FAILED tests/unit/test_slice_003_precursor.py::test_v1_phase_skill_guide_section_exists
  AssertionError: Expected exactly 1 '## Phase Skill Guide' heading in
  docs/operational-reference.md, found 0. (intent.md V1)

FAILED tests/unit/test_slice_003_precursor.py::test_v2_phase_skill_guide_content
  AssertionError: Phase Skill Guide section not found in
  docs/operational-reference.md. (V2)

FAILED tests/unit/test_slice_003_precursor.py::test_v3_living_registry_and_adr_citation
  AssertionError: Phase Skill Guide section not found. (V3)

FAILED tests/unit/test_slice_003_precursor.py::test_v4_catchup_references_phase_skill_guide
  AssertionError: S2: /catchup Mode A must reference 'Phase Skill Guide' at
  phase entry. (V4)

FAILED tests/unit/test_slice_003_precursor.py::test_v5_startslice_references_phase_skill_guide
  AssertionError: S3: /start-slice must reference 'Phase Skill Guide' at a
  phase-entry moment (Step 3 gate-pass or Step 5 intent guidance). (V5)

FAILED tests/unit/test_slice_003_precursor.py::test_v6_startslice_step3_d3_gate
  AssertionError: S4.a: Step 3 gate table Phase 2 row must check
  'adrs-referenced' field. (V6)

PASSED tests/unit/test_slice_003_precursor.py::test_inv_003_four_phase_order_and_role_names

========================= 6 failed, 1 passed in 0.06s ==========================
```

**Interpretation**: V1–V6 fail with meaningful assertion messages that cite the `intent.md` V-item each test maps to. INV-003 canary passes because `ARCHITECTURE.md:16` already carries the canonical phase/role statement. No framework errors, no typos. This is verified RED per TDD Iron Law — Phase 3 Builder can drive toward GREEN with `uv run --with pytest python -m pytest tests/unit/test_slice_003_precursor.py -v` as the loop.

## Operator dry-run checklist (V7, V8, V9)

Phase 4 Auditor runs these in a **fresh session** after Phase 3 Builder's implementation lands. They verify the behavioral assertions that cannot be automated because `/catchup` and `/start-slice` are Markdown skill files with no runtime. The Auditor executes the skills in a controlled scratch environment with two dummy slice fixtures.

### Setup: two dummy slice fixtures

Work in a scratch directory outside `.claude/current-slice/` to avoid contaminating real slice state:

```bash
mkdir -p /tmp/cairn-slice-003-dryrun/bad
mkdir -p /tmp/cairn-slice-003-dryrun/good
```

**Fixture A — gate-fail (two missing ADRs)**: `/tmp/cairn-slice-003-dryrun/bad/slice.yaml`

```yaml
id: SLICE-DUMMY-BAD
title: "D3 gate fixture: adrs-referenced with missing ADRs"
status: intent
started: 2026-04-11
completed: null
invariants-touched: []
adrs-referenced: [ADR-998-missing, ADR-999-nonexistent]
adrs-created: []
```

And `/tmp/cairn-slice-003-dryrun/bad/intent.md` with YAML frontmatter declaring the same two missing ADRs in its `adrs-referenced` field.

**Fixture B — trivial-pass (empty list)**: `/tmp/cairn-slice-003-dryrun/good/slice.yaml`

```yaml
id: SLICE-DUMMY-GOOD
title: "D3 gate fixture: empty adrs-referenced"
status: intent
started: 2026-04-11
completed: null
invariants-touched: []
adrs-referenced: []
adrs-created: []
```

And `/tmp/cairn-slice-003-dryrun/good/intent.md` with YAML frontmatter declaring empty `adrs-referenced: []`.

**Swap procedure** (Auditor uses to point `.claude/current-slice/` at each fixture):

```bash
# Save current slice state
mv .claude/current-slice .claude/current-slice.audit-backup
# Point at fixture
cp -r /tmp/cairn-slice-003-dryrun/bad .claude/current-slice
# Run the /catchup or /start-slice command under test
# Restore
rm -rf .claude/current-slice
mv .claude/current-slice.audit-backup .claude/current-slice
```

### V7 — `/catchup phase 2` on each fixture

| Fixture | Expected behavior | Auditor result |
|---|---|---|
| A (missing ADRs) | Gate failure message names BOTH `ADR-998-missing` AND `ADR-999-nonexistent`. Does not advance to Phase 2 orientation. | [ ] PASS / [ ] FAIL |
| B (empty list) | Gate passes trivially. Advances to Phase 2 Skeptic orientation and surfaces role/anti-behaviors/skills per V9. | [ ] PASS / [ ] FAIL |

### V8 — `/start-slice phase 2` on each fixture

| Fixture | Expected behavior | Auditor result |
|---|---|---|
| A (missing ADRs) | Step 3 gate fires. Failure message names BOTH slugs (E2 resolution: list all). Does not update `slice.yaml` status field. | [ ] PASS / [ ] FAIL |
| B (empty list) | Step 3 gate passes. Advances `slice.yaml` status. Surfaces role/anti-behaviors/skills per V9. | [ ] PASS / [ ] FAIL |

### V9 — role/anti-behavior/skill surfacing on gate-pass

On each successful gate-pass in V7/V8 (Fixture B), verify both `/catchup` and `/start-slice` visibly print the target phase's role, at least one anti-behavior, and at least one skill (or the explicit "no primary fit" note for Phase 1). The surfacing must textually source the Phase Skill Guide (e.g., `docs/operational-reference.md § Phase Skill Guide` citation visible in the printed output).

| Target phase | Role | Role printed? | Anti-behavior printed? | Skill or "no primary fit"? |
|---|---|---|---|---|
| Phase 1 | Reader | [ ] | [ ] | [ ] (expect "no primary fit") |
| Phase 2 | Skeptic | [ ] | [ ] | [ ] `test-driven-development` |
| Phase 3 | Builder | [ ] | [ ] | [ ] `test-driven-development` / `verification-before-completion` |
| Phase 4 | Auditor | [ ] | [ ] | [ ] `verification-before-completion` / `requesting-code-review` |

**V9 PASS criterion**: all 12 checkboxes ticked for at least one of (`/catchup`, `/start-slice`) per phase, AND the printed surfacing visibly cites the Phase Skill Guide section.

### Teardown

```bash
rm -rf /tmp/cairn-slice-003-dryrun
```

## Handoff notes for Phase 3 Builder

**Inputs Phase 3 Builder MUST load**:
- `.claude/current-slice/intent.md` — the spec (primary input)
- `tests/unit/test_slice_003_precursor.py` — the validation suite (run as tight GREEN loop)

**Inputs Phase 3 Builder MUST NOT load** (per ADR-004 D2 Builder anti-behaviors — "does not re-litigate the spec or the tests" and "does not load Phase 2's approach.md or reasoning about why tests are shaped as they are"):
- This file (`.claude/current-slice/validation/approach.md`)
- `.claude/current-slice/handoff-phase-1.md` beyond its pointer-only sections
- The future `handoff-phase-2.md` beyond its pointer-only sections

**Expected Phase 3 completion state**: 7 tests pass. 6 flip RED → GREEN; 1 stays GREEN. Command: `uv run --with pytest python -m pytest tests/unit/test_slice_003_precursor.py -v`.

**Phase 4 Auditor re-runs**: (a) the full pytest suite (`uv run --with pytest python -m pytest -v`) — not just this slice's tests, (b) the architecture validator (`uv run python scripts/validate_architecture.py`), (c) the V7/V8/V9 operator dry-run checklist above, (d) the INV-003 sub-claim (1) canary stays green, and (e) each test's file:line citation backing its assertion.

## Transparency note on input loading

The `/catchup` and `/start-slice` Markdown skill files were loaded into Skeptic's context by the command dispatch mechanism (the operator invoked them — they are the protocols Skeptic operates inside). This is a necessary effect of how cairn's slash commands work, not a Skeptic-initiated read. Skeptic's test design is driven by `intent.md`'s V1–V6 enumeration, not by the current state of those files. Knowledge that the current versions do not yet contain the required strings is empirically verified by the RED pytest output above rather than asserted from memory.

The three envelope files (`docs/operational-reference.md`, `commands/claude-code/catchup.md`, `commands/claude-code/start-slice.md`) were not read via the `Read` tool during Phase 2 ambiguity enumeration, consistent with `handoff-phase-1.md`'s do-not-load list. The skill-dispatch loading is inevitable; proactive file reading is not, and was not done.
