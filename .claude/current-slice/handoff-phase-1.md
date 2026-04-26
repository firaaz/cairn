# Phase 1 handoff — compression/lever-Y-mcp-substrate-fixup

phase: 1-intent → 2-validation
date: 2026-04-26
mode: prose-protocol (orchestrator bypassed for Phase 1 due to broken substrate)

## Drafted by

Operator-interactive session (`AGENT_ROLE` unset per ADR `cairn-substrate-and-fastmcp` D8 scope clause). The orchestrator's `phase-1-writer` agent was not dispatched: dispatching it would have run against the very stub-MCP / Grep-Glob-bypass / missing-fastmcp defects this slice fixes, producing either a hard failure (fastmcp ImportError → server boot crash → MCP unusable → query-first agent has no fallback) or a structurally-laundered draft (reads via the unintended Grep/Glob bypass, defeating ADR D8's lockdown intent).

## What ships

- `.claude/current-slice/intent.md` — three specification sections (S1 JSON-RPC dispatcher, S2 fastmcp dep, S3 READ_CLASS_TOOLS extension + frontmatter drop, S4 Phase-2 test hardening, S5 INV-010 prose amendment) + 10 closes-when verification gates.
- `.claude/current-slice/slice.yaml` — `status: validation`, `current_phase: 2`.
- `.claude/features/compression.yaml` — slice entry appended after `compression/lever-Y-mcp-substrate`.

## Envelope (12 paths)

- `mcp_servers/cairn_knowledge/server.py`
- `pyproject.toml`
- `uv.lock`
- `checks/role_guard.py`
- `.claude/agents/phase-1-writer.md`
- `docs/ARCHITECTURE.md`
- `tests/unit/test_mcp_cairn_knowledge_server.py`
- `tests/unit/test_mcp_cairn_knowledge_jsonrpc.py` (new)
- `tests/unit/test_role_guard_grep_glob_deny.py` (new)
- `.claude/current-slice/intent.md`
- `.claude/current-slice/slice.yaml`
- `.claude/features/compression.yaml`

## ADRs referenced

- `cairn-substrate-and-fastmcp` (D1 standing deps, D6 stdio JSON-RPC, D8 structural deny, D9 envelope-grant parity for new read-class tools)
- `compression-infrastructure-bootstrap` (role_guard PreToolUse mechanism authorization)

No new ADR. All three defects are operationalization of pre-committed decisions (edit-don't-decide for internal contradictions).

## Invariants touched

- INV-010 — strengthened (deny surface widened to include Grep/Glob; invariant-check `target:` literal `ROLE_DENY_READ` unchanged so the existing Check B remains green).

## Phase 2 entry guidance

Phases 2/3/4 dispatch via in-session subagents (Agent tool with `subagent_type: phase-2-skeptic` etc.), NOT via `python -m slice_orchestrator --resume`. The orchestrator's resume reconciler (`scripts/slice_orchestrator/resume.py:_reconcile_resume_state`) will refuse this hand-rolled state because:

- `result.json` is absent (orchestrator never ran for this slice).
- `slice.yaml` status is `validation` / `in-progress`.
- HEAD subject is `slice: ... — phase 1 intent` (prose-protocol convention), matching neither the `slice: <id> — init` regex nor the `handoff: phase N complete` regex the reconciler expects.

Reconciler row 1-3 default-refuses on this triple. Faking a synthetic `result.json` to coerce a row 4-6 match is a fragile workaround; subagent dispatch is cleaner for this one bootstrap slice.

After this slice closes, normal orchestrator dispatch resumes for subsequent slices.

## Phase-2 inputs (for the skeptic subagent)

- `intent.md` (only).
- `docs/ARCHITECTURE.md` (INV-010 prose for verification reference).
- ADR `cairn-substrate-and-fastmcp` D6 (MCP transport spec) and D9 (envelope-grant semantics — Grep/Glob must inherit them).
- MCP spec for JSON-RPC initialize / tools/list / tools/call shapes (skeptic chooses primary reference; modelcontextprotocol.io is the canonical spec source).
