"""RED tests for M3 fix: parse_assertion_blocks must handle nested YAML.

Tracks the INV-002 parser gap called out in
docs/plans/2026-05-06-cairn-shrink-design.md §1.1 and §2.2.

Public surface (existing): scripts/validate_architecture.parse_assertion_blocks
Import path note: cairn's pyproject sets pythonpath = ['scripts'].
"""

from __future__ import annotations

import textwrap


from validate_architecture import parse_assertion_blocks


def _block(body: str) -> str:
    """Wrap a body inside a fenced invariant-check block for INV-002."""
    return (
        textwrap.dedent(
            """
        # ARCHITECTURE.md fixture

        ## Invariants

        **INV-002** session-context fixture.

        ```invariant-check INV-002
        type: structural-parser
        target: ".claude/handoff.md"
        required-sections: ["State", "Next", "Blocked / Pending", "Pointers"]
        forbidden-sections:
          literal: ["What This Session Was About", "Self-Check"]
          regex: ['^##\\s+(Lessons|Reflection|Notes)\\b']
        forbidden-content:
          regex: ['I (was|am|will|just) ', '\\d+\\s*/\\s*\\d+']
        token-budget:
          approximation: bytes-per-token-4
          warn-at: 360
          fail-at: 440
        binding-effective-from: "<pending-slice-close-sha>"
        description: "INV-002(a) handoff structural binding"
        """
        )
        + body
        + "\n```\n"
    )


def test_required_sections_parsed_as_list_of_strings():
    """The required-sections key must arrive as a list, not a flat string."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    assert isinstance(inv["required-sections"], list)
    assert inv["required-sections"] == [
        "State",
        "Next",
        "Blocked / Pending",
        "Pointers",
    ]


def test_forbidden_sections_parsed_as_nested_dict():
    """forbidden-sections.literal and .regex must arrive as a dict-of-lists."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    fs = inv["forbidden-sections"]
    assert isinstance(fs, dict), f"Expected dict, got {type(fs).__name__}: {fs!r}"
    assert fs.get("literal") == [
        "What This Session Was About",
        "Self-Check",
    ]
    assert fs.get("regex") == ["^##\\s+(Lessons|Reflection|Notes)\\b"]


def test_forbidden_content_parsed_as_nested_dict():
    """forbidden-content.regex must arrive as a list under a dict key."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    fc = inv["forbidden-content"]
    assert isinstance(fc, dict), f"Expected dict, got {type(fc).__name__}: {fc!r}"
    assert fc.get("regex") == [
        "I (was|am|will|just) ",
        "\\d+\\s*/\\s*\\d+",
    ]


def test_token_budget_parsed_as_nested_dict_with_ints():
    """token-budget.warn-at and .fail-at must arrive as ints under a dict key."""
    blocks = parse_assertion_blocks(_block(""))
    inv = blocks["INV-002"]
    tb = inv["token-budget"]
    assert isinstance(tb, dict), f"Expected dict, got {type(tb).__name__}: {tb!r}"
    assert tb.get("warn-at") == 360
    assert tb.get("fail-at") == 440
    assert tb.get("approximation") == "bytes-per-token-4"


def test_flat_keys_still_parse_for_legacy_blocks():
    """A flat block (e.g., INV-007's grep type) must still parse correctly."""
    text = textwrap.dedent(
        """
        ## Invariants

        **INV-007** fixture.

        ```invariant-check INV-007
        type: grep
        pattern: '\\.claude/features/'
        target: "commands/claude-code/handoff.full.md"
        expect: match
        description: "Verifies handoff command references feature files"
        ```
        """
    )
    blocks = parse_assertion_blocks(text)
    inv = blocks["INV-007"]
    assert inv["type"] == "grep"
    assert inv["target"] == "commands/claude-code/handoff.full.md"
    assert inv["expect"] == "match"


def test_real_architecture_md_parses_inv_002_contract_ref_correctly():
    """Integration: real ARCHITECTURE.md pins INV-002 to the handoff contract tests."""
    from pathlib import Path

    cairn_root = Path(__file__).resolve().parents[2]
    arch = (cairn_root / "docs/ARCHITECTURE.md").read_text()
    blocks = parse_assertion_blocks(arch)
    inv = blocks["INV-002"]
    assert inv["type"] == "test-ref"
    assert inv["pattern"] == "tests/unit/test_handoff_contract.py"
