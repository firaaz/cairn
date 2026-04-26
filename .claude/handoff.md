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

---
---
slice: compression/lever-Y-mcp-substrate-fixup
phase: 4-integration
date: 2026-04-26
verdict: PASS
---

## Result

All three substrate defects are closed:
1. **S1 — Real JSON-RPC dispatcher** shipped in `mcp_servers/cairn_knowledge/server.py` via FastMCP, replacing the boot-only stub. `initialize` / `tools/list` / `tools/call` round-trip green (R1-R5).
2. **S2 — fastmcp dep** added to `pyproject.toml` and locked via `uv sync`. `python -c "import fastmcp"` exits 0 inside `.venv`.
3. **S3 — Grep/Glob lockdown** — `READ_CLASS_TOOLS` extended to `{"Read","Grep","Glob"}`; `phase-1-writer.md` frontmatter dropped Grep/Glob; envelope-grant parity covered (G1-G7 green).

INV-010 prose amended (S5); invariant-check `target:` block left at the `ROLE_DENY_READ` literal grep, as scoped.

## Verification snapshot

- `uv run python -m pytest -q` → 1025 passed, 3 skipped, 0 failed (111.54s).
- `uv run python scripts/validate_architecture.py` → ALL CHECKS PASSED (10 invariants, 17 ADRs).
- All 10 closes-when gates from intent §Verification PASS.

## Phase-3 commits in scope

- `b84aac1` phase 3 [mcp-substrate-dispatcher]
- `fb0ba21` phase 3 [role-guard-read-class-deny]
- `e2abe73` fix(mcp-substrate) per-session temp DB to remove kuzu lock contention
- `8fc0133` operator pre-resume reconciliation fixup

## Unblocked

- Substrate Slice 3 (`compression/lever-Z-substrate-full-pipeline`) — phases 2/3/4 lockdown rollout per ADR D8 second stage.

## Out-of-scope (untouched, as declared)

- Mutation surface (D7 deferral).
- Sweep-results compaction policy.
- AGENT_ENVELOPE schema changes.
- INV-010 invariant-check `target:` literal.

---
---
slice: compression/lever-Y-mcp-substrate-fixup
phase: 4-integration
date: 2026-04-26
verdict: PASS
---

## Invariants

| ID | Verdict | Evidence (file:line) | Note |
|----|---------|----------------------|------|
| INV-010 | PASS | checks/role_guard.py:22 (READ_CLASS_TOOLS = {"Read","Grep","Glob"}); checks/role_guard.py:29 (ROLE_DENY_READ table); checks/role_guard.py:134 (read-class deny branch); checks/role_guard.py:163 (Bash deny branch); docs/ARCHITECTURE.md:93 (prose names Read/Bash/Grep/Glob); docs/ARCHITECTURE.md:96-101 (invariant-check grep target `ROLE_DENY_READ` against checks/role_guard.py — unchanged); .claude/agents/phase-1-writer.md:4 (frontmatter no longer carries Grep/Glob); mcp_servers/cairn_knowledge/server.py (FastMCP JSON-RPC dispatcher with snapshot-pin preserved); pyproject.toml ([project.dependencies] includes fastmcp); validate_architecture.py exit 0 on INV-010 grep target | Closes-when 1-10 satisfied; structural deny extended to Grep/Glob; envelope-grant parity covered by tests/unit/test_role_guard_grep_glob_deny.py (G1-G7) and JSON-RPC round-trip by tests/unit/test_mcp_cairn_knowledge_jsonrpc.py (R1-R5). |

## Test sweep

`uv run python -m pytest -q` → **1025 passed, 3 skipped in 111.54s**. No failures. The pre-existing INV-004 turn-1 token-budget OOS failure documented in intent §Verification item 8 did not surface this run (env-dependent CC-session measurement; out-of-scope for this slice regardless).

## Architecture validator

`uv run python scripts/validate_architecture.py` → **ALL CHECKS PASSED** (10 invariants verified, 17 ADR files checked).

## Envelope adherence

All edits in Phase 3 commits (`b84aac1`, `fb0ba21`, `e2abe73`, `8fc0133`) lie within the declared envelope. No source/test files were modified in Phase 4 (DC-4 / spec-v1.md §13 item 8 honored).

## Closes-when gate disposition

1. fastmcp import — PASS (pyproject + uv.lock include fastmcp; pytest imports succeed).
2-4. JSON-RPC initialize/tools-list/tools-call/error — PASS (R1-R5 covered in tests/unit/test_mcp_cairn_knowledge_jsonrpc.py, all green).
5. Grep/Glob deny + envelope-grant parity — PASS (G1-G7 in tests/unit/test_role_guard_grep_glob_deny.py, all green).
6. phase-1-writer.md frontmatter — PASS (no Grep/Glob present).
7. INV-010 prose amended; invariant-check target unchanged — PASS (docs/ARCHITECTURE.md:93,96-101).
8. pytest GREEN — PASS (1025/3s/0f).
9. validate_architecture.py — PASS.
10. .claude/envelope-grants.log unchanged — PASS (no phase-1-writer dispatch performed in this slice).

## Learnings observed (optional)

None recorded.
