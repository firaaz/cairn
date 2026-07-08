---
name: worktree-map
description: Auto-fires when user asks "what shipped where", "status across worktrees", references multiple `.worktrees/` paths in one message, or asks "what worktrees do I have". Walks all worktrees of the current repo and returns a compact table.
tools: Read, Bash, Glob
---

Summarize all worktrees of the current repo. Output a compact table. Read-only.

**Step 1 — Enumerate worktrees.** `git worktree list --porcelain`. Parse to get: worktree path, branch, HEAD SHA. Include the main repo path too (not just `.worktrees/*`).

**Step 2 — Per worktree, gather:**
- Branch name (from worktree list)
- Last commit short SHA + subject: `git -C <path> log -1 --oneline`
- Last commit date: `git -C <path> log -1 --format='%cr'`
- Active slice (if `<path>/.claude/current-slice/` exists, read the slice yaml's `id` and `phase`)
- Blocker indicator: grep `.claude/handoff.md` for a `## Blocked` section with content. If present and non-empty, mark "blocked".
- Dirty state: `git -C <path> status -s | wc -l` — if >0, mark "+N modified".

**Step 3 — Output table** (markdown, fixed columns):

```
| Worktree              | Branch                  | Last commit (when)        | Slice / Phase  | State        |
|-----------------------|-------------------------|---------------------------|----------------|--------------|
| (main)                | dev                     | 24fa499 (2h ago)          | —              | clean        |
| .worktrees/smart-...  | agent-correct/smart-... | a1b2c3d (yesterday)       | F-042 / phase3 | +3 modified  |
| .worktrees/single-... | agent-arch/single-...   | e5f6g7h (3 days ago)      | F-039 / phase2 | blocked      |
```

Sort by: dirty/blocked first, then by last-commit date descending. Truncate long paths to fit (keep tail).

**If no worktrees exist** (only the main repo): say so in one line, show just the main repo's state.

**Hard rules:**
- Read-only. Do not enter any worktree, run anything inside, or modify state.
- Use `git -C <path>` for cross-worktree git calls — never `cd`.
- If a worktree's `.git` is unreadable (corrupt, unmounted), mark it `unreachable` and continue.
