"""Phase 2 RED tests for slice v1-defense-d2/inv-001-binding-implementation.

Verifies the new INV-001 binding: a `git-log-walk` validator type that
authorizes commit-subject prefixes against
``.claude/pipeline-substrate-registry.yaml`` and runs a per-prefix Python
verifier on each commit since ``binding-effective-from``.

Public surface tested (per docs/plans/2026-05-02-inv-001-binding-plan.md
§Phase 2; symbol names may shift in Phase 3 with a corresponding test
micro-edit, as that plan explicitly authorizes):

  - ``scripts/validate_architecture._load_substrate_registry``
  - ``scripts/validate_architecture._SUBSTRATE_VERIFIERS``
  - ``scripts/validate_architecture._run_git_log_walk_assertion``
  - ``.claude/pipeline-substrate-registry.yaml`` (file)
  - End-to-end: ``uv run python scripts/validate_architecture.py`` exit 0
    while the binding-effective-from placeholder is still set.

Import path note: cairn's pyproject sets ``pythonpath = ["scripts"]``
(see ``pyproject.toml [tool.pytest.ini_options]``), so the module is
imported as ``validate_architecture`` — not ``scripts.validate_architecture``.
The plan's snippet form is normalised to that import here.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_REL = Path(".claude/pipeline-substrate-registry.yaml")
REGISTRY_ABS = CAIRN_ROOT / REGISTRY_REL


# --- Helpers ---------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    """Run a git subcommand inside ``repo`` and return stripped stdout."""
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
    """Touch ``touch`` files (creating parent dirs), git add, commit, return SHA."""
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
    """Init a synthetic git repo with the real cairn substrate registry copied in.

    A first commit lands the registry so that subsequent ``base..HEAD`` walks
    have a non-empty range to operate on. The registry file is required —
    if it is absent (Phase 2 RED state, before Phase 3 creates it), this
    helper raises FileNotFoundError, which surfaces as the intended RED.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@x")
    _git(repo, "config", "user.name", "t")
    dst = repo / REGISTRY_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_ABS.exists():
        raise FileNotFoundError(
            f"Phase 2 RED: {REGISTRY_REL} does not exist yet. "
            "Phase 3 Builder will create it."
        )
    shutil.copy2(REGISTRY_ABS, dst)
    _git(repo, "add", str(REGISTRY_REL))
    _git(repo, "commit", "-q", "-m", "bootstrap: seed registry for fixture")
    return repo


# === T1 — Registry file present and parses =================================


def test_registry_yaml_present_and_parseable():
    """Registry exists at canonical path with valid YAML and required schema."""
    from validate_architecture import _load_substrate_registry

    registry = _load_substrate_registry(CAIRN_ROOT)
    assert isinstance(registry, dict)
    assert registry, "Registry must contain at least one entry once Phase 3 lands."
    for prefix, entry in registry.items():
        assert prefix.endswith(":"), f"prefix {prefix!r} must end with ':'"
        for required in ("tool", "owner-adr", "since"):
            assert required in entry, f"{prefix} missing {required}"


# === T2 — Every registered prefix has a verifier ===========================


def test_every_registered_prefix_has_verifier():
    """Every prefix in the registry has a Python verifier (or pass-through)."""
    from validate_architecture import (
        _SUBSTRATE_VERIFIERS,
        _load_substrate_registry,
    )

    registry = _load_substrate_registry(CAIRN_ROOT)
    for prefix in registry:
        assert prefix in _SUBSTRATE_VERIFIERS, (
            f"prefix {prefix!r} has no Python verifier or pass-through marker"
        )


# === T3 — Placeholder SHA → no-op-with-notice ==============================


def test_walk_with_placeholder_effective_from_is_noop(capsys):
    """``binding-effective-from: <pending-slice-close-sha>`` → no failures + notice."""
    from validate_architecture import _run_git_log_walk_assertion

    result = _run_git_log_walk_assertion(
        CAIRN_ROOT,
        "INV-001",
        {
            "type": "git-log-walk",
            "binding-effective-from": "<pending-slice-close-sha>",
            "registry": ".claude/pipeline-substrate-registry.yaml",
        },
    )
    assert result is None, f"Placeholder must yield no-op (None). Got: {result!r}"
    captured = capsys.readouterr()
    haystack = (captured.out + captured.err).lower()
    assert "binding pending effective-from" in haystack, (
        "Walker must emit a 'binding pending effective-from' notice on placeholder. "
        f"stdout={captured.out!r} stderr={captured.err!r}"
    )


# === T4 — Unregistered prefix is reported ==================================


def test_unregistered_prefix_reported(tmp_path):
    """A commit whose prefix is not in the registry is reported by SHA + token."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    _commit(
        repo,
        "sweep: x",
        touch=[".claude/sweep-results/x/notes.md", ".claude/sweep.yaml"],
    )
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "wibble: bad", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {
            "type": "git-log-walk",
            "binding-effective-from": base,
            "registry": ".claude/pipeline-substrate-registry.yaml",
        },
    )
    assert result is not None, "Walker must report unregistered prefix as a failure"
    assert "INV-001" in result, f"Failure must name the invariant. Got: {result!r}"
    assert bad_sha[:8] in result, (
        f"Failure must cite offending short SHA {bad_sha[:8]}. Got: {result!r}"
    )
    assert "wibble:" in result, f"Failure must echo offending prefix. Got: {result!r}"
    assert "not in registry" in result, (
        f"Failure must explain the miss. Got: {result!r}"
    )


# === T5 — sweep verifier rejects missing files =============================


def test_sweep_verifier_rejects_missing_sweep_results(tmp_path):
    """A ``sweep:`` commit missing ``.claude/sweep-results/`` is reported."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    bad_sha = _commit(repo, "sweep: bad", touch=["foo.txt"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {
            "type": "git-log-walk",
            "binding-effective-from": base,
            "registry": ".claude/pipeline-substrate-registry.yaml",
        },
    )
    assert result is not None
    assert bad_sha[:8] in result, f"Failure must cite short SHA. Got: {result!r}"
    assert "sweep verifier" in result, (
        f"Failure must name the verifier. Got: {result!r}"
    )
    assert ".claude/sweep-results" in result, (
        f"Failure must name the missing path. Got: {result!r}"
    )


# === T6 — sweep verifier passes when both required paths touched ============


def test_sweep_verifier_passes_with_both_touches(tmp_path):
    """A ``sweep:`` commit touching both ``sweep-results/`` and ``sweep.yaml`` passes."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(
        repo,
        "sweep: ok",
        touch=[".claude/sweep-results/abc/report.md", ".claude/sweep.yaml"],
    )

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {
            "type": "git-log-walk",
            "binding-effective-from": base,
            "registry": ".claude/pipeline-substrate-registry.yaml",
        },
    )
    assert result is None, f"Well-formed sweep commit must pass. Got: {result!r}"


# === T7 — squash-merge feat: accepted on prefix alone (F2 residual) =========


def test_squash_merge_feat_accepted_on_prefix(tmp_path):
    """``feat:`` commits are pass-through (F2 residual per pipeline-substrate-naming D5)."""
    from validate_architecture import _run_git_log_walk_assertion

    repo = _init_repo_with_registry(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "feat: add unrelated thing", touch=["random/file.py"])

    result = _run_git_log_walk_assertion(
        repo,
        "INV-001",
        {
            "type": "git-log-walk",
            "binding-effective-from": base,
            "registry": ".claude/pipeline-substrate-registry.yaml",
        },
    )
    assert result is None, (
        f"feat: prefix must be pass-through (F2 residual). Got: {result!r}"
    )


# === T8 — End-to-end: validator exits 0 with placeholder still set ==========


def test_validator_e2e_passes_with_placeholder():
    """Real ARCHITECTURE.md INV-001 block uses placeholder; full validator exits clean.

    Note (P2 Skeptic): once Phase 3 swaps INV-001's block to ``git-log-walk``
    with the literal ``<pending-slice-close-sha>``, this test asserts the
    no-op-with-notice behaviour does not regress the validator's overall exit.
    Pre-Phase-3 the test may already pass under the legacy ``file-exists``
    block; it functions then as a regression guard against accidental
    breakage during the binding swap.
    """
    proc = subprocess.run(
        ["uv", "run", "python", "scripts/validate_architecture.py"],
        cwd=str(CAIRN_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"Validator must exit 0 with placeholder set.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


# === Defensive isolation ====================================================


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    """Tests must not run under an AGENT_ROLE — defensive isolation."""
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)
