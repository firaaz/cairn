# Phase 3 implementation notes — SLICE-018

Decisions the intent.md did not pin down, recorded as the Builder so Phase 4
can audit without reconstruction.

## D1 — Two case blocks instead of one for Write

The pre-slice hook had a single `case "$FILE"` block in the Write branch
covering `.env`, lockfiles, and ADR patterns together. The fix splits this
into two case blocks within the same `if [ "$TOOL" = "Write" ]`:

1. `case "$FILE" in` — `.env` and lockfile patterns (unchanged, raw `$FILE`).
2. `case "$CANONICAL" in` — ADR exempt + deny patterns.

Reason: `.env` / lockfile patterns already use `*.env`, `*uv.lock` (no leading
`*/` requirement), so they match every input shape against the raw path.
Rewriting them against canonical form would not narrow the domain (intent §4
allows additions but forbids narrowing) but would obscure that those checks
were already correct. The split makes the canonical-form rewrite localized
to the ADR clauses, which were the actual bypass site.

The Edit branch needs only one case (ADR-only), so it stays as a single
`case "$CANONICAL" in`.

## D2 — `-f` probe uses `$PROJECT_ROOT/$CANONICAL` exactly as intent §3 directs

No alternative considered. Intent §3 mandates an absolute path for the
existence test; the canonical form is by construction relative-to-root, so
prepending `$PROJECT_ROOT/` is the obvious composition. Today's behavior on
absolute inputs is preserved (canonical form strips the prefix, then we
re-prepend `$PROJECT_ROOT`, yielding the original absolute path).

## D3 — Editorial-fix log line keeps raw `$FILE` reference, not canonical

Intent §6 allowed either choice provided it was consistent. Kept the existing
`echo "ADR_EDITORIAL_FIX: allowing edit to $FILE"` form so the log preserves
the operator's view of which path the edit was attempted against. This also
keeps the historical log format byte-stable. Test V7's `_snapshot_and_run`
only asserts the substring `identifier-scheme` appears in a new line, which
is satisfied by either form.

## D4 — Log file path stays relative (`.claude/adr-editorial-fixes.log`)

Not switched to `$PROJECT_ROOT/.claude/adr-editorial-fixes.log`. The hook is
invoked with CWD = project root by Claude Code today, and the slice tests
explicitly set `cwd=str(CAIRN_ROOT)` in `_run_hook`. Changing to an absolute
log path would be a scope creep beyond what intent §6 directs and would add
an asymmetry vs. the `2>/dev/null || true` guard already there (which silently
tolerates write failures). Held the line.

## D5 — `PROJECT_ROOT` derivation hoisted above both Write and Edit branches

A single derivation site instead of repeating the assignment inside each
branch. This is a minor structural choice; identical to scope-guard.sh's
top-of-file pattern. Avoids re-running `git rev-parse` per branch.

## D6 — Pre-existing envelope-compliance tests fire on uncommitted Phase 3 WIP

`tests/unit/test_sweep_debt_cleanup.py::test_v4_envelope_compliance` and
`tests/unit/test_slice_005_design_decomposition.py::test_v7_envelope_compliance`
both check `git diff --name-only HEAD` against historical slice envelopes
(SLICE-007 and SLICE-005 respectively). They fail for any uncommitted file
outside those old envelopes — including this slice's `checks/reversibility-guard.sh`
edit. Verified by `git stash` of the WIP edit: both tests pass against a clean
tree. They will pass once the Phase 3 implementation commit lands.

Not in scope for this slice to fix the staleness of those historical tests.
Phase 4 will see them green after the commit; the integration sweep can decide
whether to re-shape them into branch-aware checks in a separate slice.
