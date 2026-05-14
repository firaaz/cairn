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
LEGACY_SLICE_ID_BASELINE = 6  # slice ids violating D2 shape at audit (2026-05-14)

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


def test_d1_adrs_have_human_label():
    """D1 advisory: count of ADRs lacking name AND title must be ≤ baseline.

    The identifier-scheme ADR's D7 migration is forward-only; pre-existing ADRs
    were not retrofit. This test enforces no-new-drift via a baseline constant
    rather than failing on legacy state. Lower the baseline as ADRs are normalised.
    """
    unlabelled = []
    for p in _adr_files():
        front = _parse_frontmatter(p)
        has_name = isinstance(front.get("name"), str) and front["name"].strip()
        has_title = isinstance(front.get("title"), str) and front["title"].strip()
        if not (has_name or has_title):
            unlabelled.append(p.name)

    assert len(unlabelled) <= LEGACY_LABEL_BASELINE, (
        f"ADRs without name/title increased above baseline "
        f"({len(unlabelled)} > {LEGACY_LABEL_BASELINE}): {sorted(unlabelled)}"
    )


def test_d1_features_have_name():
    """D1 strict: every feature file carries a non-empty `name:`.

    Features have no legacy gap per the 2026-05-14 audit, so this is strict
    (no advisory baseline).
    """
    missing = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        if not (isinstance(front.get("name"), str) and front["name"].strip()):
            missing.append(p.name)
    assert not missing, f"feature files missing name: {missing}"


def test_d2_strict_id_shape_for_adrs_and_features():
    """D2 strict: ADR and feature ids match the flat semantic slug shape."""
    bad = []
    for p in _adr_files():
        adr_id = _parse_frontmatter(p).get("id", "")
        if not FLAT_SLUG.match(adr_id):
            bad.append(f"adr {p.name}: id={adr_id!r}")
    for p in _feature_files():
        feat_id = _parse_frontmatter(p).get("id", "")
        if not FLAT_SLUG.match(feat_id):
            bad.append(f"feature {p.name}: id={feat_id!r}")
    assert not bad, "id-shape violations:\n  " + "\n  ".join(bad)


def test_d2_slice_id_shape_advisory_baseline():
    """D2 advisory: slice id violations <= baseline.

    Slice ids predate identifier-scheme's lowercase-kebab-case rule in some
    cases (semantic uppercase categoricals, version-dotted ids, slice-moved-
    without-rekey). D1 says ids are immutable — this advisory ceiling permits
    the legacy state while gating any new violations. Lower the baseline as
    historical slices are renamed (deferred decision).
    """
    bad = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        feat_id = front.get("id", "")
        for entry in front.get("slices") or []:
            slice_id = (entry or {}).get("id", "")
            if not HIERARCHICAL_SLUG.match(slice_id):
                bad.append(f"{p.name}: id={slice_id!r}")
                continue
            prefix = slice_id.split("/", 1)[0]
            if prefix != feat_id:
                bad.append(
                    f"{p.name}: id={slice_id!r} prefix {prefix!r} "
                    f"!= feature id {feat_id!r}"
                )
    assert len(bad) <= LEGACY_SLICE_ID_BASELINE, (
        f"slice id violations increased above baseline "
        f"({len(bad)} > {LEGACY_SLICE_ID_BASELINE}):\n  " + "\n  ".join(sorted(bad))
    )


def test_d3_superseded_ids_intact():
    """D3: ADR ids are unique; every superseded-by points to an existing ADR id."""
    ids: list[str] = []
    superseded_by_pairs: list[tuple[str, str]] = []
    for p in _adr_files():
        front = _parse_frontmatter(p)
        adr_id = front.get("id", "")
        if adr_id:
            ids.append(adr_id)
        target = front.get("superseded-by") or front.get("superseded_by")
        if isinstance(target, str) and target.strip():
            superseded_by_pairs.append((p.name, target.strip()))

    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, f"duplicate ADR ids: {duplicates}"

    known = set(ids)
    unresolved = [(src, tgt) for src, tgt in superseded_by_pairs if tgt not in known]
    assert not unresolved, f"superseded-by pointing to unknown ADR ids: {unresolved}"


def test_d5_feature_files_well_formed():
    """D5: feature files carry id, name, intent, shaped-from. No epic key.

    D5 reads as default-permit on extras per schema-amendment-threshold/D1 —
    fields beyond the required four are advisory unless explicitly named-rejected
    (epic: is the sole current named rejection).
    """
    required = {"id", "name", "intent", "shaped-from"}
    bad = []
    for p in _feature_files():
        front = _parse_frontmatter(p)
        missing = required - front.keys()
        if missing:
            bad.append(f"{p.name}: missing keys {sorted(missing)}")
        if "epic" in front:
            bad.append(f"{p.name}: forbidden `epic:` key present")
    assert not bad, "feature file violations:\n  " + "\n  ".join(sorted(bad))


def _resolve_adr_id_token(token: str, known: set[str]) -> bool:
    """Return True if the ADR id portion of a cross-ref token matches a known id.

    Handles two supersedes-sections shapes:
      - slash-form: 'adr-id/D3' — base before '/' is the id
      - space-form: 'adr-id D4 (partial: ...)' — first whitespace token is the id
    Non-ADR file references (e.g. 'CLAUDE.md:26 prose') that contain '.' or ':'
    before any '/' are treated as intentional non-ADR annotations and skipped.
    """
    if not isinstance(token, str):
        return False
    head = token.strip().split()[0] if token.strip() else ""
    if not head:
        return False
    base = head.split("/")[0]
    if "." in base or ":" in base:
        return True
    return base in known


def test_d9_adr_cross_references_resolve():
    """D9: adrs-referenced / supersedes / supersedes-sections values resolve to known ADR ids."""
    known = _adr_ids()
    bad = []
    cross_ref_keys = ("adrs-referenced", "supersedes", "supersedes-sections")
    for p in _adr_files():
        front = _parse_frontmatter(p)
        for key in cross_ref_keys:
            value = front.get(key)
            if value is None:
                continue
            items = value if isinstance(value, list) else [value]
            for item in items:
                if not item:
                    continue
                if not _resolve_adr_id_token(item, known):
                    bad.append(f"{p.name} {key}: {item!r} does not resolve")
    assert not bad, "unresolved cross-references:\n  " + "\n  ".join(sorted(bad))
