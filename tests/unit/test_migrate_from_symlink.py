"""RED tests for cairn-m6-f3-migration-and-symlink-retire — migration helper.

Tests `scripts/migrate_from_symlink.sh` (Phase 3 will write it). Per intent
§Verification "Phase 2 RED test cases", 8 named cases:

  (a)  Happy-path                            -> exit 0, symlink unlinked, settings filtered
  (b)  In-flight skill-run (no env)          -> exit 2 (Pre-mortem Scenario 6)
  (c1) Cairn-self, no env vars               -> exit 3 (INV-011 / D8)
  (c2) Cairn-self + CAIRN_MIGRATE_FORCE=1    -> exit 3 (asymmetry — FORCE does NOT bypass exit 3)
  (c3) Cairn-self + CAIRN_MIGRATE_BREAK_INV011=1 -> exit 0, multi-line stderr block, symlink destroyed
  (d)  Force-mode quiescence override        -> exit 0, Scenario 6 warning on stderr
  (e)  shellcheck                            -> zero warnings (skip if not on PATH)
  (f)  dash runtime                          -> behavioural fixtures hold under /usr/bin/dash

Runs the bash script via subprocess; no Python module to import. (c3) destroys
the fixture's `.slice-system` symlink — runs in `tmp_path` ONLY (never against
the real cairn working tree).

Tests must FAIL at HEAD because `scripts/migrate_from_symlink.sh` does not yet
exist; Phase 3 makes them green.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "migrate_from_symlink.sh"


# ---------------------------------------------------------------------------
# Helpers / fixture builders
# ---------------------------------------------------------------------------


# Cairn-shaped settings.json with the three symlink-anchored hook commands
# verified directly against `.claude/settings.json` at SNAPSHOT_SHA caa7599.
CAIRN_SHAPED_SETTINGS = {
    "enabledPlugins": {
        "superpowers@claude-plugins-official": True,
    },
    "permissions": {"allow": ["Bash(jq *)"]},
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Bash|Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": "$CLAUDE_PROJECT_DIR/.slice-system/checks/reversibility-guard.sh",
                    }
                ],
            },
            {
                "matcher": "Write|Edit|MultiEdit|NotebookEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": "uv run python $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py",
                    }
                ],
            },
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": "$CLAUDE_PROJECT_DIR/.slice-system/checks/reality-check.sh",
                    }
                ],
            },
            # An unrelated hook that must SURVIVE the filter (no .slice-system substring).
            {
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": "echo unrelated-hook",
                    }
                ],
            },
        ],
    },
}


def _write_settings(claude_dir: Path) -> Path:
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(json.dumps(CAIRN_SHAPED_SETTINGS, indent=2))
    return settings_path


def _build_consumer_fixture(
    tmp_path: Path,
    *,
    symlink_target: str,
    skill_runs: list[tuple[str, bool]] | None = None,
) -> Path:
    """Build a fake consumer repo at `tmp_path`.

    `symlink_target` is the literal string the `.slice-system` symlink will
    point to (relative to `tmp_path`). For (c1)/(c2)/(c3), pass `"."` to
    create a self-symlink.

    `skill_runs` is a list of `(skill_run_id, has_sweep_notes)` tuples. If a
    skill-run has `has_sweep_notes=False`, it is in-flight — should trip exit 2
    unless `CAIRN_MIGRATE_FORCE=1`.
    """
    # `.slice-system` symlink target: for non-self targets, materialise a
    # plausible target dir so readlink returns a non-`.` value.
    if symlink_target != ".":
        target_dir = tmp_path / symlink_target
        target_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".slice-system").symlink_to(symlink_target)

    # `.claude/` tree.
    claude_dir = tmp_path / ".claude"
    _write_settings(claude_dir)

    runs_dir = claude_dir / "skill-runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    for run_id, quiesced in skill_runs or []:
        run_path = runs_dir / run_id / "integration"
        run_path.mkdir(parents=True, exist_ok=True)
        if quiesced:
            (run_path / "sweep-notes.md").write_text("# sweep notes\n")

    return tmp_path


def _require_script() -> None:
    """Fail fast if the script is missing. Phase 2 RED expects this to fail."""
    if not SCRIPT.is_file():
        pytest.fail(
            f"scripts/migrate_from_symlink.sh not found at {SCRIPT} — "
            "Phase 3 has not yet written the implementation. RED expected."
        )


def _run(
    fixture: Path,
    *,
    env_overrides: dict[str, str] | None = None,
    interpreter: str | None = None,
) -> subprocess.CompletedProcess:
    """Run the script against `fixture` (which becomes cwd).

    Inherits parent env, then layers overrides. `interpreter` (e.g.
    `/bin/dash`) lets case (f) re-run the same script under dash.
    """
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    if interpreter is not None:
        cmd = [interpreter, str(SCRIPT)]
    else:
        cmd = [str(SCRIPT)]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=fixture,
        env=env,
    )


def _read_settings(fixture: Path) -> str:
    return (fixture / ".claude" / "settings.json").read_text()


# ---------------------------------------------------------------------------
# (a) Happy-path
# ---------------------------------------------------------------------------


def test_a_happy_path_exit_0_symlink_unlinked_settings_filtered(tmp_path):
    """exit 0; symlink unlinked; settings.json contains no $CLAUDE_PROJECT_DIR/.slice-system/;
    stdout names both slash commands AND a session-restart prompt."""
    _require_script()
    fixture = _build_consumer_fixture(
        tmp_path, symlink_target="cairn-checkout", skill_runs=[]
    )
    result = _run(fixture)

    assert result.returncode == 0, (
        f"expected exit 0 happy-path, got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    # Symlink unlinked.
    assert not (fixture / ".slice-system").is_symlink(), (
        ".slice-system symlink should be unlinked after happy-path migration"
    )
    assert not (fixture / ".slice-system").exists(), (
        ".slice-system path should not exist post-migration"
    )

    # Settings.json filtered: no $CLAUDE_PROJECT_DIR/.slice-system/ substring.
    filtered = _read_settings(fixture)
    assert "$CLAUDE_PROJECT_DIR/.slice-system/" not in filtered, (
        "settings.json still contains $CLAUDE_PROJECT_DIR/.slice-system/ — "
        "filter did not remove symlink-anchored hook entries"
    )
    # Unrelated hook must survive.
    assert "echo unrelated-hook" in filtered, (
        "filter over-removed: unrelated hook entry was dropped"
    )

    # Stdout banner names the operator's next manual steps.
    assert "/plugin marketplace add https://github.com/firaaz/cairn" in result.stdout, (
        f"stdout missing /plugin marketplace add line; stdout={result.stdout}"
    )
    assert "/plugin install cairn@cairn-marketplace" in result.stdout, (
        f"stdout missing /plugin install line; stdout={result.stdout}"
    )
    # Session-restart prompt — accept either token; intent says "session-restart prompt".
    assert ("restart" in result.stdout.lower()) or (
        "session" in result.stdout.lower()
    ), f"stdout missing session-restart prompt; stdout={result.stdout}"


# ---------------------------------------------------------------------------
# (b) In-flight skill-run
# ---------------------------------------------------------------------------


def test_b_in_flight_skill_run_exit_2_no_state_change(tmp_path):
    """exit 2; stderr names 'in-flight skill-run' + offending path;
    symlink + settings.json unchanged on disk."""
    _require_script()
    fixture = _build_consumer_fixture(
        tmp_path,
        symlink_target="cairn-checkout",
        skill_runs=[("in-flight-feature-id", False)],
    )
    settings_before = _read_settings(fixture)

    result = _run(fixture)

    assert result.returncode == 2, (
        f"expected exit 2 quiescence-fail, got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    # Stderr names "in-flight skill-run" and the offending path.
    assert "in-flight skill-run" in result.stderr, (
        f"stderr missing literal 'in-flight skill-run'; stderr={result.stderr}"
    )
    assert "in-flight-feature-id" in result.stderr, (
        f"stderr does not name offending skill-run path 'in-flight-feature-id'; "
        f"stderr={result.stderr}"
    )

    # No state change.
    assert (fixture / ".slice-system").is_symlink(), (
        ".slice-system symlink should be unchanged on exit 2"
    )
    assert _read_settings(fixture) == settings_before, (
        "settings.json should be unchanged on exit 2"
    )


# ---------------------------------------------------------------------------
# (c1) Cairn-self, no env vars
# ---------------------------------------------------------------------------


def _assert_no_state_change(
    fixture: Path, *, settings_before: str, link_target_before: str
) -> None:
    assert (fixture / ".slice-system").is_symlink(), (
        ".slice-system symlink should NOT be unlinked on exit-3 refusal"
    )
    assert os.readlink(fixture / ".slice-system") == link_target_before, (
        "symlink target changed on what should have been a no-state-change refusal"
    )
    assert _read_settings(fixture) == settings_before, (
        "settings.json should be unchanged on exit-3 refusal"
    )


def test_c1_cairn_self_no_env_exit_3_with_required_stderr_tokens(tmp_path):
    """exit 3; stderr contains INV-011 / docs/ARCHITECTURE.md:91 / D8 /
    literal CAIRN_MIGRATE_BREAK_INV011 (so a typo is greppable in shell history);
    no state change."""
    _require_script()
    fixture = _build_consumer_fixture(tmp_path, symlink_target=".", skill_runs=[])
    settings_before = _read_settings(fixture)

    result = _run(fixture)

    assert result.returncode == 3, (
        f"expected exit 3 cairn-self refusal, got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    for token in (
        "INV-011",
        "docs/ARCHITECTURE.md:91",
        "D8",
        "CAIRN_MIGRATE_BREAK_INV011",
    ):
        assert token in result.stderr, (
            f"stderr missing required token {token!r}; stderr={result.stderr}"
        )

    _assert_no_state_change(
        fixture, settings_before=settings_before, link_target_before="."
    )


# ---------------------------------------------------------------------------
# (c2) Cairn-self + CAIRN_MIGRATE_FORCE=1 — asymmetry
# ---------------------------------------------------------------------------


def test_c2_cairn_self_with_FORCE_still_exits_3(tmp_path):
    """CAIRN_MIGRATE_FORCE=1 alone does NOT bypass exit 3 (asymmetry assertion)."""
    _require_script()
    fixture = _build_consumer_fixture(tmp_path, symlink_target=".", skill_runs=[])
    settings_before = _read_settings(fixture)

    result = _run(fixture, env_overrides={"CAIRN_MIGRATE_FORCE": "1"})

    assert result.returncode == 3, (
        f"CAIRN_MIGRATE_FORCE=1 must NOT bypass exit 3; got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    for token in (
        "INV-011",
        "docs/ARCHITECTURE.md:91",
        "D8",
        "CAIRN_MIGRATE_BREAK_INV011",
    ):
        assert token in result.stderr, (
            f"stderr missing required token {token!r}; stderr={result.stderr}"
        )

    _assert_no_state_change(
        fixture, settings_before=settings_before, link_target_before="."
    )


# ---------------------------------------------------------------------------
# (c3) Cairn-self + CAIRN_MIGRATE_BREAK_INV011=1 — destructive override
# ---------------------------------------------------------------------------


def test_c3_cairn_self_with_BREAK_INV011_proceeds_with_multiline_stderr(tmp_path):
    """exit 0; stderr is a multi-line block (>=3 lines) citing INV-011, D8,
    docs/ARCHITECTURE.md:91; symlink unlinked; settings.json filtered.

    SAFETY: this case destroys the test fixture's `.slice-system` symlink. It
    runs in `tmp_path` ONLY — never against the real cairn working tree.
    """
    _require_script()
    # Defensive isolation: tmp_path must NOT be inside the real cairn repo.
    assert REPO_ROOT not in tmp_path.parents and tmp_path != REPO_ROOT, (
        "Refusing to run destructive (c3) inside the real cairn repo tree; "
        f"tmp_path={tmp_path} REPO_ROOT={REPO_ROOT}"
    )

    fixture = _build_consumer_fixture(tmp_path, symlink_target=".", skill_runs=[])
    result = _run(fixture, env_overrides={"CAIRN_MIGRATE_BREAK_INV011": "1"})

    assert result.returncode == 0, (
        f"CAIRN_MIGRATE_BREAK_INV011=1 should proceed with exit 0; "
        f"got {result.returncode};\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    # Multi-line stderr block (>=3 non-empty lines) with all three tokens.
    nonempty_stderr_lines = [ln for ln in result.stderr.splitlines() if ln.strip()]
    assert len(nonempty_stderr_lines) >= 3, (
        f"BREAK_INV011 stderr should be a multi-line block (>=3 lines); "
        f"got {len(nonempty_stderr_lines)} lines:\n{result.stderr}"
    )
    for token in ("INV-011", "D8", "docs/ARCHITECTURE.md:91"):
        assert token in result.stderr, (
            f"BREAK_INV011 stderr missing token {token!r}; stderr={result.stderr}"
        )

    # Self-symlink destroyed (this is the destructive override semantics).
    assert not (fixture / ".slice-system").is_symlink(), (
        ".slice-system symlink should be unlinked under BREAK_INV011 override"
    )

    # Settings.json filtered.
    filtered = _read_settings(fixture)
    assert "$CLAUDE_PROJECT_DIR/.slice-system/" not in filtered, (
        "settings.json still contains symlink-anchored hook entries"
    )

    # Banner printed (rest of the migration runs).
    assert "/plugin marketplace add https://github.com/firaaz/cairn" in result.stdout, (
        f"stdout banner missing /plugin marketplace add; stdout={result.stdout}"
    )


# ---------------------------------------------------------------------------
# (d) Force-mode quiescence override
# ---------------------------------------------------------------------------


def test_d_force_mode_quiescence_override(tmp_path):
    """CAIRN_MIGRATE_FORCE=1 + non-quiesced skill-run -> exit 0, Pre-mortem
    Scenario 6 warning on stderr, symlink unlinked, settings filtered."""
    _require_script()
    fixture = _build_consumer_fixture(
        tmp_path,
        symlink_target="cairn-checkout",
        skill_runs=[("in-flight-feature-id", False)],
    )
    result = _run(fixture, env_overrides={"CAIRN_MIGRATE_FORCE": "1"})

    assert result.returncode == 0, (
        f"FORCE=1 should override exit 2 -> exit 0; got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    # Pre-mortem Scenario 6 warning. Accept either explicit citation or
    # the anchor token — both legible from shell history.
    stderr_lower = result.stderr.lower()
    assert ("scenario 6" in stderr_lower) or (
        "pre-mortem scenario 6" in stderr_lower
    ), f"stderr missing Pre-mortem Scenario 6 citation; stderr={result.stderr}"
    # And the orphan-state risk should be loud.
    assert ("orphan" in stderr_lower) or ("in-flight" in stderr_lower), (
        f"stderr missing orphan/in-flight warning; stderr={result.stderr}"
    )

    # State changed (unlinked + filtered).
    assert not (fixture / ".slice-system").is_symlink()
    filtered = _read_settings(fixture)
    assert "$CLAUDE_PROJECT_DIR/.slice-system/" not in filtered


# ---------------------------------------------------------------------------
# (e) shellcheck POSIX-strict (graceful skip if missing)
# ---------------------------------------------------------------------------


def test_e_shellcheck_zero_warnings():
    """shellcheck on the script reports zero warnings. Skips gracefully if
    `shellcheck` is not on PATH (Phase 4 sweep-notes records ran-vs-skipped).
    """
    if shutil.which("shellcheck") is None:
        pytest.skip("shellcheck not on PATH")
    _require_script()

    # Phase 2 picks the form most likely to match the script's actual shebang.
    # Intent §Verification (e) names `shellcheck scripts/migrate_from_symlink.sh`
    # for a `#!/bin/bash` shebang + `# shellcheck shell=bash` directive.
    result = subprocess.run(
        ["shellcheck", str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"shellcheck reported warnings (rc={result.returncode});\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


# ---------------------------------------------------------------------------
# (f) Dash runtime — re-run (a)/(b)/(c1)/(d) under dash
# ---------------------------------------------------------------------------


def _resolve_dash() -> str | None:
    for candidate in ("/usr/bin/dash", "/bin/dash"):
        if Path(candidate).exists():
            return candidate
    return shutil.which("dash")


def test_f_dash_runtime_a_happy_path(tmp_path):
    dash = _resolve_dash()
    if dash is None:
        pytest.skip("dash not on PATH")
    _require_script()

    fixture = _build_consumer_fixture(
        tmp_path, symlink_target="cairn-checkout", skill_runs=[]
    )
    result = _run(fixture, interpreter=dash)
    assert result.returncode == 0, (
        f"dash (a) expected exit 0; got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert not (fixture / ".slice-system").is_symlink()
    assert "$CLAUDE_PROJECT_DIR/.slice-system/" not in _read_settings(fixture)
    assert "/plugin install cairn@cairn-marketplace" in result.stdout


def test_f_dash_runtime_b_in_flight(tmp_path):
    dash = _resolve_dash()
    if dash is None:
        pytest.skip("dash not on PATH")
    _require_script()

    fixture = _build_consumer_fixture(
        tmp_path,
        symlink_target="cairn-checkout",
        skill_runs=[("in-flight-feature-id", False)],
    )
    result = _run(fixture, interpreter=dash)
    assert result.returncode == 2, (
        f"dash (b) expected exit 2; got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "in-flight skill-run" in result.stderr
    assert "in-flight-feature-id" in result.stderr


def test_f_dash_runtime_c1_cairn_self(tmp_path):
    dash = _resolve_dash()
    if dash is None:
        pytest.skip("dash not on PATH")
    _require_script()

    fixture = _build_consumer_fixture(tmp_path, symlink_target=".", skill_runs=[])
    result = _run(fixture, interpreter=dash)
    assert result.returncode == 3, (
        f"dash (c1) expected exit 3; got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    for token in (
        "INV-011",
        "D8",
        "docs/ARCHITECTURE.md:91",
        "CAIRN_MIGRATE_BREAK_INV011",
    ):
        assert token in result.stderr, (
            f"dash (c1) stderr missing {token!r}; stderr={result.stderr}"
        )


def test_f_dash_runtime_d_force_quiescence_override(tmp_path):
    dash = _resolve_dash()
    if dash is None:
        pytest.skip("dash not on PATH")
    _require_script()

    fixture = _build_consumer_fixture(
        tmp_path,
        symlink_target="cairn-checkout",
        skill_runs=[("in-flight-feature-id", False)],
    )
    result = _run(fixture, env_overrides={"CAIRN_MIGRATE_FORCE": "1"}, interpreter=dash)
    assert result.returncode == 0, (
        f"dash (d) expected exit 0 under FORCE; got {result.returncode};\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    stderr_lower = result.stderr.lower()
    assert ("scenario 6" in stderr_lower) or ("pre-mortem scenario 6" in stderr_lower)
    assert not (fixture / ".slice-system").is_symlink()
