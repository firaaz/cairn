# Phase 2 test approach — compression/phase-4-sweepnotes-required

Two test files, both targeting `close_slice` in `scripts/slice_orchestrator.py`
without touching production code. The shared fixture pattern mirrors
`test_close_slice_hardened.py` (tmp_path git repo, `monkeypatch.chdir`,
`SLICE_YAML`/`DEBUG_DIR` rebinding) so tests run hermetically and share
no state with the real worktree. Repo-level `git config user.email/name`
is set so `_git("commit", ...)` inside `close_slice` never depends on the
caller's global config.

**`test_close_slice_sweepnotes_required.py` — D2 presence check.**
Fixture creates an in-progress slice with NO `integration/sweep-notes.md`.
Seven assertions, one per observable consequence of an aborted close:
(1) `SystemExit` with non-zero `code`; (2) HEAD unchanged, no
`slice: <id> — complete` commit appended; (3) slice.yaml remains
`status: in-progress`; (4) current-slice tree not wiped;
(5) `<slug>-result.json` carries `status: "FAILED"`, non-zero
`exit_code`, and the stable token `reason: "sweepnotes-missing-at-close"`;
(6) stderr cites the absent path;
(7) ordering — slice.yaml is byte-identical before/after, proving the
presence check precedes the status=complete write (precondition for D4
resume reconciliation).

**`test_close_slice_add_surface.py` — staging-surface extension.**
Fixture provides a valid sweep-notes.md so the primary gate passes.
Three RED assertions drive the extension:
(a) a phase-4-written `.claude/sweep.yaml` appears under
`git show HEAD:.claude/sweep.yaml`;
(b) a pre-existing tracked sweep.yaml that phase-4 rewrites lands in the
commit tree (orphan-artifact pattern from commit a8d8f23);
(c) new files under `.claude/sweep-results/` (both `*.md` and `*.txt`,
unknown to the orchestrator by name) are staged wholesale.
Three GREEN assertions guard pre-existing behaviour: `.claude/handoff.md`
still in the commit tree, missing `sweep-results/` does not block close,
and exactly one `slice: <id> — complete` commit is produced regardless
of how much the add surface grows (INV-008 DC-4 sole-commit-source).

Ambiguities flagged and resolved from intent/ADR alone: reason-token
literal (`sweepnotes-missing-at-close`, per intent section 1 example —
mandated stable); result-json filename (`<slug>-result.json` per
`_observability_paths`); exit mechanism (`SystemExit` — matches the
existing `_persist_state` FAILED-terminal pattern). No human escalation
required.
