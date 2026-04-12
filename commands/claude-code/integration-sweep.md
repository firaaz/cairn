# /integration-sweep

Run a cross-slice integration check to catch failures no individual slice could see.

Usage: `/integration-sweep`

## Rules

1. Load invariants from `docs/ARCHITECTURE.md` § Invariants. If stale, suggest `/refresh-architecture` first.
2. Enumerate cross-slice failure modes BEFORE checking: import conflicts, schema drift, tool contract breaks, config conflicts, boundary violations, invariant interactions.
3. Check each invariant against codebase with grep/file-read evidence. Pass/fail table with file:line citations.
4. Cross-module checks: import integrity, `ruff check`, type check (if available), full test suite, schema check (if applicable).
5. Review `git log --oneline -20` for multi-module commits, workarounds, out-of-envelope edits, provisional ADRs treated as firm.
6. Write report to `.claude/current-slice/integration/sweep-notes.md` (if slice active) or `.claude/sweep-results/<date>-sweep.md`. Commit results.
7. Update `.claude/sweep.yaml` → `last-sweep-at-slice`.
8. Failures → new slices via normal pipeline. Do NOT retroactively edit completed slices.

## Load full

- If ARCHITECTURE.md is missing or validator fails: read integration-sweep.full.md for failure-mode enumeration table and cross-module check commands.
