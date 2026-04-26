"""Phase 2 RED — cost-discipline/lever-1-tier-retune.

Default-tier retune of two rows in ``AGENT_MODEL_CONFIG`` (intent.md §Spec
Detail Edit 1):

    phase-3-implementer  effort  medium → high
    phase-4-integrator   model   claude-sonnet-4-6 → claude-opus-4-7

Every retune-touching assertion below is expected to FAIL against current
``scripts/slice_orchestrator/core.py`` and PASS once Phase 3 lands the
two-row literal change. The override-precedence and unknown-role-fallback
contracts are unchanged and re-asserted here as regression guards so a
future tier flip cannot silently bypass the env-var surface.

Pre-existing T1–T11 assertions (from cost-discipline/lever-1-per-phase-model)
are retuned in-place where they pinned the old default values; structural
checks (symbol presence, argv shape, env-var precedence) are left intact.

Invariants touched: INV-003 (role names, ordering, gates — preserved by
  construction; only literals change), INV-009 (honest model_by_phase
  attribution — preserved; verified by T11-default with new opus default).
Design source: .claude/current-slice/intent.md §1-§4, §Verification.

Pytest + stdlib only (CLAUDE.md stdlib-only rule).
"""

from __future__ import annotations

import subprocess


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_so():
    """Return the cached slice_orchestrator module.

    Imported once per process; env-var tests use monkeypatch so the module
    re-evaluates os.environ on each call to _resolve_model_config (runtime
    lookup, not import-time).
    """
    import slice_orchestrator as so

    return so


def _setup_dispatch_env(monkeypatch, tmp_path):
    """Set up the minimal environment for tests that call _dispatch_once.

    - Changes cwd to tmp_path (so relative paths in the module resolve).
    - Creates the debug log directory.
    - Patches DEBUG_DIR to the absolute debug path so _write_phase_log
      doesn't write into the real repo tree.
    - Returns the imported module.
    """
    monkeypatch.chdir(tmp_path)
    debug_dir = tmp_path / ".claude" / "orchestrator-debug"
    debug_dir.mkdir(parents=True)
    (tmp_path / ".claude" / "current-slice").mkdir(parents=True)
    so = _import_so()
    monkeypatch.setattr(so, "DEBUG_DIR", debug_dir, raising=False)
    return so


def _ok_completed_process():
    """Minimal CompletedProcess returned by the _run_with_live_stderr mock."""
    return subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"status":"OK","commit_hash":"abc","summary":"model-config test"}',
        stderr="",
    )


_DISPATCH_INPUTS_P1 = {
    "phase": 1,
    "slice_id": "cost-discipline/lever-1-per-phase-model",
}
_DISPATCH_INPUTS_P3 = {
    "phase": 3,
    "slice_id": "cost-discipline/lever-1-per-phase-model",
}
_DISPATCH_INPUTS_P4 = {
    "phase": 4,
    "slice_id": "cost-discipline/lever-1-per-phase-model",
}


# ---------------------------------------------------------------------------
# Structural: AGENT_MODEL_CONFIG
# ---------------------------------------------------------------------------


def test_agent_model_config_exists_at_module_level():
    """AGENT_MODEL_CONFIG must be a non-empty dict at module level (intent §1)."""
    so = _import_so()
    cfg = getattr(so, "AGENT_MODEL_CONFIG", None)
    assert cfg is not None, (
        "AGENT_MODEL_CONFIG must be defined at module level in slice_orchestrator "
        "(intent.md §1 — module-level constant mapping role names to "
        "{model, effort} dicts)"
    )
    assert isinstance(cfg, dict) and cfg, (
        f"AGENT_MODEL_CONFIG must be a non-empty dict; got {type(cfg).__name__}"
    )


def test_agent_model_config_contains_all_five_roles():
    """All five roles in the spec must be present in AGENT_MODEL_CONFIG (intent §1)."""
    so = _import_so()
    cfg = so.AGENT_MODEL_CONFIG
    required = {
        "phase-1-writer",
        "phase-2-skeptic",
        "phase-3-implementer",
        "phase-4-integrator",
        "issue-triager",
    }
    missing = required - set(cfg.keys())
    assert not missing, (
        f"AGENT_MODEL_CONFIG missing roles: {sorted(missing)!r}. "
        "Full required set per intent.md §1: "
        "phase-1-writer, phase-2-skeptic, phase-3-implementer, "
        "phase-4-integrator, issue-triager."
    )


def test_agent_model_config_entries_have_model_and_effort_string_keys():
    """Each AGENT_MODEL_CONFIG entry must carry non-empty 'model' and 'effort' keys."""
    so = _import_so()
    cfg = so.AGENT_MODEL_CONFIG
    for role, entry in cfg.items():
        assert isinstance(entry, dict), (
            f"role {role!r}: AGENT_MODEL_CONFIG entry must be a dict; "
            f"got {type(entry).__name__}"
        )
        for key in ("model", "effort"):
            assert key in entry, (
                f"role {role!r}: AGENT_MODEL_CONFIG entry missing {key!r} key"
            )
            val = entry[key]
            assert isinstance(val, str) and val, (
                f"role {role!r}: AGENT_MODEL_CONFIG[{key!r}] must be a "
                f"non-empty string; got {val!r}"
            )


def test_agent_model_config_default_values_match_spec():
    """Verify the exact default model/effort values from intent.md §1."""
    so = _import_so()
    cfg = so.AGENT_MODEL_CONFIG
    expected = {
        "phase-1-writer": ("claude-opus-4-7", "high"),
        "phase-2-skeptic": ("claude-opus-4-7", "high"),
        # Retuned (lever-1-tier-retune): effort medium → high to restore
        # reasoning depth on cluster fan-out; Sonnet model retained for cost.
        "phase-3-implementer": ("claude-sonnet-4-6", "high"),
        # Retuned (lever-1-tier-retune): model sonnet → opus to put audit
        # quality on the higher-judgment model; effort stays low.
        "phase-4-integrator": ("claude-opus-4-7", "low"),
        "issue-triager": ("claude-opus-4-7", "medium"),
    }
    for role, (exp_model, exp_effort) in expected.items():
        got_model = cfg.get(role, {}).get("model")
        got_effort = cfg.get(role, {}).get("effort")
        assert got_model == exp_model, (
            f"AGENT_MODEL_CONFIG[{role!r}]['model']: expected {exp_model!r}, "
            f"got {got_model!r} (intent.md §1 table)"
        )
        assert got_effort == exp_effort, (
            f"AGENT_MODEL_CONFIG[{role!r}]['effort']: expected {exp_effort!r}, "
            f"got {got_effort!r} (intent.md §1 table)"
        )


# ---------------------------------------------------------------------------
# Structural: _resolve_model_config symbol
# ---------------------------------------------------------------------------


def test_resolve_model_config_symbol_exported():
    """_resolve_model_config must be accessible on the module (intent.md §2)."""
    so = _import_so()
    assert hasattr(so, "_resolve_model_config"), (
        "_resolve_model_config helper must be defined in slice_orchestrator "
        "(intent.md §2 — signature: (role: str) -> tuple[str, str | None])"
    )
    assert callable(so._resolve_model_config), "_resolve_model_config must be callable"


# ---------------------------------------------------------------------------
# T1: phase-1-writer default resolution
# ---------------------------------------------------------------------------


def test_t1_phase_1_writer_default_model_and_effort(monkeypatch):
    """T1: _resolve_model_config('phase-1-writer') → ('claude-opus-4-7', 'high')."""
    monkeypatch.delenv("CAIRN_MODEL_PHASE_1_WRITER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_1_WRITER", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-1-writer")
    assert model == "claude-opus-4-7", (
        f"T1: phase-1-writer default model must be 'claude-opus-4-7'; got {model!r}"
    )
    assert effort == "high", (
        f"T1: phase-1-writer default effort must be 'high'; got {effort!r}"
    )


# ---------------------------------------------------------------------------
# T2: phase-3-implementer default resolution (Sonnet/medium)
# ---------------------------------------------------------------------------


def test_t2_phase_3_implementer_default_model_and_effort(monkeypatch):
    """T2 (retuned): _resolve_model_config('phase-3-implementer') → ('claude-sonnet-4-6', 'high').

    Effort retune medium → high (lever-1-tier-retune §Spec Detail Edit 1).
    Sonnet model retained — bumping effort, not model, preserves Lever 1's
    cost split while restoring reasoning depth on cluster fan-out where the
    `compression/learnings-capture` empirical regression was observed.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-3-implementer")
    assert model == "claude-sonnet-4-6", (
        f"T2: phase-3-implementer default model must be 'claude-sonnet-4-6'; "
        f"got {model!r} (Lever 1 cost reduction retained: implementer on Sonnet)"
    )
    assert effort == "high", (
        f"T2 (retuned): phase-3-implementer default effort must be 'high' "
        f"(was 'medium'); got {effort!r}. Empirical signal: Phase-3 cluster "
        "fan-out worker reported OK without RED-test gating at medium — "
        "lever-1-tier-retune bumps effort to restore reasoning depth."
    )


# ---------------------------------------------------------------------------
# T3: phase-4-integrator default resolution (Sonnet/low)
# ---------------------------------------------------------------------------


def test_t3_phase_4_integrator_default_model_and_effort(monkeypatch):
    """T3 (retuned): _resolve_model_config('phase-4-integrator') → ('claude-opus-4-7', 'low').

    Model retune sonnet → opus (lever-1-tier-retune §Spec Detail Edit 1).
    Phase 4 is the audit boundary — its judgment quality decides whether
    bad implementer output reaches close. Operator stance: audit on Opus,
    accept low effort to keep cost delta narrow.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-4-integrator")
    assert model == "claude-opus-4-7", (
        f"T3 (retuned): phase-4-integrator default model must be "
        f"'claude-opus-4-7' (was 'claude-sonnet-4-6'); got {model!r}. "
        "Audit-boundary judgment rides Opus per lever-1-tier-retune §Spec "
        "Detail Edit 1."
    )
    assert effort == "low", (
        f"T3: phase-4-integrator default effort must be 'low' (unchanged); "
        f"got {effort!r}"
    )


# ---------------------------------------------------------------------------
# T4: issue-triager default resolution (Opus/medium)
# ---------------------------------------------------------------------------


def test_t4_issue_triager_default_model_and_effort(monkeypatch):
    """T4: _resolve_model_config('issue-triager') → ('claude-opus-4-7', 'medium')."""
    monkeypatch.delenv("CAIRN_MODEL_ISSUE_TRIAGER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_ISSUE_TRIAGER", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("issue-triager")
    assert model == "claude-opus-4-7", (
        f"T4: issue-triager default model must be 'claude-opus-4-7'; got {model!r}"
    )
    assert effort == "medium", (
        f"T4: issue-triager default effort must be 'medium'; got {effort!r}"
    )


# ---------------------------------------------------------------------------
# T5: CAIRN_MODEL_* overrides model; effort stays at dict default
# ---------------------------------------------------------------------------


def test_t5_cairn_model_env_overrides_model_only(monkeypatch):
    """T5: CAIRN_MODEL_PHASE_3_IMPLEMENTER overrides model; effort stays at retuned 'high'."""
    monkeypatch.setenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", "claude-opus-4-7")
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-3-implementer")
    assert model == "claude-opus-4-7", (
        f"T5: CAIRN_MODEL_PHASE_3_IMPLEMENTER='claude-opus-4-7' must override "
        f"the model; got {model!r}"
    )
    assert effort == "high", (
        f"T5: effort must remain at retuned dict default 'high' when only model is "
        f"overridden; got {effort!r} (env vars override independently)"
    )


# ---------------------------------------------------------------------------
# T6: CAIRN_EFFORT_* overrides effort; model stays at dict default
# ---------------------------------------------------------------------------


def test_t6_cairn_effort_env_overrides_effort_only(monkeypatch):
    """T6 (retuned-default): CAIRN_EFFORT_PHASE_4_INTEGRATOR overrides effort;
    model stays at the new opus default.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", raising=False)
    monkeypatch.setenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", "high")
    so = _import_so()
    model, effort = so._resolve_model_config("phase-4-integrator")
    assert model == "claude-opus-4-7", (
        f"T6 (retuned): model must remain at the new dict default "
        f"'claude-opus-4-7' when only effort is overridden; got {model!r}. "
        "Independent overrides: setting CAIRN_EFFORT_* must not perturb model."
    )
    assert effort == "high", (
        f"T6: CAIRN_EFFORT_PHASE_4_INTEGRATOR='high' must override effort; "
        f"got {effort!r}"
    )


# ---------------------------------------------------------------------------
# T7: both CAIRN_MODEL_* and CAIRN_EFFORT_* set; both override independently
# ---------------------------------------------------------------------------


def test_t7_both_env_vars_override_independently(monkeypatch):
    """T7: both CAIRN_MODEL_* and CAIRN_EFFORT_* set → both values are used."""
    monkeypatch.setenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", "claude-haiku-4-5")
    monkeypatch.setenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", "low")
    so = _import_so()
    model, effort = so._resolve_model_config("phase-3-implementer")
    assert model == "claude-haiku-4-5", (
        f"T7: CAIRN_MODEL_PHASE_3_IMPLEMENTER='claude-haiku-4-5' must appear "
        f"as model; got {model!r}"
    )
    assert effort == "low", (
        f"T7: CAIRN_EFFORT_PHASE_3_IMPLEMENTER='low' must appear as effort; "
        f"got {effort!r}"
    )


# ---------------------------------------------------------------------------
# T8: unknown role falls back to opus/high
# ---------------------------------------------------------------------------


def test_t8_unknown_role_falls_back_to_opus_high(monkeypatch):
    """T8: role not in AGENT_MODEL_CONFIG falls back to ('claude-opus-4-7', 'high')."""
    monkeypatch.delenv("CAIRN_MODEL_PHASE_99_PHANTOM", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_99_PHANTOM", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-99-phantom")
    assert model == "claude-opus-4-7", (
        f"T8: unknown role 'phase-99-phantom' must fall back to model "
        f"'claude-opus-4-7'; got {model!r} (intent.md §2 fallback)"
    )
    assert effort == "high", (
        f"T8: unknown role must fall back to effort 'high'; got {effort!r}"
    )


# ---------------------------------------------------------------------------
# T9: dispatch cmd list carries --model and --effort as separate argv entries
# ---------------------------------------------------------------------------


def test_t9_dispatch_cmd_contains_model_and_effort_as_separate_argv_entries(
    monkeypatch, tmp_path
):
    """T9: _dispatch_once builds a cmd list where '--model' and '--effort' appear
    as distinct entries (not shell-escaped or joined with their values).

    The dispatch site is _dispatch_once (called by dispatch_phase_agent).
    Monkeypatches _run_with_live_stderr to capture the cmd without spawning
    a subprocess.
    """
    so = _setup_dispatch_env(monkeypatch, tmp_path)
    monkeypatch.delenv("CAIRN_MODEL_PHASE_1_WRITER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_1_WRITER", raising=False)

    captured: list[list[str]] = []

    def fake_run(cmd, env, timeout, prefix=""):
        captured.append(list(cmd))
        return _ok_completed_process()

    monkeypatch.setattr(so, "_run_with_live_stderr", fake_run)
    so._init_state_dict(slice_id="cost-discipline/lever-1-per-phase-model")

    so._dispatch_once("phase-1-writer", _DISPATCH_INPUTS_P1)

    assert captured, (
        "T9: fake _run_with_live_stderr was never called — "
        "_dispatch_once must call _run_with_live_stderr with the cmd list"
    )
    cmd = captured[0]

    assert "--model" in cmd, (
        f"T9: '--model' must appear as a separate argv entry in the cmd; "
        f"cmd={cmd!r}. Check that _dispatch_once splices "
        "'--model', <resolved-model> after '--agent', <role>."
    )
    assert "--effort" in cmd, (
        f"T9: '--effort' must appear as a separate argv entry in the cmd; "
        f"cmd={cmd!r}. Check that _dispatch_once splices "
        "'--effort', <resolved-effort> after '--model', <resolved-model>."
    )

    model_idx = cmd.index("--model")
    effort_idx = cmd.index("--effort")

    assert model_idx + 1 < len(cmd), (
        "T9: '--model' is the last entry — there must be a value after it"
    )
    assert effort_idx + 1 < len(cmd), (
        "T9: '--effort' is the last entry — there must be a value after it"
    )

    model_val = cmd[model_idx + 1]
    effort_val = cmd[effort_idx + 1]

    assert " " not in model_val, (
        f"T9: model value must not contain spaces (not shell-joined); "
        f"got {model_val!r}. Must be a separate argv element, not 'model=X'."
    )
    assert " " not in effort_val, (
        f"T9: effort value must not contain spaces (not shell-joined); "
        f"got {effort_val!r}."
    )

    # Default values for phase-1-writer: opus/high.
    assert model_val == "claude-opus-4-7", (
        f"T9: default model for 'phase-1-writer' must be 'claude-opus-4-7'; "
        f"cmd[model_idx+1]={model_val!r}"
    )
    assert effort_val == "high", (
        f"T9: default effort for 'phase-1-writer' must be 'high'; "
        f"cmd[effort_idx+1]={effort_val!r}"
    )


def test_t9_dispatch_cmd_env_override_appears_in_argv(monkeypatch, tmp_path):
    """T9 variant: env-override propagates to the actual argv passed to subprocess.

    CAIRN_MODEL_PHASE_3_IMPLEMENTER must be the --model value in the cmd list,
    not the AGENT_MODEL_CONFIG default.
    """
    so = _setup_dispatch_env(monkeypatch, tmp_path)
    monkeypatch.setenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", "claude-opus-4-7")
    monkeypatch.setenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", "low")

    captured: list[list[str]] = []

    def fake_run(cmd, env, timeout, prefix=""):
        captured.append(list(cmd))
        return _ok_completed_process()

    monkeypatch.setattr(so, "_run_with_live_stderr", fake_run)
    so._init_state_dict(slice_id="cost-discipline/lever-1-per-phase-model")

    so._dispatch_once("phase-3-implementer", _DISPATCH_INPUTS_P3)

    assert captured, "fake _run_with_live_stderr was never called"
    cmd = captured[0]

    model_val = cmd[cmd.index("--model") + 1] if "--model" in cmd else None
    effort_val = cmd[cmd.index("--effort") + 1] if "--effort" in cmd else None

    assert model_val == "claude-opus-4-7", (
        f"T9-override: CAIRN_MODEL_PHASE_3_IMPLEMENTER='claude-opus-4-7' must "
        f"appear in argv as --model value; got {model_val!r}"
    )
    assert effort_val == "low", (
        f"T9-override: CAIRN_EFFORT_PHASE_3_IMPLEMENTER='low' must appear in "
        f"argv as --effort value; got {effort_val!r}"
    )


def test_t9_model_and_effort_are_adjacent_to_their_values_not_joined(
    monkeypatch, tmp_path
):
    """T9 structural: --model and --effort must each be a standalone flag entry.

    Rejects patterns like '--model=claude-sonnet-4-6' (joined) or
    '--model claude-sonnet-4-6' (single string with space).
    """
    so = _setup_dispatch_env(monkeypatch, tmp_path)
    monkeypatch.delenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", raising=False)

    captured: list[list[str]] = []

    def fake_run(cmd, env, timeout, prefix=""):
        captured.append(list(cmd))
        return _ok_completed_process()

    monkeypatch.setattr(so, "_run_with_live_stderr", fake_run)
    so._init_state_dict(slice_id="cost-discipline/lever-1-per-phase-model")
    so._dispatch_once("phase-4-integrator", _DISPATCH_INPUTS_P4)

    assert captured
    cmd = captured[0]

    # Must be present at all (guards against --model being omitted entirely).
    assert "--model" in cmd, (
        f"T9-structural: '--model' must be present in cmd; cmd={cmd!r}"
    )
    assert "--effort" in cmd, (
        f"T9-structural: '--effort' must be present in cmd; cmd={cmd!r}"
    )

    # No entry should be a joined form like '--model=...' or '--effort=...'
    joined_model = [e for e in cmd if e.startswith("--model=")]
    joined_effort = [e for e in cmd if e.startswith("--effort=")]
    assert not joined_model, (
        f"T9: --model must not be joined with its value (e.g. '--model=...'). "
        f"Found: {joined_model!r} in cmd={cmd!r}"
    )
    assert not joined_effort, (
        f"T9: --effort must not be joined with its value (e.g. '--effort=...'). "
        f"Found: {joined_effort!r} in cmd={cmd!r}"
    )


# ---------------------------------------------------------------------------
# T10: empty string env var does NOT override (falls back to dict default)
# ---------------------------------------------------------------------------


def test_t10_empty_model_env_var_does_not_override(monkeypatch):
    """T10 (retuned-default): CAIRN_MODEL_PHASE_3_IMPLEMENTER='' must not
    override; dict default used.

    Empty-string env var must fall through via ``or`` short-circuit. Default
    effort is now 'high' post-retune.
    """
    monkeypatch.setenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", "")
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-3-implementer")
    assert model == "claude-sonnet-4-6", (
        f"T10: empty CAIRN_MODEL_PHASE_3_IMPLEMENTER must not override; "
        f"expected dict default 'claude-sonnet-4-6', got {model!r}. "
        "Implementation must use `os.environ.get(...) or default` semantics."
    )
    assert effort == "high", (
        f"T10 (retuned): effort must remain at the new dict default 'high'; "
        f"got {effort!r}"
    )


def test_t10_empty_effort_env_var_does_not_override(monkeypatch):
    """T10 variant (retuned-default): CAIRN_EFFORT_PHASE_4_INTEGRATOR='' must not override.

    Default model is now 'claude-opus-4-7' post-retune.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", raising=False)
    monkeypatch.setenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", "")
    so = _import_so()
    model, effort = so._resolve_model_config("phase-4-integrator")
    assert effort == "low", (
        f"T10: empty CAIRN_EFFORT_PHASE_4_INTEGRATOR must not override; "
        f"expected dict default 'low', got {effort!r}."
    )
    assert model == "claude-opus-4-7", (
        f"T10 (retuned): model must remain at the new dict default "
        f"'claude-opus-4-7'; got {model!r}"
    )


# ---------------------------------------------------------------------------
# T11 (spec §4): model_by_phase records the RESOLVED model post-dispatch
# ---------------------------------------------------------------------------


def test_t11_dispatch_records_resolved_model_in_model_by_phase_override(
    monkeypatch, tmp_path
):
    """T11: after dispatch, model_by_phase[phase] equals the env-var-resolved model.

    Spec §4: 'Resolved model is recorded in model_by_phase[phase] ... so cost
    attribution stays honest when env-var overrides fire.' (INV-009 honesty)
    """
    so = _setup_dispatch_env(monkeypatch, tmp_path)
    monkeypatch.setenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", "claude-opus-4-7")
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", raising=False)

    def fake_run(cmd, env, timeout, prefix=""):
        return _ok_completed_process()

    monkeypatch.setattr(so, "_run_with_live_stderr", fake_run)
    so._init_state_dict(slice_id="cost-discipline/lever-1-per-phase-model")

    so._dispatch_once("phase-3-implementer", _DISPATCH_INPUTS_P3)

    recorded = so._state.get("model_by_phase", {}).get("phase-3-implementer")
    assert recorded == "claude-opus-4-7", (
        f"T11: model_by_phase['phase-3-implementer'] must equal the resolved "
        f"model 'claude-opus-4-7' (from CAIRN_MODEL_PHASE_3_IMPLEMENTER override); "
        f"got {recorded!r}. Spec §4 / INV-009: cost attribution must be honest "
        "under env-var overrides — model_by_phase must reflect what was SENT to "
        "claude -p, not the AGENT_MODEL_CONFIG default."
    )


def test_t11_dispatch_records_resolved_model_default_config(monkeypatch, tmp_path):
    """T11 default variant: model_by_phase reflects AGENT_MODEL_CONFIG default."""
    so = _setup_dispatch_env(monkeypatch, tmp_path)
    monkeypatch.delenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", raising=False)

    def fake_run(cmd, env, timeout, prefix=""):
        return _ok_completed_process()

    monkeypatch.setattr(so, "_run_with_live_stderr", fake_run)
    so._init_state_dict(slice_id="cost-discipline/lever-1-per-phase-model")

    so._dispatch_once("phase-4-integrator", _DISPATCH_INPUTS_P4)

    recorded = so._state.get("model_by_phase", {}).get("phase-4-integrator")
    assert recorded == "claude-opus-4-7", (
        f"T11-default (retuned): model_by_phase['phase-4-integrator'] must "
        f"equal the new default model 'claude-opus-4-7' (was "
        f"'claude-sonnet-4-6'); got {recorded!r}. INV-009 honesty: "
        "model_by_phase records the RESOLVED model — when the dict default "
        "flips, this attribution must flip with it (not lag or hardcode)."
    )


# ---------------------------------------------------------------------------
# Role normalisation: hyphens → underscores, uppercase
# ---------------------------------------------------------------------------


def test_role_normalisation_hyphens_to_underscores_uppercase(monkeypatch):
    """Role 'phase-3-implementer' must map to env key 'CAIRN_MODEL_PHASE_3_IMPLEMENTER'.

    Tests that the env-var key derivation in _resolve_model_config respects
    intent.md §2: 'role.upper().replace(\"-\", \"_\")'.
    """
    sentinel = "sentinel-model-xyzzy"
    monkeypatch.setenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", sentinel)
    so = _import_so()
    model, _ = so._resolve_model_config("phase-3-implementer")
    assert model == sentinel, (
        f"Role normalisation 'phase-3-implementer' → 'PHASE_3_IMPLEMENTER' failed. "
        f"CAIRN_MODEL_PHASE_3_IMPLEMENTER={sentinel!r} not picked up; got {model!r}. "
        "Intent §2: key = role.upper().replace('-', '_')"
    )


def test_role_normalisation_phase_2_skeptic(monkeypatch):
    """'phase-2-skeptic' must map to CAIRN_MODEL_PHASE_2_SKEPTIC."""
    sentinel = "sentinel-skeptic-model"
    monkeypatch.setenv("CAIRN_MODEL_PHASE_2_SKEPTIC", sentinel)
    so = _import_so()
    model, _ = so._resolve_model_config("phase-2-skeptic")
    assert model == sentinel, (
        f"Role normalisation 'phase-2-skeptic' → 'PHASE_2_SKEPTIC' failed; "
        f"got {model!r}"
    )


def test_role_normalisation_issue_triager(monkeypatch):
    """'issue-triager' must map to CAIRN_MODEL_ISSUE_TRIAGER."""
    sentinel = "sentinel-triager-model"
    monkeypatch.setenv("CAIRN_MODEL_ISSUE_TRIAGER", sentinel)
    so = _import_so()
    model, _ = so._resolve_model_config("issue-triager")
    assert model == sentinel, (
        f"Role normalisation 'issue-triager' → 'ISSUE_TRIAGER' failed; got {model!r}"
    )


# ---------------------------------------------------------------------------
# phase-2-skeptic (current role) also covered
# ---------------------------------------------------------------------------


def test_phase_2_skeptic_default_resolution(monkeypatch):
    """phase-2-skeptic default: ('claude-opus-4-7', 'high') — covers current role."""
    monkeypatch.delenv("CAIRN_MODEL_PHASE_2_SKEPTIC", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_2_SKEPTIC", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-2-skeptic")
    assert model == "claude-opus-4-7", (
        f"phase-2-skeptic default model must be 'claude-opus-4-7'; got {model!r}"
    )
    assert effort == "high", (
        f"phase-2-skeptic default effort must be 'high'; got {effort!r}"
    )


# =============================================================================
# lever-1-tier-retune §Verification — eight named RED tests.
# =============================================================================
#
# Mapped 1:1 to intent.md §Verification bullets. These are the canonical
# Phase-2 RED set for this slice; the T1-T11 retuning above is in-place
# coverage of the prior lever-1-per-phase-model regression surface so the
# override / argv / honest-attribution invariants are not lost behind the
# new defaults.


def test_default_phase_3_implementer_resolves_sonnet_high(monkeypatch):
    """Verification: phase-3-implementer default → ('claude-sonnet-4-6', 'high').

    intent.md §Spec Detail Edit 1, row P3: effort medium → high; model
    unchanged. Empirical motivation: cluster-fan-out worker reported OK
    without RED-test gating at sonnet/medium on
    `compression/learnings-capture` (artifacts under
    `.claude/completed-slices/compression-learnings-capture-failed/`).
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-3-implementer")
    assert (model, effort) == ("claude-sonnet-4-6", "high"), (
        f"lever-1-tier-retune: phase-3-implementer default must be "
        f"('claude-sonnet-4-6', 'high'); got ({model!r}, {effort!r}). "
        "Sonnet retained for cost; effort bumped to restore reasoning "
        "depth on cluster fan-out."
    )


def test_default_phase_4_integrator_resolves_opus_low(monkeypatch):
    """Verification: phase-4-integrator default → ('claude-opus-4-7', 'low').

    intent.md §Spec Detail Edit 1, row P4: model sonnet → opus; effort
    unchanged. Phase 4 is the audit boundary; operator stance is that
    judgment quality should ride Opus while accepting `low` effort to keep
    cost delta narrow.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-4-integrator")
    assert (model, effort) == ("claude-opus-4-7", "low"), (
        f"lever-1-tier-retune: phase-4-integrator default must be "
        f"('claude-opus-4-7', 'low'); got ({model!r}, {effort!r}). "
        "Audit boundary on Opus; effort stays low to keep cost delta narrow."
    )


def test_default_unchanged_phase_1_writer(monkeypatch):
    """Verification: phase-1-writer default unchanged at ('claude-opus-4-7', 'high').

    Regression guard on a row the retune does NOT touch — accidental drift
    on this row would mean the literal edit slipped past its intended scope.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_1_WRITER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_1_WRITER", raising=False)
    so = _import_so()
    assert so._resolve_model_config("phase-1-writer") == (
        "claude-opus-4-7",
        "high",
    ), (
        "lever-1-tier-retune regression guard: phase-1-writer default must "
        "remain ('claude-opus-4-7', 'high'). intent.md §Spec Detail Edit 1 "
        "touches only rows P3 and P4; any drift here means scope creep."
    )


def test_default_unchanged_phase_2_skeptic(monkeypatch):
    """Verification: phase-2-skeptic default unchanged at ('claude-opus-4-7', 'high')."""
    monkeypatch.delenv("CAIRN_MODEL_PHASE_2_SKEPTIC", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_2_SKEPTIC", raising=False)
    so = _import_so()
    assert so._resolve_model_config("phase-2-skeptic") == (
        "claude-opus-4-7",
        "high",
    ), (
        "lever-1-tier-retune regression guard: phase-2-skeptic default must "
        "remain ('claude-opus-4-7', 'high'). intent.md §Spec Detail Edit 1 "
        "touches only rows P3 and P4."
    )


def test_default_unchanged_issue_triager(monkeypatch):
    """Verification: issue-triager default unchanged at ('claude-opus-4-7', 'medium')."""
    monkeypatch.delenv("CAIRN_MODEL_ISSUE_TRIAGER", raising=False)
    monkeypatch.delenv("CAIRN_EFFORT_ISSUE_TRIAGER", raising=False)
    so = _import_so()
    assert so._resolve_model_config("issue-triager") == (
        "claude-opus-4-7",
        "medium",
    ), (
        "lever-1-tier-retune regression guard: issue-triager default must "
        "remain ('claude-opus-4-7', 'medium'). intent.md §Spec Detail Edit 1 "
        "touches only rows P3 and P4."
    )


def test_env_override_still_wins_phase_3_effort(monkeypatch):
    """Verification: CAIRN_EFFORT_PHASE_3_IMPLEMENTER=medium beats new 'high' default.

    intent.md §Spec Detail Edit 2: 'Override-precedence tests (env var beats
    default) MUST still pass against the new defaults — exercise both
    phase-3-implementer and phase-4-integrator override cases explicitly so
    future tier flips cannot silently bypass the override surface.'

    Operator-revert path: the slice's own §Why narrative names this exact
    env var as the way to revert P3 effort.
    """
    monkeypatch.delenv("CAIRN_MODEL_PHASE_3_IMPLEMENTER", raising=False)
    monkeypatch.setenv("CAIRN_EFFORT_PHASE_3_IMPLEMENTER", "medium")
    so = _import_so()
    model, effort = so._resolve_model_config("phase-3-implementer")
    assert effort == "medium", (
        f"lever-1-tier-retune: CAIRN_EFFORT_PHASE_3_IMPLEMENTER='medium' "
        f"must beat the new dict default 'high'; got {effort!r}. The env-var "
        "surface is the documented operator-revert path for this retune; "
        "if a future tier flip silently bypasses it the override contract "
        "is broken."
    )
    assert model == "claude-sonnet-4-6", (
        f"P3 model must remain at the (unchanged) dict default "
        f"'claude-sonnet-4-6' when only effort env var is set; got {model!r}"
    )


def test_env_override_still_wins_phase_4_model(monkeypatch):
    """Verification: CAIRN_MODEL_PHASE_4_INTEGRATOR=claude-sonnet-4-6 beats new opus default.

    Operator-revert path named in intent.md §Why for the P4 retune.
    """
    monkeypatch.setenv("CAIRN_MODEL_PHASE_4_INTEGRATOR", "claude-sonnet-4-6")
    monkeypatch.delenv("CAIRN_EFFORT_PHASE_4_INTEGRATOR", raising=False)
    so = _import_so()
    model, effort = so._resolve_model_config("phase-4-integrator")
    assert model == "claude-sonnet-4-6", (
        f"lever-1-tier-retune: CAIRN_MODEL_PHASE_4_INTEGRATOR='claude-sonnet-4-6' "
        f"must beat the new dict default 'claude-opus-4-7'; got {model!r}. "
        "Operator-revert path must keep working post-retune."
    )
    assert effort == "low", (
        f"P4 effort must remain at dict default 'low' when only model env "
        f"var is set; got {effort!r}"
    )


def test_unknown_role_falls_back_to_opus_high(monkeypatch):
    """Verification: unknown role → ('claude-opus-4-7', 'high') fallback unchanged.

    intent.md §Spec Detail: '_resolve_model_config is not edited — its body,
    env-var precedence, and unknown-role fallback (claude-opus-4-7 / high)
    remain byte-identical.' This test is a regression guard on that
    invariant — if the body of _resolve_model_config is rewritten as part
    of the literal edit, this catches it.
    """
    # Use a clearly-fictitious role name; ensure no stray env var pollutes.
    fake_role = "phase-99-phantom-retune"
    env_key = fake_role.upper().replace("-", "_")
    monkeypatch.delenv(f"CAIRN_MODEL_{env_key}", raising=False)
    monkeypatch.delenv(f"CAIRN_EFFORT_{env_key}", raising=False)
    so = _import_so()
    assert so._resolve_model_config(fake_role) == (
        "claude-opus-4-7",
        "high",
    ), (
        "lever-1-tier-retune contract: unknown-role fallback must remain "
        "('claude-opus-4-7', 'high') byte-identical to current behaviour. "
        "intent.md §Spec Detail forbids edits to _resolve_model_config body."
    )
