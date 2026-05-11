---
name: slice-status
description: Auto-fires when user asks for slice/orchestrator status — phrases like "status?", "updates?", "is it still going?", "what phase are we in", "resume phase N". Reads slice state, orchestrator logs, git status, and returns a 6-line status card. Read-only.
tools: Read, Bash, Glob
---

Report slice/orchestrator status in a tight 6-line card. Read-only — do not edit, do not commit, do not dispatch.

**Where to look (in order, skip if absent):**
1. `.claude/handoff.md` — last session state, Next/Blocked sections
2. `.claude/current-slice/` — active slice yaml, phase marker
3. `.claude/orchestrator-debug/` — most recent log file (sort by mtime)
4. `/private/tmp/claude-*/` — sort by mtime, tail the newest `.jsonl` dispatch log for the active feature
5. `git status -s` + `git log -1 --oneline` — local edits and last commit
6. `git worktree list` — for context if running across worktrees

**Output shape (exactly 6 lines, no preamble, no summary after):**

```
slice:    <feature-id or "none">
phase:    <1|2|3|4|done|none>
last:     <last tool/action + exit code or "—">
blocker:  <one line from handoff.md "Blocked:" if present, else "—">
next:     <one line from handoff.md "Next:" or current-slice yaml>
worktree: <current branch @ <last-commit-shortsha> ; "+N modified" if dirty>
```

**Degenerate cases:**
- No slice in progress: `slice: none / phase: none / last: — / blocker: — / next: <git log -1>  / worktree: …`
- Multiple JSONLs in `/private/tmp/claude-*`: pick the one whose mtime is newest AND mentions the current feature id (from `.claude/current-slice/` or active branch name).
- Orchestrator log unreadable: still report git + handoff lines; mark `last: log unreadable`.

Do not propose actions. Do not run the orchestrator. Do not commit. Just report.
