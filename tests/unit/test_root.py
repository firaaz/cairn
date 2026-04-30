"""Phase 2 RED tests for slice substrate/root-resolver — scripts/_root.project_root contract.

Asserts intent.md §Specification:
  - Resolution precedence: CLAUDE_PROJECT_DIR -> git rev-parse --show-toplevel -> RuntimeError.
  - No __file__-relative resolution (the .slice-system -> . symlink canonicalizes wrong; L-017).
  - RuntimeError carries a loud, actionable message naming both attempted mechanisms.

These tests target the *contract*, not a mechanism. Any Phase-3 implementation
that satisfies the precedence chain and the symlink-trap regression passes.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Import target: scripts/_root.py exposes project_root().
# pyproject.toml [tool.pytest.ini_options] pythonpath = ["scripts"], so this
# resolves to scripts/_root.py at top-level.
# ---------------------------------------------------------------------------


def _import_root_module():
    """Import scripts/_root.py freshly; fail loudly if missing."""
    if "_root" in sys.modules:
        del sys.modules["_root"]
    import _root  # noqa: F401  -- import for side effect; returned below

    return sys.modules["_root"]


# ---------------------------------------------------------------------------
# Precedence 1: CLAUDE_PROJECT_DIR env var
# ---------------------------------------------------------------------------


def test_project_root_returns_env_var_when_set(tmp_path, monkeypatch):
    """CLAUDE_PROJECT_DIR set -> project_root() returns Path(value).resolve()."""
    target = tmp_path / "consumer"
    target.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(target))

    mod = _import_root_module()
    result = mod.project_root()

    assert isinstance(result, Path)
    assert result == target.resolve()


def test_project_root_resolves_relative_env_var(tmp_path, monkeypatch):
    """A relative CLAUDE_PROJECT_DIR is resolved to an absolute path."""
    target = tmp_path / "consumer"
    target.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "consumer")

    mod = _import_root_module()
    result = mod.project_root()

    assert result.is_absolute()
    assert result == target.resolve()


def test_project_root_ignores_empty_env_var(tmp_path, monkeypatch):
    """Empty CLAUDE_PROJECT_DIR string must not short-circuit precedence.

    Intent §Specification: "if set and non-empty -> return Path(value).resolve()".
    Empty value falls through to git rev-parse.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    monkeypatch.chdir(repo)

    mod = _import_root_module()
    result = mod.project_root()

    assert result == repo.resolve()


# ---------------------------------------------------------------------------
# Precedence 2: git rev-parse --show-toplevel
# ---------------------------------------------------------------------------


def test_project_root_falls_back_to_git_toplevel(tmp_path, monkeypatch):
    """No env var -> git rev-parse --show-toplevel from cwd."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(repo)

    mod = _import_root_module()
    result = mod.project_root()

    assert result == repo.resolve()


def test_project_root_git_toplevel_from_subdirectory(tmp_path, monkeypatch):
    """git rev-parse must climb to the toplevel even when cwd is a subdir."""
    repo = tmp_path / "repo"
    deep = repo / "a" / "b" / "c"
    deep.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(deep)

    mod = _import_root_module()
    result = mod.project_root()

    assert result == repo.resolve()


# ---------------------------------------------------------------------------
# Precedence 3: loud RuntimeError when neither available
# ---------------------------------------------------------------------------


def test_project_root_raises_runtime_error_when_no_env_and_no_git(
    tmp_path, monkeypatch
):
    """Neither env var nor git toplevel -> RuntimeError naming both mechanisms."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    not_a_repo = tmp_path / "bare"
    not_a_repo.mkdir()
    monkeypatch.chdir(not_a_repo)

    mod = _import_root_module()

    with pytest.raises(RuntimeError) as excinfo:
        mod.project_root()

    msg = str(excinfo.value)
    assert "CLAUDE_PROJECT_DIR" in msg, (
        "RuntimeError must name CLAUDE_PROJECT_DIR (intent §Specification: 'loud, "
        f"actionable message naming both env-var and git-toplevel paths'). got: {msg!r}"
    )
    # Mention git toplevel mechanism
    assert "git" in msg.lower(), (
        f"RuntimeError must name the git rev-parse mechanism, got: {msg!r}"
    )


# ---------------------------------------------------------------------------
# Symlink trap regression — L-017
# ---------------------------------------------------------------------------


def test_project_root_does_not_use_file_dunder_resolution(tmp_path, monkeypatch):
    """Even when imported from a different install location, project_root()
    must reflect the *consumer's* git toplevel, not scripts/_root.py's own
    canonicalized __file__ location.

    This is the core regression for L-017: the .slice-system -> . symlink
    means Path(__file__).resolve() in the consumer points back to cairn's
    own substrate.
    """
    repo = tmp_path / "consumer"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(repo)

    mod = _import_root_module()
    result = mod.project_root()

    cairn_install = Path(__file__).resolve().parent.parent.parent
    assert result == repo.resolve(), (
        "project_root() must resolve to the cwd's git toplevel, not via __file__. "
        f"got {result}, expected {repo.resolve()}, cairn install at {cairn_install}"
    )
    assert result != cairn_install, (
        "project_root() returned cairn's own install — __file__-resolution leak "
        "(L-017 regression)"
    )


def test_project_root_through_slice_system_symlink(tmp_path, monkeypatch):
    """When cwd is inside `.slice-system/` (symlink to '.'), project_root()
    must still return the real repo root.

    Intent §Verification 4: "project_root() invoked from a cwd inside
    .slice-system/ (tmp_path symlink) returns real toplevel, not the
    symlinked view."
    """
    repo = tmp_path / "consumer"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    slice_system = repo / ".slice-system"
    slice_system.symlink_to(".", target_is_directory=True)

    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(slice_system)

    mod = _import_root_module()
    result = mod.project_root()

    assert result == repo.resolve(), (
        f"project_root() returned {result}, expected real repo {repo.resolve()}; "
        "symlink-traversal canonicalization leak"
    )


# ---------------------------------------------------------------------------
# Module hygiene — banned constructs in scripts/_root.py source
# ---------------------------------------------------------------------------


def test_project_root_function_does_not_use_file_dunder_for_root_inference():
    """Intent §Specification bans __file__-based resolution within project_root().
    The .slice-system symlink would canonicalize wrong (L-017).

    Note: package_root() in the same module legitimately uses __file__ — that's
    package-location inference, a different concept (see module docstring's
    two-roots disambiguation). This test scopes the ban to project_root()'s
    function body via AST, not the whole module.
    """
    import ast

    cairn_root = Path(__file__).resolve().parent.parent.parent
    src = cairn_root / "scripts" / "_root.py"
    assert src.exists(), (
        f"scripts/_root.py missing — slice substrate/root-resolver intent "
        f"requires this module at {src}"
    )

    tree = ast.parse(src.read_text())
    project_root_fn = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "project_root"
        ),
        None,
    )
    assert project_root_fn is not None, "project_root() function missing from _root.py"

    file_dunder_uses = [
        node.lineno
        for node in ast.walk(project_root_fn)
        if isinstance(node, ast.Name) and node.id == "__file__"
    ]
    assert not file_dunder_uses, (
        f"project_root() body uses __file__ at lines {file_dunder_uses} — banned "
        "for project-root inference per intent §Specification (L-017 root cause). "
        "If you need package-location inference, use package_root() instead."
    )


def test_root_module_exports_project_root():
    """Public surface: scripts/_root.project_root must be a callable."""
    mod = _import_root_module()
    assert hasattr(mod, "project_root")
    assert callable(mod.project_root)


# ---------------------------------------------------------------------------
# Subprocess cwd discipline — _root.py's own git call
# ---------------------------------------------------------------------------


def test_project_root_git_call_does_not_inherit_alien_cwd(tmp_path, monkeypatch):
    """Subprocess git rev-parse must run in the resolution-context cwd
    (intent: cwd=os.getcwd()), not silently accept the parent process's
    leftover cwd in a way that leaks across calls.

    Concretely: if cwd is set to a non-git directory and CLAUDE_PROJECT_DIR
    is unset, project_root() must raise — *not* return some other repo's
    toplevel from process-wide ambient state.
    """
    not_a_repo = tmp_path / "elsewhere"
    not_a_repo.mkdir()
    monkeypatch.chdir(not_a_repo)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

    mod = _import_root_module()
    with pytest.raises(RuntimeError):
        mod.project_root()
