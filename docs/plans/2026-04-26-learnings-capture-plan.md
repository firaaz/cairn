# Learnings Capture — Implementation Plan

> **For agentic workers:** This plan is INPUT to cairn's slice pipeline (slice id `compression/learnings-capture`). Phase 1 derives `intent.md` from §Goal/§Architecture/§Envelope below. Phase 2 writes the tests in each Task's "Tests Phase 2 writes" block (one commit). Phase 3 implements per "Implementation Phase 3 ships" block (one commit). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Restore the per-slice learning-capture surface that the compressed protocol structurally lost. The legacy serial-protocol single-CC-session model captured operator-noticed patterns mid-flight; today's orchestrator + subagent-phase model has no equivalent capture point. L-010 (the WS4/WS1 paired-instance Phase-4 role-lock differential) only existed because of post-close forensic exploration. Add two complementary capture surfaces — both written to slice envelopes already preserved by `slice-artifact-preservation`, so 3×-rule promotion to `docs/lessons.md` reads from a permanent record.

**Architecture:** Two surfaces, layered:

1. **Phase-4 integrator emits `## Learnings observed (optional)` in `sweep-notes.md`.** Free-form prose, judgment-based. The integrator already runs the cross-phase audit and sees patterns; this just adds a named place to record them. Empty section is fine — the prompt frames it as "only fill when something surprised you."

2. **Orchestrator emits `orchestrator-events.jsonl` at `.claude/current-slice/integration/orchestrator-events.jsonl`.** Mechanical, structured. New helper `_record_orchestrator_event(slice_id, event_type, **fields)` appends one JSONL line per detected event. v1 emission sites: phase re-dispatch (`phase_redispatch`), B15 cap trip (`redispatch_cap_exceeded`), INV-009 cost-threshold breach (`cost_threshold_breach`), INV-009 token-threshold breach (`token_threshold_breach`), subprocess timeout (`agent_timeout`). Each line: `{"ts": ISO8601, "slice_id": str, "phase": int|null, "event_type": str, ...fields}`.

Both surfaces ride the existing artifact-preservation pipeline: `_ARTIFACT_RELPATHS` in `lifecycle.py` gains `integration/orchestrator-events.jsonl`; `sweep-notes.md` is already in the list. At close, both are copied to `.claude/sweep-results/<slug>/artifacts/` and survive the DC-5 wipe permanently.

**Tech Stack:** stdlib only — `json` for JSONL, `datetime.timezone.utc` for ISO8601, no new deps. Phase-4 integrator prompt amendment is markdown-only.

**Slice id:** `compression/learnings-capture`
**Feature:** `compression`
**Branch:** `slice/compression-learnings-capture`
**Worktree:** `.worktrees/learnings-capture/` (spawned from `feature/compression`; runs serially, not in parallel with substrate Slice 2)

---

## Sequencing context

- **Predecessor:** `compression/slice-artifact-preservation` (closed, merged at `b846652`) — provides the archival pipeline this slice's `orchestrator-events.jsonl` rides on.
- **Successor:** `compression/lever-Y-mcp-substrate` (substrate Slice 2) — opens AFTER this slice closes, so Slice 2's first-use of the FastMCP adapter exercises the new learning-capture surfaces.
- **Why before Slice 2:** Slice 2 is wide (FastMCP adapter + ADR ratification + D8 lockdown + D9 envelope-grant + D12 SHA pinning). Its size + cross-cutting surface make it likely to surface novel patterns; capture infrastructure should exist before it runs, not after.
- **No ADR needed:** the slice adds two small mechanisms layered on existing ADRs (`slice-artifact-preservation` for archival, `phase-lock-and-role-declaration` constrains the Phase-4 integrator's prompt surface). Neither contract is amended; neither V-property is rewritten. `adrs-created: []`, `adrs-referenced: [slice-artifact-preservation, phase-lock-and-role-declaration]`.

---

## Envelope

```yaml
envelope:
  - "scripts/slice_orchestrator/lifecycle.py"
  - "scripts/slice_orchestrator/core.py"
  - "scripts/slice_orchestrator/dispatch.py"
  - ".claude/agents/phase-4-integrator.md"
  - "tests/unit/test_orchestrator_events_capture.py"
  - ".claude/features/compression.yaml"
  - ".claude/current-slice/{intent.md,validation/approach.md,implementation/notes.md,integration/sweep-notes.md}"
  - ".claude/current-slice/handoff-phase-{1,2,3,4}.md"
out-of-scope:
  - "Per-phase-1/2/3 learning surfaces — deferred until Phase-4 + orchestrator-events surface proves insufficient (recurrence-watching pattern)"
  - "Automatic 3×-rule promotion to docs/lessons.md — operator-driven workflow stays manual"
  - "Post-close commit detection (the L-010 WS1 fixup-after-close pattern) — orchestrator can't observe inline; separate slice if needed"
  - "Empty-handoff-commit detection (L-008 follow-up) — different fix, different slice"
  - ".claude/learning.md V5 cap revision — stays minimal cross-session staging by design"
  - "Test for orchestrator events that requires actual phase-agent dispatch (use unit-level mocks of the dispatch boundary)"
  - "New ADR — this slice is mechanism addition only"
  - "Any change to phase-1/2/3-* agent prompts (Phase-4 only)"
```

---

## File Structure

```
scripts/slice_orchestrator/
  lifecycle.py            # MODIFY: add 'integration/orchestrator-events.jsonl' to _ARTIFACT_RELPATHS
  core.py                 # MODIFY: add _record_orchestrator_event helper; emit at re-dispatch, B15 cap, cost/token threshold sites
  dispatch.py             # MODIFY: emit agent_timeout event at subprocess.TimeoutExpired catch site

.claude/agents/
  phase-4-integrator.md   # MODIFY: prompt amendment — frame `## Learnings observed (optional)` subsection in sweep-notes.md template

tests/unit/
  test_orchestrator_events_capture.py   # NEW: ~7 RED tests covering helper + emission sites + jsonl format + integration-with-archival

.claude/features/compression.yaml       # APPEND: slice entry (Phase 1 writes)
```

**Notes on file decomposition:**
- The helper `_record_orchestrator_event` lives in `core.py` (with the other shared orchestrator utilities) and is called from `core.py` (re-dispatch, B15, cost/token) and `dispatch.py` (timeout). Single source-of-truth for the schema.
- Test file is ONE file with all 7 RED tests; they share fixtures (a temp slice dir + a populated `.claude/current-slice/integration/`).
- `lifecycle.py` change is one-line: extending `_ARTIFACT_RELPATHS` with the events-jsonl entry. Verify `_copy_artifacts_to_sweep_results` already F5-tolerates absent files (it does, per ADR D6) so a slice with zero orchestrator events doesn't fail the close.

---

## Tasks

### Task 1: `_record_orchestrator_event` helper + JSONL schema

**Files:**
- Modify: `scripts/slice_orchestrator/core.py`
- Test: `tests/unit/test_orchestrator_events_capture.py`

**Tests Phase 2 writes** (in one commit, all RED initially):

```python
# tests/unit/test_orchestrator_events_capture.py
"""Slice compression/learnings-capture — orchestrator events surface."""

import json
from pathlib import Path
from scripts.slice_orchestrator import core


def test_t1a_helper_appends_jsonl_line(tmp_path, monkeypatch):
    """Helper writes one JSON-encoded line per call to events file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".claude/current-slice/integration").mkdir(parents=True)
    core._record_orchestrator_event("test/slice", "phase_redispatch", from_phase=4, to_phase=3)
    line = (tmp_path / ".claude/current-slice/integration/orchestrator-events.jsonl").read_text()
    record = json.loads(line)
    assert record["slice_id"] == "test/slice"
    assert record["event_type"] == "phase_redispatch"
    assert record["from_phase"] == 4
    assert record["to_phase"] == 3
    assert "ts" in record


def test_t1b_helper_includes_iso8601_utc_timestamp(tmp_path, monkeypatch):
    """Timestamp field is ISO8601 with explicit UTC offset."""
    # ts ends in '+00:00' or 'Z'; parseable by datetime.fromisoformat


def test_t1c_helper_appends_not_overwrites(tmp_path, monkeypatch):
    """Two calls produce two lines, not one overwritten."""


def test_t1d_helper_creates_parent_dir_if_missing(tmp_path, monkeypatch):
    """Helper creates integration/ if absent; matches F5-tolerance posture."""


def test_t2a_redispatch_emits_event(monkeypatch):
    """When dispatch_triager returns RE_DISPATCH, orchestrator emits a phase_redispatch event with from_phase, to_phase."""
    # Mock dispatch_triager + _record_orchestrator_event; assert call args


def test_t2b_b15_cap_emits_event():
    """Second re-dispatch on the same phase triggers redispatch_cap_exceeded event with phase, count fields."""


def test_t3_lifecycle_archives_events_jsonl():
    """_ARTIFACT_RELPATHS includes integration/orchestrator-events.jsonl; close_slice copies it to sweep-results."""
    # Set up a fake integration/ with an events.jsonl, run close_slice, assert copied artifact exists
```

**Implementation Phase 3 ships** (in one commit):

```python
# scripts/slice_orchestrator/core.py — add near top, after imports
import json
from datetime import datetime, timezone

_ORCHESTRATOR_EVENTS_REL = ".claude/current-slice/integration/orchestrator-events.jsonl"

def _record_orchestrator_event(slice_id, event_type, **fields):
    """Append one JSONL event to the per-slice orchestrator events file.

    Layered on slice-artifact-preservation: file is in _ARTIFACT_RELPATHS,
    so it survives DC-5 wipe at close. F5-tolerant — creates parent dir
    if missing. Schema: {ts, slice_id, event_type, ...caller-supplied fields}.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "slice_id": slice_id,
        "event_type": event_type,
        **fields,
    }
    path = Path(_ORCHESTRATOR_EVENTS_REL)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")
```

Wire into existing call sites in `core.py` (re-dispatch handling, B15 cap-trip branch) and `dispatch.py` (TimeoutExpired catch). Wire INV-009 cost/token threshold breach emission alongside the existing breach-detection logic. Each call site adds ONE line: `_record_orchestrator_event(slice_id, "<event_type>", <relevant fields>)`.

---

### Task 2: `_ARTIFACT_RELPATHS` extension for archival

**Files:**
- Modify: `scripts/slice_orchestrator/lifecycle.py`
- Test: `tests/unit/test_orchestrator_events_capture.py` (Task 1's `test_t3_lifecycle_archives_events_jsonl`)

**Tests Phase 2 writes:** see Task 1's test file (`test_t3_lifecycle_archives_events_jsonl`).

**Implementation Phase 3 ships:** add `"integration/orchestrator-events.jsonl"` to the existing `_ARTIFACT_RELPATHS` tuple in `lifecycle.py`. Verify the existing F5-tolerance posture in `_copy_artifacts_to_sweep_results` already handles "events file does not exist" (a slice with zero orchestrator events) without raising. No new logic; one tuple entry.

---

### Task 3: Phase-4 integrator prompt amendment

**Files:**
- Modify: `.claude/agents/phase-4-integrator.md`
- Test: none (prompt edit is verifiable by reading the file; agent-prompt assertions tend to be brittle)

**Tests Phase 2 writes:** none for this task (a prompt-content assertion test would be brittle and add maintenance cost without proportional value; the structural test that sweep-notes.md is preserved already exists post-WS4).

**Implementation Phase 3 ships:** amend `.claude/agents/phase-4-integrator.md`'s sweep-notes.md template guidance to add a new optional subsection. Add prose under the existing sweep-notes.md template description (not as a new agent instruction, but as a new template element) along these lines:

```markdown
## Learnings observed (optional)

Brief free-form notes on anything that surprised you during the audit:
novel patterns, cross-phase signals worth naming, instances where a
contract held under unexpected pressure, or instances where it bent.
Skip the section entirely if nothing notable came up — empty is the
honest default. The operator promotes durable patterns to
`docs/lessons.md` via the 3×-rule manually; this section's job is
to make those candidates legible at slice close.
```

The amendment is additive, doesn't change any existing instruction, and doesn't expand the integrator's write surface (sweep-notes.md is already a Write target).

---

## Closes-when

- [ ] Full pytest passes (`uv run pytest -q`); 7 new tests pass; no regressions in pre-existing 924-passing baseline.
- [ ] `_record_orchestrator_event` helper exists in `core.py` and is wired at all v1 emission sites (re-dispatch, B15 cap, cost-threshold, token-threshold, agent-timeout).
- [ ] `lifecycle.py:_ARTIFACT_RELPATHS` includes `integration/orchestrator-events.jsonl`.
- [ ] `.claude/agents/phase-4-integrator.md` includes the `## Learnings observed (optional)` template guidance.
- [ ] An end-to-end smoke run of any small slice produces a populated `orchestrator-events.jsonl` archived under `.claude/sweep-results/<slug>/artifacts/` (validate by inspection at the slice's close — this is a closes-when-evidence step, not a test).
- [ ] Architecture validator passes (still expects 8 known cairn-substrate-and-fastmcp INV failures — those resolve at substrate Slice 2, not here).

---

## Out-of-band notes for the next session

- This slice closes BEFORE substrate Slice 2 opens. Slice 2's first-use of the FastMCP adapter then exercises the new learning-capture surfaces, providing first concrete in-flight evaluation.
- The 8 pre-existing test failures (validate_architecture complaining about `cairn-substrate-and-fastmcp` firm without ARCHITECTURE.md INV) are out-of-scope here; they resolve when Slice 2 lands the ADR's INV declaration. Do NOT touch ARCHITECTURE.md in this slice.
- L-010's WS1 post-close-fixup pattern (Phase-4 source-rewrite) is NOT in this slice's scope to fix — only to OBSERVE. The orchestrator-events surface gives L-010-class incidents a permanent record going forward; remediation (if pattern recurs) is a different slice per L-010's deferred-mechanism note.
