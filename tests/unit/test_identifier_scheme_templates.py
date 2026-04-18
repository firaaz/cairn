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
# V1 - slice template (start-slice.full.md slice.yaml block)
# ---------------------------------------------------------------------------


def test_v1a_slice_yaml_template_has_name_field():
    text = _read(START_SLICE_FULL)
    slice_yaml_blocks = [
        b
        for b in _yaml_blocks(text)
        if re.search(r"^status:\s*intent\b", b, re.MULTILINE)
    ]
    assert slice_yaml_blocks, (
        "start-slice.full.md missing slice.yaml template block (status: intent)"
    )
    for block in slice_yaml_blocks:
        assert re.search(r"^name:\s*", block, re.MULTILINE), (
            "slice.yaml template block missing `name:` field "
            "(intent Specification Detail, Slice template)"
        )


def test_v1b_slice_yaml_template_hierarchical_id_guidance():
    text = _read(START_SLICE_FULL)
    assert re.search(r"<feature(?:-id)?>/<slice[-_]slug>", text), (
        "start-slice.full.md does not document hierarchical "
        "<feature-id>/<slice-slug> id: form (intent Specification Detail + ADR D2)"
    )


def test_v1c_slice_template_documents_legacy_slice_nnn_accepted():
    text = _read(START_SLICE_FULL)
    legacy_context = re.search(r"SLICE-NNN", text)
    assert legacy_context, (
        "start-slice.full.md does not mention legacy SLICE-NNN form (intent V1: "
        '"legacy SLICE-NNN remains accepted by hooks during transition")'
    )
    window_start = max(0, legacy_context.start() - 400)
    window_end = min(len(text), legacy_context.end() + 400)
    window = text[window_start:window_end]
    assert re.search(
        r"accept|legacy|transition|coexist|Phase 1|permitted",
        window,
        re.IGNORECASE,
    ), "SLICE-NNN mention not framed as accepted-during-transition"


# ---------------------------------------------------------------------------
# V2 - feature template (start-slice.full.md Feature file section)
# ---------------------------------------------------------------------------


def _feature_section(text: str) -> str:
    m = re.search(r"### Feature file.*?(?=\n##\s|\n### |\Z)", text, re.DOTALL)
    assert m, "start-slice.full.md missing ### Feature file section"
    return m.group(0)


def test_v2a_feature_template_has_name_field():
    text = _read(START_SLICE_FULL)
    section = _feature_section(text)
    assert re.search(r"\bname:\s*", section), (
        "Feature file section missing `name:` field (intent Specification Detail, "
        "Feature template + ADR D5)"
    )


def test_v2b_feature_template_has_shaped_from_field():
    text = _read(START_SLICE_FULL)
    section = _feature_section(text)
    assert "shaped-from:" in section, (
        "Feature file section missing `shaped-from:` field "
        "(intent Specification Detail, Feature template + ADR D5)"
    )


def test_v2c_feature_slice_list_entry_hierarchical_id():
    text = _read(START_SLICE_FULL)
    section = _feature_section(text)
    assert re.search(r"id:\s*<feature(?:-id)?>/<slice[-_]slug>", section), (
        "Feature slice-list entry shape does not use hierarchical "
        "<feature>/<slice-slug> id: form (intent Specification Detail, Feature template)"
    )


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
# V4 - handoff template (handoff.full.md)
# ---------------------------------------------------------------------------


def test_v4a_handoff_features_section_normative_format():
    """handoff.full.md must reference ADR identifier-scheme D8 as the normative
    source for the `## Features` cross-feature index format.
    """
    text = _read(HANDOFF_FULL)
    d8_ref = re.search(
        r"(?:ADR\s+identifier-scheme|identifier-scheme).{0,80}D8|D8.{0,200}Features",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    assert d8_ref, (
        "handoff.full.md missing normative reference to ADR identifier-scheme D8 "
        "for the `## Features` format (intent V4)"
    )


def test_v4b_handoff_features_has_worked_example():
    text = _read(HANDOFF_FULL)
    code_blocks = re.findall(r"```(?:markdown)?\n(.*?)```", text, re.DOTALL)
    matched = any(
        re.search(r"^##\s*Features\s*$", block, re.MULTILINE)
        and re.search(r"^- [a-z][\w-]*:\s", block, re.MULTILINE)
        for block in code_blocks
    )
    assert matched, (
        "handoff.full.md missing worked-example code block containing `## Features` "
        "heading with `- <feature-id>: ...` lines (intent V4, ADR D8 normative example)"
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


# ---------------------------------------------------------------------------
# V12 - template self-consistency
# ---------------------------------------------------------------------------


def test_v12_slice_template_self_consistent_with_slice_yaml_produced():
    """Running /start-slice Step 4 should produce a slice.yaml with hierarchical
    id: + name:, matching this slice's own slice.yaml (which uses name: already).
    """
    text = _read(START_SLICE_FULL)
    step4 = re.search(r"## Step 4.*?(?=\n## |\Z)", text, re.DOTALL)
    assert step4, "start-slice.full.md missing Step 4 (Initialize New Slice)"
    step4_text = step4.group(0)
    step4_yaml_blocks = _yaml_blocks(step4_text)
    slice_yaml_blocks = [b for b in step4_yaml_blocks if "status: intent" in b]
    assert slice_yaml_blocks, "Step 4 missing slice.yaml example block"
    for block in slice_yaml_blocks:
        assert re.search(r"^name:\s*", block, re.MULTILINE), (
            "Step 4 slice.yaml example does not include `name:` - template is not "
            "self-consistent with this slice's own slice.yaml (intent V12)"
        )
