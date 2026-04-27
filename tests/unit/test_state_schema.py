"""Phase 2 RED — state-dict schema v1.0 (Observability D4).

Spec: intent.md §State-dict schema v1.0 + docs/adr/orchestrator-observability.md.
Firmly committed fields: schema_version="1.0", slice_id, started_at, ended_at,
status, exit_code, current_phase, phases_completed, phase_timings,
retries_by_phase, cluster_dispatches, degradation_reason, observability_errors,
final_commit, summary. Additive-safe: worktree_path, orchestrator_pid.
Status enum non-terminal {IN_PROGRESS, DEGRADED}, terminal
{OK, FAILED, ABORTED, ESCALATED, SIGNALED}.

Expected at Phase 2: every test FAILS with AttributeError — the schema
helpers, the module-level state dict, and the status enum do not yet exist.
"""

from __future__ import annotations


REQUIRED_FIELDS = {
    "schema_version",
    "slice_id",
    "started_at",
    "ended_at",
    "status",
    "exit_code",
    "current_phase",
    "phases_completed",
    "phase_timings",
    "retries_by_phase",
    "cluster_dispatches",
    "degradation_reason",
    "observability_errors",
    "final_commit",
    "summary",
}

ADDITIVE_FIELDS = {"worktree_path", "orchestrator_pid"}

NON_TERMINAL = {"IN_PROGRESS", "DEGRADED"}
TERMINAL = {"OK", "FAILED", "ABORTED", "ESCALATED", "SIGNALED"}


def _fresh_state(monkeypatch, tmp_path):
    """Bring `so` into a freshly-initialised state on an empty tmp worktree."""
    monkeypatch.chdir(tmp_path)
    import slice_orchestrator as so

    init = getattr(so, "_init_state_dict", None)
    assert init is not None, "_init_state_dict missing (Phase 3 must add it)"
    init(slice_id="demo/slice-x")
    return so


def test_state_dict_includes_schema_version(monkeypatch, tmp_path):
    so = _fresh_state(monkeypatch, tmp_path)
    assert so._state["schema_version"] == "1.0"


def test_state_dict_required_fields_present(monkeypatch, tmp_path):
    so = _fresh_state(monkeypatch, tmp_path)
    missing = REQUIRED_FIELDS - set(so._state.keys())
    assert not missing, f"required schema v1.0 fields missing: {missing!r}"


def test_status_enum_values_match_spec(monkeypatch, tmp_path):
    so = _fresh_state(monkeypatch, tmp_path)
    values = set(getattr(so, "STATUS_VALUES", []))
    assert values == NON_TERMINAL | TERMINAL, (
        f"STATUS_VALUES must equal the spec enum; got {values!r}"
    )
    terminal = set(getattr(so, "TERMINAL_STATUS", []))
    assert terminal == TERMINAL, (
        f"TERMINAL_STATUS must equal {TERMINAL!r}; got {terminal!r}"
    )


def test_worktree_path_and_orchestrator_pid_populated_on_init(monkeypatch, tmp_path):
    so = _fresh_state(monkeypatch, tmp_path)
    for field in ADDITIVE_FIELDS:
        assert field in so._state, f"additive schema field {field!r} missing"
    assert so._state["worktree_path"], "worktree_path must be populated at init"
    assert isinstance(so._state["orchestrator_pid"], int), (
        "orchestrator_pid must be an int at init"
    )
    assert so._state["orchestrator_pid"] > 0
