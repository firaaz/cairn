"""Phase 2 RED tests for slice substrate/root-resolver — path-discipline lint gate.

Intent §Specification §"Lint gate":
  Extend arch-validate (or a sibling check on the same CI path) with a
  regex-or-AST scan that fails when:
    - Path("\\.claude literal appears outside scripts/_root.py and tests/.
    - Path.cwd() appears in any scripts/ or mcp_servers/ module.
    - subprocess.run([..., "git", ...]) appears without a cwd= kwarg.

  Failure message names the offending file:line and points at
  scripts/_root.py:project_root.

Phase-2 design call (intent §Risks): the lint gate lives at
``scripts/lint_paths.py`` (matching the §Risks "scripts/lint_paths.py
(purer)" option) and is invoked via ``python -m lint_paths`` (top-level
because ``pyproject.toml`` puts ``scripts/`` on ``pythonpath``). Phase 3
may also wire it into ``scripts/validate_architecture.py`` as long as
the module-level entrypoint exists and behaves per these tests.

Each test invokes the gate against a synthetic project tree to keep the
test hermetic and resilient to background cairn migrations.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
LINT_GATE_PATH = CAIRN_ROOT / "scripts" / "lint_paths.py"


# ---------------------------------------------------------------------------
# Helpers — invoke the lint gate as a subprocess, scoped to a target tree
# ---------------------------------------------------------------------------


def _invoke_gate(
    target_root: Path, env_extra: dict | None = None
) -> subprocess.CompletedProcess:
    """Run the lint gate against `target_root` (treated as a project root).

    Strategy: run ``python -m lint_paths`` with cwd=target_root and
    CLAUDE_PROJECT_DIR pointing at target_root. The gate must scan
    ``scripts/`` and ``mcp_servers/`` of that root.
    """
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(target_root)
    # Make scripts/lint_paths.py importable as the top-level `lint_paths`
    # module by prepending cairn's scripts dir to PYTHONPATH.
    env["PYTHONPATH"] = (
        str(CAIRN_ROOT / "scripts") + os.pathsep + env.get("PYTHONPATH", "")
    )
    if env_extra:
        env.update(env_extra)

    return subprocess.run(
        [sys.executable, "-m", "lint_paths"],
        cwd=target_root,
        env=env,
        capture_output=True,
        text=True,
    )


def _make_tree(
    root: Path,
    files: dict[str, str],
) -> None:
    """Materialize a synthetic project tree under root from {relpath: contents}."""
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body).lstrip("\n"))


# ---------------------------------------------------------------------------
# Existence — the lint gate module ships in the slice
# ---------------------------------------------------------------------------


def test_lint_gate_module_exists():
    """scripts/lint_paths.py is the Phase-2-chosen home for the gate."""
    assert LINT_GATE_PATH.exists(), (
        f"scripts/lint_paths.py missing at {LINT_GATE_PATH}; intent §Lint gate "
        "requires a lint module wired into the same CI path as arch-validate."
    )


# ---------------------------------------------------------------------------
# Clean trees — gate exits 0
# ---------------------------------------------------------------------------


def test_gate_passes_on_clean_tree(tmp_path):
    """Empty scripts/ and mcp_servers/ — no violations, exit 0."""
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "scripts/clean.py": """
                from pathlib import Path
                import subprocess
                def f(root: Path) -> None:
                    subprocess.run(["git", "status"], cwd=root, check=True)
            """,
            "mcp_servers/clean.py": "x = 1\n",
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode == 0, (
        f"gate failed on clean tree: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "blanket post-migration check — RED until orchestrator-paths + "
        "mcp-server clusters land + scope-overflow targets "
        "(integration_gate.py, validate_architecture.py, dogfood_evaluate.py) "
        "are migrated; pending follow-ups under firaaz/cairn#3"
    ),
)
def test_gate_passes_on_post_migration_cairn_tree():
    """Intent §Verification 2: 'lint gate exits 0 against post-migration tree'.

    Run the real cairn checkout through the gate. After Phase 3 migration,
    this must pass. (RED until migration ships.)
    """
    result = _invoke_gate(CAIRN_ROOT)
    assert result.returncode == 0, (
        "lint gate must exit 0 against the post-migration cairn tree.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Violation 1: Path(".claude/...") literal in scripts/ outside _root.py
# ---------------------------------------------------------------------------


def test_gate_flags_dotclaude_literal_in_scripts(tmp_path):
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "scripts/leaky.py": """
                from pathlib import Path
                X = Path(".claude/foo")
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode != 0, "gate must flag Path('.claude/...') literal"
    combined = result.stdout + result.stderr
    assert "scripts/leaky.py" in combined, (
        f"failure must name offending file. got: {combined!r}"
    )
    # Intent: "Failure message names the offending file:line"
    assert ":2" in combined or "line 2" in combined or "L2" in combined, (
        f"failure must name offending line. got: {combined!r}"
    )
    # Intent: "and points at scripts/_root.py:project_root."
    assert "project_root" in combined or "_root.py" in combined, (
        f"failure must point at scripts/_root.py:project_root as remediation. "
        f"got: {combined!r}"
    )


def test_gate_flags_dotclaude_literal_in_mcp_servers(tmp_path):
    _make_tree(
        tmp_path,
        {
            "mcp_servers/__init__.py": "",
            "mcp_servers/leaky.py": """
                from pathlib import Path
                P = Path(".claude/cairn_query/index.kz")
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode != 0
    assert "mcp_servers/leaky.py" in (result.stdout + result.stderr)


def test_gate_exempts_root_module_from_dotclaude_ban(tmp_path):
    """scripts/_root.py is the canonical home of the literal — exempt by intent."""
    _make_tree(
        tmp_path,
        {
            "scripts/_root.py": """
                from pathlib import Path
                # The canonical anchor; allowed here only.
                CLAUDE_DIR = Path(".claude")
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode == 0, (
        f"_root.py must be exempt from the .claude-literal ban.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_gate_exempts_tests_directory_from_dotclaude_ban(tmp_path):
    """Intent §Specification: 'Tests under tests/ are exempt'."""
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "tests/unit/test_thing.py": """
                from pathlib import Path
                p = Path(".claude/whatever")
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode == 0, (
        f"tests/ must be exempt from the .claude-literal ban.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Violation 2: Path.cwd() in scripts/ or mcp_servers/
# ---------------------------------------------------------------------------


def test_gate_flags_path_cwd_in_scripts(tmp_path):
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "scripts/cwd_leak.py": """
                from pathlib import Path
                def root() -> Path:
                    return Path.cwd()
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode != 0, "gate must flag Path.cwd() in scripts/"
    combined = result.stdout + result.stderr
    assert "scripts/cwd_leak.py" in combined
    assert "Path.cwd" in combined or "cwd" in combined.lower()


def test_gate_flags_path_cwd_in_mcp_servers(tmp_path):
    _make_tree(
        tmp_path,
        {
            "mcp_servers/__init__.py": "",
            "mcp_servers/cwd_leak.py": """
                from pathlib import Path
                X = Path.cwd()
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode != 0


def test_gate_does_not_flag_path_cwd_in_tests_dir(tmp_path):
    """tests/ exemption applies to the cwd ban as well."""
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "tests/unit/test_x.py": """
                from pathlib import Path
                p = Path.cwd()
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Violation 3: subprocess.run([..., "git", ...]) without cwd=
# ---------------------------------------------------------------------------


def test_gate_flags_git_subprocess_without_cwd(tmp_path):
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "scripts/leaky_git.py": """
                import subprocess
                def head() -> str:
                    return subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True, text=True, check=True,
                    ).stdout
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode != 0, (
        "gate must flag subprocess.run(['git', ...]) without cwd= kwarg"
    )
    combined = result.stdout + result.stderr
    assert "scripts/leaky_git.py" in combined


def test_gate_accepts_git_subprocess_with_cwd(tmp_path):
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "scripts/clean_git.py": """
                import subprocess
                from pathlib import Path
                def head(root: Path) -> str:
                    return subprocess.run(
                        ["git", "rev-parse", "HEAD"], cwd=root,
                        capture_output=True, text=True, check=True,
                    ).stdout
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode == 0, (
        f"gate must accept git subprocess with cwd=. "
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Failure-message contract
# ---------------------------------------------------------------------------


def test_gate_failure_names_remediation_anchor(tmp_path):
    """Intent: failure message 'points at scripts/_root.py:project_root'.

    The remediation anchor must appear at least once in the gate's output
    when any violation is detected, so that a developer reading the gate
    output is told exactly which module to delegate to.
    """
    _make_tree(
        tmp_path,
        {
            "scripts/__init__.py": "",
            "scripts/leaky.py": """
                from pathlib import Path
                X = Path(".claude/whatever")
            """,
        },
    )
    result = _invoke_gate(tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "_root" in combined and "project_root" in combined, (
        "gate failure must name scripts/_root.py:project_root as the remediation "
        f"target. got: {combined!r}"
    )
