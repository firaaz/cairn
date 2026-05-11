# Cairn — Consumer Prerequisites

Setup for any machine that consumes the cairn plugin (via `/plugin install cairn@cairn-marketplace`).

## Required

1. **Claude Code ≥ 2.0.74** — native LSP support shipped Dec 2025; the cairn workflow agents rely on it.

2. **ast-grep** — tree-sitter-based structural search and rewrite, used by the navigation/refactor agents (`root-cause-hunter`, `pytest-triage`, `adr-context`):
   ```
   brew install ast-grep
   # or: cargo install ast-grep
   ```
   Verify: `sg --version`.

3. **Pyright** — Python LSP backend. The `pyright-lsp` plugin auto-installs on session start, but a clean global install is cleaner:
   ```
   pipx install pyright
   # or: npm install -g pyright
   ```
   Verify: `which pyright`.

4. **Enable Claude Code's LSP tool.** Add to `~/.claude/settings.json`:
   ```json
   {
     "env": {
       "ENABLE_LSP_TOOL": "1"
     }
   }
   ```
   Verify in a fresh session: `echo $ENABLE_LSP_TOOL` returns `1`.

5. **Superpowers plugin at user scope.** The cairn agents reference `superpowers:systematic-debugging` for debugging methodology. Install once at user scope so it resolves in every project:
   ```
   /plugin install superpowers@claude-plugins-official
   ```
   (Choose user scope when prompted.)

6. **Ruff** — already pulled in via any `pyproject.toml` that lists it. If your project doesn't have it: `uv add --dev ruff` or `pipx install ruff`. Used by `handoff-closer` for pre-commit lint/format and by `pytest-triage` for diagnostics.

## How to install the cairn plugin

```
/plugin install cairn@cairn-marketplace
```

Marketplace declared at `https://github.com/firaaz/cairn.git`, ref `release` (see `.claude-plugin/marketplace.json`). To update later: `/plugin update cairn`.

## Code-intelligence stack (rationale)

Cairn's agents are designed for **worktree-heavy parallel agentic development**. The code-intelligence stack reflects that:

| Need | Tool | Why |
|---|---|---|
| Type-aware navigation, find-references, diagnostics | Pyright via Claude Code's native LSP | ~150MB per session, fits one-process-per-worktree naturally. Real type inference. |
| Structural find / AST rewrite / rename | ast-grep | Stateless CLI. Zero process overhead. Tree-sitter — multi-language. Handles rename since LSP rename isn't exposed by the LSP-tool surface. |
| Text/regex fallback | ripgrep (via built-in `Grep`) | Stateless. |
| Auto-fix / format / imports | Ruff | Stateless. |
| Library docs lookup | Context7 MCP (optional) | Light. |

## Why not Serena?

Serena was evaluated as the semantic code intelligence layer. It was rejected for cairn-style workflows because:

- **One active project at a time** is a hard architectural constraint (per the maintainer's response in oraios/serena#758). No officially-supported multi-project mode.
- **Heavy daemon (~300–500 MB per instance) per session**, with cold-start indexing. Multi-worktree sessions multiply this — 3–4 concurrent worktrees can pin 1–2 GB.
- **stdio mode (the Claude Code default) spawns a fresh server per Claude Code session.** Zombie risk on crashes, no resource sharing.
- **HTTP-mode sharing** doesn't help: only one project active at a time across all clients, which breaks down with worktrees that have different filesystem roots.
- **Designed for IDE-style "one persistent workspace" usage**, not for the short-lived multi-project sessions agentic + worktree development creates.

For Python-only work, Pyright LSP covers ~80% of Serena's value (find-references, workspace-symbol, goto-def, type info) at much lower resource cost. ast-grep covers the structural-edit gap. Net stack: zero baseline daemon overhead beyond Pyright (which fits worktree shape naturally).

If your workflow shifts to single-project, single-session work, re-evaluate. For now, ast-grep + Pyright LSP is the right stack.
