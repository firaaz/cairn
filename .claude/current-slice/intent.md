---
slice_id: cost-discipline/lever-1-per-phase-model
name: "Lever 1 — per-phase model configuration"
phase: 1
status: draft
preconditions_met:
  - "cost-discipline/track-0-telemetry: complete (slice.yaml status=complete, phase 4)"
design_source: "docs/plans/2026-04-23-cost-discipline-design.md §Lever 1 :100-150"
invariants_touched:
  - INV-003  # dispatch plumbing only; no agent-prompt or role-definition changes
  - INV-009  # model_by_phase attribution stays honest under env-var overrides
invariants_preserved:
  - INV-004  # status output bounded — no new /status lines
  - INV-006  # feature file (.claude/features/cost-discipline.yaml) already exists
  - INV-008  # close_slice untouched
---

## What / Why / Boundary

**What.** Land per-phase model configuration in `scripts/slice_orchestrator.py`: a module-level
`AGENT_MODEL_CONFIG` dict, a `_resolve_model_config(role)` helper with env-var override
precedence, dispatch-site splicing of `--model`/`--effort` into the `claude -p` invocation, and
`model_by_phase[phase]` recording the resolved model so Track 0 cost attribution stays honest
under overrides. Accompanied by new unit tests and `docs/operational-reference.md` docs.

**Why.** Phases 3/4 (implementer, integrator) are mechanical enough to run on Sonnet (~5x cheaper
than Opus) with no quality regression — flagged in operator memory `project_per_phase_model_and_thinking.md`
(2026-04-23) but never acted on. Track 0 now makes the cost impact measurable; this lever
captures the reduction. Target: >=30% cheaper on phases 3+4 vs pre-change parity env-var run.

**Boundary.** No agent-prompt edits (content stays model-agnostic). No per-slice model overrides
(premature). No `--max-budget-usd` plumbing (design OQ#3, deferred). No new ADR (knob, not
structural change). No schema_version bump. No close_slice or feature-file changes.

---

## Specification

### 1. `AGENT_MODEL_CONFIG` — module-level constant

Location: `scripts/slice_orchestrator.py`, near top with other module constants.

```python
# Per-phase model defaults.
# Phases 1/2 are synthesis-heavy -> Opus/high.
# Phases 3/4 are mechanical -> Sonnet/medium+low.
# Per operator memory project_per_phase_model_and_thinking.md (2026-04-23).
# --effort values from `claude -p --help`: low | medium | high | xhigh | max
AGENT_MODEL_CONFIG: dict[str, dict[str, str]] = {
    "phase-1-writer":       {"model": "claude-opus-4-7",   "effort": "high"},
    "phase-2-skeptic":      {"model": "claude-opus-4-7",   "effort": "high"},
    "phase-3-implementer":  {"model": "claude-sonnet-4-6", "effort": "medium"},
    "phase-4-integrator":   {"model": "claude-sonnet-4-6", "effort": "low"},
    "issue-triager":        {"model": "claude-opus-4-7",   "effort": "medium"},
}
```

### 2. `_resolve_model_config(role)` — helper function

```python
def _resolve_model_config(role: str) -> tuple[str, str | None]:
    """Return (model, effort) for role, with env-var override precedence.

    Env-var names: CAIRN_MODEL_<ROLE_UPPER_UNDERSCORE> and
                   CAIRN_EFFORT_<ROLE_UPPER_UNDERSCORE>.
    Example: role "phase-3-implementer" -> CAIRN_MODEL_PHASE_3_IMPLEMENTER.

    Unknown role falls back to {"model": "claude-opus-4-7", "effort": "high"}.
    """
    key = role.upper().replace("-", "_")
    default = AGENT_MODEL_CONFIG.get(role, {"model": "claude-opus-4-7", "effort": "high"})
    model = os.environ.get(f"CAIRN_MODEL_{key}") or default["model"]
    effort = os.environ.get(f"CAIRN_EFFORT_{key}") or default["effort"]
    return model, effort
```

- Pure function; no I/O. Env-var wins if non-empty; dict default wins otherwise.
- Returns `(model, effort)` — both are strings when a config entry exists; effort is the
  dict default ("high") for an unknown role fallback.

### 3. Dispatch plumbing — `scripts/slice_orchestrator.py:984-992`

Current cmd list (approximately):
```python
cmd = ["claude", "-p", "--agent", role, "--permission-mode", perm_mode, *inputs]
```

After this slice, splice `--model` and `--effort` immediately after `--agent <role>`:
```python
model, effort = _resolve_model_config(role)
cmd = ["claude", "-p", "--agent", role,
       "--model", model, "--effort", effort,
       "--permission-mode", perm_mode, *inputs]
```

- `subprocess.Popen`/`run` is called with a list (not shell=True); no shell-escaping surprises.
- Resolved model is recorded in `model_by_phase[phase]` (Track 0 field) **before** the
  subprocess call, so cost attribution is correct even if the subprocess raises.

### 4. `model_by_phase[phase]` recording

Call `_record_phase_cost` (or equivalent Track 0 state update) with the resolved model at the
same dispatch site so `model_by_phase` always reflects the actual model sent to `claude -p`,
not a stale default. Idempotency contract unchanged: overwrites on retry, does not accumulate.

### 5. New test file: `tests/unit/test_slice_orchestrator_model_config.py`

Required test cases (all stdlib unittest or pytest-compatible, no third-party deps):

| ID | Description |
|----|-------------|
| T1 | Default resolution: `_resolve_model_config("phase-1-writer")` returns `("claude-opus-4-7", "high")` |
| T2 | Default resolution: `_resolve_model_config("phase-3-implementer")` returns `("claude-sonnet-4-6", "medium")` |
| T3 | Default resolution: `_resolve_model_config("phase-4-integrator")` returns `("claude-sonnet-4-6", "low")` |
| T4 | Default resolution: `_resolve_model_config("issue-triager")` returns `("claude-opus-4-7", "medium")` |
| T5 | `CAIRN_MODEL_PHASE_3_IMPLEMENTER=claude-opus-4-7` overrides model; effort stays `"medium"` |
| T6 | `CAIRN_EFFORT_PHASE_4_INTEGRATOR=high` overrides effort independently; model stays `"claude-sonnet-4-6"` |
| T7 | Both `CAIRN_MODEL_*` and `CAIRN_EFFORT_*` set: both override independently |
| T8 | Unknown role `"phase-99-phantom"` falls back to `("claude-opus-4-7", "high")` |
| T9 | Dispatch cmd list contains `"--model"` and `"--effort"` as **separate** entries (not shell-escaped, not joined) |
| T10 | `CAIRN_MODEL_PHASE_3_IMPLEMENTER` empty string does NOT override (falls back to dict default) |

Env-var tests must set/unset vars within the test (monkeypatch or `os.environ` + teardown) to
avoid test-order coupling.

### 6. `docs/operational-reference.md` — env-var documentation

Add a subsection under the existing `CAIRN_<KNOB>` env-var pattern section:

```
### Per-phase model and effort overrides

CAIRN_MODEL_<ROLE>   — override the model for a named role. Example:
                        CAIRN_MODEL_PHASE_3_IMPLEMENTER=claude-opus-4-7
CAIRN_EFFORT_<ROLE>  — override the effort level for a named role. Example:
                        CAIRN_EFFORT_PHASE_4_INTEGRATOR=medium

Role name normalization: replace hyphens with underscores and uppercase.
Full role name list:
  PHASE_1_WRITER, PHASE_2_SKEPTIC, PHASE_3_IMPLEMENTER,
  PHASE_4_INTEGRATOR, ISSUE_TRIAGER

Default table (AGENT_MODEL_CONFIG):
  phase-1-writer:      claude-opus-4-7   / high
  phase-2-skeptic:     claude-opus-4-7   / high
  phase-3-implementer: claude-sonnet-4-6 / medium
  phase-4-integrator:  claude-sonnet-4-6 / low
  issue-triager:       claude-opus-4-7   / medium

Unknown role falls back to claude-opus-4-7 / high.
```

---

## Verification

**Phase 2 acceptance gates (skeptic):**

1. `uv run pytest tests/unit/test_slice_orchestrator_model_config.py` — all 10 tests pass.
2. `uv run pytest tests/unit/` — full suite green; no regressions.
3. `grep -n "AGENT_MODEL_CONFIG\|_resolve_model_config\|--model.*effort\|--effort" scripts/slice_orchestrator.py` — all three symbols present.
4. `model_by_phase` is populated with the resolved model string in the dispatch site code path.
5. `docs/operational-reference.md` contains the CAIRN_MODEL_ / CAIRN_EFFORT_ family with the full role list.

**Cross-slice validation (post-close, sweep-notes):**

Run two comparable slices:
- Slice A: default config (Sonnet on phases 3/4).
- Slice B: `CAIRN_MODEL_PHASE_3_IMPLEMENTER=claude-opus-4-7 CAIRN_MODEL_PHASE_4_INTEGRATOR=claude-opus-4-7` (pre-change parity).

Compare `cost_by_phase_usd` from the two `<slug>-result.json` files. Target: Slice A >=30% cheaper
on phases 3+4 combined. Record outcome in sweep-notes at close.
