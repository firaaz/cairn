---
slice: compression/lever-Y-mcp-substrate
phase: 4-integration
date: 2026-04-26
verdict: OK
---

# Handoff — Phase 4 (OK)

## Summary

Substrate Slice 2 closes clean post operator-fixup (0e531e0). FastMCP
server adapter (`mcp_servers/cairn_knowledge/`), `.mcp.json` stdio
registration, `role_guard.py` ROLE_DENY_READ + envelope-object grant
table, `dispatch.py` AGENT_ENVELOPE object shape with
`cairn_query_snapshot` (D12), and the phase-1-writer query-first prompt
all landed within envelope across Phase 3 commits cc57844..3d4e630. The
operator fixup 0e531e0 added INV-010 to docs/ARCHITECTURE.md, amended
the intent envelope, and bumped EXPECTED_INVARIANT_IDS to track INV-010 —
clearing the 8 pre-existing cairn-substrate-and-fastmcp validator
failures that V1 demanded.

`uv run pytest -q`: 995 passed / 1 failed / 3 skipped. The single
failure is `test_inv004_turn1_token_budget` (environment-dependent CC
session measurement, pre-existing out-of-scope; tracked in
`.claude/handoff.md` under "INV-004 rebaseline").

`uv run python scripts/validate_architecture.py`: ALL CHECKS PASSED
(10 invariants verified, 17 ADR files checked).

V1–V7 all met; V8 (cost-delta >=40%) is intentionally deferred per
intent to the first phase-1-writer dispatch in a downstream slice.

## Pointers

- `.claude/current-slice/integration/sweep-notes.md` — full roll-up + Learnings observed.
- Phase-3 commits: cc57844, 6ffe779, bd76014, e51d89b, 3d4e630.
- Operator fixup commit: 0e531e0 (full audit body).
- ADR: `docs/adr/cairn-substrate-and-fastmcp.md` (status: accepted, firm).
- INV-010: `docs/ARCHITECTURE.md`.

## Carry-forward

- Slice 3 (compression/lever-Z-substrate-full-pipeline) — generalize
  query-first + lockdown to phases 2/3/4; capture V8 cost-delta on its
  first phase-1-writer dispatch.
- L-014 candidate (firm-ADR with no referencing INV → Check B trap) — 1
  observation; await second recurrence before promotion.
- L-011 — no recurrence this slice; roadmap §11 fix still queued.
- INV-004 token-budget rebaseline — unchanged from prior handoff.

---
# Sweep notes — compression/lever-Y-mcp-substrate

date: 2026-04-26
slice: compression/lever-Y-mcp-substrate
phase: 4-integration
verdict: OK (post operator-fixup 0e531e0)

## Invariant verification

`invariants-touched: [INV-010]` after envelope amendment + operator fixup
(commit 0e531e0). INV-010 declares the structural commitments of the
substrate's MCP adapter, role_guard ROLE_DENY_READ table, AGENT_ENVELOPE
snapshot pinning (D12), envelope-grant escape (D9), and D15 operator-memory
permanent exclusion.

| invariant | status | file:line |
|-----------|--------|-----------|
| INV-010 | PASS | docs/ARCHITECTURE.md (added by 0e531e0); invariant-check greps `ROLE_DENY_READ` in checks/role_guard.py (added 6ffe779 in Phase 3) |

`uv run python scripts/validate_architecture.py` -> ALL CHECKS PASSED
(10 invariants verified, 17 ADR files checked).

## Test suite

`uv run pytest -q`: 995 passed / 1 failed / 3 skipped in 132s.

Single failure: `tests/unit/test_context_budget.py::test_inv004_turn1_token_budget`
(103574 > 40000). Environment-dependent INV-004 measurement against a live
`claude` CLI session — pre-existing CC-version drift, NOT introduced by this
slice and NOT in V1 set. INV-004 rebaseline remains tracked in
`.claude/handoff.md`.

The 8 pre-existing `cairn-substrate-and-fastmcp` validator failures that V1
demanded clear are all GREEN post-fixup, exactly as 0e531e0 predicted.

## validate_architecture.py

ALL CHECKS PASSED — 10 invariants verified, 17 ADR files checked.

## Phase-3 spot-check (within envelope)

- mcp_servers/cairn_knowledge/ added (e51d89b)
- checks/role_guard.py ROLE_DENY_READ + envelope-object grant (6ffe779)
- scripts/slice_orchestrator/dispatch.py snapshot pinning (bd76014)
- .claude/agents/phase-1-writer.md MCP-first prompt + .mcp.json stub (cc57844)
- docs/operational-reference.md AGENT_ENVELOPE object docs (3d4e630)
- Operator fixup 0e531e0: docs/ARCHITECTURE.md INV-010, EXPECTED_INVARIANT_IDS bump, intent envelope amendment.

No source-level scope drift across Phase 3 + operator fixup.

## Verification roll-up vs intent

- V1 — MET (995 passed; 8 substrate-and-fastmcp failures cleared).
- V2 — MET (FastMCP + 4 tools per e51d89b; test_mcp_cairn_knowledge_server.py).
- V3 — MET (test_mcp_cairn_knowledge_tools.py).
- V4 — MET (test_role_guard_phase_1_lockdown.py).
- V5 — MET (test_role_guard_envelope_grant.py).
- V6 — MET (test_orchestrator_snapshot_pinning.py).
- V7 — MET (test_phase_1_writer_query_first.py).
- V8 — DEFERRED per intent (not a Phase-4 gate for this slice; captured on next phase-1-writer dispatch).

## Learnings observed (optional)

- L-014 candidate (1 obs): firm/accepted ADR co-landed without an
  ARCHITECTURE.md INV referencing it leaves Check B red until a slice
  enumerates `docs/ARCHITECTURE.md` in its envelope. Resolved here via
  operator fixup 0e531e0. Promote to lessons on second recurrence.
- L-011: no recurrence — 5 Phase-3 clusters all landed as discrete commits
  cc57844..3d4e630 without orphan. Roadmap §11 fix remains queued.
