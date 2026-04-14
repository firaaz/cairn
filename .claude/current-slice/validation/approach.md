# SLICE-012 Phase 2 — Validation Approach

## Ambiguity Resolutions

| # | Ambiguity | Resolution | Source |
|---|-----------|------------|--------|
| A1 | `snapshot_diff.py` exit code for first-run: table says 2, parenthetical says "exits 0" | Exit code **2**. The structured exit-code table governs; parenthetical "exits 0" is drafting noise. | Intent §2 |
| A2 | `integration_gate.py` — does Step 3 failure short-circuit Step 4? | **No short-circuit.** "Each sub-check is logged with pass/fail" implies all checks run. | Intent §1 |
| A3 | `snapshot_diff.py` — does "under scripts/" mean recursive? | **Yes.** "Under" = all descendants. `commands/claude-code/` is "under `commands/`". | Intent §2 |
| A4 | `snapshot_diff.py` — repo root discovery | **CWD = repo root**, matching `validate_architecture.py` convention. | ARCHITECTURE.md |
| A5 | `snapshot_diff.py` JSON entry key names | Tests verify size (int) and hash (64-char hex) present per entry; exact key names are Phase 3 choice. | Intent §2 |
| A6 | `integration_gate.py` — invocation mechanism for Check D | **Implementation detail.** Tests verify exit codes and output, not whether import or subprocess is used. | Intent §1 boundary |
| A7 | `snapshot_diff.py --diff` with no `intent.md` | **All changes flagged.** No envelope = nothing whitelisted. | Intent §2 cross-ref logic |
| A8 | `snapshot_diff.py --diff` with no prior snapshot | Creates snapshot and exits **2** (per A1). | Intent §2 |

## Test Design

### test_snapshot_diff.py (22 tests)

Three test classes:

- **TestSnapshotCreation** (12 tests) — `--snapshot` mode: file creation, scoped scanning (`.py` under `scripts/`, `checks/`, `tests/`; `.md` under `commands/`, `docs/`), recursive descent, exclusion of out-of-scope dirs, JSON structure (sorted keys, size, SHA-256 hash per entry).
- **TestDiffMode** (9 tests) — `--diff` mode: clean diff exits 0, in-envelope changes ignored, out-of-envelope changes exit 1 with file named, new/deleted files detected, first-run exits 2, no-intent case flags all, wildcard glob matching.
- **TestFalsification** (1 test) — ADR-003 D3 planted violation: out-of-envelope file modification must be caught.

### test_integration_gate.py (8 tests)

Five test classes:

- **TestExitCodes** (4 tests) — exit 0 on clean project; exit 1 on invariant failure, ruff failure, pytest failure.
- **TestOutputFormat** (1 test) — output logs pass/fail per sub-check.
- **TestNoShortCircuit** (1 test) — Step 4 runs even when Step 3 fails (A2).
- **TestPrerequisites** (1 test) — exit 2 when ruff not on PATH.
- **TestFalsification** (1 test) — ADR-003 D3 planted invariant violation: file-exists pointing to nonexistent file, gate must exit 1 and name the invariant.

### Testing approach

All tests use subprocess invocation against the script CLI, matching the pattern established by `test_invariant_assertions.py`. Temp directories via pytest `tmp_path` fixture provide isolation. No mocks — real file trees, real process execution. Tests are mechanism-agnostic; any Phase 3 implementation satisfying intent.md passes.
