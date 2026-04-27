# /dev-mode

Cairn-internal morning briefing. Five sections, ~2500 chars. Cairn-the-project dev aid — not part of cairn-the-methodology, not shipped to consumers.

Usage: `/dev-mode`

## Cairn-detection guard

Before any data gathering, verify `commands/claude-code/start-slice.md` exists in cwd. If absent, emit one line and stop:

```
/dev-mode is cairn-internal — run from inside the cairn repo (any worktree).
```

No git, file, or MCP calls below this guard.

## Dashboard output

Fixed five-section template. Every section has a defined empty-state line so the dashboard is always five sections tall. Header line shows project name + ISO timestamp.

```
DEV MODE — cairn — <YYYY-MM-DD HH:MM>

WORKTREES
  <branch>           <dirty>   <ahead-of-dev>   <flag?>
  …

SLICE
  <id> · status: <status>
  (or: No active slice — /start-slice to open one)

FEATURES
  <id>   <slice-count> slices   "<truncated-name>"
  …

GH PROJECTS (cairn board)
  In Progress (<n>)   <items>
  Blocked (<n>)       <items>
  Todo (top 3)        <items>
  (or: GH Projects MCP not configured — see .local/README.md §2)

DOC HEALTH
  Plan-docs >Nd:   <stale>/<total>   (oldest: <date>)
  Lessons:         <total>
  Memories >Nd:    <stale>/<total>
```

## Source contract

1. **Worktrees** — `git worktree list --porcelain`. For each worktree:
   - Branch from `branch refs/heads/<name>` line; fall back to short SHA if detached.
   - Dirty count via `(cd <path> && git status --porcelain | wc -l)`. Render `clean` if 0, `+N mod` otherwise.
   - Ahead-of-dev count via `git rev-list --count <branch>..dev` from the main worktree's git dir. Render `N ahead of dev` (omit if 0).
   - **L-016 watch flag** — if a non-`dev` branch has any commit ahead of dev whose subject starts with `feat:`, `slice:`, or `feature:`, append `← L-016 watch`. Trigger query: `git log <branch>..dev --oneline | grep -E '^[a-f0-9]+ (feat|slice|feature):'`. (L-016 names sibling-feature commits, not days, as the trigger; cite L-016 by id in the flag.)

2. **Slice** — read `.claude/current-slice/slice.yaml`. Render `<id> · status: <status>`. If `id: none` (or file absent), render `No active slice — /start-slice to open one`.

3. **Features** — enumerate `.claude/features/*.yaml`. For each: emit `<id>   <len(slices)> slices   "<name truncated to 40 chars>"`. Sort by id. Cap output at 8 entries; if more, append `… +N more` line.

4. **GH Projects** — Projects v2 tools live behind the personal Docker MCP `ghcr.io/github/github-mcp-server` (registered in `~/.claude.json`, see `.local/README.md` §2). They are NOT in `github@claude-plugins-official` — the repo-enabled plugin covers issues/PRs/commits/files but is a strict subset of the Docker server.
   - Tool discovery: try `mcp__github__projects_get` / `mcp__github__projects_list` (Docker MCP names). If neither is callable in the current session, render the fallback line and stop — do NOT call any plugin tool as a substitute.
   - On success: target the `cairn` board; bucket items by status field into `In progress` / `In review` / `Blocked` / `Ready` / `Backlog` / `Done`. Render counts for each non-`Done` bucket. For `In progress`, `In review`, `Blocked`: list all items as `#<num> <title>` (or `<title>` for draft items without an issue number). For `Ready` and `Backlog`: list top 3 each by priority/order. Omit `Done` from the dashboard (not load-bearing for "what's in flight"). The `Backlog` bucket is where pre-spec ideas live — surfacing them keeps the briefing honest about pending capture rather than dropping them.
   - On any failure (tools absent, auth failure, network, board not found): render the single fallback line `GH Projects MCP not configured — see .local/README.md §2`. Do NOT prompt for credentials, do NOT retry.

5. **Doc health** — counts and staleness, all excluding `.slice-system` to avoid the symlink loop. mtime is the staleness proxy — note that `git checkout` bumps mtime, so a freshly-checked-out worktree will show 0 stale even on logically-old files. This is a known approximation; the dashboard surfaces *recent activity*, not git-creation age.
   - Plan-docs: `find docs/plans -maxdepth 1 -name '*.md' -mtime +${CAIRN_DEVMODE_PLAN_STALE_DAYS:-30}` for stale count; total via same find without `-mtime`. Oldest by mtime: `ls -t docs/plans/*.md | tail -1` then `stat` for the date. Render as `(oldest: YYYY-MM-DD)`.
   - Memories: `find ~/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/memory -maxdepth 1 -name '*.md' -mtime +${CAIRN_DEVMODE_MEMORY_STALE_DAYS:-60}` for stale; total without `-mtime`.
   - Lessons: `docs/lessons.md` is a single file; entries are `## L-NNN: <title>` headings with no per-entry date field. Render as count-only: `Lessons: <total>` (no stale check, no threshold). The `CAIRN_DEVMODE_LESSON_STALE_DAYS` knob is reserved for future use if a `created:` convention is added to lesson entries.

## Rendering

Render each section independently. If any single source fails (command non-zero, file unreadable, parse error), emit a one-line `<SECTION>: error — <one-sentence cause>` for that section and continue. The dashboard must always be five sections tall; one broken source ≠ no briefing.

Total output target ~2500 chars. If features or worktrees overflow, truncate with `… +N more` rather than dropping the section.

Order sections exactly as listed: WORKTREES → SLICE → FEATURES → GH PROJECTS → DOC HEALTH. Rationale: most-immediate (where am I right now) → most-strategic (what should I be looking at).

## Environment knobs

- `CAIRN_DEVMODE_PLAN_STALE_DAYS` (default 30) — applied to plan-doc mtime
- `CAIRN_DEVMODE_MEMORY_STALE_DAYS` (default 60) — applied to memory-file mtime

Per cairn's no-hardcoded-knobs rule. These are local to this command — not documented in `docs/operational-reference.md` because `/dev-mode` is cairn-internal, not cairn-product.

(`CAIRN_DEVMODE_LESSON_STALE_DAYS` is reserved; lessons currently render as count-only because `docs/lessons.md` entries carry no per-lesson date field. Add a `created: YYYY-MM-DD` line under each `## L-NNN` heading and re-introduce the knob if/when staleness becomes useful.)

## What this command does NOT do

- No write actions. Read-only briefing.
- No prompts. If MCP isn't installed, point at the README; don't ask.
- No `--full` variant. Single-pass dashboard. If it later grows, lift the heavy view into a separate command.
- No cross-project briefing. Cairn-only. If you want a multi-project view, that's a different command on a different branch.
