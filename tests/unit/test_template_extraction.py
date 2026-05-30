"""F2.2 template-extraction tests.

Per ``docs/plans/2026-05-08-cairn-m5-f2-consumer-doc-surface.md`` Section
F2.2 Step 1, asserts existence + shape contracts for the five new templates:

- ``templates/feature-plan.md``
- ``templates/intent.md`` (FLI-2: must surface all eight Phase-1 schema
  section headings — intent.md line 47)
- ``templates/sweep-notes.md``
- ``templates/adr-frontmatter.yaml``
- ``templates/active-envelope.yaml`` (FLI-5: defaults to ``mode: off`` and
  includes the self-pattern in the commented example block — intent.md line 50)

These tests are RED at Phase 2 (the templates do not exist yet).
"""

from __future__ import annotations

from pathlib import Path

import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = CAIRN_ROOT / "templates"

FEATURE_PLAN = TEMPLATES / "feature-plan.md"
INTENT = TEMPLATES / "intent.md"
SWEEP_NOTES = TEMPLATES / "sweep-notes.md"
ADR_FRONTMATTER = TEMPLATES / "adr-frontmatter.yaml"
ACTIVE_ENVELOPE = TEMPLATES / "active-envelope.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    assert path.exists(), f"Template not found: {path.relative_to(CAIRN_ROOT)}"
    text = path.read_text()
    assert len(text) > 200, (
        f"{path.relative_to(CAIRN_ROOT)} must be >200 chars; got {len(text)}"
    )
    return text


def _split_frontmatter(md_text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body) from a markdown file with YAML
    frontmatter; raise AssertionError if no frontmatter block is present."""
    assert md_text.startswith("---\n"), (
        "Markdown template must begin with a YAML frontmatter block (---\\n...)"
    )
    closing = md_text.find("\n---\n", 4)
    assert closing != -1, "YAML frontmatter block not closed with '\\n---\\n'"
    front_raw = md_text[4:closing]
    body = md_text[closing + len("\n---\n") :]
    parsed = yaml.safe_load(front_raw) or {}
    assert isinstance(parsed, dict), "Frontmatter must parse as a YAML mapping"
    return parsed, body


# ---------------------------------------------------------------------------
# Sub-test 1: templates/feature-plan.md
# ---------------------------------------------------------------------------


def test_feature_plan_template_shape() -> None:
    """``templates/feature-plan.md`` exists, parses YAML frontmatter, and
    contains the keys ``id``, ``envelope``, ``firmness``, ``status``, ``date``
    per plan F2.2 Step 1 (mirrors operational-reference.md:39-46).
    """
    text = _read(FEATURE_PLAN)
    front, _body = _split_frontmatter(text)
    required = {"id", "envelope", "firmness", "status", "date"}
    missing = required - set(front.keys())
    assert not missing, (
        f"templates/feature-plan.md frontmatter missing keys: {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# Sub-test 2: templates/intent.md (FLI-2 — eight schema headings in order)
# ---------------------------------------------------------------------------


def test_intent_template_shape_and_eight_headings() -> None:
    """``templates/intent.md`` carries the four schema-required frontmatter
    keys and surfaces all eight Phase-1 schema section headings in order per
    FLI-2 (intent.md line 47) and plan F2.2 Step 1.
    """
    text = _read(INTENT)
    front, body = _split_frontmatter(text)

    required_front = {"id", "name", "snapshot-sha", "invariants-touched"}
    missing = required_front - set(front.keys())
    assert not missing, (
        f"templates/intent.md frontmatter missing keys: {sorted(missing)}"
    )

    expected_headings = [
        "## What",
        "## Why",
        "## Boundary",
        "## Specification",
        "## Verification",
        "## Risk Surface",
        "## Feature-Local Invariants",
        "## Explicit Scope-Out",
    ]
    body_lines = body.splitlines()
    cursor = 0
    found_at: dict[str, int] = {}
    for heading in expected_headings:
        match_idx = None
        for i in range(cursor, len(body_lines)):
            if body_lines[i].strip() == heading:
                match_idx = i
                break
        assert match_idx is not None, (
            f"templates/intent.md missing heading {heading!r} (or out of order). "
            f"FLI-2 (intent.md line 47) requires all eight in order."
        )
        found_at[heading] = match_idx
        cursor = match_idx + 1

    # Order check (redundant given the cursor walk, but explicit assertion).
    indices = [found_at[h] for h in expected_headings]
    assert indices == sorted(indices), (
        f"templates/intent.md headings out of order. Found at: {found_at}"
    )


# ---------------------------------------------------------------------------
# Sub-test 2b: templates/intent.md ## Contract block (cairn-trial-d-scope-split)
# ---------------------------------------------------------------------------


def test_intent_template_has_contract_block_with_parseable_yaml() -> None:
    """``templates/intent.md`` carries a ``## Contract`` heading whose fenced
    YAML block parses (``yaml.safe_load`` succeeds) and exposes a
    ``must-satisfy`` key (cairn-trial-d-scope-split intent.md lines 36-40).

    ADD-not-REPLACE: this is additive — the eight-heading-in-order assertion in
    ``test_intent_template_shape_and_eight_headings`` must stay green (FLI-5).

    RED at HEAD: the ``## Contract`` block does not exist in the template yet.
    """
    text = _read(INTENT)
    _front, body = _split_frontmatter(text)
    body_lines = body.splitlines()

    contract_idx = next(
        (i for i, ln in enumerate(body_lines) if ln.strip() == "## Contract"),
        None,
    )
    assert contract_idx is not None, (
        "templates/intent.md must contain a '## Contract' heading "
        "(cairn-trial-d-scope-split intent.md line 36)."
    )

    # Find the fenced yaml block that follows the heading (before the next '## ').
    fence_open = None
    fence_close = None
    for i in range(contract_idx + 1, len(body_lines)):
        ln = body_lines[i]
        if ln.strip().startswith("## "):
            break
        if fence_open is None and ln.strip().startswith("```"):
            fence_open = i
            continue
        if fence_open is not None and ln.strip() == "```":
            fence_close = i
            break
    assert fence_open is not None and fence_close is not None, (
        "templates/intent.md '## Contract' section must contain a fenced YAML block."
    )

    block = "\n".join(body_lines[fence_open + 1 : fence_close])
    parsed = yaml.safe_load(block)
    assert isinstance(parsed, dict), (
        "The '## Contract' fenced block must parse as a YAML mapping; "
        f"got {type(parsed).__name__}"
    )
    assert "must-satisfy" in parsed, (
        "The '## Contract' YAML must expose a 'must-satisfy' key "
        "(cairn-trial-d-scope-split intent.md line 37)."
    )


def test_intent_template_contract_tags_match_exception_tags() -> None:
    """FLI-6 template↔code tag parity: the four exception tags documented in
    ``templates/intent.md`` equal ``scripts/lib/atomicity.EXCEPTION_TAGS``
    exactly (cairn-trial-d-scope-split FLI-6 / Verification drift audit).

    RED at HEAD: ``scripts/lib/atomicity`` does not exist and the template has
    no tag documentation yet.
    """
    from lib.atomicity import EXCEPTION_TAGS  # RED: module absent at HEAD

    text = _read(INTENT)
    for tag in EXCEPTION_TAGS:
        assert tag in text, (
            f"templates/intent.md must document the exception tag {tag!r} "
            f"(FLI-6 tag parity with scripts/lib/atomicity.EXCEPTION_TAGS)."
        )


# ---------------------------------------------------------------------------
# Sub-test 3: templates/sweep-notes.md
# ---------------------------------------------------------------------------


def test_sweep_notes_template_body_sections() -> None:
    """``templates/sweep-notes.md`` body contains ``## Test results``,
    ``## Validator results``, ``## Invariant verification``, and
    ``## Adjacent code regression check`` per plan F2.2 Step 1 (Phase 4
    rules).
    """
    text = _read(SWEEP_NOTES)
    # Frontmatter is optional in the plan but mentioned at Step 4; we check
    # only the required body sections to stay permissive on layout.
    required_sections = [
        "## Test results",
        "## Validator results",
        "## Invariant verification",
        "## Adjacent code regression check",
    ]
    missing = [s for s in required_sections if s not in text]
    assert not missing, f"templates/sweep-notes.md missing body sections: {missing}"


# ---------------------------------------------------------------------------
# Sub-test 4: templates/adr-frontmatter.yaml
# ---------------------------------------------------------------------------


def test_adr_frontmatter_template_keys() -> None:
    """``templates/adr-frontmatter.yaml`` is parseable YAML and carries every
    key the live ADR shape uses per plan F2.2 Step 1.
    """
    assert ADR_FRONTMATTER.exists(), "templates/adr-frontmatter.yaml not found"
    raw = ADR_FRONTMATTER.read_text()
    assert len(raw) > 200, (
        f"templates/adr-frontmatter.yaml must be >200 chars; got {len(raw)}"
    )

    # Strip leading YAML document markers if present (`---`); pyyaml handles them.
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict), (
        "templates/adr-frontmatter.yaml must parse as a YAML mapping"
    )

    required = {
        "id",
        "name",
        "status",
        "firmness",
        "date",
        "topic",
        "invariants-touched",
        "supersedes",
        "superseded-by",
    }
    missing = required - set(parsed.keys())
    assert not missing, (
        f"templates/adr-frontmatter.yaml missing keys: {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# Sub-test 5: templates/active-envelope.yaml (FLI-5)
# ---------------------------------------------------------------------------


def test_active_envelope_template_default_mode_off_and_self_pattern() -> None:
    """``templates/active-envelope.yaml`` defaults to ``mode: off`` and the
    commented example block contains the self-pattern
    ``^\\.claude/active-envelope\\.yaml$`` per FLI-5 (intent.md line 50) and
    plan F2.2 Step 1.
    """
    assert ACTIVE_ENVELOPE.exists(), "templates/active-envelope.yaml not found"
    raw = ACTIVE_ENVELOPE.read_text()
    assert len(raw) > 200, (
        f"templates/active-envelope.yaml must be >200 chars; got {len(raw)}"
    )

    # Active YAML lines (non-comment) parse to a mapping with mode: off.
    active_yaml = "\n".join(
        line for line in raw.splitlines() if not line.lstrip().startswith("#")
    )
    parsed = yaml.safe_load(active_yaml) or {}
    assert isinstance(parsed, dict), (
        "templates/active-envelope.yaml active block must parse as a mapping"
    )
    mode = parsed.get("mode")
    # YAML parses bare `off` to False; accept either the boolean or the
    # string-quoted form.
    assert mode in (False, "off"), (
        f"templates/active-envelope.yaml must default to 'mode: off' per FLI-5; "
        f"got mode={mode!r}"
    )

    # Self-pattern must appear in the commented example block.
    self_pattern_present = (
        r"^\.claude/active-envelope\.yaml$" in raw
        or r"^\\.claude/active-envelope\\.yaml$" in raw
    )
    assert self_pattern_present, (
        r"templates/active-envelope.yaml must include the self-pattern "
        r"'^\.claude/active-envelope\.yaml$' in its commented example "
        r"block per FLI-5 (intent.md line 50)."
    )

    # The self-pattern must live in a comment line (it is the *example*, not
    # the active default — the default is mode: off with no paths list).
    self_pattern_in_comment = any(
        line.lstrip().startswith("#") and r"^\.claude/active-envelope\.yaml$" in line
        for line in raw.splitlines()
    )
    assert self_pattern_in_comment, (
        "Self-pattern must appear inside the commented `paths:` example "
        "block, not as an active default, per plan F2.2 Step 6."
    )
