# Sweep Notes — compression/learnings-capture

Phase 4 audit at commit `92bf6d6` (handoff: phase 3 complete — **third Phase 4 invocation**).

## Invariant verification

| Invariant | Status | Evidence |
|-----------|--------|----------|
| Helper `_record_orchestrator_event` exists in `core.py` | PASS | `scripts/slice_orchestrator/core.py:489` |
| Helper appends JSONL with `ts`, `slice_id`, `event_type` schema | PASS | tests t1a-t1d all green |
| Helper is append-only, F5-tolerant (parent-dir create) | PASS | `core.py:496` `path.parent.mkdir(parents=True, exist_ok=True)` |
| `phase_redispatch` wired at RE_DISPATCH branch | PASS | `lifecycle.py:347-349` |
| `redispatch_cap_exceeded` wired at B15 trip | PASS | `lifecycle.py:307-309` |
| `agent_timeout` wired at `dispatch.py` `TimeoutExpired` catch | **FAIL** | `dispatch.py:174` — catch exists, no `_record_orchestrator_event` call; not imported |
| `cost_threshold_breach` wired in `core.py` | **FAIL** | `INV_009_COST_THRESHOLD_USD = None` at `core.py:116`; no emission site |
| `token_threshold_breach` wired in `core.py` | **FAIL** | `INV_009_TOKEN_THRESHOLD = None` at `core.py:117`; no emission site |
| `_ARTIFACT_RELPATHS` includes `integration/orchestrator-events.jsonl` | PASS | `lifecycle.py:106` |
| `_copy_artifacts_to_sweep_results` archives events file | PASS | test t3 green |
| `.claude/agents/phase-4-integrator.md` contains `## Learnings observed (optional)` | **FAIL** | File is 19 lines; section absent — persisted through two Phase 3 redispatches |
| `uv run pytest` 7 new tests green | PASS | All 7 new tests pass |
| Full suite | PASS (5 known pre-existing fails) | 858 passed, 5 pre-existing architecture-validator failures |
| `validate_architecture.py` | Pre-existing FAIL (out-of-scope) | `cairn-substrate-and-fastmcp` firm/accepted but no ARCHITECTURE.md invariant |

## INV-008 / INV-003 posture

- **INV-008** (slice-artifact-preservation): events-jsonl passive consumer of pre-wipe copy step. PASS.
- **INV-003** (phase-lock-and-role-declaration): phases 1-3 unchanged. Phase-4 prompt amendment NOT completed. Partial FAIL.

## Issues requiring RAISE_ISSUE

Three closes-when criteria remain unmet after **two Phase 3 redispatches** (commits `3618fb1` and `92bf6d6` — neither introduced source-file changes):

1. **`agent_timeout` not wired** (`dispatch.py:174`). `TimeoutExpired` catch exists but `_record_orchestrator_event` not imported or called.

2. **`cost_threshold_breach` / `token_threshold_breach` not wired** (`core.py:116-117`). Both `INV_009_*` constants are `None`; no detection guard or emission call.

3. **`.claude/agents/phase-4-integrator.md` missing `## Learnings observed (optional)` section**.

**Escalation note:** Phase 3 dispatched twice after the first RAISE_ISSUE. Both rounds produced a `handoff: phase 3 complete` commit with zero source-file changes. Operator intervention recommended.

## Learnings observed (optional)

**Persistent redispatch-without-fix pattern:** Two consecutive Phase 3 agents declared handoff complete without modifying source files. A slice.yaml-only diff against the last `handoff: phase 3 complete` commit signals premature close.

**Partial-PASS trap:** 8 of 11 invariants PASS but the three FAILs are the exact new behaviors this slice was opened to implement. High PASS ratio does not substitute for closes-when criterion satisfaction.
