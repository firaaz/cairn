# Phase 3 (Implementation) — Builder Notes

**Slice**: SLICE-003-precursor
**Role**: Builder
**Scope**: Two decisions that intent.md and the Phase 2 tests did not pin down. Everything else in this slice was discoverable from `intent.md` + `tests/unit/test_slice_003_precursor.py` alone.

## Decision 1 — ADR slug resolution mechanism for the D3 gate

**Context**: `intent.md` S4.a names the verification command as `git log --oneline -- docs/adr/<adr-slug>.md ≥1 commit for each declared ADR`, but leaves the mapping from a slug like `ADR-004` to a filename ambiguous. Phase 2 handoff flagged this as a Builder-decides item. Three options were visible:

1. **Filename glob on numeric suffix** — `docs/adr/<NNN>-*.md` (where `<NNN>` is the slug's numeric portion).
2. **Exact filename lookup** — require the full descriptive filename in `adrs-referenced`.
3. **`docs/adr/index.md` lookup** — parse the index to map slugs to filenames.

**Chosen**: Option 1, filename glob on numeric suffix.

**Reasoning**:

- **Matches actual file naming.** Every ADR in `docs/adr/` today follows the pattern `NNN-descriptive-kebab-case.md` (e.g., `004-phase-lock-and-role-declaration.md`). The numeric suffix is the load-bearing identifier; the descriptive tail is editorial.
- **Keeps `adrs-referenced` authorable.** Authors write `adrs-referenced: [ADR-004]` naturally. Option 2 would force them to remember the full filename (brittle under rename; privileges the tail over the slug contract). Option 3 adds an index-parse dependency and couples the gate to `index.md`'s correctness, introducing a second failure mode.
- **Rename tolerance.** If ADR-004's descriptive tail were ever renamed editorially (within the `ADR_EDITORIAL_FIX=1` escape per `checks/reversibility-guard.sh`), the glob still resolves. The contract is stable against editorial churn.
- **One-line verification.** `git log --oneline -- docs/adr/004-*.md` is a single command, matching the single-command style of the other gate rows in the Step 3 table.

**Documented in**: `commands/claude-code/start-slice.md` Step 3 — the Phase 2 row's Verification cell and the "D3 gate semantics" prose paragraph. Example in the doc uses `ADR-004` → `docs/adr/004-*.md` explicitly.

**Edge case not handled**: a two-digit numeric collision (e.g., `ADR-04` vs `ADR-040`) would be ambiguous under the glob. This is not a concern for v1 — the ADR corpus is far from that boundary. If the corpus ever approaches 100 ADRs, the glob pattern can be tightened to `<NNN>-*.md` with a pre-check that the slug was zero-padded to three digits at write time (already true by existing convention).

## Decision 2 — V6 failure-path plurality commitment (E2 operator resolution)

**Context**: Phase 2 handoff recorded operator escalation E2: the V6 failure message MUST name **every** missing ADR slug when multiple are missing, not just the first. The test (`test_v6_startslice_step3_d3_gate`) only asserts the substring `missing ADR` appears in Step 3; it does not test plurality. Builder had to commit to the plurality contract in prose.

**Chosen**: Explicit plurality commitment in the Step 3 "D3 gate failure path" prose paragraph, with a concrete multi-slug example.

**Prose (as landed in `commands/claude-code/start-slice.md` Step 3)**:

> When one or more ADRs are missing from `docs/adr/`, the gate MUST fail and the failure message MUST name **every** missing ADR slug, not just the first. Example: `Gate FAILED: missing ADR files for slugs [ADR-004, ADR-007]. intent.md references ADRs that are not yet committed to docs/adr/. Either commit the missing ADRs first (via /decision or /new-adr), or remove them from adrs-referenced in intent.md.` The plurality commitment matters because silent truncation ("missing ADR: ADR-004") would let a slice drift past a second unresolved decision on retry. List all missing slugs in every failure message.

**Why the example uses a bracketed list**: the test regex is `missing\s+adr` (case-insensitive). The chosen phrasing "missing ADR files for slugs [...]" satisfies the regex while also making the list-all contract visually obvious to a future operator. Prose about the retry failure mode ("silent truncation would let a slice drift past a second unresolved decision") is load-bearing: it gives the reason for the plurality rule so future Builder-role agents do not weaken it.

## Decisions discoverable from tests alone (not reproduced here)

Per the Phase 2 handoff "Decisions already pinned by the tests" section, the following were not Builder judgment calls — they were discoverable by reading `tests/unit/test_slice_003_precursor.py`:

- Exactly one `## Phase Skill Guide` heading (V1).
- Four phase names + four role names + ≥1 primary skill + Phase 1 em-dash/"no primary fit" + ≥1 excluded skill (V2 with A5 sub-check).
- "Living registry" phrase + "ADR-004" literal citation (V3).
- `Phase Skill Guide` substring inside `catchup.md` Mode A region (V4).
- `Phase Skill Guide` substring inside `start-slice.md` Step 3 or Step 5 region (V5).
- `adrs-referenced` substring + empty-passes semantics + `missing ADR` substring in Step 3 (V6).

## GREEN evidence

- Slice tests: `7 passed in 0.01s` — all six V1–V6 flipped RED→GREEN; INV-003 canary stayed GREEN throughout.
- Full project test suite: `13 passed in 0.51s` — no regressions in `test_validate_architecture.py`.
- Working tree at Phase 3 end contained exactly three modified files, all inside the declared envelope: `docs/operational-reference.md`, `commands/claude-code/catchup.md`, `commands/claude-code/start-slice.md`. No envelope expansion was required.

## Things for Phase 4 Auditor to check (pointers, not reasoning)

- V7–V9 behavioral dry-run: per intent.md Verification § "Behavioral assertions", Auditor runs `/catchup phase 2` and `/start-slice phase 2` on two dummy fixtures (one with `adrs-referenced: [ADR-999-nonexistent]`, one with `adrs-referenced: []`) and verifies the gate fails with a named slug vs. passes trivially, and that role/anti-behavior/skill surfacing is visibly printed on gate-pass.
- INV-003 evidence: four sub-claims, each backed by `file:line` citations in the three envelope files plus the pre-existing INV-003 text in `docs/ARCHITECTURE.md`. The INV-003 canary test in `tests/unit/test_slice_003_precursor.py::test_inv_003_four_phase_order_and_role_names` is a regression guard on sub-claim (1) only — the Auditor check is the authoritative pass/fail.
- Phase 2's `validation/approach.md` is Auditor's input (per Phase 2 handoff); Builder did not read it and has no comment on its content.
