---
slice: housekeeping/post-slice-a-tidy
date: 2026-04-19
phase: 1-intent
invariants-touched: []
adrs-referenced: []
envelope:
  - "tests/unit/test_slice_orchestrator_state_machine.py"
  - ".claude/platform-probe.md"
  - ".claude/current-slice/*"
out-of-scope:
  - "orchestrator code paths (brief persistence, feature-file scanning) — dogfooding findings, separate slice"
  - "8 pre-existing baseline failures (test_adr_rename_sweep, test_hook_relpath_bypass, test_hook_tolerance)"
  - "INV-004 turn-1 budget borderline — separate slice when tripped"
  - "adjustments to .gitignore (already correct)"
---

### What and Why

First slice under the compressed dispatch protocol, scoped to four janitorial items that accumulated during or after Slice A (compression/infrastructure). None of them change runtime behaviour; they close protocol-adjacent loose ends so the next behaviour-bearing slice starts from a clean substrate. This slice is also the first real dogfood of the orchestrator — findings get recorded in integration notes for future protocol work.

### Specification Detail

**A. Ruff F841 — `tests/unit/test_slice_orchestrator_state_machine.py:147`.**
The variable `calls: list[dict] = []` is declared in `test_v2_5_run_phase_loop_ok_advances_phase` and never read. Remove the line. No other changes to the test body; assertion semantics untouched.

**B. `.claude/handoff.md` gitignore reconciliation — verify-only.**
`.gitignore` line 14 already contains `.claude/handoff.md`; `git ls-files .claude/handoff.md` returns empty. Verification step only: no file edits. Recorded in Phase 4 sweep notes as "no drift".

**C. `.claude/platform-probe.md` — retire.**
The file is slice-scoped evidence (frontmatter: `slice: compression/infrastructure, phase: 3-implementation, purpose: V8 evidence`). That slice is closed at `a09e5e8`. Content is preserved in git history. Action: `git rm .claude/platform-probe.md`. Do not replace with a stub — the retirement IS the outcome.

**D. Empty `.claude/current-slice/` subdirs — verify-only.**
`validation/`, `implementation/`, `integration/` existed as empty dirs in the working tree after the prior close-out wipe (`a09e5e8`). Git does not track empty dirs, so `ls -la .claude/current-slice/` now shows only `slice.yaml`. No action required; verification step confirms no pruning is outstanding.

### Boundary

**Out of scope explicitly:**
- Any change to the orchestrator (`scripts/slice_orchestrator.py`) or phase agents (`.claude/agents/*.md`). The two dogfooding findings (brief-loss between init and phase-loop; writer not scanning existing features) are recorded in integration notes and handed off to a follow-up slice.
- Ruff/lint fixes in any file other than the one F841 line.
- `.gitignore` edits of any kind.
- `.claude/handoff.md` content edits — only gitignore-status verification.

### Verification

1. `uv run ruff check tests/unit/test_slice_orchestrator_state_machine.py` exits 0 with no F841 finding.
2. `uv run python -m pytest tests/unit/test_slice_orchestrator_state_machine.py` passes — the removed line was genuinely unused and does not affect test outcome.
3. `git ls-files .claude/platform-probe.md` returns empty (file removed from index).
4. `git ls-files .claude/handoff.md` returns empty AND `.gitignore` line 14 still reads `.claude/handoff.md` — B verify-only confirmation.
5. `ls .claude/current-slice/` shows `slice.yaml` and any active Phase 2+ artifacts only — no leftover empty subdirs from prior slice.
6. Full suite: `uv run python -m pytest` shows no new failures beyond the 8 pre-existing baseline failures documented in `.claude/handoff.md` (Blocked / Pending).
7. Architecture validator: `uv run python .slice-system/scripts/validate_architecture.py` exits 0.
8. Integration notes at `.claude/current-slice/integration/sweep-notes.md` contain a "Dogfooding findings" section listing at minimum: (i) brief-loss between `init_new_slice` and `run_phase_loop` dispatches; (ii) writer not scanning `.claude/features/` before proposing slice_id.
