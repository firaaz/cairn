# Phase-2 Skeptic Approach — compression/lever-Y-mcp-substrate

## What I am asserting

Intent verification gates V1–V7. V8 is a post-close cost-delta measurement
(next-slice integration sweep) and is explicitly NOT a Phase-4 PASS gate
for this slice; no test for V8.

## Test files (one per envelope-declared file)

- `test_mcp_cairn_knowledge_server.py` — V2: package layout, four-tool
  registry surface, stdio subprocess boots, server.py reads
  `AGENT_ENVELOPE.cairn_query_snapshot`.
- `test_mcp_cairn_knowledge_tools.py` — V3: each of the four tools
  returns typed pydantic records (or row dicts for `cypher`) over the
  rebuilt-from-canonical kuzu corpus. ADR-D15 structural check: `tools.py`
  source contains no operator-memory references.
- `test_role_guard_phase_1_lockdown.py` — V4: subprocess invocation of
  `checks/role_guard.py` denies Read+Bash on the six canonical-knowledge
  path families for `phase-1-writer`; allows when AGENT_ROLE unset
  (D8 carve-out); other phases unaffected (Slice-3 territory).
- `test_role_guard_envelope_grant.py` — V5: object-shape envelope grants
  Read on locked-down paths AND emits exactly one line to
  `.claude/envelope-grants.log`; non-matching object envelopes still deny;
  legacy array envelopes still round-trip via `_envelope_patterns`.
- `test_orchestrator_snapshot_pinning.py` — V6: monkeypatching
  `dispatch._run_with_live_stderr` to capture the `env` dict, asserts
  phase-1-writer dispatch sets `AGENT_ENVELOPE` as a JSON object with
  `cairn_query_snapshot=git rev-parse HEAD` and a `paths` array; sentinel
  `unknown-sha-<iso8601>` on git failure (D12); phase-3 array envelope
  passes through unchanged.
- `test_phase_1_writer_query_first.py` — V7: agent frontmatter no longer
  lists Read/Bash; prompt body names all four MCP tools; P1/P2
  escape-hatch directives preserved; `.mcp.json` registers cairn-knowledge.

## Ambiguities resolved (not flagged)

- A1. V2 "exactly four tools enumerated": black-box registry surface check
  (TOOLS dict/list OR module-level callables) plus subprocess-boot smoke.
  Protocol handshake is integration scope.
- A2. V4 "Bash" denial scope: tool_name=Bash with `command` substring
  scanning for canonical paths (ADR D8 covers cat/head/grep).
- A3. V6 sentinel format: loose `^unknown-sha-\d{4}-\d{2}-\d{2}` per D12.
- A4. V5 grant-log line: asserts granted-path + phase-1 substring; strict
  format deferred.

No spec ambiguities require RAISE_ISSUE.
