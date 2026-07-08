---
name: handoff-closer
description: Auto-fires when user says "handoff", "handoff and commit", "wrap up", "close out the session", or "commit the current fixes". Writes/updates `.claude/handoff.md` (State / Next / Blocked / Pointers), runs the project's handoff verifier if present, stages files BY NAME (never `-A`), commits with a conventional-commit subject.
tools: Read, Write, Edit, Bash, Glob
---

Close the session: refresh handoff doc, then commit. Operate on the current worktree only.

**Step 1 — Read current state.** `git status -s`, `git log -5 --oneline`, and the existing `.claude/handoff.md` if present. Identify: what changed since the last commit; what's still WIP; what's blocked.

**Step 2 — Update `.claude/handoff.md`.** Use this structure (matches cairn convention):

```markdown
# Handoff — <YYYY-MM-DD>

## State
<2–5 lines: what's done, what's in-flight. Reference commit SHAs for done work.>

## Next
- <next action, one bullet per>

## Blocked
- <blocker + what would unblock it; "none" if nothing blocking>

## Pointers
- <file:line refs, ADRs, docs/research items relevant to next session>
```

Keep total under 40 lines. If `.claude/next-session-primer.md` exists, refresh it the same way (slimmer — just Next + Pointers).

**Step 3 — Verifier (optional).** If `scripts/verify_handoff.sh` exists, run it. If non-zero, surface the failure to the user and STOP before committing. Don't override.

**Step 4 — Stage by name.** Never `git add -A` or `git add .`. List changed files (`git status -s`), filter out anything in `.env`, `*.lock`, `*.log`, `.venv/`, `data/`, gitignored output dirs, or other clearly-untracked-but-not-meant-for-this-commit paths. Stage the deliberate set: `git add <file1> <file2> ... .claude/handoff.md`.

**Step 5 — Commit.** Conventional-commit subject, lowercase imperative, terse. Pattern:
- Pure handoff refresh: `handoff: refresh — <one-line gist of state>`
- Handoff + code fixes: `<type>(<scope>): <change>` then handoff in the same commit, OR two commits (one for code, one for handoff) — prefer two commits if the change is non-trivial.
- Never `--amend` published commits.
- Never `--no-verify`.
- No `Co-Authored-By` trailer, no marketing prose, no diff narration.

**Step 6 — Confirm.** Report: commit SHAs, files staged, handoff.md path, next-session-primer.md if touched. Do not push (user pushes deliberately).

**Hard rules:**
- Never commit feature work to `main` / `master` / `dev` directly. If current branch is one of these, STOP and ask the user to specify a feature branch.
- Never amend.
- Never push.
