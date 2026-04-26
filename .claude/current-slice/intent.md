---
slice: compression/lever-Y-mcp-substrate-fixup
date: 2026-04-26
phase: 1-intent
invariants-touched: [INV-010]
adrs-referenced: [cairn-substrate-and-fastmcp, compression-infrastructure-bootstrap]
envelope:
  - "mcp_servers/cairn_knowledge/server.py"
  - "pyproject.toml"
  - "uv.lock"
  - "checks/role_guard.py"
  - ".claude/agents/phase-1-writer.md"
  - "docs/ARCHITECTURE.md"
  - "tests/unit/test_mcp_cairn_knowledge_server.py"
  - "tests/unit/test_mcp_cairn_knowledge_jsonrpc.py"
  - "tests/unit/test_role_guard_grep_glob_deny.py"
  - ".claude/current-slice/intent.md"
  - ".claude/current-slice/slice.yaml"
  - ".claude/features/compression.yaml"
out-of-scope:
  - "Phases 2/3/4 lockdown extension (Slice 3 — compression/lever-Z-substrate-full-pipeline)"
  - "Mutation surface for the substrate (ADR D7 explicit deferral)"
  - "Compaction policy for sweep-results artifacts"
  - "Any change to the existing four MCP tools' signatures or return shapes"
  - "Any new ADR — this slice operationalizes existing D1/D6/D8 commitments"
  - "AGENT_ENVELOPE schema changes — object shape and `paths`/`cairn_query_snapshot` keys are already shipped"
  - "Bash read-class deny widening (already covers cat/head/grep tokens via _bash_path_tokens)"
  - "INV-010 invariant-check `target:` block — grep target stays `ROLE_DENY_READ` in `checks/role_guard.py`"
  - "scripts/cairn_query/** internals (substrate Slice 1 territory; this slice consumes its public interface)"
  - "scripts/slice_orchestrator/dispatch.py AGENT_ENVELOPE construction (Slice 2 already shipped phase-1-writer envelope wiring)"
---

### What and Why

Substrate Slice 2 (`compression/lever-Y-mcp-substrate`, closed `305cd02`) shipped the structural pieces of the cairn-knowledge MCP — `mcp_servers/cairn_knowledge/`, `.mcp.json` registration, `ROLE_DENY_READ` table, `AGENT_ENVELOPE.cairn_query_snapshot` pinning, phase-1-writer query-first prompt — but three defects make the substrate non-functional in practice. The first phase-1-writer dispatch after Slice 2 hits a stub MCP server, a missing `fastmcp` dependency, and a Read-only deny gate that Grep/Glob bypass unchallenged. Roadmap §12 names all three. This slice fixes them so the substrate's cost-reduction value-prop and structural lockdown enforceability (ADR `cairn-substrate-and-fastmcp` D1/D6/D8) hold under the next dispatch. **Gates substrate Slice 3** (`compression/lever-Z-substrate-full-pipeline`).

### Specification Detail

#### S1 — MCP server ships a real JSON-RPC dispatcher

`mcp_servers/cairn_knowledge/server.py` MUST replace the `_stdin_reader` stub (current lines 61-76, which discards stdin) with a JSON-RPC 2.0 dispatcher over stdio per the MCP transport spec referenced by ADR D6. The dispatcher MUST:

- **Initialize handshake.** Accept the MCP `initialize` request on stdin, respond on stdout with the server's protocolVersion, capabilities (`tools.listChanged: false`), and serverInfo (`name: cairn-knowledge`, `version` from package metadata or `"0.1.0"`).
- **`tools/list` request.** Respond with exactly the four tool descriptors named in ADR D6 / INV-010: `lookup`, `search`, `path_bindings`, `cypher`. Each descriptor MUST include the tool's name, description, and JSON-schema for its input arguments matching the four callables in `mcp_servers/cairn_knowledge/tools.py`. The TOOLS dict in `tools.py` is the source of truth for the four-tool set; the dispatcher derives names from `TOOLS.keys()`.
- **`tools/call` request.** Dispatch to the matching callable in `tools.py`, return the callable's result encoded per MCP's content schema (text content with the JSON-serialized return value is acceptable v1). KeyError from `lookup` MUST surface as a JSON-RPC error response (code -32602 invalid params or -32603 internal error — implementation choice as long as it is a valid JSON-RPC error, not a process crash).
- **Snapshot pinning preserved.** The existing `AGENT_ENVELOPE.cairn_query_snapshot` read at startup (server.py:95-97) and `cairn_query.rebuild_from_sources(..., snapshot_id=...)` call (lines 102-106) MUST remain — D12 / INV-010 require them. The dispatcher uses the same `_get_storage()` lazy singleton in `tools.py` (line 31-36), which is rebuilt eagerly at startup with the pinned snapshot, so per-call snapshot consultation is not required.
- **Choice of substrate.** The dispatcher MUST use the `fastmcp` library named in ADR D1 (the framework choice rationale in D1/D6 is binding). If, during Phase 3, the chosen library's import path or API surface differs from the assumption that `fastmcp` is the PyPI package name, Phase 3 RAISES_ISSUE rather than silently substituting; an ADR amendment via `/decision` is the correct path to switch to a different library or hand-rolled dispatcher.
- **Termination semantics.** The server exits cleanly on stdin EOF (orchestrator closed the pipe) and on SIGTERM/SIGINT. The current keep-alive `time.sleep(1)` polling loop is removed in favour of blocking on the dispatcher's stdin read.

#### S2 — `fastmcp` added to pyproject.toml standing dep set

`pyproject.toml` `[project] dependencies` MUST include `fastmcp` with a version constraint (operator-chosen during Phase 3, narrow-pinned per ADR D1 risk-register guidance: "Slice 2 pins FastMCP to a minor version"). `uv.lock` MUST be regenerated by `uv sync` so the lockfile reflects the new dep transitively. After `uv sync`, `python -c "import fastmcp"` MUST exit 0 inside the project venv.

The pre-existing five v1 standing deps (pyyaml, pydantic, kuzu, mistune, typer) MUST remain unchanged — D1 specifies the standing set; this fix restores the missing entry without disturbing the others.

#### S3 — `READ_CLASS_TOOLS` extended to {Read, Grep, Glob}

`checks/role_guard.py` line 22 `READ_CLASS_TOOLS = {"Read"}` MUST become `READ_CLASS_TOOLS = {"Read", "Grep", "Glob"}`. The downstream branch at line 133 (`if tool_name in READ_CLASS_TOOLS and role in ROLE_DENY_READ`) already routes via the same `file_path` / envelope-grant logic, so no additional code path is required for Grep/Glob. The hook MUST extract the path-equivalent argument from the tool's `tool_input`:

- **Grep.** `tool_input.get("path")` is the search root (defaults to working directory if absent — absent path is treated as not matching the deny patterns, since it is not a deny-list path on its face). The deny check applies to `path` only; the `pattern` argument is not a path.
- **Glob.** `tool_input.get("path")` is the search root in the same way; `tool_input.get("pattern")` is a glob pattern, not a path, and is not subject to the deny check on its own. (A glob pattern that matches a deny-list file is allowed to surface filenames; the read of the matched file is what later triggers the deny via Read.)

D9 envelope-grant behavior MUST extend to Grep and Glob with the same semantics as Read: an envelope `paths` regex matching the path-input grants the call, logged once to `.claude/envelope-grants.log`. Tests in S3 cover this parity.

The `phase-1-writer` agent's `tools:` frontmatter at `.claude/agents/phase-1-writer.md:4` MUST drop `Grep` and `Glob`, leaving `tools: Write, Edit` (defense-in-depth outer gate, matching Slice 2's stated discipline of "Read/Bash removed from tools frontmatter").

#### S4 — Phase-2 tests harden from boot-liveness to JSON-RPC round-trip

The existing Phase-2 tests in `tests/unit/test_mcp_cairn_knowledge_server.py` under-stated V2/V3:
- `test_v2_module_main_subprocess_starts_stdio_server` (lines 70-106) only asserts "did not crash on boot" within 1s.
- `test_v2_server_module_has_envelope_snapshot_pinning_hook` (lines 109-125) is a string-presence assertion, not a behavioral one.

A new test file `tests/unit/test_mcp_cairn_knowledge_jsonrpc.py` MUST add round-trip coverage:

- **R1 initialize handshake.** Spawn the server subprocess with stdin/stdout piped, write a JSON-RPC `initialize` request newline-terminated, read the response, assert the response is well-formed JSON-RPC 2.0 with the matching id and a `result` containing `protocolVersion` + `capabilities` + `serverInfo.name == "cairn-knowledge"`.
- **R2 tools/list returns four tools.** After initialize, send `tools/list`, parse response, assert `result.tools` has exactly the four names `{lookup, search, path_bindings, cypher}` — same set INV-010 names.
- **R3 tools/call routes to the implementation.** Send `tools/call` for `lookup` with a deterministic argument that yields a known record (e.g., `{"entity_type": "invariant", "id": "INV-010"}`), assert the response is non-error and contains the expected record fields.
- **R4 tools/call surfaces KeyError as JSON-RPC error.** Send `tools/call` for `lookup` with a non-existent id, assert the response is a JSON-RPC error (any valid error code), not a process crash.
- **R5 stdin EOF terminates cleanly.** Close stdin after R4, assert the subprocess exits with returncode 0 (or SIGTERM-equivalent on platforms where MCP servers conventionally terminate via signal) within a small window.

The two existing under-stated tests MAY remain as smoke-coverage of the boot path; they are not deleted (Phase 4 of this slice asserts the full suite passes, including these).

A new test file `tests/unit/test_role_guard_grep_glob_deny.py` MUST cover:

- **G1 Grep on locked-down path is denied for phase-1-writer.** With `AGENT_ROLE=phase-1-writer`, `tool_name=Grep`, `tool_input.path` matching a `ROLE_DENY_READ` pattern (e.g., `docs/ARCHITECTURE.md` or `docs/adr/`), `role_guard.main()` returns 1 and emits a stderr diagnostic naming the role and path.
- **G2 Glob on locked-down path is denied for phase-1-writer.** Same as G1 but `tool_name=Glob`.
- **G3 Grep with envelope-grant is allowed.** With `AGENT_ENVELOPE` containing a `paths` entry matching the path, the call returns 0 and appends one line to `.claude/envelope-grants.log`.
- **G4 Glob with envelope-grant is allowed.** Same as G3 but `tool_name=Glob`.
- **G5 Grep on non-locked path is allowed.** With path outside `ROLE_DENY_READ` patterns, the call returns 0, no diagnostic, no log entry.
- **G6 Grep without `path` argument is allowed.** A Grep call that omits `path` (search-from-CWD default) is not denied — the deny check is against an explicit path argument.
- **G7 Non-phase-1-writer roles are unaffected.** With `AGENT_ROLE=phase-3-implementer`, Grep on a deny-listed path returns 0 (deny is per-role; phases 2/3/4 lockdown is Slice 3 scope).

#### S5 — INV-010 prose amendment

`docs/ARCHITECTURE.md` line 93 INV-010 prose currently reads "Direct Read/Bash access to ... is denied by `checks/role_guard.py`'s `ROLE_DENY_READ` table". It MUST be amended to "Direct Read/Grep/Glob/Bash access to ..." (or equivalent — the constraint is that the prose names the actual set of tools the lockdown denies). The `invariant-check INV-010` block at lines 95-101 MUST NOT be touched — its grep target `ROLE_DENY_READ` literal in `checks/role_guard.py` is unaffected by the constant's value, only by its name; the name does not change.

### Boundary

- **Out: phases 2/3/4 lockdown extension.** Slice 3 (`compression/lever-Z-substrate-full-pipeline`) adds `phase-2-skeptic`, `phase-3-implementer`, `phase-4-integrator` to the `ROLE_DENY_READ` table per ADR D8 second-stage rollout. This slice keeps the lockdown phase-1-writer-only.
- **Out: mutation surface.** ADR D7 explicit deferral. The dispatcher exposes only the four read-only tools.
- **Out: new ADR.** All three defects are operationalization of existing D1 (fastmcp dep), D6 (stdio JSON-RPC transport), and D8 (structural deny at the role_guard layer). The ADR text already authorizes these. If Phase 3 discovers `fastmcp` is the wrong package name, that is a `RAISE_ISSUE` → operator decision, not a unilateral substitution.
- **Out: `AGENT_ENVELOPE` schema.** Slice 2 already shipped the object shape with `paths` and `cairn_query_snapshot` keys (verified by `_envelope_patterns` in `role_guard.py:67-90` and `server.py:_parse_envelope`). This slice consumes the schema; it does not change it.
- **Out: Bash deny widening.** `_bash_path_tokens` already extracts path-like tokens from Bash commands (line 104-112). The "cat/head/grep equivalents" coverage from ADR D8 is in place at the Bash layer; this slice only adds the literal `Grep` and `Glob` *tool* names to the read-class set.
- **Out: cairn_query internals.** The substrate's extractor and storage layer (`scripts/cairn_query/**`) are not touched. The dispatcher consumes the public callables already exposed in `mcp_servers/cairn_knowledge/tools.py`.
- **Out: INV-010 invariant-check `target:` block.** Stays at the `ROLE_DENY_READ` literal grep — the constant's set membership widens, the name does not.
- **Out: AGENT_ENVELOPE construction in dispatch.py.** Slice 2 already wired `phase-1-writer` to receive the object-shape envelope with `cairn_query_snapshot`. No orchestrator-side changes here.

### Verification

#### Closes when

1. `python -c "import fastmcp"` exits 0 inside `.venv`.
2. `python -m mcp_servers.cairn_knowledge` accepts a JSON-RPC `initialize` request on stdin and emits a well-formed JSON-RPC response on stdout (R1).
3. `tools/list` over JSON-RPC returns exactly `{lookup, search, path_bindings, cypher}` (R2).
4. `tools/call` for `lookup` with a known id returns the record (R3); with an unknown id returns a JSON-RPC error (R4).
5. `checks/role_guard.py` denies `Grep` and `Glob` on `ROLE_DENY_READ` paths for `phase-1-writer` and grants when envelope `paths` matches (G1-G7).
6. `.claude/agents/phase-1-writer.md` frontmatter `tools:` line does not contain `Grep` or `Glob`.
7. `docs/ARCHITECTURE.md` INV-010 prose names Grep and Glob in the deny surface; invariant-check grep target unchanged.
8. Full pytest passes: `uv run python -m pytest` is GREEN modulo the pre-existing INV-004 turn-1 token-budget OOS fail (`test_inv004_turn1_token_budget`, env-dependent, documented in `.claude/handoff.md` and not introduced by this slice).
9. Architecture validator passes: `uv run python scripts/validate_architecture.py` exits 0 with INV-010 reported PASS.
10. `.claude/envelope-grants.log` is unchanged at slice close (this slice does NOT use the envelope-grant escape; intent is drafted in this operator-interactive session, not by phase-1-writer; the canonical knowledge reads the operator/this session performed are not subject to D8 because `AGENT_ROLE` is unset per ADR D8 scope clause).
