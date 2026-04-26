---
slice: compression/learnings-capture
date: 2026-04-26
phase: 1-intent
invariants-touched: []
adrs-referenced: [slice-artifact-preservation, phase-lock-and-role-declaration]
adrs-created: []
envelope:
  - "scripts/slice_orchestrator/lifecycle.py"
  - "scripts/slice_orchestrator/core.py"
  - "scripts/slice_orchestrator/dispatch.py"
  - ".claude/agents/phase-4-integrator.md"
  - "tests/unit/test_orchestrator_events_capture.py"
  - ".claude/features/compression.yaml"
  - ".claude/current-slice/intent.md"
  - ".claude/current-slice/validation/approach.md"
  - ".claude/current-slice/implementation/notes.md"
  - ".claude/current-slice/integration/sweep-notes.md"
  - ".claude/current-slice/handoff-phase-1.md"
  - ".claude/current-slice/handoff-phase-2.md"
  - ".claude/current-slice/handoff-phase-3.md"
  - ".claude/current-slice/handoff-phase-4.md"
out-of-scope:
  - "Per-phase-1/2/3 learning surfaces — deferred until Phase-4 + orchestrator-events surface proves insufficient (recurrence-watching pattern)"
  - "Automatic 3×-rule promotion to docs/lessons.md — operator-driven workflow stays manual"
  - "Post-close commit detection (the L-010 WS1 fixup-after-close pattern) — orchestrator can't observe inline; separate slice if needed"
  - "Empty-handoff-commit detection (L-008 follow-up) — different fix, different slice"
  - ".claude/learning.md V5 cap revision — stays minimal cross-session staging by design"
  - "Test for orchestrator events that requires actual phase-agent dispatch (use unit-level mocks of the dispatch boundary)"
  - "New ADR — this slice is mechanism addition only"
  - "Any change to phase-1/2/3-* agent prompts (Phase-4 only)"
---

### What and Why

The compressed slice protocol structurally lost the per-slice learning-capture surface that the legacy single-CC-session model captured mid-flight. L-010 (the WS4/WS1 paired-instance Phase-4 role-lock differential) only existed because of post-close forensic exploration — there was no in-flight place to record it. This slice restores capture by adding two complementary surfaces, both archived by the existing `slice-artifact-preservation` pipeline so the 3×-rule promotion to `docs/lessons.md` reads from a permanent record:

1. **Phase-4 integrator** emits an optional `## Learnings observed` subsection inside `sweep-notes.md` — free-form prose, judgment-based, empty by default ("only fill when something surprised you").
2. **Orchestrator** emits mechanical structured events at `.claude/current-slice/integration/orchestrator-events.jsonl` (phase_redispatch, redispatch_cap_exceeded, cost_threshold_breach, token_threshold_breach, agent_timeout).

Both ride the existing `_ARTIFACT_RELPATHS` archival pipeline (`sweep-notes.md` already listed; events-jsonl added) and survive DC-5 wipe into `.claude/sweep-results/<slug>/artifacts/`.

### Boundary

Out of scope: per-phase 1/2/3 learning surfaces; automatic 3×-rule promotion; post-close commit detection (L-010 WS1); empty-handoff-commit detection (L-008); `.claude/learning.md` V5 revision; any new ADR; any phase-1/2/3 agent-prompt change (Phase-4 only).

### Specification Detail

**Helper contract (`scripts/slice_orchestrator/core.py`).** New function `_record_orchestrator_event(slice_id: str, event_type: str, **fields) -> None`. Appends one JSON-encoded line to `.claude/current-slice/integration/orchestrator-events.jsonl`. Schema per record:

```json
{"ts": "<ISO8601 with explicit UTC offset>", "slice_id": "<str>", "event_type": "<str>", ...caller-supplied fields}
```

- `ts`: `datetime.now(timezone.utc).isoformat()` — parseable by `datetime.fromisoformat`; ends `+00:00`.
- File mode: append (`"a"`); never overwrite. Each call writes exactly one line ending in `\n`.
- Parent-directory creation: `path.parent.mkdir(parents=True, exist_ok=True)` — F5-tolerant of missing `integration/`.
- No `_git` calls; helper is commit-site-free (DC-4 preserved by construction).

**Emission sites (v1 set).** Each call site adds exactly one line invoking `_record_orchestrator_event(...)` with the canonical event_type token and relevant fields:

| event_type | Site | Required extra fields |
|---|---|---|
| `phase_redispatch` | `core.py` re-dispatch handler (dispatch_triager → RE_DISPATCH branch) | `from_phase: int`, `to_phase: int` |
| `redispatch_cap_exceeded` | `core.py` B15 second-redispatch-on-same-phase trip | `phase: int`, `count: int` |
| `cost_threshold_breach` | `core.py` INV-009 cost threshold breach detection | `threshold_usd: float`, `observed_usd: float` |
| `token_threshold_breach` | `core.py` INV-009 token threshold breach detection | `threshold_tokens: int`, `observed_tokens: int` |
| `agent_timeout` | `dispatch.py` `subprocess.TimeoutExpired` catch site | `phase: int`, `timeout_seconds: int` |

**Archival wiring (`scripts/slice_orchestrator/lifecycle.py`).** The existing `_ARTIFACT_RELPATHS` tuple gains the single entry `"integration/orchestrator-events.jsonl"`. No other change to `lifecycle.py`. The existing `_copy_artifacts_to_sweep_results` helper's F5-tolerance (per ADR `slice-artifact-preservation` D6) handles the zero-events case (events file absent) silently — a slice that emitted no orchestrator events does NOT fail the close.

**Phase-4 integrator prompt amendment (`.claude/agents/phase-4-integrator.md`).** Additive amendment to the integrator's `sweep-notes.md` template guidance: introduce an `## Learnings observed (optional)` subsection framed as free-form notes on anything that surprised the auditor (novel patterns, cross-phase signals, contracts holding under pressure, contracts bending). Empty section is the honest default; the operator promotes patterns to `docs/lessons.md` via the manual 3×-rule. The amendment does not expand the integrator's write surface (`sweep-notes.md` is already a Write target) and does not change any existing instruction.

**Invariant posture.** No invariant amended. INV-008 contract (slice-close-contract / slice-artifact-preservation): the new events-jsonl is a passive consumer of the already-committed pre-wipe copy step — no change to DC-3 idempotency, DC-4 sole-commit-source, DC-5 wipe, DC-7 slug-keyed observability. INV-003 contract (phase-lock-and-role-declaration): only the Phase-4 (Auditor) prompt is touched; phases 1–3 unchanged; role declarations unchanged; no rename/reorder. `adrs-referenced` lists both ADRs because their contracts constrain the slice's edits even though neither is rewritten.

**Stdlib-only.** Implementation uses `json` (JSONL), `datetime.timezone.utc` (ISO8601), `pathlib.Path` (already imported in `core.py`). No new third-party dependency. Phase-4 integrator amendment is markdown only.

### Verification

Phase 2 ships ~7 RED tests in the new file `tests/unit/test_orchestrator_events_capture.py`:

- `test_t1a_helper_appends_jsonl_line` — one call writes one JSON-decodable line containing `slice_id`, `event_type`, supplied fields, and a `ts` key.
- `test_t1b_helper_includes_iso8601_utc_timestamp` — `ts` ends `+00:00` (or `Z`) and parses via `datetime.fromisoformat`.
- `test_t1c_helper_appends_not_overwrites` — two successive calls produce two lines, not one overwritten.
- `test_t1d_helper_creates_parent_dir_if_missing` — helper creates `.claude/current-slice/integration/` when absent (F5-tolerance).
- `test_t2a_redispatch_emits_event` — `RE_DISPATCH` triager outcome causes `phase_redispatch` emission with `from_phase`, `to_phase` fields (mocking the dispatch boundary, not actual agent dispatch).
- `test_t2b_b15_cap_emits_event` — second redispatch on the same phase emits `redispatch_cap_exceeded` with `phase`, `count`.
- `test_t3_lifecycle_archives_events_jsonl` — `_ARTIFACT_RELPATHS` includes `integration/orchestrator-events.jsonl`; `close_slice` copies a populated events file into `.claude/sweep-results/<slug>/artifacts/`.

Phase 4 closure evidence (closes-when, not test):

- `uv run pytest -q` passes; the 7 new tests pass; no regression in the pre-existing 924-test passing baseline.
- `_record_orchestrator_event` exists in `core.py` and is wired at all five v1 emission sites (re-dispatch, B15, cost-threshold, token-threshold, agent-timeout).
- `_ARTIFACT_RELPATHS` in `lifecycle.py` contains the new entry.
- `.claude/agents/phase-4-integrator.md` contains the `## Learnings observed (optional)` template guidance.
- End-to-end smoke run of any small slice produces a populated `orchestrator-events.jsonl` archived under `.claude/sweep-results/<slug>/artifacts/` — verified by inspection at slice close.
- Architecture validator passes (still expects 8 known `cairn-substrate-and-fastmcp` INV failures; those resolve at substrate Slice 2, not here — do NOT touch ARCHITECTURE.md).
