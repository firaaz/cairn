# Phase 3 Implementation Notes — SLICE-015 (identifier-scheme/scheme-adr)

## Deliverables produced

- `docs/adr/identifier-scheme.md` — new governing ADR, frontmatter + body covering all 10 sections from intent.md:36-48 (D1 two-field schema, D2 ID shape per entity type, D3 versioning on supersession, D4 slice branch naming, D5 feature metadata, D6 `name:` style, D7 three-phase migration, D8 open questions resolved, D9 cross-reference format, Consequences). Body precisely enumerates the bootstrap-window gap in Consequences per intent.md:48 (glob `*/docs/adr/[0-9]*` at `reversibility-guard.sh:51,68` does not match flat-slug filename `identifier-scheme.md`).
- `docs/adr/005-semantic-identity.md` — frontmatter-only edit per intent.md:50: `status: accepted → superseded`, `superseded-by: null → identifier-scheme`. Body untouched (`git diff --stat` shows 4 lines, all in frontmatter).
- `docs/adr/index.md` — added `identifier-scheme` row, marked ADR-005 as `superseded (by identifier-scheme)`.

## Verification results

Steps V1–V4 and V7 from intent.md:67-78 pass. V5 (full pytest) and V6 (validator) fail in five tests, all root-caused by a single spec/test tension that is intentionally deferred to Phase 4. Documented below for the Phase 4 D1/D3 gate.

## Deferred to Phase 4 (5 test failures, single root cause: ADR-005 supersession)

The intent.md:67-78 verification list states V5 should pass with no test impact. That expectation is contradicted by the spec's own scoping decision at intent.md:62-63 (ARCHITECTURE.md regeneration is a Phase 4 D1 gate action, not Phase 3 work). The five failures below are the load-bearing consequence of that scoping choice.

### Group A — `INV-005 references superseded ADR-005` (4 failures)

- `tests/unit/test_validate_architecture.py::test_v1_cairn_self_dogfood_baseline`
- `tests/unit/test_invariant_assertions.py::TestCairnSelfDogfood::test_cairn_self_validation_still_passes`
- `tests/unit/test_invariant_assertions.py::TestSlice011ZeroWarnings::test_zero_check_d_failures`
- `tests/unit/test_sweep_debt_cleanup.py::test_v5_architecture_validator`

All four invoke `scripts/validate_architecture.py`, which emits `Check C: INV-005 (line 49) references ADR-005 which is superseded`. The reference site is `docs/ARCHITECTURE.md:49` — the INV-005 narrative cites `(ADR-005)`. Phase 4 D1 gate runs `/refresh-architecture`, which regenerates ARCHITECTURE.md from the current ADR corpus; INV-005's source citation will then point at `identifier-scheme` and the validator will pass.

**Phase 4 action:** run `/refresh-architecture`. No code change required; the regeneration is mechanical.

### Group B — brittle ADR-status assertion (1 failure)

- `tests/unit/test_slice_005_design_decomposition.py::test_v2_frontmatter_valid`

The test at `tests/unit/test_slice_005_design_decomposition.py:119` asserts `fm["status"] == "accepted"` for every ADR. Predates the supersession case. Triggered by intent.md:50's mandated `status: superseded` edit on ADR-005.

**Phase 4 action:** widen the assertion to `fm["status"] in ("accepted", "superseded")`. Two-line patch in the test file. Fix belongs in this slice's Phase 4 close, not in a future slice — the brittle assertion is exposed by this slice's spec-mandated edit.

## Pre-existing noise (NOT this slice — handoff.md:17)

- `tests/unit/test_slice_005_design_decomposition.py::test_v7_envelope_compliance`
- `tests/unit/test_sweep_debt_cleanup.py::test_v4_envelope_compliance`

Both fire on any uncommitted state outside past slice envelopes. Documented as known noise in `.claude/handoff.md:17` and the prior phase-2 handoff. No action in Phase 4 of this slice; tracked for a hygiene slice elsewhere.

## What was not done

- **No ARCHITECTURE.md edit.** Per intent.md:62-63, regeneration is Phase 4 D1 gate.
- **No test patches.** Builder anti-behavior is "do not re-litigate the spec or the tests"; Group B's fix is queued for Phase 4.
- **No hook code touched.** Per intent.md:54-56, scope-guard / reversibility-guard / reality-check are `identifier-scheme/hook-tolerance` scope.
- **No template/CLAUDE.md/operational-reference edits.** Per intent.md:57-59, those are `identifier-scheme/template-updates` scope.
- **No rename of any existing entity.** Per intent.md:60-62, Phase 2 of the migration handles that.

## Bootstrap-window status

The new ADR `docs/adr/identifier-scheme.md` is now committed and unprotected by `reversibility-guard.sh`'s ADR append-only enforcement (glob mismatch — body of the ADR D9/Consequences explains precisely). Constraint at `.claude/features/identifier-scheme.yaml` pins `identifier-scheme/hook-tolerance` as the immediately-next slice. No flat-slug ADRs may be authored in the bootstrap window.
