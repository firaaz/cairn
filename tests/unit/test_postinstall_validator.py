"""RED tests for cairn-m5-f1-packaging A9, A10 — post-install validator (D5).

Pins:
- A9 — Missing-dep checks (`jq`, `ruff`) emit stderr warnings naming the
  dep and the no-op'd hook(s); validator does NOT exit non-zero on dep
  absence alone.
- A10 — Positive enforcement is fatal:
  - basic case: tmp `CLAUDE_PROJECT_DIR` + `mode: operator` envelope whose
    `paths` does not cover file F; validator invokes role_guard against F;
    asserts deny landed.
  - **plugin-cache simulation canary** (operator-confirmed amendment at
    SHA e18dfd7): copy `checks/role_guard.py` to a tmp dir DIFFERENT FROM
    `CLAUDE_PROJECT_DIR`, invoke the COPY via subprocess, and verify
    enforcement still anchors via env (not the copy's `__file__`). This is
    the canary against any future `__file__`-anchoring regression.
  - silent-pass canary: stub a "broken" role_guard that exits 0 even for
    out-of-envelope writes; validator MUST exit 1 with stderr message.

Module import follows project convention (pyproject.toml `pythonpath = ["scripts"]`):
`from postinstall_validate import ...` — NOT `from scripts.postinstall_validate import ...`.

Tests must FAIL at HEAD because `scripts/postinstall_validate.py` does not exist.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = REPO_ROOT / "scripts" / "postinstall_validate.py"
ROLE_GUARD = REPO_ROOT / "checks" / "role_guard.py"


def _require_validator() -> None:
    if not VALIDATOR.is_file():
        pytest.fail(f"postinstall_validate.py not found at {VALIDATOR}")


def _import_validator():
    """Bare-module import per pythonpath = ["scripts"]."""
    _require_validator()
    import importlib

    if "postinstall_validate" in sys.modules:
        del sys.modules["postinstall_validate"]
    return importlib.import_module("postinstall_validate")


# ---------------------------------------------------------------------------
# A9 — Dep-check warnings are non-fatal
# ---------------------------------------------------------------------------


def _run_validator(
    env: dict | None = None,
    plugin_root: Path | None = None,
    project_dir: Path | None = None,
) -> subprocess.CompletedProcess:
    """Invoke validator as a subprocess with controlled env."""
    _require_validator()
    full_env = dict(os.environ) if env is None else dict(env)
    if plugin_root is not None:
        full_env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    if project_dir is not None:
        full_env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        capture_output=True,
        text=True,
        env=full_env,
    )


def test_a9_validator_warns_on_missing_jq(tmp_path):
    """With PATH stripped of jq, validator emits a 'jq' warning on stderr but
    still exits 0 (or at minimum: dep-check alone does not flip it to non-zero
    when enforcement self-test passes).

    NB: We pin only the WARNING-naming + non-fatal contract here. The
    enforcement self-test must still pass for the validator to exit 0; we
    point CLAUDE_PROJECT_DIR at a tmp dir with a properly-configured envelope
    so enforcement passes and only the dep warning fires.
    """
    # Build a sandboxed env with no jq/ruff on PATH but python still resolvable.
    sandbox_path = tmp_path / "bin"
    sandbox_path.mkdir()
    # Symlink only python; nothing else.
    py_link = sandbox_path / "python3"
    py_link.symlink_to(sys.executable)

    env = {
        "PATH": str(sandbox_path),
        "HOME": str(tmp_path),
    }
    # Set up a working enforcement target so the self-test passes.
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    proc = _run_validator(
        env=env,
        plugin_root=REPO_ROOT,
        project_dir=project_dir,
    )
    # Whatever the validator's overall exit, it must not be non-zero SOLELY
    # because of the dep miss — so the stderr must name jq + warn-style word,
    # not a fatal error that says "missing jq → abort".
    assert "jq" in proc.stderr, (
        f"A9: validator stderr must mention missing jq; got stderr={proc.stderr!r}"
    )
    assert (
        "warn" in proc.stderr.lower()
        or "warning" in proc.stderr.lower()
        or "no-op" in proc.stderr.lower()
    ), (
        f"A9: jq miss must be reported as a warning, not a fatal error; "
        f"stderr={proc.stderr!r}"
    )


def test_a9_validator_warns_on_missing_ruff(tmp_path):
    sandbox_path = tmp_path / "bin"
    sandbox_path.mkdir()
    py_link = sandbox_path / "python3"
    py_link.symlink_to(sys.executable)

    env = {
        "PATH": str(sandbox_path),
        "HOME": str(tmp_path),
    }
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    proc = _run_validator(
        env=env,
        plugin_root=REPO_ROOT,
        project_dir=project_dir,
    )
    assert "ruff" in proc.stderr, (
        f"A9: validator stderr must mention missing ruff; got stderr={proc.stderr!r}"
    )
    assert (
        "warn" in proc.stderr.lower()
        or "warning" in proc.stderr.lower()
        or "no-op" in proc.stderr.lower()
    ), f"A9: ruff miss must be reported as a warning; stderr={proc.stderr!r}"


def test_a9_dep_miss_alone_does_not_set_fatal_exit(tmp_path):
    """With both jq and ruff absent but enforcement working, validator exits 0
    (or at minimum: the validator's check_dep function returns False without
    sys.exit). We assert via direct module call to isolate from the
    enforcement self-test."""
    rg = _import_validator()
    assert hasattr(rg, "check_dep"), (
        "A9: validator must expose check_dep(name) function"
    )
    # check_dep on a known-missing name returns falsy AND does not exit.
    result = rg.check_dep("definitely-not-installed-xyzzy-123")
    assert result is False or result is None, (
        f"A9: check_dep on missing dep must return falsy; got {result!r}"
    )


# ---------------------------------------------------------------------------
# A10 — Positive enforcement is FATAL (basic case)
# ---------------------------------------------------------------------------


def _write_operator_envelope(project_dir: Path, allowed_pattern: str) -> Path:
    """Create $project_dir/.claude/active-envelope.yaml with mode: operator."""
    claude = project_dir / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    envelope = claude / "active-envelope.yaml"
    envelope.write_text(
        textwrap.dedent(
            f"""\
            mode: operator
            paths:
              - {allowed_pattern}
            """
        )
    )
    return envelope


def test_a10_basic_positive_enforcement_passes(tmp_path):
    """Basic A10: tmp CLAUDE_PROJECT_DIR; envelope `paths: ["^docs/"]`; tool
    target `scripts/foo.py` is OUTSIDE envelope → role_guard exits 1 →
    validator's enforcement self-test sees deny → validator returns success
    for the enforcement check.
    """
    rg = _import_validator()
    assert hasattr(rg, "check_envelope_enforcement"), (
        "A10: validator must expose check_envelope_enforcement(project_dir)"
    )
    project_dir = tmp_path / "consumer"
    project_dir.mkdir()
    # Note: the validator itself owns writing the envelope per its own
    # contract. Some implementations may wrap envelope write inside the call;
    # we assert the contract: function returns truthy iff a real deny landed.
    # The validator decides the test target path internally; we only pin the
    # observable: a passing enforcement self-test means True.
    result = rg.check_envelope_enforcement(project_dir)
    assert result is True, (
        f"A10: check_envelope_enforcement must return True when a real "
        f"deny was observed against an out-of-envelope write; got {result!r}"
    )


def test_a10_validator_fails_loud_on_silent_pass(tmp_path):
    """Silent-pass canary: stub a broken role_guard that exits 0 unconditionally.
    The validator must exit non-zero with stderr saying enforcement did not
    deny / installation is not safe.
    """
    _require_validator()
    # Build a fake plugin-root with a broken role_guard.
    fake_plugin = tmp_path / "fake-plugin"
    (fake_plugin / "checks").mkdir(parents=True)
    fake_role_guard = fake_plugin / "checks" / "role_guard.py"
    fake_role_guard.write_text(
        textwrap.dedent(
            """\
            import sys
            # Broken role_guard: exits 0 unconditionally — simulates the
            # pre-D5 fail-open under plugin-cache invocation.
            sys.exit(0)
            """
        )
    )

    project_dir = tmp_path / "consumer"
    project_dir.mkdir()

    proc = _run_validator(
        plugin_root=fake_plugin,
        project_dir=project_dir,
    )
    assert proc.returncode != 0, (
        f"A10 (silent-pass canary): validator MUST exit non-zero when "
        f"enforcement silently passes an out-of-envelope write; got rc=0\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    stderr_low = proc.stderr.lower()
    # Accept any of these keywords — the contract is "fail loud", not exact
    # wording. intent.md A10 says: "envelope enforcement did not deny ... not safe".
    assert any(
        kw in stderr_low
        for kw in ("not safe", "did not deny", "enforcement", "self-test failed")
    ), (
        f"A10 (silent-pass canary): validator stderr must explain that "
        f"enforcement self-test failed; got stderr={proc.stderr!r}"
    )


# ---------------------------------------------------------------------------
# A10 — Plugin-cache simulation canary (operator-confirmed amendment)
# ---------------------------------------------------------------------------


def test_a10_plugin_cache_simulation_role_guard_anchors_via_env(tmp_path):
    """Plugin-cache simulation: copy `checks/role_guard.py` to a tmp directory
    DIFFERENT from the test's CLAUDE_PROJECT_DIR. Invoke the COPY via
    subprocess. Verify enforcement still anchors correctly via
    CLAUDE_PROJECT_DIR (NOT the copy's `__file__` path).

    This is the canary that catches any future regression where someone
    re-introduces `__file__`-anchored CAIRN_ROOT — the copy's `__file__`
    would point at the cache and silently fail-open under operator envelope.
    """
    if not ROLE_GUARD.is_file():
        pytest.fail(f"role_guard.py not found at {ROLE_GUARD}")

    # Plugin cache: a separate directory the copy lives in.
    plugin_cache = tmp_path / "plugin-cache" / "checks"
    plugin_cache.mkdir(parents=True)
    copy_path = plugin_cache / "role_guard.py"
    shutil.copy2(ROLE_GUARD, copy_path)

    # Project dir is DIFFERENT from the plugin cache.
    project_dir = tmp_path / "consumer-project"
    project_dir.mkdir()

    # Write an envelope under project_dir that does NOT cover scripts/foo.py.
    _write_operator_envelope(project_dir, allowed_pattern="^docs/")

    # Confirm the cache directory has NO envelope file (it shouldn't, by
    # construction — we only put one under project_dir).
    assert not (plugin_cache.parent / ".claude" / "active-envelope.yaml").exists(), (
        "test setup invariant: plugin cache must not contain an envelope"
    )

    tool_input = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "scripts/foo.py",
            "old_string": "x",
            "new_string": "y",
        },
    }
    env = dict(os.environ)
    env.pop("AGENT_ROLE", None)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)

    proc = subprocess.run(
        [sys.executable, str(copy_path)],
        input=json.dumps(tool_input),
        text=True,
        capture_output=True,
        env=env,
    )
    # The COPY must read the envelope from $CLAUDE_PROJECT_DIR (project_dir),
    # see scripts/foo.py is out-of-envelope, and DENY (exit 1).
    # If anchoring is broken (uses __file__), the copy looks for the envelope
    # under plugin_cache/.claude/active-envelope.yaml, sees nothing, and
    # silently fail-opens with exit 0 — the regression we are pinning against.
    assert proc.returncode == 1, (
        f"A10 (plugin-cache canary): role_guard.py invoked from a copy at "
        f"{copy_path} with $CLAUDE_PROJECT_DIR={project_dir} must DENY an "
        f"out-of-envelope write (exit 1). Got rc={proc.returncode}.\n"
        f"This indicates CAIRN_ROOT is anchored on __file__, not on "
        f"$CLAUDE_PROJECT_DIR — the D5 regression.\n"
        f"stderr={proc.stderr!r}"
    )
    assert proc.stderr.strip(), (
        "A10 (plugin-cache canary): denial must emit non-empty stderr; "
        "got empty stderr"
    )
