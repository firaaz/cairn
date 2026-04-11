# Phase 3 (Implementation) — Handoff to Phase 4 (Integration)

**Slice**: SLICE-003-precursor
**Role completed**: Builder
**Artifacts**:
- `docs/operational-reference.md` — new `## Phase Skill Guide` section (S1.a–d)
- `commands/claude-code/catchup.md` — Mode A surfacing instruction (S2)
- `commands/claude-code/start-slice.md` — Step 3 D3 gate row + semantics + failure-path + surfacing (S3, S4)
- `.claude/current-slice/implementation/notes.md` — Builder judgment-call log; **Auditor does not need to load this**, see the "Auditor should NOT load" section below
**Committed**: `562ea80`
**Gate status**: PASSED — Phase 3 artifacts committed; tree clean post-commit; slice tests 7/7 GREEN; full project suite 13/13 passed.

## Inputs Phase 4 Auditor should load (in order)

1. `.claude/current-slice/intent.md` — the spec; primary input. V7–V9 behavioral assertions and the INV-003 sub-claim map live here.
2. `.claude/current-slice/validation/approach.md` — Phase 2's ambiguity-resolution reasoning and test-design rationale. **This exists specifically for the Auditor.** Builder did not load it per ADR-004 D2 anti-behavior; Auditor loads it to understand the validation suite's design intent when judging invariant pass/fail.
3. The three envelope files at commit `562ea80`:
   - `docs/operational-reference.md`
   - `commands/claude-code/catchup.md`
   - `commands/claude-code/start-slice.md`
4. `docs/ARCHITECTURE.md` — for the canonical INV-003 statement.
5. `docs/adr/004-phase-lock-and-role-declaration.md` — for the D1/D2/D3/D4 source text that Phase 4 evidence must cite.

## What Phase 4 Auditor should NOT load

Per ADR-004 D2 Auditor anti-behavior ("Auditor does not rewrite the implementation") and the Phase 4 `/catchup` isolation rule ("Exclude: Phase 3's implementation/notes.md — check the code, not the reasoning"):

- `.claude/current-slice/implementation/notes.md` beyond its pointer-only sections. It exists to record Builder's two judgment calls (ADR slug resolution mechanism, V6 plurality prose) so they are not lost — Auditor should check the code itself, not Builder's reasoning about the code.
- Phase 1's `handoff-phase-1.md` and Phase 2's `handoff-phase-2.md` beyond their pointer-only sections.
- This handoff's "Decisions Builder made" section beyond its factual content — treat it as a pointer index, not an explanation.

## Phase 4 runnable checks

Three commands plus one file-evidence pass:

1. **Full test suite**: `uv run python -m pytest` — target: all passing, including the 7 slice tests and the 6 `test_validate_architecture.py` tests. Phase 3 verified `13 passed` at `562ea80`; Phase 4 re-runs in a fresh session for independent confirmation.
2. **Architecture validator**: `uv run python scripts/validate_architecture.py` — checks consistency between `docs/ARCHITECTURE.md` invariants and the `docs/adr/` corpus. Cairn's note: the validator has historically failed in this repo until the meta-dogfood architecture/ADR layer exists; Auditor reads the output with that context, not as a pass/fail on this slice's envelope alone.
3. **V7–V9 operator dry-run**: per `intent.md` Verification § "Behavioral assertions", create two dummy slice fixtures with `adrs-referenced: [ADR-999-nonexistent]` and `adrs-referenced: []` respectively, and run `/catchup phase 2` + `/start-slice phase 2` on each. V7/V8 assertion: gate fails with the missing slug named vs. passes trivially. V9 assertion: on gate-pass, role name + anti-behaviors + at least one skill (or Phase 1 em-dash) are printed, visibly sourced from the Phase Skill Guide. The two dummy fixtures are the operator's responsibility to spin up; neither is committed.
4. **INV-003 invariant evidence pass**: per `intent.md` Verification § "Invariant check", produce `file:line` citations in the three envelope files backing each INV-003 sub-claim. Sub-claim (1) (four phases in fixed order with fixed role names) is additionally covered by the existing `test_inv_003_four_phase_order_and_role_names` canary, which remains GREEN and serves as a rename-drift regression guard — but the primary Phase 4 evidence is the `file:line` citation pass, not the canary.

## Decisions Builder made (pointer only; reasoning is in implementation/notes.md which Auditor should NOT re-load)

Two Builder judgment calls that the tests and `intent.md` did not pin down:

1. **ADR slug resolution**: filename-glob on numeric suffix (`docs/adr/<NNN>-*.md`). Documented in `start-slice.md` Step 3 Phase 2 row Verification cell and the adjacent "D3 gate semantics" prose paragraph. Auditor judges this by reading the Step 3 text, not by reading `implementation/notes.md`.
2. **V6 plurality**: failure message prose in `start-slice.md` Step 3 "D3 gate failure path" paragraph commits to naming **every** missing ADR slug with a multi-slug example. Auditor judges this by reading the Step 3 text.

## Things Phase 4 Auditor should watch for

- **Regression paranoia**: V1–V6 passed at Phase 3 commit time, but Phase 4 re-runs in a fresh session specifically to catch anything that the Builder session's context might have masked. If the slice tests fail in Phase 4's fresh run but passed in Phase 3's run at `562ea80`, investigate the delta — do not patch.
- **Cross-doc consistency**: The Phase Skill Guide text in `docs/operational-reference.md` is lifted from ADR-004:50–85. Auditor should spot-check that no drift was introduced during the lift. This is not a test assertion; it is a judgment call on textual fidelity.
- **INV-003 sub-claim (3)** asserts "referenced by both `/catchup` and `/start-slice` at phase entry". Phase 3 landed V4 (catchup) and V5 (start-slice Step 3) as substring checks, but the Auditor should verify that the surfacing instruction is positioned at a *phase-entry moment* in each skill — not in an unrelated section that happens to contain the phrase.

## Phase advancement

`slice.yaml` advanced: `status: implementation` → `status: integration`.
