---
slice: housekeeping/inv004-rebaseline
date: 2026-04-16
phase: 1-intent
invariants-touched: [INV-004]
adrs-referenced: []
envelope:
  - "tests/unit/test_context_budget.py"
  - "docs/plans/measurements/2026-04-12-slice-003.txt"
  - "docs/ARCHITECTURE.md"
  - "uv.lock"
out-of-scope:
  - "Dedicated ADR for the context budget (the ARCHITECTURE.md 'pending ADR' note stays unchanged)"
  - "Cairn tier-1 prune investigation to reduce session-start overhead"
  - "D3 bypass classification substrate implementation (ADR landed; separate slice queued)"
  - "validate_architecture.py flat-slug widening (identifier-scheme follow-on)"
  - "reversibility-guard.sh relative-path bypass (identifier-scheme follow-on)"
  - "Refactor of _run_and_measure() or the measurement harness"
  - "Changes to which token fields are summed or how 'turn-1' is defined"
---

### What and Why

CC binary drifted from 2.1.107 to 2.1.110 and added ~8k tokens of system-prompt overhead outside cairn's control, pushing INV-004 turn-1 measurement to 28511 vs. the 22000 budget. Integration sweep #11 failed on this (and would fail every subsequent sweep) until the invariant is re-baselined.

This slice raises `BUDGET_HARD` to 30000 (with aspirational `BUDGET_ASPIRATIONAL=25000`), amends the INV-004 text in `docs/ARCHITECTURE.md` inline, and commits two carry-over drifts that have blocked sweeps since #5 (`uv.lock` requires-python sync, and the measurement file re-generation). The new ceiling accepts the CC drift as operational reality while preserving budget discipline at ~5% headroom above current measurement. A dedicated context-budget ADR remains pending per the existing ARCHITECTURE.md note — not triggered by this slice.

### Specification Detail

- `tests/unit/test_context_budget.py`:
  - `BUDGET_HARD = 30_000` (was `22_000`)
  - `BUDGET_ASPIRATIONAL = 25_000` (was `20_000`)
  - `D1_BASELINE = 27_314` unchanged — it is the historical CC-2.1.107 reference point used by `_record_measurement` to compute delta arithmetic, not itself a budget
  - Test name, skip predicate, measurement formula, and all other logic unchanged
  - The top-of-file docstring "asserts ≤22k" is updated to "asserts ≤30k"

- `docs/ARCHITECTURE.md`, INV-004 paragraph:
  - "≤22,000 total tokens" → "≤30,000 total tokens"
  - Append provenance sentence naming SLICE-017 and CC 2.1.110 as the re-baseline trigger (keeps the "ADR-002; dedicated ADR pending" parenthetical intact)
  - Invariant-check block (`type: test-ref`, `pattern: tests/unit/test_context_budget.py`, description) unchanged

- `docs/plans/measurements/2026-04-12-slice-003.txt`:
  - Re-generated deterministically by the test run under the new budget constants
  - Format produced by `_record_measurement` stays the same (6 lines: CC version / Turn-1 tokens / D1 baseline / Delta / Hard budget / Aspirational)
  - Committed after the test passes, replacing the uncommitted CC-2.1.107 baseline with the CC-2.1.110 re-baseline state

- `uv.lock`:
  - Committed as-is. The `requires-python = ">=3.11"` diff already matches `pyproject.toml:5` — no edit required, this is a catch-up commit
  - Not regenerated via `uv sync` during the slice; the current file is the target state

### Boundary

Explicitly out of scope:
- Adding new fixtures, parametrizing by CC version, caching measurements, or refactoring `_run_and_measure()`
- Writing a new ADR (context budget or otherwise)
- Pruning cairn tier-1 content to reduce session-start overhead (if pursued, that is a separate slice)
- D3 bypass classification substrate (`log format`, `snapshot_diff` parser, reclassify log) — ADR landed, implementation is a separate slice
- `validate_architecture.py` flat-slug widening (identifier-scheme follow-on)
- `reversibility-guard.sh` relative-path bypass hardening (identifier-scheme follow-on)
- Changing the `.slice-system` symlink or hook dependency contracts
- Any edit to `commands/claude-code/*.md`, `checks/*.sh`, or `scripts/*` outside the envelope

### Verification

Concrete, evidence-based checks (Phase 4 Auditor produces citations for each):

1. `uv run pytest tests/unit/test_context_budget.py -v` — `test_inv004_turn1_token_budget` PASSES (not skipped, not xfailed). Recorded tokens ≤ 30_000.

2. `docs/plans/measurements/2026-04-12-slice-003.txt` after test run:
   - Line 1: `CC version: 2.1.110 (Claude Code)` (or whatever `claude --version` reports at measurement time)
   - Line 5: `Hard budget (30000): PASS`
   - Line 6: `Aspirational (25000): PASS` or `MISS` — whichever is actual; must not be stale "(20000)" or "(22000)" text
   - File is clean in `git status` after the closing commit

3. `uv run pytest` (full suite) — no regressions; all previously-passing tests still pass

4. `uv run python .slice-system/scripts/validate_architecture.py` exits 0; INV-004 invariant-check block still resolves to `tests/unit/test_context_budget.py`

5. `docs/ARCHITECTURE.md` INV-004 paragraph:
   - Contains literal "≤30,000 total tokens"
   - Does not contain "≤22,000" in the INV-004 invariant definition
   - Provenance sentence citing SLICE-017 + CC 2.1.110 present
   - Invariant-check fenced block unchanged (grep `type: test-ref` + `pattern: "tests/unit/test_context_budget.py"`)

6. `git status --short` — no residue from `uv.lock` or `docs/plans/measurements/2026-04-12-slice-003.txt` after the final commit; envelope fully clean

7. `python3 scripts/integration_gate.py` exits 0 — Phase 4 sanity check that the gate is green for the first time since sweep #11 opened
