# Phase 1 (Intent) — Handoff to Phase 2 (Validation)

**Slice**: SLICE-003-precursor
**Role completed**: Reader
**Artifact**: `.claude/current-slice/intent.md` (100 lines, committed `7ff5d74`)
**Gate status**: PASSED — intent.md committed, `adrs-referenced: [ADR-004]` exists in corpus (see `docs/adr/004-phase-lock-and-role-declaration.md`).

## Ambiguities the Skeptic should know about

These are places the intent deliberately left room, either because Reader discipline forbids over-specification or because Builder is the right level of the stack to decide. Skeptic's validation suite should not assume resolution in either direction — design tests that verify the *required content fields*, not any specific format.

1. **Phase entry moment granularity.** S2 says `/catchup` Mode A Phase N sub-sections must surface role/anti-behaviors/skills "at phase entry". `catchup.md` Mode A has a per-phase load block followed by an orientation report block. Intent does NOT pin down whether surfacing happens inside the load block, between the two, or as a third block. Skeptic should design tests that accept any consistent placement, and flag if Builder's choice drifts across the four phases.

2. **Phase Skill Guide section structure.** S1 says "section body carries the D4 table from ADR-004 verbatim" but does not forbid sub-section structure (e.g., `### Phase 1 — Reader` subsections under `## Phase Skill Guide`). Builder may choose flat-table or sub-sectioned layout. V2 tests the *content* (four phases × four roles × skill coverage), not the structure.

3. **V6 failure message plurality.** S4.c requires the D3 gate failure to name the missing ADR slug(s). If multiple ADRs are missing, intent does not specify whether the message lists all or the first. Skeptic should decide the test's expectation (I'd lean "lists all", but this is Skeptic's call per constraint-enumeration).

4. **Optional test landing zone.** Envelope permits `tests/unit/test_slice_003_precursor*.py` but does not require it. Skeptic decides whether a Python test file is written or whether verification is a pure-Markdown operator checklist. Structural assertions V1–V6 are grep-runnable either way; the test file choice is about whether those greps get codified as a test or stay as protocol text.

## What Phase 2 should NOT carry over

- **This Phase 1 session's reasoning** about why the envelope is 3 files, why F7 was dropped, why the slice-ID counter diverges from the plan. None of that belongs in test design. Skeptic sees intent.md + ARCHITECTURE.md + ADR-004 only.
- **SLICE-002 backburner context.** Archived at `.claude/completed-slices/SLICE-002-stopped/` per plan P0b amendment. Skeptic does not need to know this slice existed.
- **The walkthrough discussion** between Reader and operator. Reader's framing is done; Skeptic's framing starts from intent.md as a black-box input.

## Inputs Skeptic should load (Phase 2 declared)

1. `.claude/current-slice/intent.md` (this slice's Phase 1 artifact)
2. `docs/ARCHITECTURE.md` (for INV-003 exact wording, lines 16 + 20–27)
3. `docs/adr/004-phase-lock-and-role-declaration.md` (named in `adrs-referenced`; specifically D2 table lines 50–55, D3 gate lines 57–61, D4 mapping lines 63–85, Risk F6 line 186)

Do NOT load: `catchup.md`, `start-slice.md`, `operational-reference.md` internal content (they are the *subjects* of the spec, not inputs to Skeptic's ambiguity enumeration). Do NOT load this handoff's "ambiguities" list as a substitute for reading intent.md itself — read intent.md first, enumerate your own ambiguities, then cross-check.
