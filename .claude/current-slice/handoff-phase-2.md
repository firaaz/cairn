---
slice: integration-gate/configurable-pytest-timeout
phase: 2-validation
branch: feature/identifier-scheme
as-of: 2026-04-17 9e3ef4b
---

## State
Phase 2 tests committed at 9e3ef4b — 20 tests in `tests/unit/test_integration_gate_timeout.py`, 2 pure-RED (env-override checks 1 + 2) and 18 contract-fixation invariants. Phase 3 gate met: tests committed, envelope respected, `scripts/integration_gate.py` untouched.

## Next
Builder: add `CAIRN_PYTEST_TIMEOUT` / `CAIRN_RUFF_TIMEOUT` reads inside `_run_step4b` / `_run_step4a`; accept positive-int only; fall back silently to 120 / 60 on missing/empty/non-numeric/zero/negative/float; pass via `timeout=` kwarg on `subprocess.run`. Only code change is the kwarg value.

## Blocked / Pending
- Carry-over: `docs/plans/measurements/2026-04-12-slice-003.txt` uncommitted → handoff obs §8.1 #8.
- Out-of-scope remains: Step 3 validator timeout (`scripts/integration_gate.py:65`), pytest `-x` flag, raising defaults, consumer docs, CLI/config surfaces.

## Pointers
- `.claude/current-slice/intent.md` — envelope, spec, 10 verification checks; Phase 3 sole spec input.
- `tests/unit/test_integration_gate_timeout.py` — RED suite Phase 3 must turn green.
- `scripts/integration_gate.py:82-121` — `_run_step4a` / `_run_step4b`; hardcoded `timeout=60` line 90, `timeout=120` line 112.
