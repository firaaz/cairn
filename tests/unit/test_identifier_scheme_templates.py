"""Phase 2 validation tests for identifier-scheme/template-updates.

Verifies intent.md checks V1-V7 and V12 against the envelope files. Each
assertion targets the specific spec commitment in intent.md's Specification
Detail section.

RED state (before Phase 3):
  - start-slice.full.md still emits `title:` in slice.yaml template (no `name:`)
  - Feature file section lacks `name:` / `shaped-from:` template
  - new-adr.full.md frontmatter lacks `name:`; id: guidance is ADR-NNN form
  - handoff.full.md lacks the normative `## Features` worked example from ADR D8
  - decision.full.md lacks hierarchical <adr-id>/<decision-slug> guidance
  - CLAUDE.md lacks the id:/name: prompt rule
  - operational-reference.md lacks the per-entity id-shape section

Tests target the .full.md files where templates/normative content live. The
lightweight .md variants are permitted-but-not-required updates per the
envelope; see validation/approach.md for the scope decision.

Structural assertions only - no behavior execution. Pytest + stdlib only.
"""

from __future__ import annotations

import re
from pathlib import Path


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
CMD = CAIRN_ROOT / "commands" / "claude-code"
DOCS = CAIRN_ROOT / "docs"

START_SLICE_FULL = CMD / "start-slice.full.md"
NEW_ADR_FULL = CMD / "new-adr.full.md"
HANDOFF_FULL = CMD / "handoff.full.md"
DECISION_FULL = CMD / "decision.full.md"
CLAUDE_MD = CAIRN_ROOT / "CLAUDE.md"
OPS_REF = DOCS / "operational-reference.md"


def _read(p: Path) -> str:
    assert p.is_file(), f"envelope file missing: {p.relative_to(CAIRN_ROOT)}"
    return p.read_text(encoding="utf-8")


def _yaml_blocks(text: str) -> list[str]:
    """Extract fenced ```yaml ... ``` blocks from markdown text."""
    return re.findall(r"```yaml\n(.*?)```", text, re.DOTALL)


# ---------------------------------------------------------------------------
# V3 - ADR template (new-adr.full.md)
# ---------------------------------------------------------------------------


def test_v3a_adr_frontmatter_template_has_name_field():
    text = _read(NEW_ADR_FULL)
    frontmatter_blocks = [b for b in _yaml_blocks(text) if "status:" in b]
    assert frontmatter_blocks, "new-adr.full.md missing ADR frontmatter template block"
    for block in frontmatter_blocks:
        assert re.search(r"^name:\s*", block, re.MULTILINE), (
            "ADR frontmatter template missing `name:` field "
            "(intent Specification Detail, ADR template + ADR D1)"
        )


def test_v3b_adr_id_flat_slug_guidance():
    text = _read(NEW_ADR_FULL)
    assert re.search(
        r"flat.{0,20}(semantic )?slug|semantic.{0,20}slug",
        text,
        re.IGNORECASE,
    ), (
        "new-adr.full.md `id:` guidance missing flat/semantic slug form "
        "(intent Specification Detail, ADR template + ADR D2)"
    )
    assert re.search(r"`[a-z][a-z0-9]+(?:-[a-z0-9]+)+`", text), (
        "new-adr.full.md missing a flat-slug id: example "
        "(e.g. `identifier-scheme`, `parallelism-v1`)"
    )


def test_v3c_adr_cross_ref_id_values_not_filenames():
    text = _read(NEW_ADR_FULL)
    cross_ref_guidance = re.search(
        r"(supersedes|adrs-referenced)[^.]{0,400}\bid\b",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    assert cross_ref_guidance, (
        "new-adr.full.md missing id-values-not-filenames guidance for "
        "supersedes:/adrs-referenced: (intent Specification Detail, ADR template + ADR D9)"
    )


def test_v3d_adr_decision_point_hierarchical_cross_ref_guidance():
    text = _read(NEW_ADR_FULL)
    assert re.search(r"<adr-id>/<decision[-_]slug>", text), (
        "new-adr.full.md missing hierarchical <adr-id>/<decision-slug> "
        "decision-point cross-reference guidance (intent Specification Detail, ADR template)"
    )


# ---------------------------------------------------------------------------
# V5 - decision template (decision.full.md)
# ---------------------------------------------------------------------------


def test_v5a_decision_hierarchical_cross_ref_default():
    text = _read(DECISION_FULL)
    assert re.search(r"<adr-id>/<decision[-_]slug>", text), (
        "decision.full.md missing hierarchical <adr-id>/<decision-slug> "
        "cross-ADR citation guidance (intent Specification Detail, Decision command)"
    )


# ---------------------------------------------------------------------------
# V6 - CLAUDE.md prompt rule
# ---------------------------------------------------------------------------


def test_v6a_claude_md_has_id_name_prompt_rule():
    text = _read(CLAUDE_MD)
    assert "`id:`" in text and "`name:`" in text, (
        "CLAUDE.md missing prompt-level assertion of `id:` + `name:` two-field model "
        "(intent Specification Detail, CLAUDE.md prompt rule + ADR D1)"
    )


def test_v6b_claude_md_prompt_rule_points_to_full_protocol():
    """Pointer to full protocol must appear in the same sentence/paragraph as
    the `id:`/`name:` prompt rule, not elsewhere in the file (preamble).
    """
    text = _read(CLAUDE_MD)
    # Locate the paragraph containing both `id:` and `name:` (the prompt rule).
    paragraphs = re.split(r"\n\s*\n", text)
    rule_paragraphs = [p for p in paragraphs if "`id:`" in p and "`name:`" in p]
    assert rule_paragraphs, (
        "CLAUDE.md: no paragraph contains both `id:` and `name:` "
        "(prompt rule not found)"
    )
    matched = any(
        "docs/adr/identifier-scheme.md" in p or "docs/operational-reference.md" in p
        for p in rule_paragraphs
    )
    assert matched, (
        "CLAUDE.md prompt rule paragraph does not point to full protocol "
        "(docs/adr/identifier-scheme.md or docs/operational-reference.md)"
    )


# ---------------------------------------------------------------------------
# V7 - docs/operational-reference.md identity section
# ---------------------------------------------------------------------------


def test_v7a_ops_ref_has_per_entity_id_shape_table():
    text = _read(OPS_REF)
    table_rows = re.findall(r"^\|.*\|.*\|.*\|.*\|", text, re.MULTILINE)
    matched = any(
        "Entity" in row
        and re.search(r"id:?\s*shape", row, re.IGNORECASE)
        and "Example" in row
        and "Hierarchy" in row
        for row in table_rows
    )
    assert matched, (
        "operational-reference.md missing per-entity id-shape table "
        "(columns: Entity | id: shape | Example | Hierarchy?) from ADR D2 "
        "(intent Specification Detail, operational-reference elaboration)"
    )


def test_v7b_ops_ref_documents_all_four_entities():
    text = _read(OPS_REF)
    # Find the identity/identifier section and check entities appear within it
    identity_section = re.search(
        r"##\s*(?:Identifier|Identity|Identifiers).*?(?=\n##\s[^#]|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    assert identity_section, (
        "operational-reference.md missing identity/identifier section header "
        "(intent Specification Detail, operational-reference elaboration)"
    )
    region = identity_section.group(0)
    for entity in ("ADR", "Decision point", "Slice", "Feature"):
        assert entity in region, (
            f"operational-reference.md identity section missing entity `{entity}` "
            "(ADR D2 enumerates ADR / Decision point / Slice / Feature)"
        )


def test_v7c_ops_ref_documents_name_as_frontmatter_slot():
    text = _read(OPS_REF)
    identity_section = re.search(
        r"##\s*(?:Identifier|Identity|Identifiers).*?(?=\n##\s[^#]|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    assert identity_section, "operational-reference.md missing identity section"
    region = identity_section.group(0)
    assert re.search(r"frontmatter", region, re.IGNORECASE), (
        "operational-reference.md identity section missing `name:` frontmatter-slot framing"
    )


def test_v7d_ops_ref_documents_shaped_from_provenance():
    text = _read(OPS_REF)
    identity_section = re.search(
        r"##\s*(?:Identifier|Identity|Identifiers).*?(?=\n##\s[^#]|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    assert identity_section, "operational-reference.md missing identity section"
    region = identity_section.group(0)
    assert "shaped-from" in region, (
        "operational-reference.md identity section missing `shaped-from:` "
        "feature-provenance documentation (intent Specification Detail + ADR D5)"
    )
