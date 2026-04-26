---
slice: compression/learnings-capture
date: 2026-04-26
phase: 1-intent
retry-of: compression/learnings-capture (failed; archived at .claude/completed-slices/compression-learnings-capture-failed/, archive commit 4fc3157)
invariants-touched: []
adrs-referenced: [slice-artifact-preservation, phase-lock-and-role-declaration]
adrs-created: []
envelope:
  - "scripts/slice_orchestrator/lifecycle.py"
  - "scripts/slice_orchestrator/core.py"
  - "scripts/slice_orchestrator/dispatch.py"
  - ".claude/agents/phase-4-integrator.md"
  - "tests/unit/test_orchestrator_events_capture.py"
  - "tests/unit/test_phase_4_integrator_prompt.py"
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
  - "Post-close commit detection (L-010 WS1 fixup-after-close pattern) — orchestrator can't observe inline; separate slice if needed"
  - "Empty-handoff-commit detection (L-008 follow-up) — different fix, different slice"
  - ".claude/learning.md V5 cap revision — stays minimal cross-session staging by design"
  - "Test for orchestrator events that requires actual phase-agent dispatch (use unit-level mocks of the dispatch boundary)"
  - "New ADR — this slice is mechanism addition only"
  - "Any change to phase-1/2/3-* agent prompts (Phase-4 only)"
  - "Source-rewrite of any orchestrator surface area not listed in the v1 emission-site table (e.g. resume.py, telemetry.py, git.py)"
---

### What and Why

The compressed slice protocol structurally lost the per-slice learning-capture surface that the legacy single-CC-session model captured mid-flight. L-010 (the WS4/WS1 paired-instance Phase-4 role-lock differential) only existed because of post-close forensic exploration — there was no in-flight place to record it. This slice restores capture by adding two complementary surfaces, both archived by the existing `slice-artifact-preservation` pipeline so the operator-driven 3×-rule promotion to `docs/lessons.md` reads from a permanent record:

1. **Phase-4 integrator** emits an optional `## Learnings observed` subsection inside `sweep-notes.md` — free-form prose, judgment-based, empty by default ("only fill when something surprised you").
2. **Orchestrator** emits mechanical structured events at `.claude/current-slice/integration/orchestrator-events.jsonl` (phase_redispatch, redispatch_cap_exceeded, cost_threshold_breach, token_threshold_breach, agent_timeout).

Both ride the existing `_ARTIFACT_RELPATHS` archival pipeline (`sweep-notes.md` already listed; events-jsonl added) and survive DC-5 wipe into `.claude/sweep-results/<slug>/artifacts/`.

This is a **retry** of the prior `compression/learnings-capture` slice (failed at B15 cap with three closes-when criteria unmet — agent_timeout, cost/token threshold breach, phase-4-integrator.md amendment). The prior slice's root cause was structural, not capability-shaped: a Phase-3 cluster (the prompt-amendment worker) ran without a RED-test progress signal because the prior intent excluded prompt-content tests as "brittle." The cluster observed GREEN test status (vacuous — no test bound the work) and reported OK. The retry closes that gap: **every Phase-3 cluster carries a RED test** — including the prompt-amendment cluster, gated by a string-presence assertion against the agent file (a brittleness trade-off explicitly accepted as the price of progress signal).

### Boundary

Out of scope: per-phase 1/2/3 learning surfaces; automatic 3×-rule promotion; post-close commit detection (L-010 WS1); empty-handoff-commit detection (L-008); `.claude/learning.md` V5 revision; any new ADR; any phase-1/2/3 agent-prompt change (Phase-4 only); source-rewrite of orchestrator modules outside the v1 emission-site table. **L-013 guard**: this intent's What/Why cites the prior failed slice for context only — the retry's envelope is the same surface area, not adjacent surface area; do not let the citation broaden scope.

### Specification Detail

**Helper contract (`scripts/slice_orchestrator/core.py`).** New function `_record_orchestrator_event(slice_id: str, event_type: str, **fields) -> None`. Appends one JSON-encoded line to `.claude/current-slice/integration/orchestrator-events.jsonl`. Schema per record:

```json
{"ts": "<ISO8601 with explicit UTC offset>", "slice_id": "<str>", "event_type": "<str>", ...caller-supplied fields}
```

- `ts`: `datetime.datetime.now(datetime.timezone.utc).isoformat()` — parseable by `datetime.fromisoformat`; ends `+00:00`.
- File mode: append (`"a"`); never overwrite. Each call writes exactly one line ending in `\n`.
- Parent-directory creation: `path.parent.mkdir(parents=True, exist_ok=True)` — F5-tolerant of missing `integration/`.
- No `_git` calls; helper is commit-site-free (DC-4 preserved by construction).

**Seed material (`stash@{0}`).** A partial Phase-3 orphan from `cost-discipline/lever-1-tier-retune` (carved out as L-013 scope drift; see commit `c683a9d` post-mortem) contains: the `_record_orchestrator_event` helper body in `core.py`, `phase_redispatch` + `redispatch_cap_exceeded` event emissions in `lifecycle.py`, and `"integration/orchestrator-events.jsonl"` added to `_ARTIFACT_RELPATHS`. **Phase 3 may use the stash as a seed but must verify each carved hunk against this intent's spec — the stash was scope-drift, not vetted spec.** Remaining wiring NOT in stash, which Phase 3 must produce: `agent_timeout` emission in `dispatch.py` (TimeoutExpired catch site), `cost_threshold_breach` + `token_threshold_breach` emissions in `core.py` (INV-009 detection sites), and the `phase-4-integrator.md` prompt amendment.

**Emission sites (v1 set).** Each call site adds exactly one line invoking `_record_orchestrator_event(...)` with the canonical event_type token and relevant fields:

| event_type | Site (file) | Required extra fields |
|---|---|---|
| `phase_redispatch` | `lifecycle.py` re-dispatch handler (RE_DISPATCH branch in `run_phase_loop`) | `from_phase: int`, `to_phase: int` |
| `redispatch_cap_exceeded` | `lifecycle.py` B15 second-redispatch-on-same-phase trip (`run_phase_loop`) | `phase: int`, `count: int` |
| `cost_threshold_breach` | `core.py` INV-009 cost threshold breach detection site | `threshold_usd: float`, `observed_usd: float` |
| `token_threshold_breach` | `core.py` INV-009 token threshold breach detection site | `threshold_tokens: int`, `observed_tokens: int` |
| `agent_timeout` | `dispatch.py` `subprocess.TimeoutExpired` catch site | `phase: int`, `timeout_seconds: int` |

(Note: `phase_redispatch` and `redispatch_cap_exceeded` are emitted from `lifecycle.py` — that's where `run_phase_loop` lives in the post-Lever-2 hexagonal split. The stash carve confirms this. Cost/token-threshold sites live in `core.py` per the slice's INV-009 surface; `agent_timeout` lives in `dispatch.py` where subprocess ownership is.)

**Archival wiring (`scripts/slice_orchestrator/lifecycle.py`).** The existing `_ARTIFACT_RELPATHS` tuple gains the single entry `"integration/orchestrator-events.jsonl"` (immediately after the existing `"integration/sweep-notes.md"`). No other change to `_ARTIFACT_RELPATHS`. The existing `_copy_artifacts_to_sweep_results` helper's F5-tolerance (per ADR `slice-artifact-preservation` D6) handles the zero-events case (events file absent) silently — a slice that emitted no orchestrator events does NOT fail the close.

**Phase-4 integrator prompt amendment (`.claude/agents/phase-4-integrator.md`).** Additive amendment to the integrator's `sweep-notes.md` template guidance: introduce an `## Learnings observed (optional)` subsection framed as free-form notes on anything that surprised the auditor (novel patterns, cross-phase signals, contracts holding under pressure, contracts bending). Empty section is the honest default; the operator promotes patterns to `docs/lessons.md` via the manual 3×-rule. The amendment does not expand the integrator's write surface (`sweep-notes.md` is already a Write target) and does not change any existing instruction.

**Invariant posture.** No invariant amended. INV-008 contract (slice-close-contract / slice-artifact-preservation): the new events-jsonl is a passive consumer of the already-committed pre-wipe copy step — no change to DC-3 idempotency, DC-4 sole-commit-source, DC-5 wipe, DC-7 slug-keyed observability. INV-003 contract (phase-lock-and-role-declaration): only the Phase-4 (Auditor) prompt is touched; phases 1–3 unchanged; role declarations unchanged; no rename/reorder. `adrs-referenced` lists both ADRs because their contracts constrain the slice's edits even though neither is rewritten.

**Stdlib-only.** Implementation uses `json` (JSONL), `datetime.timezone.utc` (ISO8601), `pathlib.Path` (already imported in `core.py`). No new third-party dependency. Phase-4 integrator amendment is markdown only.

**Discipline notes (consume, do not re-derive).**
- **L-011** — every phase agent that touches envelope source MUST `git commit` its content before returning OK; an `--allow-empty` boundary commit from `commit_phase_handoff` is not equivalent. After every Phase-N handoff, `git log -p <handoff>~..<handoff>` plus `git status` is the cheapest catch.
- **L-012** — no tier flip is in play; this slice runs on existing per-phase defaults. Dogfood verification at close (smoke-run any small slice and inspect `orchestrator-events.jsonl` archived under `.claude/sweep-results/<slug>/artifacts/`) remains a closes-when item.
- **L-013** — cited prior-slice surface area is the same as this retry's envelope; out-of-envelope source changes from Phase 3 are RAISE_ISSUE by default. After every Phase-3 redispatch, `git status` against the envelope must be audited.

### Verification

**Cluster-RED-test discipline (the retry's distinguishing constraint).** Every Phase-3 cluster has at least one RED test pinned to it; GREEN test status alone is not a progress signal. Two test files cover the work:

`tests/unit/test_orchestrator_events_capture.py` (~7 tests, helper + orchestrator-side emission + archival):

- `test_t1a_helper_appends_jsonl_line` — one call writes one JSON-decodable line containing `slice_id`, `event_type`, supplied fields, and a `ts` key.
- `test_t1b_helper_includes_iso8601_utc_timestamp` — `ts` ends `+00:00` (or `Z`) and parses via `datetime.fromisoformat`.
- `test_t1c_helper_appends_not_overwrites` — two successive calls produce two lines, not one overwritten.
- `test_t1d_helper_creates_parent_dir_if_missing` — helper creates `.claude/current-slice/integration/` when absent (F5-tolerance).
- `test_t2a_redispatch_emits_event` — `RE_DISPATCH` triager outcome causes `phase_redispatch` emission with `from_phase`, `to_phase` fields (mocking the dispatch boundary, not actual agent dispatch).
- `test_t2b_b15_cap_emits_event` — second redispatch on the same phase emits `redispatch_cap_exceeded` with `phase`, `count`.
- `test_t3_lifecycle_archives_events_jsonl` — `_ARTIFACT_RELPATHS` includes `integration/orchestrator-events.jsonl`; `close_slice` copies a populated events file into `.claude/sweep-results/<slug>/artifacts/`.

`tests/unit/test_phase_4_integrator_prompt.py` (NEW — the retry's gap-closing addition; pins the prompt-amendment cluster):

- `test_t4a_phase4_integrator_prompt_has_learnings_section` — `.claude/agents/phase-4-integrator.md` contains the literal substring `## Learnings observed` (string-presence assertion; brittleness explicitly accepted as the price of binding the prompt-amendment cluster to a RED test).
- `test_t4b_phase4_integrator_prompt_marks_learnings_optional` — same file additionally contains the literal token `optional` on the same line or within the immediate `## Learnings observed …` heading line (defends against the section being added but framed as required, which would silently change Phase-4 contract).

Optional additional clusters (Phase 2's discretion, NOT required by this intent — listed so Phase 2 doesn't need to invent them):

- A `test_t2c_cost_threshold_emits_event` and `test_t2d_token_threshold_emits_event` are encouraged if Phase 2 finds a clean unit-mockable seam at the INV-009 detection sites in `core.py`. If not, the closes-when call-site grep (below) is the progress signal for those two emissions.
- A `test_t2e_agent_timeout_emits_event` is encouraged if `dispatch.py`'s TimeoutExpired site can be exercised via subprocess mock; otherwise covered by closes-when grep.

**Phase 4 closure evidence (closes-when, structural — each is a non-test progress signal):**

- `uv run pytest -q` passes; both new test files pass; no regression in the pre-existing passing baseline.
- `_record_orchestrator_event` exists in `core.py` and is wired at all five v1 emission sites (`grep -n _record_orchestrator_event scripts/slice_orchestrator/{core,lifecycle,dispatch}.py` returns >=6 lines: 1 def + 5 call sites).
- `_ARTIFACT_RELPATHS` in `lifecycle.py` contains the new entry `"integration/orchestrator-events.jsonl"`.
- `.claude/agents/phase-4-integrator.md` contains the `## Learnings observed (optional)` template guidance (also bound by RED test t4a/t4b).
- End-to-end smoke: a small dogfood slice produces a populated `orchestrator-events.jsonl` archived under `.claude/sweep-results/<slug>/artifacts/` — verified by inspection at slice close.
- Architecture validator passes (still expects 8 known `cairn-substrate-and-fastmcp` INV failures; those resolve at substrate Slice 2, not here — do NOT touch ARCHITECTURE.md).
- Phase-4 audit explicitly verifies `git status` against the envelope is clean at every Phase-3 handoff (L-011/L-013 guard).
