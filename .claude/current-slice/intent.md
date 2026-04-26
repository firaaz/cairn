---
slice: cost-discipline/lever-1-tier-retune
date: 2026-04-26
phase: 1-intent
invariants-touched: []
adrs-referenced: [cost-per-slice-budget, phase-lock-and-role-declaration, orchestrator-observability]
adrs-created: []
envelope:
  - "scripts/slice_orchestrator/core.py"
  - "tests/unit/test_slice_orchestrator_model_config.py"
  - "docs/operational-reference.md"
  - ".claude/features/cost-discipline.yaml"
  - ".claude/current-slice/intent.md"
  - ".claude/current-slice/validation/approach.md"
  - ".claude/current-slice/implementation/notes.md"
  - ".claude/current-slice/integration/sweep-notes.md"
  - ".claude/current-slice/handoff-phase-1.md"
  - ".claude/current-slice/handoff-phase-2.md"
  - ".claude/current-slice/handoff-phase-3.md"
  - ".claude/current-slice/handoff-phase-4.md"
out-of-scope:
  - "Phase semantics, gate logic, artifact contracts, role assignments (per brief)"
  - "Agent prompt bodies — `.claude/agents/phase-*.md` are not touched (no instruction-content drift; only the orchestrator-side tier defaults change)"
  - "Dispatch wiring rewrite — `--model` / `--effort` already plumbed through `dispatch.py:_dispatch_once` via `_resolve_model_config`; this slice only edits the default-tier dict + tests + docs"
  - "Env-var override mechanism — `CAIRN_MODEL_<ROLE>` / `CAIRN_EFFORT_<ROLE>` already exists and ships unchanged (verified via test that override still wins over the new defaults)"
  - "INV-009 threshold setting — cost-per-slice baseline accumulation continues independently; this slice changes one input to that baseline (the default tier) but does not touch `INV_009_COST_THRESHOLD_USD` / `INV_009_TOKEN_THRESHOLD`"
  - "Pricing table additions — if `claude-opus-4-7` low-effort cost rows need re-validation, that is a separate Track-0 concern; existing `PRICING_TABLE_2026_04_24` row for opus is reused"
  - "Per-slice model overrides (in slice.yaml) — premature; env-var family is the v1 override surface"
  - "New ADR — knob retune backed by single-incident empirical signal; ADR introduction deferred until a second tier-retune incident or a structural change to the model-config surface"
  - "Test-file relocation to `tests/unit/scripts/slice_orchestrator/` — brief mentioned that path, but project convention is flat `tests/unit/test_*.py` and an existing `test_slice_orchestrator_model_config.py` is the natural extension point; relocation is a separate housekeeping concern"
---

### What and Why

**What.** Retune the per-phase model + effort defaults that the orchestrator passes to `claude -p` via `--model` / `--effort`. Two changes to `AGENT_MODEL_CONFIG` in `scripts/slice_orchestrator/core.py`:

| Role | Old default | New default |
|---|---|---|
| `phase-3-implementer` | `claude-sonnet-4-6` / `medium` | `claude-sonnet-4-6` / **`high`** |
| `phase-4-integrator` | `claude-sonnet-4-6` / `low` | **`claude-opus-4-7`** / `low` |

Phases 1, 2, and `issue-triager` defaults are unchanged. The `_resolve_model_config(role)` helper, the `--model` / `--effort` splice in `_dispatch_once`, and the `CAIRN_MODEL_<ROLE>` / `CAIRN_EFFORT_<ROLE>` env-var override surface all remain mechanically identical — the brief's "wire per-phase model + extended-thinking selection" wording reflects intent, but the wiring shipped under `cost-discipline/lever-1-per-phase-model`; this slice retunes the inputs that wiring already consumes.

**Why.** Empirical signal from the failed slice `compression/learnings-capture` (artifacts under `.claude/completed-slices/compression-learnings-capture-failed/`): three consecutive Phase 3 invocations under the prior `sonnet-4-6 / medium` default declared handoff complete with zero source-file changes against three explicit unresolved closes-when items, while Phase 4 under `sonnet-4-6 / low` correctly caught the gap and escalated. The two retune directions follow:

- **P3 effort `medium` → `high`.** Cluster fan-out worker reported OK without RED-test gating — symptomatic of underweighted reasoning at the implementer step. Bumping effort (not model) preserves the Sonnet cost advantage that motivated Lever 1's split while restoring reasoning depth where the failure mode was observed. Per-phase configurability remains intact; operators can revert via `CAIRN_EFFORT_PHASE_3_IMPLEMENTER=medium`.
- **P4 model `sonnet-4-6` → `opus-4-7` (effort stays `low`).** The integrator phase is the audit boundary — its judgment quality determines whether bad implementer output reaches close. Per the brief, the operator's stance is that audit quality should ride Opus while accepting `low` effort to keep the cost delta narrow. Operators can revert via `CAIRN_MODEL_PHASE_4_INTEGRATOR=claude-sonnet-4-6`.

### Boundary

In scope: the two-row default-dict edit; one entry-point test in `tests/unit/test_slice_orchestrator_model_config.py` extending the existing default-resolution coverage; corresponding cell updates in the `docs/operational-reference.md` env-var table. Out of scope (full list in frontmatter): agent prompt bodies, dispatch wiring rewrite, env-var mechanism changes, INV-009 thresholds, new pricing-table rows, per-slice overrides, new ADR, test-file relocation.

### Specification Detail

**Edit 1 — `scripts/slice_orchestrator/core.py:41-47`.** Replace two value-pairs in the `AGENT_MODEL_CONFIG` literal:

```python
AGENT_MODEL_CONFIG: dict[str, dict[str, str]] = {
    "phase-1-writer":      {"model": "claude-opus-4-7",   "effort": "high"},   # unchanged
    "phase-2-skeptic":     {"model": "claude-opus-4-7",   "effort": "high"},   # unchanged
    "phase-3-implementer": {"model": "claude-sonnet-4-6", "effort": "high"},   # was medium
    "phase-4-integrator":  {"model": "claude-opus-4-7",   "effort": "low"},    # was sonnet
    "issue-triager":       {"model": "claude-opus-4-7",   "effort": "medium"}, # unchanged
}
```

No other change to `core.py`. `_resolve_model_config` is **not** edited — its body, env-var precedence, and unknown-role fallback (`claude-opus-4-7` / `high`) remain byte-identical.

**Edit 2 — `tests/unit/test_slice_orchestrator_model_config.py`.** Update the default-resolution assertions for `phase-3-implementer` (effort → `"high"`) and `phase-4-integrator` (model → `"claude-opus-4-7"`). Override-precedence tests (env var beats default) MUST still pass against the new defaults — exercise both `phase-3-implementer` and `phase-4-integrator` override cases explicitly so future tier flips cannot silently bypass the override surface.

**Edit 3 — `docs/operational-reference.md`.** Update four cells in the env-var table at lines 410-413: change the "Default" column for `CAIRN_EFFORT_PHASE_3_IMPLEMENTER` to `high`, the "Default" for `CAIRN_MODEL_PHASE_4_INTEGRATOR` to `claude-opus-4-7`. Append a one-sentence rationale parenthetical to the new defaults pointing at this slice for empirical context. The existing Lever 1 narrative ("Sonnet is ~5× cheaper than Opus for implementation work") remains accurate for `phase-3-implementer` model and stays unedited.

**Invariant posture.**

- `INV-003` (`phase-lock-and-role-declaration`): role names, ordering, and gates unchanged. Only orchestrator-owned tier defaults change. **Preserved by construction.**
- `INV-008` (`slice-close-contract` / `slice-artifact-preservation`): no `_git` site touched, no commit-source change, no wipe change. **Preserved by construction.**
- `INV-009` (`cost-per-slice-budget`, provisional/advisory): one input to the per-slice baseline changes; the invariant *shape* and the threshold-setting D2 procedure are unchanged. The slice's own close-time `<slug>-result.json` will exhibit the new cost mix — this is the intended next data point in the baseline accumulation, not an invariant breach.

**Stdlib-only / no new deps.** All edits are existing-file mutations of literals or markdown table cells. No imports added, no third-party deps introduced.

**Public-interface scrutiny only (P1 modification-slice rule).** Confirmed by inspection of public surfaces only: `AGENT_MODEL_CONFIG` is module-level on `core.py`; `_resolve_model_config` is exported via `__init__.py` re-export per `cost-discipline/lever-2-orchestrator-split` package contract; `--model` / `--effort` splice is in `dispatch.py:_dispatch_once`; env-var family is documented at `docs/operational-reference.md:400-415`. No internal-helper reads were performed.

### Verification

**Phase 2 RED-test set (extends `tests/unit/test_slice_orchestrator_model_config.py`).**

- `test_default_phase_3_implementer_resolves_sonnet_high` — `_resolve_model_config("phase-3-implementer")` returns `("claude-sonnet-4-6", "high")` with empty environment.
- `test_default_phase_4_integrator_resolves_opus_low` — `_resolve_model_config("phase-4-integrator")` returns `("claude-opus-4-7", "low")` with empty environment.
- `test_default_unchanged_phase_1_writer` — `("claude-opus-4-7", "high")` (regression guard against accidental drift on unchanged rows).
- `test_default_unchanged_phase_2_skeptic` — `("claude-opus-4-7", "high")` (regression guard).
- `test_default_unchanged_issue_triager` — `("claude-opus-4-7", "medium")` (regression guard).
- `test_env_override_still_wins_phase_3_effort` — `CAIRN_EFFORT_PHASE_3_IMPLEMENTER=medium` resolves effort to `"medium"` despite new `"high"` default.
- `test_env_override_still_wins_phase_4_model` — `CAIRN_MODEL_PHASE_4_INTEGRATOR=claude-sonnet-4-6` resolves model to `"claude-sonnet-4-6"` despite new opus default.
- `test_unknown_role_falls_back_to_opus_high` — unchanged fallback contract for unknown roles.

**Phase 4 closure evidence (closes-when, not test).**

- `uv run pytest -q` passes; the extended model-config tests pass; no regression in the pre-existing passing baseline.
- `AGENT_MODEL_CONFIG` literal in `scripts/slice_orchestrator/core.py` matches the table above.
- `docs/operational-reference.md` env-var table reflects the new defaults; no stale `medium` / `claude-sonnet-4-6` entries on rows P3-effort / P4-model.
- `_resolve_model_config` body byte-identical to current state (diff confirms only literal-dict cells changed in `core.py`).
- Architecture validator passes (still expects the known `cairn-substrate-and-fastmcp` INV failures; do NOT touch ARCHITECTURE.md).
- Slice's own `<slug>-result.json` shows `model_by_phase["phase-3-implementer"] == "claude-sonnet-4-6"` and `model_by_phase["phase-4-integrator"] == "claude-opus-4-7"` — i.e., the slice exercises its own retune at close (live dogfood of the new defaults).
