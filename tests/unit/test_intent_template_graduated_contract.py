"""Graduated-contract + completeness-floor template contract (ADR
intent-management-loop D3).

D3 makes the ``## Contract`` block's DEPTH graduate by change size, with a
completeness floor: a one-line ``scope-statement`` the front-challenge attacks,
and contract-depth the close-review smell-tests against diff size. There is NO
hard cardinality gate — enforcement lives in the subagents, not in a mechanical
clause-count check. So this test pins only the TEMPLATE GUIDANCE that D3 adds:

  1. the four exception-tag names (parity with the live atomicity tag set),
  2. the one-line ``scope-statement`` completeness-floor requirement,
  3. the graduation rule (trivial → one-liner; medium/heavy → full grammar +
     premise grounding),
  4. that the floor is enforced by the front-challenge / close-review, not by
     the mechanical gate.

These are template-prose assertions. The atomicity MECHANISM (the gate, the
shy heuristic, the validator assertion) is unchanged and stays pinned by
``test_atomicity*`` and ``test_template_extraction``. ADD-not-REPLACE: the
eight-heading-in-order + parseable-contract assertions there must stay green.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
INTENT = CAIRN_ROOT / "templates" / "intent.md"


def _read() -> str:
    assert INTENT.exists(), f"template not found: {INTENT}"
    return INTENT.read_text()


def _contract_section(text: str) -> str:
    """Return the text of the ``## Contract`` section (heading to EOF or next
    top-level heading)."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "## Contract"), None)
    assert start is not None, "templates/intent.md must contain a '## Contract' heading"
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_four_exception_tags_documented_match_live_tag_set() -> None:
    """The four tag names in the template equal the live
    ``scripts/lib/atomicity.EXCEPTION_TAGS`` exactly (D3 dial parity)."""
    from lib.atomicity import EXCEPTION_TAGS

    section = _contract_section(_read())
    for tag in EXCEPTION_TAGS:
        assert tag in section, (
            f"templates/intent.md '## Contract' section must document the "
            f"exception tag {tag!r} (D3 graduated dial)."
        )


def test_scope_statement_completeness_floor_required() -> None:
    """The contract documents the one-line ``scope-statement`` completeness
    floor (D3). RED at HEAD: the template has no scope-statement requirement."""
    section = _contract_section(_read())
    assert "scope-statement" in section, (
        "templates/intent.md '## Contract' must require a one-line "
        "'scope-statement' (D3 completeness floor)."
    )
    lowered = section.lower()
    assert "completeness floor" in lowered, (
        "the scope-statement must be named the completeness floor (D3)."
    )


def test_graduation_rule_documented() -> None:
    """The contract documents that depth GRADUATES by size — trivial work is a
    one-liner; heavy work is the full grammar + premise grounding (D3).

    RED at HEAD: no graduation guidance exists in the template."""
    lowered = _contract_section(_read()).lower()
    assert "graduat" in lowered, (
        "templates/intent.md '## Contract' must document that contract depth "
        "graduates by change size (D3)."
    )
    assert "trivial" in lowered, "graduation must name the trivial (one-liner) floor."
    assert "premise grounding" in lowered, (
        "graduation must say heavy work adds premise grounding."
    )


def test_floor_is_subagent_enforced_not_a_cardinality_gate() -> None:
    """D3: the floor is attacked by the front-challenge and smell-tested by the
    close-review — there is NO hard cardinality gate. The template must say so
    so a reader does not expect the mechanical gate to enforce depth."""
    lowered = _contract_section(_read()).lower()
    assert "no hard cardinality gate" in lowered or "no cardinality gate" in lowered, (
        "the contract must state there is no hard cardinality gate (D3)."
    )
    assert "front-challenge" in lowered or "intent-challenge" in lowered, (
        "the contract must name the front-challenge as the scope-statement attacker."
    )
    assert "close-review" in lowered, (
        "the contract must name the close-review as the depth-vs-diff smell test."
    )


def test_trivial_worked_example_is_floor_only_and_parses() -> None:
    """The first contract fence is the trivial worked example: a
    ``scope-statement`` plus exactly one bare ``must-satisfy`` clause, and it
    parses as a YAML mapping (the floor a graduated contract may stop at)."""
    section = _contract_section(_read())
    lines = section.splitlines()
    fence_open = next(
        (i for i, ln in enumerate(lines) if ln.strip().startswith("```")), None
    )
    assert fence_open is not None, "contract section must carry a fenced yaml example"
    fence_close = next(
        (i for i in range(fence_open + 1, len(lines)) if lines[i].strip() == "```"),
        None,
    )
    assert fence_close is not None, "first contract fence must close"
    block = "\n".join(lines[fence_open + 1 : fence_close])
    parsed = yaml.safe_load(block)
    assert isinstance(parsed, dict), "trivial worked example must parse as a mapping"
    assert "scope-statement" in parsed, (
        "the trivial worked example must carry a scope-statement (the floor)."
    )
    assert "must-satisfy" in parsed and isinstance(parsed["must-satisfy"], list), (
        "the trivial worked example must carry a must-satisfy list."
    )
