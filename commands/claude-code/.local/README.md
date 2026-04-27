# `commands/claude-code/.local/` — cairn-internal dev aids

This directory is a carve-out for cairn-the-project tooling that is **not** part of cairn-the-methodology and **does not ship to consumers**.

## Why a `.local/` carve-out?

Cairn ships to consumers via `.slice-system → .` symlink. Consumers wire commands into Claude Code with:

```sh
ln -s .slice-system/.claude/commands .claude/commands
```

Claude Code discovers slash commands at the top level of `.claude/commands/` only — it does **not** recurse into subdirectories. So files placed here:

- ✅ Live versioned in cairn (clone cairn on a new machine → these files come with you).
- ✅ Are invisible to consumer projects (Claude Code in a consumer doesn't see `.local/` contents).
- ❌ Are NOT auto-discovered as slash commands in cairn either — you have to symlink them into `~/.claude/commands/` per machine (one-time setup).

## What belongs here

Cairn-the-project dev aids: personal tooling that helps you develop cairn but isn't part of what cairn ships. Examples:

- `/dev-mode` — morning briefing dashboard (worktrees, active slice, features, GH Projects, doc health).

What does **not** belong here:
- Anything cairn-the-methodology consumers should run (those go in `commands/claude-code/` top level — they ship).
- Anything that imports from `scripts/cairn_query/` or `mcp_servers/cairn_knowledge/` and depends on cairn-product internals (those should be cairn-product features and live in proper homes).

## Per-machine setup

One-time setup on each machine where you develop cairn. Order: gh auth → MCP launcher → Claude config → command symlink → board.

The MCP authenticates by calling `gh auth token` at container-launch time, so no secret is ever stored in `~/.claude.json` or `.envrc`. Rotation happens through `gh`.

### 1. Grant the gh CLI a `project` scope

If gh isn't authenticated yet on this machine, run `gh auth login` and pick scopes including `project`. If gh is already logged in (e.g. `gh auth status` shows a token), just add the missing scope:

```sh
gh auth refresh -h github.com -s project
```

Verify: `gh auth status` should list `project` (and `repo`, `read:org`) under **Token scopes**.

### 2. Install the MCP launcher script

Save the following at `~/.claude/bin/github-mcp.sh` and `chmod +x` it. The wrapper pulls a fresh token from `gh auth token` on every MCP-server launch — no secret touches a config file.

```sh
#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "github-mcp.sh: gh CLI not found on PATH" >&2; exit 127
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "github-mcp.sh: docker not found on PATH" >&2; exit 127
fi

token="$(gh auth token 2>/dev/null || true)"
if [[ -z "$token" ]]; then
  echo "github-mcp.sh: gh auth token returned empty — run \`gh auth login\` first" >&2; exit 1
fi

exec docker run -i --rm \
  -e "GITHUB_PERSONAL_ACCESS_TOKEN=$token" \
  -e GITHUB_TOOLSETS=all \
  ghcr.io/github/github-mcp-server:latest
```

Pull the image once: `docker pull ghcr.io/github/github-mcp-server:latest`.

**Why `GITHUB_TOOLSETS=all`.** The upstream image ships a default toolset that excludes `projects` (GitHub Projects v2 board management) on some image versions. `/dev-mode` §4 reads from that board, so we force-enable everything to avoid silent degradation. If you want a tighter surface, replace `all` with a comma list (e.g. `repos,issues,pull_requests,projects`).

Smoke test the wrapper outside Claude Code:

```sh
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  | ~/.claude/bin/github-mcp.sh
```

Expect log lines containing `starting server version=v…` and `server session connected`. EOF afterwards is normal.

### 3. Point your personal Claude config at the launcher

Edit `~/.claude.json` (NOT cairn's `.mcp.json` — that ships to consumers). Add:

```json
{
  "mcpServers": {
    "github": {
      "command": "/Users/<you>/.claude/bin/github-mcp.sh"
    }
  }
}
```

Restart Claude Code so it picks up the new `mcpServers.github` block — the MCP container is launched per-session and caches the token for the session's lifetime, so mid-session edits to either the wrapper or `gh`'s scopes don't take effect until restart.

Verify from inside Claude Code:

1. `mcp__github__get_me` → expect your login + id (auth wired correctly).
2. `mcp__github__projects_list` (any `projects_*` tool) appears in the tool list (toolset wired correctly).
3. Call `projects_list` with your user as `owner` → expect 200, even if the list is empty (scope on the token is sufficient).

> **Note:** Docker MCP supersedes the `github@claude-plugins-official` plugin for /dev-mode purposes (and exposes a strict superset of its tools). If both are enabled, you'll get duplicate tool registrations under different namespaces — pick one and disable the other in `.claude/settings.json` to keep the tool list clean.

### 4. Symlink `dev-mode.md` into your personal commands directory

From the cairn repo root:

```sh
mkdir -p ~/.claude/commands
ln -s "$(pwd)/commands/claude-code/.local/dev-mode.md" ~/.claude/commands/dev-mode.md
```

Idempotent guard: `[ -L ~/.claude/commands/dev-mode.md ] || ln -s ...`

### 5. Create the cairn GH Project board

Manual GitHub UI step — there is no API-only flow that's worth scripting for a one-time setup.

1. Go to https://github.com/users/firaaz/projects (or your org page).
2. Click **New project** → choose the **Kanban** or **Team planning** template. Both ship the same Status field defaults (`Backlog / Ready / In progress / In review / Done`); Team planning adds Priority / Size / Estimate / Start date / Target date as inert extras (`/dev-mode` only reads Status, so they cost nothing). Pick whichever you'll actually use.
3. Name it **exactly** `cairn` — `/dev-mode` and any other cairn aid that talks to Projects v2 looks up the board by this name. The same name must be used on every machine so all your sessions see the same board.
4. After creation, open Settings → Custom fields → Status and add `Blocked` as a sixth option (the presets ship five; `/dev-mode` renders a Blocked bucket and needs the option to exist for items to land there). Optional: also add `Archived` if you want to retire items without deleting them.
5. Link it to the `cairn` repo (project settings → Manage access → Add repository).

**One board, account-owned.** Because `firaaz` owns the board and every machine authenticates as `firaaz` via the gh-cli wrapper (§2), `gh project list --owner @me` (and `mcp__github__projects_list` once the Docker MCP is connected) resolves to the same project from every machine — no per-machine config needed. The project's number appears in its URL (`/projects/N`); record it locally if convenient, but the lookup contract is the **name**, not the number.

Now `/dev-mode` will surface its contents under the GH PROJECTS section.

## Verification

After setup:

1. `cd` into the cairn repo. Run `/dev-mode`. Expect a five-section dashboard. GH Projects should either populate from the board or surface the `MCP not configured` line — if it shows the latter despite step 3, restart Claude Code.
2. `cd` to any non-cairn directory. Run `/dev-mode`. Expect the single-line `run from inside the cairn repo (any worktree)` bail.
3. `cd` to a real cairn consumer (e.g. `~/Developer/lab/complex-rag-analysis`). Confirm `ls .claude/commands/` does **not** include `dev-mode.md`. Try `/dev-mode` in Claude Code — expect "command not found".

If consumer-side step 3 fails, the `.local/` carve-out is broken — investigate before shipping any other dev-aid here.

## Future-packaging path

If `/dev-mode` (or any other `.local/` aid) earns its keep and you decide it should ship to consumers as part of cairn-the-methodology:

1. Generalize away cairn-specific assumptions (board name, repo paths, env-var prefix).
2. Move the file from `commands/claude-code/.local/dev-mode.md` to `commands/claude-code/dev-mode.md` (top level).
3. Add a feature-yaml entry and run it through the formal slice ceremony at promotion time — that's the moment to add tests.
4. Consumers who pull cairn after the promotion will get the command automatically via their existing `.slice-system` symlink.

Until then, `.local/` is the right home.
