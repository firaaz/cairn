---
slice: compression/learnings-capture
phase: 3
as-of: HEAD
author: operator (post-orchestrator-escalation fixup)
---

## Status: OK (operator-completed — L-011 fixup)

Phase 3 ran through the orchestrator across two cluster fan-outs. The `phase4-prompt-amendment` cluster committed cleanly (`7894c01`). The `agent_timeout` cluster committed cleanly (`f2da04f`). The `orchestrator-events` cluster (helper + lifecycle.py emission sites + `_ARTIFACT_RELPATHS`) edited the working tree but never committed — its agent's response was wrapped in backticks so the orchestrator classified it `malformed` (debug log `compression-learnings-capture-phase-3-phase-3-implementer-20260426T081225Z.log`). The handoff boundary `ded0066` ("handoff: phase 3 complete") landed `--allow-empty`, leaving the orphan in the working tree.

This is the L-011 anti-pattern (third documented recurrence; cf. `cost-discipline/lever-1-tier-retune` L-011 instance + `compression/learnings-capture` failed-slice instance).

## Resolution: operator commit fixup + INV-009 caller inline-wired

Phase 4 (first invocation) RAISE_ISSUE'd cleanly with two findings:
- **F1 (L-011, blocking)** — `core.py` + `lifecycle.py` envelope source mods uncommitted; `ded0066` is `--allow-empty`.
- **F2 (functional gap)** — `_check_inv009_thresholds` defined but never called; 2 of 5 v1 emission sites functionally dead.

Per L-011 sanctioned options (a) re-dispatch or (b) operator commit-with-audit, the operator chose (b) plus inline F2 wiring. Rationale:
1. Phase 3 had already attempted twice (debug logs `080638Z` + `081225Z`); third attempt has empirical risk of repeating the trap.
2. Phase 4 verified the orphan is spec-compliant — no judgment-weight content review remains.
3. F2 wiring is small + well-scoped (single call site after `_record_phase_cost` in `dispatch.py`); deferring to a follow-up slice would leave dead code as a recurrence trap for the next slice that touches this module.

## Files captured in fixup commit

- `scripts/slice_orchestrator/core.py` — `_record_orchestrator_event` helper (line 489) + `_check_inv009_thresholds` wrapper (line 507) carved from `stash@{0}` and verified against intent §Specification Detail.
- `scripts/slice_orchestrator/lifecycle.py` — `_record_orchestrator_event` import (line 26) + `_ARTIFACT_RELPATHS` entry `"integration/orchestrator-events.jsonl"` + emission sites for `phase_redispatch` (line 307) and `redispatch_cap_exceeded` (line 347).
- `scripts/slice_orchestrator/dispatch.py` — `_check_inv009_thresholds` import + caller wired immediately after `_record_phase_cost` (within the existing defensive try block, so cost-telemetry tolerance covers threshold-check too).
- `.claude/current-slice/slice.yaml` — `current_phase: 4` orchestrator state.
- `.claude/current-slice/handoff-phase-3.md` — this file.

## Cluster-RED-test discipline (intent's distinguishing constraint) — observed

The retry's structural fix held: every Phase-3 cluster carried a RED test gate. The `phase4-prompt-amendment` cluster passed t4a/t4b only after the agent file was edited. The `orchestrator-events` cluster's tests required the helper definition + emission sites; tests would have stayed RED if the working-tree edits had been reverted.

The L-011 trap is orthogonal to RED-test discipline — the cluster's content was correct, only the commit step was missing. RED tests cannot detect "code written but not committed."

## Pending

L-011 is now at 3+ documented recurrences. The lesson's own "Mechanism: deferred pending recurrence" framing should be lifted to one of its two candidate fixes (prompt tightening + post-handoff diff verification, OR move content commits to the orchestrator). Tracked as a follow-up; outside this slice's envelope per L-013 guard.

---
---
slice: compression/learnings-capture
phase: 4
date: 2026-04-26
auditor: phase-4-integrator
status: OK
---

## Status

Phase 4 audit OK. Slice envelope clean against intent §Spec; all 5 v1 emission sites wired; phase-4-integrator prompt amendment landed in `7894c01` and verified by RED tests t4a/t4b; archival entry present in `_ARTIFACT_RELPATHS`. INV-008 + INV-003 PASS (see sweep-notes.md).

## What changed in this slice

- `scripts/slice_orchestrator/core.py` — `_record_orchestrator_event` (l489), `_check_inv009_thresholds` (l507).
- `scripts/slice_orchestrator/lifecycle.py` — emission at `phase_redispatch` (l307), `redispatch_cap_exceeded` (l347); `_ARTIFACT_RELPATHS += "integration/orchestrator-events.jsonl"` (l106).
- `scripts/slice_orchestrator/dispatch.py` — `agent_timeout` emission (l200); `_check_inv009_thresholds` caller (l235).
- `.claude/agents/phase-4-integrator.md` — `## Learnings observed (optional)` template guidance (l13).
- `tests/unit/test_orchestrator_events_capture.py` + `tests/unit/test_phase_4_integrator_prompt.py` — RED→GREEN coverage of all clusters including the prior gap (prompt-amendment cluster).

## Pre-existing failures (carried)

- 8 pytest failures + architecture validator: `cairn-substrate-and-fastmcp` ADR firm/accepted with no ARCHITECTURE.md invariant. Resolves at substrate Slice 2 (`compression/lever-Y-mcp-substrate`).

## Stash hygiene

- `stash@{0}` (Phase-3 orphan from `cost-discipline/lever-1-tier-retune`) was the seed for this slice's `core.py`/`lifecycle.py` carve. Its content has now landed in this slice's commits (`7894c01`, `f2da04f`, `354167a`). **Recommend dropping `stash@{0}` after slice close** (`git stash drop stash@{0}`) — operator action.

## Lessons in flight

- **L-011 third recurrence** observed inside this slice (Phase 3 orchestrator-events cluster left envelope uncommitted; operator fixup `354167a`). RED-test discipline held but cannot detect "written, not committed." The lesson's "deferred pending recurrence" stance is ripe for promotion to one of its two candidate fixes. Tracked for next handoff; out of envelope per L-013.

## Next slice

- `compression/lever-Y-mcp-substrate` (substrate Slice 2) — opens on close per brief; resolves the 8 pre-existing validator failures by introducing the missing ARCHITECTURE.md invariant for `cairn-substrate-and-fastmcp`.

---
---
slice: compression/learnings-capture
phase: 4
date: 2026-04-26
auditor: phase-4-integrator
---

## Invariants observed

| Invariant / Contract | Result | Evidence (file:line) |
|---|---|---|
| INV-008 / slice-artifact-preservation (DC-3 idempotent, DC-4 sole commit, DC-5 wipe, DC-7 slug-keyed) — passive consumer; events-jsonl added to archived set without disturbing copy step | PASS | scripts/slice_orchestrator/lifecycle.py:106 (`"integration/orchestrator-events.jsonl"` in `_ARTIFACT_RELPATHS`); test_orchestrator_events_capture.py::test_t3_lifecycle_archives_events_jsonl |
| INV-003 / phase-lock-and-role-declaration — only Phase-4 (Auditor) prompt amended; phases 1-3 untouched; role declarations unchanged | PASS | .claude/agents/phase-4-integrator.md:13 (`## Learnings observed (optional)` line); diff confined to Phase-4 agent |

## Closes-when checklist (intent §Verification)

- `uv run pytest -q`: 947 passed, 3 skipped, 8 failed — all 8 failures are the pre-existing `cairn-substrate-and-fastmcp` ADR-without-ARCHITECTURE-invariant condition (resolves at substrate Slice 2). Out of scope per intent.
- New tests: `tests/unit/test_orchestrator_events_capture.py` + `tests/unit/test_phase_4_integrator_prompt.py` — 15/15 PASS.
- `_record_orchestrator_event` defined in `core.py:489`; wired at 5 v1 emission sites:
  - `phase_redispatch` — `lifecycle.py:307`
  - `redispatch_cap_exceeded` — `lifecycle.py:347`
  - `cost_threshold_breach` / `token_threshold_breach` — `core.py:520`/`core.py:527` (via `_check_inv009_thresholds`, called from `dispatch.py:235`)
  - `agent_timeout` — `dispatch.py:200`
- `_ARTIFACT_RELPATHS` contains `"integration/orchestrator-events.jsonl"` — `lifecycle.py:106`.
- `.claude/agents/phase-4-integrator.md` contains `## Learnings observed (optional)` — line 13. Bound by RED tests t4a/t4b.
- Architecture validator: PRE-EXISTING FAILURE (cairn-substrate-and-fastmcp); tolerated per intent.
- L-011/L-013 envelope-clean audit at Phase-3 handoff: Phase 3 left orphan in working tree; operator fixup commit `354167a` captured all envelope source mods (per handoff-phase-3.md §Resolution). `git status` clean at Phase-4 entry.
- End-to-end smoke: deferred — close_slice will exercise the archival path on this slice's own close (events file may be empty since this slice did not redispatch / breach; F5-tolerance per `_copy_artifacts_to_sweep_results` handles the zero-events case silently per intent §Archival wiring).

## Out-of-scope failures (documented per spec-v1 §13)

- 8 pytest failures all trace to `cairn-substrate-and-fastmcp` ADR being firm/accepted with no ARCHITECTURE.md invariant. Identical signature to baseline before this slice; resolves at substrate Slice 2 (`compression/lever-Y-mcp-substrate`).

## Learnings observed (optional)

- L-011 recurred a third time inside this very slice (Phase 3 orchestrator-events cluster left envelope source uncommitted; operator fixup `354167a`). The retry's RED-test discipline held — every cluster carried a test gate — but RED tests cannot detect "code written, not committed." The handoff-phase-3.md author flags L-011's "Mechanism: deferred pending recurrence" framing as ripe for promotion to one of its two candidate fixes (prompt-tightening vs. orchestrator-side commit move). Out-of-envelope per L-013 guard; tracked for next handoff.
- The phase-4-integrator prompt amendment cluster's brittleness trade-off (string-presence assertion against the agent file) was the structural fix for the prior failure mode (cluster-no-RED-test). It worked: t4a/t4b stayed RED until the prompt edit landed in commit `7894c01`.
