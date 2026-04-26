---
slice: compression/lever-Y-mcp-substrate-fixup
phase: 2-validation
branch: feature/compression
as-of: 2026-04-26 0650527
---

## State
`compression/lever-Y-mcp-substrate-fixup` Phase 1 intent committed (`0650527`) via prose protocol — orchestrator bypassed because phase-1-writer dispatch would hit the broken substrate this slice fixes. `slice.yaml` at `status: validation`, `current_phase: 2`. Envelope: 12 paths covering server.py JSON-RPC dispatcher, pyproject fastmcp dep, role_guard READ_CLASS_TOOLS extension, INV-010 prose, and two new test files.

## Next
Dispatch `phase-2-skeptic` via Agent tool with `intent.md` as sole input — write tests for R1-R5 (JSON-RPC round-trip) and G1-G7 (Grep/Glob deny + envelope-grant parity).

## Blocked / Pending
- Orchestrator `--resume` will refuse this slice → use in-session subagent dispatch for Phases 2/3/4 (resume.py rows 1-3 default-refuse on missing result.json + non-init/non-handoff HEAD).
- Slice 3 (`compression/lever-Z-substrate-full-pipeline`) → depends on this slice closing.
- L-011 structural fix → roadmap §11 unchanged.
- L-014 candidate (1 obs) → promote on second recurrence.
- INV-004 rebaseline + `agent-managed-planning-substrate` ADR → unchanged.

## Features
- compression: fixup slice in Phase 2; gates Slice 3.
- cost-discipline: lever-1 complete; further levers parked.

## Pointers
- `.claude/current-slice/intent.md` — full S1-S5 spec + 10 closes-when gates.
- `.claude/current-slice/handoff-phase-1.md` — orchestrator-bypass rationale + Phase 2 input list.
- `mcp_servers/cairn_knowledge/server.py:61-76` — `_stdin_reader` stub the dispatcher replaces.
- `checks/role_guard.py:22,133-145` — `READ_CLASS_TOOLS` and read-class deny branch.
- `docs/ARCHITECTURE.md:93-101` — INV-010 prose + invariant-check block.
- `tests/unit/test_mcp_cairn_knowledge_server.py:70-125` — under-stated V2/V3 tests retained as smoke.
