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

One-time setup on each machine where you develop cairn. Order matters: PAT → MCP entry → command symlink → board.

### 1. Generate a fine-grained GitHub PAT

Visit https://github.com/settings/personal-access-tokens, click **Generate new token**:

- **Token name:** `cairn-dev-mode-mcp` (or any label you'll recognize)
- **Resource owner:** your user (`firaaz`)
- **Repository access:** Only select repositories → `cairn`
- **Permissions:**
  - Repository → Contents: **Read-only** (or whatever you already give other tools)
  - Repository → Issues: **Read-only**
  - Account → Projects: **Read-only** (this is `read:project`)

Save the token in your password manager. Do not commit it anywhere.

### 2. Add the GitHub MCP server to your personal Claude config

Edit `~/.claude.json` (NOT cairn's `.mcp.json` — that ships to consumers and would leak your PAT entry into their tooling). Add an entry under `mcpServers`:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

(Requires Docker. If you'd rather run the binary directly, `gh extension install github/gh-mcp` and adjust the `command`/`args` accordingly.)

Restart Claude Code so it picks up the new MCP server.

### 3. Symlink `dev-mode.md` into your personal commands directory

From the cairn repo root:

```sh
mkdir -p ~/.claude/commands
ln -s "$(pwd)/commands/claude-code/.local/dev-mode.md" ~/.claude/commands/dev-mode.md
```

Idempotent guard: `[ -L ~/.claude/commands/dev-mode.md ] || ln -s ...`

### 4. Create the cairn GH Project board

Manual GitHub UI step — there is no API-only flow that's worth scripting for a one-time setup.

1. Go to https://github.com/users/firaaz/projects (or your org page).
2. Click **New project** → **Board**.
3. Name it `cairn` (or note the actual name; it just needs to be discoverable by `projects_list`).
4. Default columns: `Todo`, `In Progress`, `Done`. Add `Blocked` and `Archived`.
5. Link it to the `cairn` repo (project settings → Add repository).

Now `/dev-mode` will surface its contents under the GH PROJECTS section.

## Verification

After setup:

1. `cd` into the cairn repo. Run `/dev-mode`. Expect a five-section dashboard. GH Projects should either populate from the board or surface the `MCP not configured` line — if it shows the latter despite step 2, restart Claude Code.
2. `cd` to any non-cairn directory. Run `/dev-mode`. Expect the single-line `not in a cairn worktree` bail.
3. `cd` to a real cairn consumer (e.g. `~/Developer/lab/complex-rag-analysis`). Confirm `ls .claude/commands/` does **not** include `dev-mode.md`. Try `/dev-mode` in Claude Code — expect "command not found".

If consumer-side step 3 fails, the `.local/` carve-out is broken — investigate before shipping any other dev-aid here.

## Future-packaging path

If `/dev-mode` (or any other `.local/` aid) earns its keep and you decide it should ship to consumers as part of cairn-the-methodology:

1. Generalize away cairn-specific assumptions (board name, repo paths, env-var prefix).
2. Move the file from `commands/claude-code/.local/dev-mode.md` to `commands/claude-code/dev-mode.md` (top level).
3. Add a feature-yaml entry and run it through the formal slice ceremony at promotion time — that's the moment to add tests.
4. Consumers who pull cairn after the promotion will get the command automatically via their existing `.slice-system` symlink.

Until then, `.local/` is the right home.
