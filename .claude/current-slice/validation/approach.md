# Phase 2 approach — compression/lever-Y-mcp-substrate-fixup

## Strategy

Three independently-failing defects collapsed into one fixup slice; tests
must hold each defect's contract independently so Phase 3 can land them in
any order without test cross-talk.

- **§S1 (JSON-RPC dispatcher):** black-box subprocess round-trip in
  `test_mcp_cairn_knowledge_jsonrpc.py`. Spawn `python -m
  mcp_servers.cairn_knowledge`, write newline-delimited JSON-RPC, read
  responses via `select()` (no deadlock on crash). R1-R5 cover the five
  contract points; one source-text guard refutes the stub marker
  `discards input` and the keep-alive `while True: time.sleep(1)` pattern
  so Phase 3 cannot leave the stub in place while answering one request
  via a side channel.
- **§S2 (fastmcp dep):** parse `pyproject.toml` with `tomllib`; assert
  `fastmcp` is in `[project].dependencies` with a non-empty version
  constraint (D1 narrow-pin). Boundary test preserves the five existing
  standing deps. Closes-when #1 (`import fastmcp` exits 0) is enforced
  as a subprocess test.
- **§S3 (READ_CLASS_TOOLS + frontmatter):** subprocess hook tests over
  `checks/role_guard.py` mirroring `test_role_guard_envelope_grant.py`.
  G1-G7 + module-level constant-equality test + frontmatter `tools:`
  line tokenisation.
- **§S5 (INV-010 prose):** regex-extract the INV-010 paragraph and
  assert `Grep`/`Glob` appear; boundary test asserts the invariant-check
  fence's `pattern: "ROLE_DENY_READ"` and target stay unchanged.

## Ambiguities (resolved from intent/ADRs — none flagged for human)

1. **MCP tools/call content shape.** Intent §S1: "JSON-serialized return
   value is acceptable v1". Test substring-asserts `"INV-010"` in the
   serialized response — does not pin a content schema.
2. **JSON-RPC error code.** Intent §S1: "any valid JSON-RPC error code".
   Test accepts top-level `error` object OR `result.isError=true` (MCP
   allows both for tools/call).
3. **Termination rc on EOF.** Intent §S1: "rc=0 or SIGTERM-equivalent".
   Test accepts `rc == 0 or rc < 0`.
4. **Boot timeout.** Eager corpus rebuild dominates first-response
   latency; `CAIRN_MCP_BOOT_TIMEOUT_SEC` env override (default 45s) per
   CLAUDE.md no-hardcoded-timeouts guidance.
5. **fastmcp install state.** `import fastmcp` test fails until Phase 3
   runs `uv sync`. That is the intended RED.

No new ADR; all three defects operationalise D1/D6/D8.
