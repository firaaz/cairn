# Upgrading from pre-compression cairn

The `compression` feature reshapes how cairn is consumed. Updating the
`.slice-system → .` symlink alone does **not** make the new wiring functional
in an existing consumer. This guide enumerates the **5 wiring deltas** a
consumer must apply post-merge, in the order most projects will hit them.

The deltas are independent in principle but partially ordered in practice:
hooks (delta 1) require the substrate deps (delta 3) to be importable; the MCP
server (delta 2) needs the same deps; agent discoverability (delta 4) is
orthogonal but agents themselves invoke hooks and the MCP server, so it
becomes useful only after 1-3 land; CLAUDE.md cleanup (delta 5) is the final
sweep that reflects the new contract surface.

Each section below is ≤200 words and ends with a one-line **Verify** snippet.

---

## 1. Hook registration in `.claude/settings.json`

Cairn now enforces role-keyed write-path discipline through two hooks that
must be registered in the consumer's `.claude/settings.json`:

- `checks/role_guard.py` as a **PreToolUse** hook on the matcher
  `Write|Edit|MultiEdit|NotebookEdit`. Without this entry the role-guard
  enforcement (INV-003 narrow exception per
  `compression-infrastructure-bootstrap`) silently no-ops in the consumer —
  every role can write everywhere, defeating the substrate program's
  enforceability commitment.
- `scripts/role-cheatsheet.sh` (or the consumer's equivalent role-context
  banner) as a **SessionStart** hook so each new agent session sees its
  current role's allowed write surfaces upfront.

Both hooks ship in cairn under `checks/` and `scripts/` and are reachable from
the consumer via `.slice-system/checks/role_guard.py` /
`.slice-system/scripts/role-cheatsheet.sh`. Use those paths in the
`settings.json` `command:` fields verbatim — the symlink resolves them at
hook-invocation time.

If the consumer already has unrelated PreToolUse / SessionStart hooks,
append the cairn entries; do not replace.

**Verify:**

```sh
jq -e '.hooks.PreToolUse[]?.hooks[]?.command | select(test("role_guard"))' .claude/settings.json
```

---

## 2. MCP server registration in `.mcp.json`

The cairn-knowledge MCP server exposes the canonical-knowledge query surface
(`lookup`, `search`, `path_bindings`, `cypher`) that all four phase agents now
depend on for read access to ADRs, invariants, lessons, and spec sections.
Register it in the consumer's `.mcp.json` as a **stdio** server (per ADR
`cairn-substrate-and-fastmcp` D6 — stdio is the only supported transport for
cairn-knowledge in v1):

```json
{
  "mcpServers": {
    "cairn-knowledge": {
      "command": "python",
      "args": ["-m", "mcp_servers.cairn_knowledge"]
    }
  }
}
```

**Open question — module resolution.** `python -m mcp_servers.cairn_knowledge`
only resolves when the working directory contains the `mcp_servers/` package
on `sys.path`. Two paths:

- **Recommended (whole-directory symlink layout):** consumers using the
  `.slice-system → .` self-symlink at the consumer root resolve trivially —
  cairn's own root is the CWD when Claude Code spawns the MCP subprocess.
- **Non-symlink layouts (vendored / partial sync):** set `PYTHONPATH` in the
  MCP server entry's `env:` block to point at the cairn checkout, e.g.
  `"env": {"PYTHONPATH": "/abs/path/to/cairn"}`. This is the documented
  escape hatch.

**Verify:**

```sh
jq -e '.mcpServers["cairn-knowledge"] | .command and (.args | index("mcp_servers.cairn_knowledge"))' .mcp.json
```

---

## 3. Python dependencies (`pydantic`, `kuzu`, `mistune`, `typer`, `fastmcp`)

The substrate ships five third-party Python deps (per ADR
`cairn-substrate-and-fastmcp` D3, which retired the stdlib-only constraint —
see delta 5). The consumer has two integration paths:

**Path A — shared cairn venv (recommended for self-symlinked consumers).** Run
`cd .slice-system && uv sync` once at clone time; the orchestrator and the
MCP server then both run under cairn's `.venv`. Tradeoff: clean isolation
(consumer's own deps untouched), but the consumer must ensure cairn's `.venv`
exists before any Claude Code session starts. Add a setup step to the
consumer's onboarding script.

**Path B — vendored into consumer `pyproject.toml`.** Add `pydantic`, `kuzu`,
`mistune`, `typer`, and `fastmcp` to the consumer's own `pyproject.toml` and
`uv sync`. Tradeoff: no two-venv coordination, but the consumer now
co-versions five deps it does not directly use; pin upstream cairn's
versions to avoid drift.

Most consumers should pick Path A — the substrate is cairn's contract surface
and isolating its deps under cairn's venv keeps the consumer's dep graph
small.

**Verify:**

```sh
cd .slice-system && uv run python -c "import pydantic, kuzu, mistune, typer, fastmcp"
```

---

## 4. Agent + slash-command discoverability

Claude Code reads agents from the consumer's `.claude/agents/` and slash
commands from the consumer's `.claude/commands/` — **not** from
`.slice-system/.claude/agents/` or `.slice-system/.claude/commands/`. The
self-symlink `.slice-system → .` does not transitively expose nested
`.claude/` content to Claude Code's discovery path.

The cleanest migration is **whole-directory symlinks** at the consumer root:

```sh
ln -s .slice-system/.claude/agents .claude/agents
ln -s .slice-system/.claude/commands .claude/commands
```

This makes every cairn-shipped agent (`phase-1-writer`, `phase-2-validator`,
`phase-3-implementer`, `phase-4-integrator`, plus the supporting
sub-agents) and every slash command (`/start-slice`, `/close-slice`,
`/decision`, etc.) discoverable to Claude Code in the consumer.

If the consumer already has its own `.claude/agents/` or `.claude/commands/`
directories with consumer-specific entries, prefer per-file symlinks for the
cairn-shipped names rather than overwriting the directories. Keep cairn's
canonical paths the source of truth — never copy-paste the agent or command
files into the consumer (they will drift).

**Verify:**

```sh
test -L .claude/agents && test -L .claude/commands && readlink .claude/agents | grep -q slice-system
```

---

## 5. CLAUDE.md updates for retired constraints

Two long-standing cairn constraints have been **retired** by ADR
`cairn-substrate-and-fastmcp` and any consumer's `CLAUDE.md` that quotes or
relies on them needs a sweep:

- **Stdlib-only target** — retired by ADR `cairn-substrate-and-fastmcp` **D3**.
  The substrate now ships `pydantic`, `kuzu`, `mistune`, `typer`, and
  `fastmcp`; new code under `mcp_servers/`, `scripts/cairn_query/`, and
  related substrate surfaces is permitted to depend on them. Pre-substrate
  bash hooks and orchestrator code remain stdlib-only by their own scope, not
  by global rule.
- **Rust-mapping end-of-v1 target** — retired by ADR
  `cairn-substrate-and-fastmcp` **D4**. New Python code is no longer required
  to be one-for-one Rust-portable (no decorators / no metaprogramming
  constraint). Function-based Python remains the preferred style for the
  orchestrator and bash-replacement work, but the substrate is free to use
  pydantic models, typer command decorators, and fastmcp server decorators.

CLAUDE.md surgery itself is consumer-side and slice-by-slice — this guide
flags the two retired constraints; the consumer chooses when to delete the
matching prose. Cite ADR `cairn-substrate-and-fastmcp` D3 and D4 in the
removal commit.

**Verify:**

```sh
grep -nE "stdlib-only|Rust-mapping|one-for-one Rust" CLAUDE.md || echo "CLAUDE.md sweep clean"
```
