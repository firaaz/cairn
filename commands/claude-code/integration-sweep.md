# /integration-sweep

Run a cross-slice integration check to catch failures no individual slice could see.

Usage: `/integration-sweep`

## Rules

1. Load invariants from `docs/ARCHITECTURE.md` § Invariants. If stale, suggest `/refresh-architecture` first.
2. Enumerate cross-slice failure modes BEFORE checking: import conflicts, schema drift, tool contract breaks, config conflicts, boundary violations, invariant interactions.
3. Run `python3 scripts/integration_gate.py` — mechanizes invariant checking (delegates to `validate_architecture.py` Check D) and cross-module checks (ruff + pytest). Exit 0 = pass, 1 = fail, 2 = missing prerequisites.
4. Run `python3 scripts/snapshot_diff.py --diff` — detects out-of-envelope file changes since last snapshot. Exit 0 = clean, 1 = out-of-envelope changes found. Then `python3 scripts/snapshot_diff.py --snapshot` to update the baseline.
5. Review `git log --oneline -20` for multi-module commits, workarounds, out-of-envelope edits, provisional ADRs treated as firm.
6. Staleness check: cross-reference `handoff.md` § Blocked / Pending entries against git history — flag any items that are already resolved (completed slices, merged work, superseded ADRs).
7. Write report to `.claude/current-slice/integration/sweep-notes.md` (if slice active) or `.claude/sweep-results/<date>-sweep.md`. Commit results.
8. Update `.claude/sweep.yaml` → `last-sweep-at-slice`.
9. Failures → new slices via normal pipeline. Do NOT retroactively edit completed slices.

## Load full

- If ARCHITECTURE.md is missing or validator fails: read integration-sweep.full.md for failure-mode enumeration table and cross-module check commands.
