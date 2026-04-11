# Phase 2 (Validation) — Handoff to Phase 3 (Implementation)

**Slice**: SLICE-003-precursor
**Role completed**: Skeptic
**Artifacts**:
- `tests/unit/test_slice_003_precursor.py` — 7 pytest functions, 6 RED (V1–V6) + 1 GREEN (INV-003 sub-claim 1 regression canary)
- `.claude/current-slice/validation/approach.md` — Phase 4 Auditor input; **Builder must NOT load this**
**Committed**: `c7b10a2`
**Gate status**: PASSED — Phase 2 artifacts committed; tree clean post-commit.

## Inputs Phase 3 Builder should load (in order)

1. `.claude/current-slice/intent.md` — the spec; primary input (the "what to build")
2. `tests/unit/test_slice_003_precursor.py` — the validation suite; the GREEN target
3. `docs/adr/004-phase-lock-and-role-declaration.md:72-85` — D4 mapping table and explicit-exclusions list, the source Builder lifts into the new Phase Skill Guide section per S1.a and S1.b

**GREEN loop**: `uv run --with pytest python -m pytest tests/unit/test_slice_003_precursor.py -v`
**Target state**: 7 passed. Six tests flip from RED to GREEN as Builder writes production code; one (INV-003 canary) stays GREEN throughout.

## What Phase 3 Builder should NOT load

Per ADR-004 D2 Builder anti-behaviors ("does not re-litigate the spec or the tests", "does not load Phase 2's approach.md or reasoning about why tests are shaped as they are"):

- `.claude/current-slice/validation/approach.md` — Phase 2's ambiguity-resolution reasoning and test-design rationale. Builder reads the test assertions directly; approach.md exists for Phase 4 Auditor.
- `.claude/current-slice/handoff-phase-1.md` beyond its pointer-only sections (inputs list, gate status).
- This handoff's "Things not pinned by the tests" section beyond its factual content. Read the tests and `intent.md` first; treat this handoff as a pointer index, not a design doc.

## Things not pinned by the tests (Builder must decide)

Two items are not discoverable from test code alone — they require Builder to choose:

1. **ADR slug resolution in the D3 gate.** `adrs-referenced: [ADR-004]` in an `intent.md` must resolve to a check against `docs/adr/004-phase-lock-and-role-declaration.md` (or equivalent). Options: glob `docs/adr/<NNN>-*.md`, exact filename match, or `docs/adr/index.md` lookup. V6 tests that the gate exists and references the `adrs-referenced` field; it does **not** test the resolution mechanism. Builder picks one and documents it in the Step 3 gate table row or adjacent prose.

2. **V6 failure-path plurality (E2 operator resolution: list all).** V6's test asserts the substring `"missing ADR"` appears in Step 3 (case-insensitive). It does **not** enforce the plurality decision. Per E2 operator resolution, the Step 3 failure-path prose MUST commit to naming **every** missing ADR slug when multiple are missing — not just the first. One line of prose satisfies this (e.g., "The failure message lists every missing ADR slug."). This is a Builder commitment to the operator, captured in file text so future operators read it.

## Decisions already pinned by the tests

Builder can discover these by reading `tests/unit/test_slice_003_precursor.py` directly — listed here only so the full shape of the handoff is visible:

- V1 requires exactly one `## Phase Skill Guide` heading in `docs/operational-reference.md`.
- V2 requires all four phase names, all four role names, ≥1 primary superpowers skill name, Phase 1 escape (em-dash or "no primary fit"), and ≥1 excluded-skill name from the S1.b list (A5 sub-assertion).
- V3 requires the phrase "living registry" (case-insensitive) and the citation "ADR-004" within the Phase Skill Guide section.
- V4 requires the string "Phase Skill Guide" inside `/catchup` Mode A (between `### Mode A` and `### Mode B`).
- V5 requires the string "Phase Skill Guide" inside `/start-slice` Step 3 OR Step 5 region.
- V6 requires `adrs-referenced`, empty-passes-trivially semantics, and "missing ADR" failure-path text inside `/start-slice` Step 3.

## Phase advancement

`slice.yaml` advanced: `status: validation` → `status: implementation`.
