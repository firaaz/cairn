"""RED tests for M3 fix: INV-001 walker accepts scoped Conventional Commits.

Tracks the M2 dogfood finding: cairn-shrink branch uses scoped CC form
(`feat(m2-dogfood-extract-invariant-ids):`) which the prior `subject.startswith(prefix)`
match rejected because the registry keys are bare prefixes (`feat:`).

Public surface (existing): scripts/validate_architecture._run_git_log_walk_assertion
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_REL = Path(".claude/pipeline-substrate-registry.yaml")


def _git(repo: Path, *args: str) -> str:
    out = subprocess.check_output(
        ["git", *args],
        cwd=str(repo),
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@x",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@x",
        },
    )
    return out.strip()


def _commit(repo: Path, subject: str, touch: list[str]) -> str:
    for rel in touch:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("x\n")
        else:
            path.write_text(path.read_text() + "x\n")
        _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", subject, "--allow-empty")
    return _git(repo, "rev-parse", "HEAD")


def _init_repo_with_registry(tmp_path: Path) -> Path:
    """Init a synthetic git repo seeded with the inline fallback prefix list.

    Registry file retired per pipeline-substrate-naming-superseded (E6);
    fixture uses _FALLBACK_REGISTRY so the validator has a known prefix set.
    """
    from validate_architecture import _FALLBACK_REGISTRY

    import yaml

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@x")
    _git(repo, "config", "user.name", "t")
    dst = repo / REGISTRY_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        yaml.dump(
            {"entries": list(_FALLBACK_REGISTRY.values())},
            default_flow_style=False,
        )
    )
    _git(repo, "add", str(REGISTRY_REL))
    _git(repo, "commit", "-q", "-m", "bootstrap: seed registry for fixture")
    return repo


def test_scoped_feat_commit_passes(tmp_path):
    """`feat(m3-foo): ...` must map to bare type `feat:` and pass-through."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "feat(m3-foo): add a thing", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"Scoped feat must pass-through. Got: {result!r}"


def test_scoped_test_commit_passes(tmp_path):
    """`test(m3-foo): ...` must map to bare type `test:` and pass-through."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "test(m3-foo): RED tests", touch=["tests/unit/test_x.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"Scoped test must pass-through. Got: {result!r}"


def test_scoped_chore_commit_passes(tmp_path):
    """`chore(m3-foo): ...` must map to bare type `chore:` and pass-through."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "chore(m3-foo): housekeeping", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"Scoped chore must pass-through. Got: {result!r}"


def test_scoped_fix_commit_pass_through_not_sweep_constrained(tmp_path):
    """`fix(m3-foo): ...` is feature-level fix, NOT sweep-constrained.

    Bare `fix:` still routes to the sweep-only verifier (preserving the
    integration-sweep semantic). Scoped `fix(<scope>):` is a developer commit
    and uses pass-through.
    """
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "fix(m3-foo): correct a bug", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, (
        f"Scoped fix must pass-through (not sweep-constrained). Got: {result!r}"
    )


def test_bare_fix_passes_unconstrained(tmp_path):
    """`fix: ...` is an ordinary defect-commit prefix since the sweep
    apparatus retired (carrier-hierarchy-and-process-diet)."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "fix: ordinary defect fix", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"fix: must pass unconstrained; got {result!r}"


def test_bare_sweep_still_constrained(tmp_path):
    """Bare `sweep: ...` must still require both sweep-results/ and sweep.yaml."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "sweep: bad", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is not None, "Bare sweep without required paths must still fail"
    assert bad_sha[:8] in result


def test_design_prefix_registered_passes(tmp_path):
    """`design: add cairn-shrink design doc` must pass (registry entry added)."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "design: add foo design", touch=["docs/plans/x.md"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"`design:` prefix must pass-through. Got: {result!r}"


def test_plan_prefix_registered_passes(tmp_path):
    """`plan(m2): dispatch skill plan` must pass (registry entry added)."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "plan(m2): dispatch skill", touch=["docs/plans/y.md"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is None, f"`plan:` prefix must pass-through. Got: {result!r}"


def test_unknown_scoped_prefix_still_rejected(tmp_path):
    """A `wibble(m3): ...` prefix that doesn't map to a registered bare type fails."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "wibble(m3): nope", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {"type": "git-log-walk", "binding-effective-from": base},
    )
    assert result is not None, "Unknown scoped prefix must still fail"
    assert bad_sha[:8] in result
    assert "wibble" in result


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)
