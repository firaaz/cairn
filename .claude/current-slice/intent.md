---
slice: integration-gate/configurable-pytest-timeout
date: 2026-04-17
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "scripts/integration_gate.py"
  - "tests/unit/test_integration_gate*.py"
out-of-scope:
  - "Step 3 validator timeout (scripts/integration_gate.py:65) — no bypass evidence, not in directive"
  - "pytest `-x` short-circuit flag (separate concern from sweep #14 obs §8.2)"
  - "Raising default timeout values — defaults must preserve cairn-self behavior"
  - "Consumer-side documentation or example env configs"
  - "CLI flag or config-file mechanism — env var is the only surface"
---

### What and Why

`scripts/integration_gate.py` hardcodes `timeout=60` on the ruff subprocess (line 90) and `timeout=120` on the pytest subprocess (line 112). Downstream consumers with larger suites — notably `complex-rag-analysis` at ~917s — exceed the pytest ceiling, triggering 5 of the 10 most recent D3 bypasses. Those bypasses are false infrastructure-class failures; they erode signal in `.claude/d3-bypasses.log` and force operators past a gate that would otherwise pass. This slice makes both timeouts overridable via environment variables while preserving cairn-self defaults, so downstream repos can raise the ceiling without cairn raising its own.

### Specification Detail

**Environment variables.**
- `CAIRN_PYTEST_TIMEOUT` — integer seconds, consumed by `_run_step4b`. Default `120` when unset, empty, or invalid.
- `CAIRN_RUFF_TIMEOUT` — integer seconds, consumed by `_run_step4a`. Default `60` when unset, empty, or invalid.

**Parsing contract.**
- Values are read inside each `_run_step*` function at call time (not at module import) so tests can `monkeypatch.setenv` around a single invocation.
- A value is accepted only if it parses as a positive integer (`int(value) > 0`). Any other form — missing, empty string, non-numeric, zero, negative, float — falls back silently to the default. Silent fallback is intentional: a `subprocess.TimeoutExpired` on a zero or negative timeout would be a worse failure mode for consumers than a working default, and we do not want gate output polluted with config-warning lines.

**Behavior preserved.**
- `subprocess.run(..., timeout=<value>)` is the only behavior change. No logging, no stdout echo, no CLI flag, no config file.
- Exit-code contract (0 / 1 / 2) unchanged.
- Output message strings unchanged (existing PASS / FAIL / "timed out" messages remain character-for-character identical).
- Step 3 validator timeout at line 65 remains hardcoded at 60s — out of scope.
- The `-x` short-circuit flag on pytest remains — out of scope.

### Boundary

- No change to Step 3 (`_run_step3`) timeout handling.
- No change to pytest invocation flags (`-x`, `--tb=short` preserved).
- No change to ruff invocation arguments.
- No change to default values — cairn-self behavior unchanged when env is empty.
- No new CLI surface, no new config file, no new logging.
- No change to `main()` control flow, `_check_prerequisites`, or `_find_validator`.
- No change to consumer-facing documentation in this slice (a docs touch-up, if needed, is a follow-up).

### Verification

Concrete checks (Phase 2 validation suite realizes each):

1. **Env override takes effect (pytest).** With `CAIRN_PYTEST_TIMEOUT=300` set and `subprocess.run` mocked, `_run_step4b` passes `timeout=300` to `subprocess.run`.
2. **Env override takes effect (ruff).** With `CAIRN_RUFF_TIMEOUT=10` set and `subprocess.run` mocked, `_run_step4a` passes `timeout=10` to `subprocess.run`.
3. **Default preserved (pytest).** With no env var, `_run_step4b` passes `timeout=120`.
4. **Default preserved (ruff).** With no env var, `_run_step4a` passes `timeout=60`.
5. **Empty string falls back to default.** `CAIRN_PYTEST_TIMEOUT=""` → `timeout=120`. Same for ruff.
6. **Non-numeric falls back to default.** `CAIRN_PYTEST_TIMEOUT="abc"` → `timeout=120`.
7. **Zero falls back to default.** `CAIRN_PYTEST_TIMEOUT="0"` → `timeout=120`.
8. **Negative falls back to default.** `CAIRN_PYTEST_TIMEOUT="-5"` → `timeout=120`.
9. **Silent fallback — no stderr pollution.** Invalid values do not emit warnings to stdout or stderr (gate output character-identical to current).
10. **Exit-code contract intact.** Existing `tests/unit/test_integration_gate.py` assertions for exit codes 0 / 1 / 2 continue to pass.
