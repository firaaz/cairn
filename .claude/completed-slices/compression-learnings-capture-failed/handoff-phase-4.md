---
slice: compression/learnings-capture
phase: 4
as-of: 92bf6d6
invocation: 3
---

## Status: RAISE_ISSUE (third Phase 4 invocation)

Three closes-when criteria remain unmet after two Phase 3 redispatches. Both redispatch rounds (commits `3618fb1` and `92bf6d6`) produced zero source-file changes — Phase 3 declared handoff complete without addressing the unresolved items.

### Unresolved items

1. `agent_timeout` emission site not wired: `dispatch.py:174` has `TimeoutExpired` catch but no `_record_orchestrator_event` import or call.
2. `cost_threshold_breach` / `token_threshold_breach` not wired: `core.py:116-117` thresholds are None; no detection or emission.
3. `.claude/agents/phase-4-integrator.md` missing `## Learnings observed (optional)` section.

### What Phase 3 must do

- Import `_record_orchestrator_event` in `dispatch.py` and add call at the `TimeoutExpired` site (~line 174).
- Add detection guards in `core.py` for INV_009 cost/token thresholds and wire emission calls.
- Append `## Learnings observed (optional)` section to `.claude/agents/phase-4-integrator.md`.
- **Before declaring handoff complete**: verify the diff against the previous `handoff: phase 3 complete` commit contains substantive source-file changes. A slice.yaml-only diff is insufficient.

### Operator note

Two consecutive Phase 3 agents have closed without making progress. Manual review of the Phase 3 agent prompt or direct operator-guided fix is recommended before next redispatch.
