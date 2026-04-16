---
slice: housekeeping/stale-22k-cleanup
date: 2026-04-16
phase: 1-intent
invariants-touched: [INV-004]
adrs-referenced: []
envelope:
  - "docs/ARCHITECTURE.md"
  - "tests/unit/test_context_budget.py"
out-of-scope:
  - "Budget constants in test_context_budget.py (BUDGET_HARD, BUDGET_ASPIRATIONAL, D1_BASELINE) — SLICE-017 already set these to the 30k re-baseline"
  - "INV-004 paragraph body text in docs/ARCHITECTURE.md — SLICE-017 already re-baselined the ceiling to ≤30,000 and added the 2.1.110 / SLICE-017 provenance"
  - "Regression-assertion lines in test_context_budget.py (line 121 docstring mention, lines 148–149 assertions) — these intentionally contain the literal ``≤22,000`` as a guard against the stale value creeping back into ARCHITECTURE.md"
  - "All other ADRs, hooks, commands, measurement files, and uv.lock"
---

### What and Why

Two stale ``≤22,000`` / ``22k`` references survived the SLICE-017 re-baseline and now contradict the canonical invariant text. The documentation drift causes two concrete harms:

1. `docs/ARCHITECTURE.md:46` — the `invariant-check INV-004` block's `description` field says "Points to the test suite that machine-checks the 22k token budget", which disagrees with the surrounding paragraph that declares ≤30,000 at line 41. A reader auditing INV-004 gets two different ceilings within seven lines.
2. `tests/unit/test_context_budget.py:103` — `test_inv004_turn1_token_budget`'s docstring still reads "turn-1 total context ≤22,000 tokens on a fresh 'hi' session", while its assertion (line 107) checks `tokens <= BUDGET_HARD` where `BUDGET_HARD = 30_000` (line 17). Docstring-vs-assertion divergence is exactly the kind of drift that erodes the test as reviewable documentation of the invariant.

This slice is a pure docs/docstring correction — it does not touch any enforcement path, any constant, any paragraph that has already been re-baselined, and does not move INV-004's ceiling. INV-004's semantic statement is already ≤30,000; this slice aligns the two stragglers.

### Specification Detail

**Change 1 — `docs/ARCHITECTURE.md` line 46 (description inside the INV-004 invariant-check block).**

Before:
```
description: "Points to the test suite that machine-checks the 22k token budget"
```

After:
```
description: "Points to the test suite that machine-checks the 30k token budget"
```

The change is confined to the `description:` string inside the fenced `invariant-check INV-004` block that begins at line 43. No other line in `docs/ARCHITECTURE.md` is modified. The paragraph at line 41 (the invariant text itself, including the "≤30,000 total tokens" ceiling and the SLICE-017 / 2.1.110 provenance) is untouched.

**Change 2 — `tests/unit/test_context_budget.py` line 103 (docstring of `test_inv004_turn1_token_budget`).**

Before:
```python
    """INV-004 — turn-1 total context ≤22,000 tokens on a fresh 'hi' session."""
```

After:
```python
    """INV-004 — turn-1 total context ≤30,000 tokens on a fresh 'hi' session."""
```

The change is confined to this one-line docstring. The function body, decorator, and assertion message are untouched. In particular, `BUDGET_HARD = 30_000` at line 17 continues to be the sole source of the numeric ceiling the test actually enforces; the docstring edit brings the human-readable claim back into alignment with the machine-checked value.

**Explicit non-changes (regression guards).**

These lines MUST retain the literal string ``≤22,000`` or ``22,000`` exactly as they currently appear:

- `tests/unit/test_context_budget.py:121` — inside the docstring of `test_inv004_architecture_rebaselined`: the clause `the stale ``≤22,000`` literal is gone`. This clause *documents* the regression check and intentionally names the stale value it is guarding against.
- `tests/unit/test_context_budget.py:148` — the assertion `assert "≤22,000" not in paragraph, (`. This is the regression guard itself — removing the literal here would neuter the assertion.
- `tests/unit/test_context_budget.py:149` — the f-string `f"INV-004 still contains stale '≤22,000' literal.\nParagraph: {paragraph!r}"`. This is the failure message paired with the assertion on 148; the literal must match line 148 so the failure message names the exact string that triggered it.

A validation test will pin these three lines explicitly so that a future cleanup pass cannot remove them under the mistaken belief that they are more 22k drift.

### Boundary

Out of scope for this slice (each already addressed or intentionally preserved):

- Any change to the BUDGET_HARD / BUDGET_ASPIRATIONAL / D1_BASELINE constants in `test_context_budget.py` — SLICE-017 set these.
- Any change to the INV-004 paragraph prose in `docs/ARCHITECTURE.md` — SLICE-017 already re-baselined it with the ≤30,000 ceiling and the "SLICE-017 (2026-04-16) for Claude Code 2.1.110" provenance.
- Any edit to the module-level docstring of `test_context_budget.py` (lines 1–8) — it already reads "asserts ≤30k".
- Any edit to the measurement file at `docs/plans/measurements/2026-04-12-slice-003.txt` — out of envelope, written by the test at runtime.
- Any new ADR, any change to hook scripts, any change to slash commands, any `uv.lock` or `pyproject.toml` edit.
- The 22,000 numeric literal does not appear anywhere else in the envelope files outside the five lines enumerated above (two being updated, three being preserved); the slice does not need to sweep for additional occurrences.

### Verification

A Phase 2 test (new, added to `tests/unit/test_context_budget.py` — the envelope permits it) will assert, using plain text reads (no pytest fixtures beyond what already exists in that module):

1. **ARCHITECTURE.md INV-004 invariant-check block has the corrected description.** Read `docs/ARCHITECTURE.md`, locate the fenced block beginning `` ```invariant-check INV-004 `` and ending at the next closing `` ``` ``, and assert it contains the substring `machine-checks the 30k token budget` AND does NOT contain `machine-checks the 22k token budget`. Scoping to this block (rather than the whole file) prevents false positives / negatives if "22k" ever legitimately appears elsewhere in ARCHITECTURE.md.

2. **`test_inv004_turn1_token_budget` docstring reflects the 30,000 ceiling.** Read `tests/unit/test_context_budget.py` as text, locate the `def test_inv004_turn1_token_budget` line, and assert the next non-blank line is the docstring containing `≤30,000 tokens` AND does NOT contain `≤22,000 tokens`. Text-level scan (not `__doc__` attribute) avoids importing the module, which would require the `claude` CLI skip logic to fire.

3. **Regression-guard lines in `test_inv004_architecture_rebaselined` are preserved.** Read the same file as text and assert all three of the following exact substrings are still present somewhere in the file body:
   - `the stale ``≤22,000`` literal is gone` (the docstring clause)
   - `assert "≤22,000" not in paragraph` (the assertion)
   - `INV-004 still contains stale '≤22,000' literal` (the assertion's failure-message prefix)

   If any one is missing, the validation test fails with a message that names the missing line, pointing the Phase 3 worker at the specific regression-guard they broke.

4. **The pre-existing `test_inv004_architecture_rebaselined` test continues to pass.** It already asserts `"≤30,000 total tokens" in paragraph`, `"≤22,000" not in paragraph`, `"SLICE-017" in paragraph`, and `"2.1.110" in paragraph` against the INV-004 *paragraph body* (lines 41). Since this slice does not touch that paragraph, that test should stay green — any red there signals an out-of-envelope edit and Phase 3 must be rolled back.

5. **Full test suite passes.** `uv run python -m pytest` green under Phase 4.

6. **Invariant validator passes.** `uv run python .slice-system/scripts/validate_architecture.py` exits zero.

7. **Invariant evidence table (Phase 4).** INV-004 — PASS. Evidence:
   - `docs/ARCHITECTURE.md:41` continues to state "≤30,000 total tokens" (untouched by this slice).
   - `docs/ARCHITECTURE.md:46` now states "30k token budget" (updated).
   - `tests/unit/test_context_budget.py:17` continues to set `BUDGET_HARD = 30_000` (untouched).
   - `tests/unit/test_context_budget.py:103` docstring now states "≤30,000 tokens" (updated).
   - `tests/unit/test_context_budget.py:148` continues to assert `"≤22,000" not in paragraph` (regression guard preserved).
