"""Build cairn's `dist/` plugin payload from canonical sources.

Allow-list IS the contract. Plugin manifests have no include/exclude glob
fields per ADR D3 — payload curation is by physical separation. The build
script never traverses `.slice-system → .` (CLAUDE.md symlink-recursion
hazard); only the explicit pairs below are copied. Future hook additions
that want `scripts/_root.py` or `scripts/lib/` must add explicit rows.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer

ALLOW_LIST: list[tuple[str, str]] = [
    (".claude/skills/cairn-tdd-feature", "skills/cairn-tdd-feature"),
    (".claude/skills/cairn-intent", "skills/cairn-intent"),
    (".claude/agents/intent-challenge.md", "agents/intent-challenge.md"),
    (".claude/agents/intent-review.md", "agents/intent-review.md"),
    ("templates/intent.md", "templates/intent.md"),
    (".claude/agents/phase-1-tdd.md", "agents/phase-1-tdd.md"),
    (".claude/agents/phase-2-tdd.md", "agents/phase-2-tdd.md"),
    (".claude/agents/phase-3-tdd.md", "agents/phase-3-tdd.md"),
    (".claude/agents/phase-4-tdd.md", "agents/phase-4-tdd.md"),
    (".claude/agents/triager-tdd.md", "agents/triager-tdd.md"),
    (".claude/agents/role-topology.yaml", "agents/role-topology.yaml"),
    ("checks/reversibility-guard.sh", "checks/reversibility-guard.sh"),
    ("checks/reality-check.sh", "checks/reality-check.sh"),
    ("checks/role_guard.py", "checks/role_guard.py"),
    ("templates/handoff.md", "templates/handoff.md"),
    (".claude-plugin/plugin-template.json", ".claude-plugin/plugin.json"),
    (".claude-plugin/hooks-template.json", "hooks/hooks.json"),
    ("scripts/postinstall_validate.py", "postinstall_validate.py"),
]


def _clean(dist_root: Path) -> None:
    if dist_root.exists():
        shutil.rmtree(dist_root)
    dist_root.mkdir(parents=True)


def _copy_pair(repo_root: Path, dist_root: Path, src_rel: str, dst_rel: str) -> None:
    # Refuse to follow the .slice-system self-symlink under any input root.
    src = repo_root / src_rel
    if not src.exists():
        raise FileNotFoundError(f"build_dist: missing source {src}")
    dst = dist_root / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        # Copy tree without following symlinks; hard-skip any nested .slice-system.
        shutil.copytree(
            src,
            dst,
            symlinks=False,
            ignore=shutil.ignore_patterns(".slice-system", "__pycache__"),
        )
    else:
        shutil.copy2(src, dst)


def build(repo_root: Path, dist_root: Path) -> None:
    repo_root = repo_root.resolve()
    dist_root = dist_root.resolve()
    _clean(dist_root)
    for src_rel, dst_rel in ALLOW_LIST:
        if src_rel.startswith(".slice-system"):
            continue
        _copy_pair(repo_root, dist_root, src_rel, dst_rel)


def main(
    repo_root: Path = typer.Option(Path.cwd(), "--repo-root"),
    dist_root: Path = typer.Option(None, "--dist-root"),
) -> int:
    if dist_root is None:
        dist_root = repo_root / "dist"
    build(repo_root, dist_root)
    return 0


if __name__ == "__main__":
    sys.exit(typer.run(main) or 0)
