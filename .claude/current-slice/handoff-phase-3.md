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
