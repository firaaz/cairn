---
slice: housekeeping/stale-22k-cleanup
date: 2026-04-16
phase: 2-validation
role: Skeptic
input: .claude/current-slice/intent.md
output: tests appended to tests/unit/test_context_budget.py
---

### Ambiguity enumeration

All five ambiguities resolved by grounding in the current file state of the envelope — no human escalation.

1. **Regression-guard substrings (intent verification #3).** Intent lists three substrings that must remain in `tests/unit/test_context_budget.py`. Confirmed verbatim at lines 121, 148, 149 (read at as-of commit `cf4519a`). Resolution: pin all three as literal substrings; use plain `in file_text` checks.
2. **"Next non-blank line" after `def test_inv004_turn1_token_budget` (intent verification #2).** Confirmed: the function body's first non-blank line is the docstring at line 103. No blank line between def and docstring. Resolution: scan forward from the def line and take the first non-blank line.
3. **INV-004 fenced-block delimiters (intent verification #1).** Confirmed opening at ``docs/ARCHITECTURE.md:43`` (`` ```invariant-check INV-004 ``) and closing at line 47 (` ``` `). Resolution: locate the exact opening fence, then read until the first subsequent line equal to ` ``` `.
4. **Skip logic for new tests.** Intent is explicit: text-level reads were chosen specifically so the new tests do NOT require the `claude` CLI skip fixture. Resolution: the three new tests run unconditionally — no `@pytest.mark.skipif` decorator.
5. **Test 3 is a guardrail, not a classical RED.** Intent verification #3 pins lines that already hold the correct values; the test passes today and must keep passing. This is a forward-looking safety net against Phase 3 overreach, not a driver for Phase 3 to make a change. Classical TDD expects each new test to fail first. Resolution: tests 1 and 2 provide the RED that drives Phase 3 (the two stale literals remain in the codebase at commit `cf4519a`); test 3 is committed as a preserved-invariant pin with a failure message that names the missing guard. This deviation from strict RED is documented here and is load-bearing for the slice's self-stated verification.

### Test design

Three new tests appended to `tests/unit/test_context_budget.py` — the envelope explicitly permits this.

- `test_inv004_invariant_check_block_description_rebaselined`
  - Reads `docs/ARCHITECTURE.md`. Locates the line starting `` ```invariant-check INV-004 `` and the next line equal to ` ``` `. Extracts the lines between them (the block body).
  - Asserts `"machine-checks the 30k token budget"` substring is present.
  - Asserts `"machine-checks the 22k token budget"` substring is NOT present.
  - Expected state at commit `cf4519a`: FAIL — current line 46 still reads `"22k"`.
- `test_inv004_turn1_token_budget_docstring_rebaselined`
  - Reads `tests/unit/test_context_budget.py` as text. Locates `def test_inv004_turn1_token_budget(`. Takes the first non-blank line after it.
  - Asserts that line contains `≤30,000 tokens`.
  - Asserts that line does NOT contain `≤22,000 tokens`.
  - Expected state at commit `cf4519a`: FAIL — current line 103 still reads `≤22,000 tokens`.
- `test_inv004_regression_guards_preserved`
  - Reads `tests/unit/test_context_budget.py` as text.
  - For each of the three required substrings, asserts presence; failure message names the missing substring.
  - Required substrings (literal, copied from intent.md, confirmed present at commit `cf4519a`):
    - `` the stale ``≤22,000`` literal is gone ``
    - `` assert "≤22,000" not in paragraph ``
    - `` INV-004 still contains stale '≤22,000' literal ``
  - Expected state at commit `cf4519a`: PASS (guardrail, not classical RED — see ambiguity #5).

### RED verification plan

1. Run `uv run python -m pytest tests/unit/test_context_budget.py -v` in the worktree.
2. Expect:
   - `test_inv004_invariant_check_block_description_rebaselined` — FAIL, message naming the stale `22k` substring.
   - `test_inv004_turn1_token_budget_docstring_rebaselined` — FAIL, message naming the stale `≤22,000` substring in the docstring line.
   - `test_inv004_regression_guards_preserved` — PASS (guardrail).
   - `test_inv004_architecture_rebaselined` — PASS (untouched, already green at `cf4519a`).
   - `test_inv004_turn1_token_budget` — SKIPPED (claude CLI likely absent in CI-style run; not relevant to this slice).
3. If any FAIL message does not name the stale substring it's catching, revise the test message (not the assertion) so Phase 3 gets a usable pointer.
4. If `test_inv004_regression_guards_preserved` fails at this stage, the intent's premise is wrong (a regression guard is already gone) — STOP and escalate to the user.

### Non-actions (Skeptic anti-behaviors)

- No edit to `docs/ARCHITECTURE.md` in this phase. The stale `22k` in the invariant-check block's `description:` field is Phase 3's job.
- No edit to the line 103 docstring. Phase 3's job.
- No edit to any constant, enforcement path, or regression-guard line.
- No implementation notes. Phase 3 receives `intent.md` + these tests only; it does NOT read this approach.md.
