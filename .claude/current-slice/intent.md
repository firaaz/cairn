---
slice: compression/lever-Y-mcp-substrate
date: 2026-04-26
phase: 1-intent
invariants-touched: [INV-010]
adrs-referenced:
  - cairn-substrate-and-fastmcp
  - phase-lock-and-role-declaration
  - compression-infrastructure-bootstrap
envelope:
  - "mcp_servers/cairn_knowledge/**"
  - ".mcp.json"
  - "checks/role_guard.py"
  - "scripts/slice_orchestrator/dispatch.py"
  - ".claude/agents/phase-1-writer.md"
  - "tests/unit/test_mcp_cairn_knowledge_server.py"
  - "tests/unit/test_mcp_cairn_knowledge_tools.py"
  - "tests/unit/test_role_guard_phase_1_lockdown.py"
  - "tests/unit/test_role_guard_envelope_grant.py"
  - "tests/unit/test_orchestrator_snapshot_pinning.py"
  - "tests/unit/test_phase_1_writer_query_first.py"
  - "docs/operational-reference.md"
  - "docs/ARCHITECTURE.md"   # operator-fixup 2026-04-26: introduces INV-010 to satisfy validate_architecture.py Check B for the firm/accepted ADR cairn-substrate-and-fastmcp; gap missed by Phase 1 (intent set invariants-touched: [] from the ADR's frontmatter, which is a different semantic from Check B's "every firm ADR has at least one referencing INV"). Phase 4 RAISE_ISSUE → triager ESCALATE_TO_USER at run 1; envelope amended pre-resume.
  - "tests/unit/test_invariant_assertions.py"   # operator-fixup 2026-04-26: bumps EXPECTED_INVARIANT_IDS range(1, 10) → range(1, 11) to track INV-010. Co-amended with docs/ARCHITECTURE.md above.
out-of-scope:
  - "Mutation surface (typed-claim writes by agents) — deferred per ADR D7."
  - "Phases 2/3/4 query-first conversion + lockdown — Slice 3 (compression/lever-Z-substrate-full-pipeline)."
  - "AGENT_ENVELOPE extension to phases 2/3/4 — Slice 3."
  - "Compaction policy for sweep-results artifacts — separate ADR."
  - "GitHub Project board automation — gated behind Slice 3."
  - "Any change to scripts/cairn_query/ extractor or storage logic (Slice 1 owned that)."
  - "Re-litigating any decision in ADR cairn-substrate-and-fastmcp §8.1 — those are firm."
  - "L-011 (Phase-3 cluster fan-out commit gap) — roadmap §11 fix queued separately; carry awareness only."
---

# Intent — compression/lever-Y-mcp-substrate

## What and Why

Substrate Slice 2 of the knowledge-substrate program. Slice 1 shipped `scripts/cairn_query/` (typed pydantic + kuzudb + typer CLI) for operator-only consumption; this slice wraps that module in a FastMCP stdio server so phase agents can query typed records over MCP instead of re-reading canonical markdown. Per ADR `cairn-substrate-and-fastmcp` D8/D16, the cost-reduction value-prop only holds when direct-Read access is structurally revoked at the role_guard layer — prompt-only enforcement is empirically inadequate (L-005 pattern). We prove the thesis on phase-1-writer alone (single phase POC); Slice 3 generalizes to phases 2/3/4. Cost-delta target: ≥40% Phase-1 reduction vs Lever-1 baseline ($2.96 / 105k cache_creation).

## Specification Detail

### S1 — FastMCP server adapter (greenfield)

New package `mcp_servers/cairn_knowledge/`:
- `server.py` — FastMCP server bootstrap; reads `cairn_query_snapshot` from `AGENT_ENVELOPE` JSON at session init, pins the session to that SHA, lazily builds/loads `KuzuStorage` via `scripts.cairn_query.rebuild_from_sources(snapshot_id=<sha>)`.
- `tools.py` — exactly four read-only MCP tool definitions wrapping `scripts.cairn_query` public API:
  - `lookup(entity_type: EntityType, id: str) -> Entity` — discriminated-union pydantic return.
  - `search(entity_type: EntityType, filters: dict | None = None) -> list[Entity]`
  - `path_bindings(path: str) -> list[Entity]` — workhorse inverse view.
  - `cypher(query: str) -> list[dict]` — escape hatch.
- Module entry: `python -m mcp_servers.cairn_knowledge` runs the stdio server.
- Transport: stdio (per ADR D6); SSE/websocket explicitly out of scope.
- D15 enforcement (structural): the server module imports `scripts.cairn_query` only; operator memory under `~/.claude/projects/.../memory/` is not referenced anywhere in `mcp_servers/` and the four tools' query surface is bounded by `EntityType` (which has no operator-memory variant). No opt-in flag, no path argument that could escape into operator-memory paths.

### S2 — `.mcp.json` registration

New file `.mcp.json` at repo root registering one server entry under stdio transport:
```json
{
  "mcpServers": {
    "cairn-knowledge": {
      "command": "python",
      "args": ["-m", "mcp_servers.cairn_knowledge"],
      "env": {}
    }
  }
}
```
Loaded by Claude Code subprocesses spawned with the project root as cwd. `AGENT_ENVELOPE` is inherited from the parent (orchestrator) process per `dispatch.py:_dispatch_once` env-copy semantics; the MCP server reads it at session init, not per-call.

### S3 — Snapshot pinning via AGENT_ENVELOPE (`scripts/slice_orchestrator/dispatch.py`)

Today's `_dispatch_once(role, inputs, envelope=None, …)` sets `AGENT_ENVELOPE` only when an explicit JSON-array envelope is passed (phase-3 cluster usage). Extension contract:
- For phase-1-writer (and any phase agent reached this slice — read scope is just phase-1-writer here), the orchestrator MUST set `cairn_query_snapshot` in the per-phase `AGENT_ENVELOPE` payload at dispatch time. Resolution: `git rev-parse HEAD` invoked from cwd at dispatch entry; on failure, sentinel `unknown-sha-<iso8601>` per ADR D12.
- Encoding: `AGENT_ENVELOPE` becomes a JSON object `{"paths": [...], "cairn_query_snapshot": "<sha>"}` for phase-1-writer dispatch. Pre-existing phase-3-implementer JSON-array-only consumption is preserved verbatim by `role_guard._envelope_patterns` (which already tolerates non-list shapes by warning + fallback). Slice 3 generalizes the object shape to all phases.
- `init_new_slice`'s call to `dispatch_phase_agent("phase-1-writer", …)` (lifecycle.py:401-411) gains a snapshot-resolution helper invocation; the helper's signature lives in dispatch.py.

### S4 — `checks/role_guard.py` ROLE_POLICIES extension (D8 lockdown + D9 envelope grant)

Per `compression-infrastructure-bootstrap` §40, `role_guard.py` is the authorized PreToolUse mechanism. This slice extends its policy *table content*, not its mechanism class. Concrete additions:

- New `READ_TOOLS = {"Read", "Bash"}` set (Bash covers cat/head/grep equivalents per ADR D8).
- New `ROLE_DENY_READ` table:
  ```python
  ROLE_DENY_READ = {
      "phase-1-writer": [
          r"^scripts/cairn_query/",
          r"^docs/ARCHITECTURE\.md$",
          r"^docs/adr/",
          r"^docs/lessons\.md$",
          r"^docs/spec-v1\.md$",
          r"^docs/operational-reference\.md$",
      ],
  }
  ```
- New main-flow branch when `tool_name in READ_TOOLS` and `role in ROLE_DENY_READ`:
  1. If path matches no deny pattern → return 0 (allow).
  2. If path matches a deny pattern AND the slice's `AGENT_ENVELOPE` paths array contains a regex granting that path → return 0 (envelope-grant escape; D9), AND append one line to `.claude/envelope-grants.log` (`<slice-id> <YYYY-MM-DD> <granted-path> <granting-phase>`).
  3. Otherwise → emit stderr deny message and return 1.
- `_envelope_patterns` already handles JSON-array envelopes; extended to read from the `paths` key when envelope is the new object shape (S3), with backward-compat for the array shape.
- Default-allow when `AGENT_ROLE` is unset (preserves the pipeline-substrate session carve-out per ADR D8 scope clause).
- 3-in-10 abuse tripwire: after appending to `envelope-grants.log`, scan the last 10 slice-ids from the log; if the same path appears in ≥3 of them, emit advisory stderr warning per ADR D9.

### S5 — phase-1-writer agent (`/.claude/agents/phase-1-writer.md`)

- `tools:` frontmatter tightened: remove `Read` and `Bash` from the available-tools list (defense-in-depth outer gate per ADR D8 layered model). Keep `Write`, `Edit`, `Grep`, `Glob` — the agent still needs Write for intent.md authoring; Grep/Glob over `.claude/current-slice/` and the slice envelope remain available since those paths are not in `ROLE_DENY_READ`.
- Prompt body gains a query-first directive listing the four MCP tools by name: "Use the cairn-knowledge MCP server (`lookup`, `search`, `path_bindings`, `cypher`) to query canonical knowledge. Do not attempt to Read `docs/ARCHITECTURE.md`, `docs/adr/**`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md`, or `scripts/cairn_query/**` — those reads are denied by `role_guard.py`. If you need a path outside the MCP query surface, the slice envelope must grant it."
- Existing P1/P2 escape-hatch directives (heredoc, no-preempt-refusal) preserved verbatim.

### S6 — D9 envelope-grant enumeration for phase-1-writer

Phase-1-writer's known canonical-source reads in current usage:
- `docs/ARCHITECTURE.md` — invariants context. **Routed through MCP**: `search(entity_type=INVARIANT)` and `lookup(entity_type=INVARIANT, id=…)`.
- `docs/adr/*.md` (multiple) — ADR context. **Routed through MCP**: `search(entity_type=DECISION, filters={…})` and `lookup(entity_type=DECISION, id=…)`.
- `docs/lessons.md` — lesson context (e.g. L-011 awareness). **Routed through MCP**: `search(entity_type=LESSON)`.
- `docs/spec-v1.md` — spec section context. **Routed through MCP**: `search(entity_type=SPEC_SECTION)`.
- `docs/operational-reference.md` — Phase Skill Guide + env-var docs. **Routed through MCP**: `search(entity_type=OP_RULE)`.
- `scripts/cairn_query/**` — should never be needed by phase-1-writer (it's the MCP backend). **Denied without grant**.

Slices that legitimately edit any locked-down path (e.g. an ADR-amendment slice) declare the path in `slice.yaml`'s envelope; `role_guard.py` reads that envelope and grants Read for that path during that slice only.

### S7 — `docs/operational-reference.md`

Document any new env-var knobs introduced by S3/S4 (e.g. `CAIRN_SUBSTRATE_SNAPSHOT_OVERRIDE` if needed for testing). If no new operator-facing knob is added, this file is touched only to add a one-paragraph Phase Skill Guide note for phase-1-writer pointing at the cairn-knowledge MCP tools (per `phase-lock-and-role-declaration` D4 surfacing commitment).

## Boundary

- **Phases 2/3/4** keep direct Read access; their lockdown is Slice 3.
- **Mutation tools** (any write through MCP) are out of scope and out of the v1 surface (ADR D6/D7).
- **scripts/cairn_query/** internals are not touched. Public API (`rebuild_from_sources`, `lookup`, `search`, `path_bindings`, `cypher`, the `EntityType` enum) is the import contract.
- **No edits to ADR cairn-substrate-and-fastmcp** — already committed at fdf039d, status: accepted, firmness: firm. Re-litigation of any §8.1 decision is rejected at envelope-check time.
- **L-011 (Phase-3 cluster fan-out commit gap)** is queued at roadmap §11. This slice's Phase 3 will likely fan out into ≈5 candidate clusters (FastMCP package, role_guard table, dispatch.py snapshot, agent prompt, .mcp.json). Operator may apply the post-close fixup pattern (memory: phase4_rolelock_fixup; prior precedent: commit 354167a) if the orphan recurs. Carry awareness only — do not attempt the structural fix here.
- **operator memory** under `~/.claude/projects/.../memory/` is permanently excluded from MCP tool surface (ADR D15). No opt-in flag, no path-argument escape hatch. Structurally enforced by the bounded `EntityType` enum.
- **GitHub Project automation** remains gated behind Slice 3 per project memory.
- **Compaction policy for sweep-results** is a separate ADR.

## Verification

V1. `uv run pytest` passes in full, including the 8 currently-failing `cairn-substrate-and-fastmcp` validator tests (baseline 947 pass / 8 OOS / 3 skip → all green).

V2. `python -m mcp_servers.cairn_knowledge` starts a stdio MCP server. An MCP `initialize` request returns capabilities with exactly four tools enumerated: `lookup`, `search`, `path_bindings`, `cypher`. (Test: `tests/unit/test_mcp_cairn_knowledge_server.py`.)

V3. Each of the four MCP tools, called with valid input on the current corpus, returns a typed pydantic record (single or list as per signature). `lookup(INVARIANT, "INV-008")` returns the populated Invariant model; `path_bindings("docs/ARCHITECTURE.md")` returns ≥1 entity; `cypher("MATCH (i:Invariant) RETURN i.id LIMIT 1")` returns a non-empty row list. (Test: `tests/unit/test_mcp_cairn_knowledge_tools.py`.)

V4. `role_guard.py` denies `Read` and `Bash` tool calls on `docs/ARCHITECTURE.md`, `docs/adr/*.md`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md`, and `scripts/cairn_query/**` when `AGENT_ROLE=phase-1-writer` and no envelope grant covers the path. Default-allow when `AGENT_ROLE` is unset (pipeline-substrate carve-out). (Test: `tests/unit/test_role_guard_phase_1_lockdown.py`.)

V5. `role_guard.py` ALLOWS Read on a locked-down path when `AGENT_ENVELOPE` (object shape) grants it via the `paths` array, AND appends one line to `.claude/envelope-grants.log` with the slice-id, date, granted path, and granting phase. (Test: `tests/unit/test_role_guard_envelope_grant.py`.)

V6. `AGENT_ENVELOPE` written by `dispatch._dispatch_once` for `phase-1-writer` contains a `cairn_query_snapshot` field equal to `git rev-parse HEAD` at dispatch time; on simulated `git rev-parse` failure, the field is the sentinel `unknown-sha-<iso8601>`. Pre-existing phase-3-implementer envelope shape (JSON array of regex patterns) round-trips through `role_guard._envelope_patterns` unchanged. (Test: `tests/unit/test_orchestrator_snapshot_pinning.py`.)

V7. `.claude/agents/phase-1-writer.md` `tools:` frontmatter no longer contains `Read` or `Bash`; the prompt body lists the four MCP tools (`lookup`, `search`, `path_bindings`, `cypher`) by name and directs query-first behavior. (Test: `tests/unit/test_phase_1_writer_query_first.py` — string-presence assertions.)

V8. Cost-delta measurement path: at integration sweep, capture phase-1 `cache_creation` from `.claude/orchestrator-debug/<slug>-result.json` for the next slice that runs phase-1-writer post-close, and compare against the Lever-1 baseline ($2.96 / 105k cache_creation for Phase 1) recorded in roadmap §10. Target ≥40% Phase-1 reduction. The measurement is captured in sweep-notes.md under "Cost-delta evidence" but is not a Phase-4 PASS gate for THIS slice (the next slice's first run is the measurement event); this slice's gate is V1–V7.
