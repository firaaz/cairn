"""RED tests for cairn-m5-f1-packaging A3, A4, A5 — `dist/` build script (D3).

Pins:
- A3 — Build populates exactly the allow-listed surfaces (allow-list IS contract).
- A4 — Build never leaks excluded surfaces (`tests/`, `docs/`, `.venv/`,
  `uv.lock`, `pyproject.toml`, `commands/`, `slice_orchestrator/`,
  `.claude/skill-runs/`, `docs/{adr,plans,reviews}/`).
- A5 — Build is idempotent (two runs → byte-identical) AND symlink-safe
  (never traverses `.slice-system → .`).

Per intent.md verification §"Build-output evidence": invoke build script
into a tmp dir, enumerate result, assert presence + absence + byte-identity.

Module import follows project convention (pyproject.toml `pythonpath = ["scripts"]`):
`from build_dist import ...` — NOT `from scripts.build_dist import ...`.

Tests must FAIL at HEAD because `scripts/build_dist.py` does not exist.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_dist.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_build_script() -> None:
    if not BUILD_SCRIPT.is_file():
        pytest.fail(f"build_dist.py not found at {BUILD_SCRIPT}")


def _run_build(repo_root: Path, dist_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--repo-root",
            str(repo_root),
            "--dist-root",
            str(dist_root),
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )


def _file_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _walk_files(root: Path) -> list[Path]:
    """Return relative file paths under root; do NOT follow symlinks."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for f in filenames:
            full = Path(dirpath) / f
            out.append(full.relative_to(root))
    return sorted(out)


# ---------------------------------------------------------------------------
# A3 — Allow-list coverage
# ---------------------------------------------------------------------------

# Required allow-listed surfaces, expressed as paths relative to dist_root.
REQUIRED_ALLOWLIST = [
    Path(".claude-plugin/plugin.json"),
    Path("skills/cairn-tdd-feature/SKILL.md"),
    Path("agents/phase-1-tdd.md"),
    Path("agents/phase-2-tdd.md"),
    Path("agents/phase-3-tdd.md"),
    Path("agents/phase-4-tdd.md"),
    Path("agents/triager-tdd.md"),
    Path("agents/role-topology.yaml"),
    Path("checks/reversibility-guard.sh"),
    Path("checks/reality-check.sh"),
    Path("checks/role_guard.py"),
    Path("templates/handoff.md"),
    Path("hooks/hooks.json"),
    Path("postinstall_validate.py"),
]


def test_a3_build_invocation_succeeds(tmp_path):
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc = _run_build(REPO_ROOT, dist_root)
    assert proc.returncode == 0, (
        f"A3: build_dist.py exited rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )


def test_a3_allowlist_paths_all_present(tmp_path):
    """Every allow-listed surface in REQUIRED_ALLOWLIST exists post-build."""
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc = _run_build(REPO_ROOT, dist_root)
    assert proc.returncode == 0, f"build failed: {proc.stderr}"
    missing = [p for p in REQUIRED_ALLOWLIST if not (dist_root / p).is_file()]
    assert not missing, f"A3: allow-listed paths missing from dist tree: {missing}"


# ---------------------------------------------------------------------------
# A4 — Deny-list (negative) — asserted as inverse of allow-list
# ---------------------------------------------------------------------------

# Top-level path components that MUST NOT appear under dist_root after build.
EXCLUDED_TOPLEVEL = [
    "tests",
    "docs",
    ".venv",
    "uv.lock",
    "pyproject.toml",
    "commands",
    ".claude",  # NB: .claude-plugin is allowed, .claude (skill-runs etc) is not
]

# Specific subtrees that must not appear even nested.
EXCLUDED_SUBPATHS = [
    Path("scripts/slice_orchestrator"),
    Path("docs/adr"),
    Path("docs/plans"),
    Path("docs/reviews"),
    Path(".claude/skill-runs"),
]


def test_a4_no_excluded_toplevel_dirs_or_files(tmp_path):
    """Post-build tree contains none of the excluded top-level surfaces."""
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc = _run_build(REPO_ROOT, dist_root)
    assert proc.returncode == 0, f"build failed: {proc.stderr}"
    leaked: list[str] = []
    for top in EXCLUDED_TOPLEVEL:
        candidate = dist_root / top
        if candidate.exists():
            leaked.append(str(candidate.relative_to(dist_root)))
    assert not leaked, f"A4: excluded surfaces leaked into dist tree: {leaked}"


def test_a4_no_excluded_subtrees(tmp_path):
    """Excluded subtrees do not appear nested anywhere under dist."""
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc = _run_build(REPO_ROOT, dist_root)
    assert proc.returncode == 0, f"build failed: {proc.stderr}"
    rels = _walk_files(dist_root)
    leaked: list[str] = []
    for r in rels:
        for sub in EXCLUDED_SUBPATHS:
            try:
                r.relative_to(sub)
                leaked.append(str(r))
                break
            except ValueError:
                continue
    assert not leaked, f"A4: excluded subtrees leaked: {leaked}"


def test_a4_no_pyproject_or_uvlock_in_dist(tmp_path):
    """Specific assertion: pyproject.toml and uv.lock must not be copied."""
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc = _run_build(REPO_ROOT, dist_root)
    assert proc.returncode == 0, f"build failed: {proc.stderr}"
    for forbidden in ("pyproject.toml", "uv.lock"):
        assert not (dist_root / forbidden).exists(), (
            f"A4: {forbidden} must not appear in dist tree"
        )


# ---------------------------------------------------------------------------
# A5 — Idempotence + symlink-safety
# ---------------------------------------------------------------------------


def _tree_signature(root: Path) -> dict[str, str]:
    """Return {relpath: sha256} for every regular file under root."""
    return {str(r): _file_hash(root / r) for r in _walk_files(root)}


def test_a5_idempotent_two_runs_byte_identical(tmp_path):
    """Two consecutive build runs produce byte-identical output trees."""
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc1 = _run_build(REPO_ROOT, dist_root)
    assert proc1.returncode == 0, f"first build failed: {proc1.stderr}"
    sig1 = _tree_signature(dist_root)

    proc2 = _run_build(REPO_ROOT, dist_root)
    assert proc2.returncode == 0, f"second build failed: {proc2.stderr}"
    sig2 = _tree_signature(dist_root)

    assert sig1 == sig2, (
        f"A5: idempotence violated. "
        f"only-in-1={set(sig1) - set(sig2)} "
        f"only-in-2={set(sig2) - set(sig1)} "
        f"hash-diffs={[k for k in sig1 if k in sig2 and sig1[k] != sig2[k]]}"
    )


def test_a5_build_cleans_output_before_populating(tmp_path):
    """A stray file in dist_root is removed by the next build run (clean-then-populate)."""
    _require_build_script()
    dist_root = tmp_path / "dist"
    proc = _run_build(REPO_ROOT, dist_root)
    assert proc.returncode == 0, f"build failed: {proc.stderr}"

    # Plant a stray file.
    stray = dist_root / "STRAY_FILE.txt"
    stray.write_text("should be removed by next clean build")
    assert stray.exists()

    proc2 = _run_build(REPO_ROOT, dist_root)
    assert proc2.returncode == 0, f"second build failed: {proc2.stderr}"
    assert not stray.exists(), (
        "A5: build_dist must clean output dir before populating; "
        "stray file survived second run"
    )


def test_a5_symlink_safe_does_not_traverse_slice_system(tmp_path):
    """When invoked from a working tree containing `.slice-system → .`, the
    build must not produce a `.slice-system` subtree under dist (which would
    indicate the script followed the recursive self-symlink).
    """
    _require_build_script()

    # Stage a fake repo-root that mirrors the canonical tree but contains a
    # self-pointing .slice-system symlink, like a downstream consumer.
    fake_root = tmp_path / "fake-repo"
    fake_root.mkdir()
    # Stage the necessary canonical surfaces by symlinking from the real repo.
    for entry in (".claude-plugin", ".claude", "checks", "templates", "scripts"):
        src = REPO_ROOT / entry
        if src.exists():
            os.symlink(src, fake_root / entry)
    # Add the recursive self-symlink hazard.
    (fake_root / ".slice-system").symlink_to(fake_root)

    dist_root = tmp_path / "dist"
    proc = _run_build(fake_root, dist_root)

    # The build may fail (script chose to error out) or succeed; either way,
    # the output tree must NOT contain a `.slice-system` directory or any path
    # whose first component matches the symlink-recursion hazard.
    if dist_root.exists():
        rels = _walk_files(dist_root)
        leaked = [str(r) for r in rels if r.parts and r.parts[0] == ".slice-system"]
        assert not leaked, (
            f"A5: build traversed `.slice-system → .` recursive symlink; "
            f"leaked paths: {leaked[:5]}"
        )


# ---------------------------------------------------------------------------
# A11 (thin shape assertion) — CI workflow file presence + minimum shape.
# Placed here per Phase-2 brief "thin shape-assertion test at e.g. test_build_dist.py
# (workflow shape) is acceptable".
# ---------------------------------------------------------------------------


def test_a11_dist_gate_workflow_file_exists():
    """`.github/workflows/dist-gate.yml` exists at the repo root."""
    workflow = REPO_ROOT / ".github" / "workflows" / "dist-gate.yml"
    assert workflow.is_file(), f"A11: dist-gate workflow not found at {workflow}"


def test_a11_dist_gate_workflow_runs_build_and_validator():
    """Workflow file references the build script, the build_dist test file, and
    the post-install validator — the three steps required by intent.md A11."""
    workflow = REPO_ROOT / ".github" / "workflows" / "dist-gate.yml"
    if not workflow.is_file():
        pytest.fail(f"A11: dist-gate workflow not found at {workflow}")
    text = workflow.read_text()
    assert "build_dist.py" in text, "A11: workflow must invoke scripts/build_dist.py"
    assert "test_build_dist.py" in text or "tests/unit/test_build_dist" in text, (
        "A11: workflow must run the allow-list assertions test file"
    )
    assert "postinstall_validate.py" in text, (
        "A11: workflow must invoke scripts/postinstall_validate.py self-test"
    )


def test_a11_dist_gate_workflow_triggers_on_pr_and_pushes_to_dev_main():
    """Workflow triggers on PRs and pushes to dev/main."""
    workflow = REPO_ROOT / ".github" / "workflows" / "dist-gate.yml"
    if not workflow.is_file():
        pytest.fail(f"A11: dist-gate workflow not found at {workflow}")
    text = workflow.read_text()
    assert "pull_request" in text, "A11: workflow must trigger on pull_request"
    # dev and main branch references in `push:` triggers
    assert "dev" in text, "A11: workflow must reference dev branch"
    assert "main" in text, "A11: workflow must reference main branch"
