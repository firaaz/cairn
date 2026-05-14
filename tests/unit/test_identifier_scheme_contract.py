"""Trial B: docs/adr/identifier-scheme.md decisions enforced as a contract.

See docs/plans/2026-05-14-cairn-adr-contract-trial-b.md.
Scope: D1 (entity has id + human label), D2 (id shape per type),
D3 (supersession id integrity), D5 (feature metadata), D9 (cross-ref resolution).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
ADR_DIR = CAIRN_ROOT / "docs" / "adr"
FEATURE_DIR = CAIRN_ROOT / ".claude" / "features"

LEGACY_LABEL_BASELINE = (
    10  # ADRs lacking both `name:` and `title:` at audit (2026-05-14)
)

FLAT_SLUG = re.compile(r"^[a-z][a-z0-9-]*$")
HIERARCHICAL_SLUG = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$")


def _parse_frontmatter(path: Path) -> dict:
    """Return parsed YAML frontmatter (or whole-file YAML for .yaml inputs)."""
    text = path.read_text()
    if path.suffix == ".yaml":
        return yaml.safe_load(text) or {}
    if not text.startswith("---\n"):
        return {}
    rest = text[4:]
    end = rest.find("\n---\n")
    if end < 0:
        return {}
    return yaml.safe_load(rest[:end]) or {}


def _adr_files() -> list[Path]:
    """All ADR files except the index."""
    return sorted(p for p in ADR_DIR.glob("*.md") if p.name != "index.md")


def _feature_files() -> list[Path]:
    """All feature files."""
    return sorted(FEATURE_DIR.glob("*.yaml"))


def _adr_ids() -> set[str]:
    """All ADR `id:` values."""
    return {_parse_frontmatter(p).get("id", "") for p in _adr_files()} - {""}


def test_d1_entities_have_id():
    """D1: every entity file (ADR, feature) has id in frontmatter."""
    missing = []
    for p in _adr_files() + _feature_files():
        front = _parse_frontmatter(p)
        if not isinstance(front.get("id"), str) or not front["id"].strip():
            missing.append(str(p.relative_to(CAIRN_ROOT)))
    assert not missing, f"entities missing id: {missing}"


def test_d1_entities_have_human_label():
    """D1 advisory: count of entities lacking name AND title must be ≤ baseline.

    The identifier-scheme ADR's D7 migration is forward-only; pre-existing ADRs
    were not retrofit. This test enforces no-new-drift via a baseline constant
    rather than failing on legacy state. Lower the baseline as ADRs are normalised.
    """
    legacy = []
    for p in _adr_files():
        front = _parse_frontmatter(p)
        has_name = isinstance(front.get("name"), str) and front["name"].strip()
        has_title = isinstance(front.get("title"), str) and front["title"].strip()
        if not (has_name or has_title):
            legacy.append(p.name)

    assert len(legacy) <= LEGACY_LABEL_BASELINE, (
        f"ADRs without name/title increased above baseline "
        f"({len(legacy)} > {LEGACY_LABEL_BASELINE}): {sorted(legacy)}"
    )

    # Feature files should ALL have name (no legacy gap there per audit).
    feat_missing = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        if not (isinstance(front.get("name"), str) and front["name"].strip()):
            feat_missing.append(p.name)
    assert not feat_missing, f"feature files missing name: {feat_missing}"
