"""Conformance contract for the canonical Claude-side cairn-intent + using-cairn skills
(ADR using-cairn-carrier-contract D1/D4).

Pins only the mechanical surface: the skill files exist, their frontmatter PARSES (the F1
unquoted-colon-space YAML regression guard), the cairn-intent skill dispatches both
fresh-context agents by name, and its Step 1 load-or-form runs unconditionally as the carrier's
fallback. Loop behaviour is the Trial-E integration test, not here.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS = CAIRN_ROOT / ".claude" / "skills"
CAIRN_INTENT = SKILLS / "cairn-intent" / "SKILL.md"
USING_CAIRN = SKILLS / "using-cairn" / "SKILL.md"


def _frontmatter_and_body(text: str) -> tuple[dict, str]:
    assert text.startswith("---\n"), "skill must open with YAML frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    return yaml.safe_load(frontmatter), body


def test_cairn_intent_skill_exists_and_frontmatter_parses():
    frontmatter, _ = _frontmatter_and_body(CAIRN_INTENT.read_text())
    assert frontmatter["name"] == "cairn-intent"


def test_using_cairn_skill_exists_and_frontmatter_parses():
    # Regression guard for the F1 unquoted-colon-space bug that broke YAML parsing.
    frontmatter, _ = _frontmatter_and_body(USING_CAIRN.read_text())
    assert frontmatter["name"] == "using-cairn"


def test_cairn_intent_dispatches_both_fresh_context_agents():
    body = CAIRN_INTENT.read_text()
    assert "intent-challenge" in body, (
        "cairn-intent must dispatch the front-loaded challenge agent"
    )
    assert "intent-review" in body, (
        "cairn-intent must dispatch the fresh close-review agent"
    )


def test_cairn_intent_step1_is_the_unconditional_carrier_fallback():
    body = CAIRN_INTENT.read_text().lower()
    assert "load-or-form" in body or "load or form" in body
    # The carrier never gates; Step 1 runs regardless of whether it fired (D4/D5).
    assert "optimization, not the only path" in body, (
        "cairn-intent must state the carrier is an optimization, not the only path"
    )


def test_cairn_intent_does_not_duplicate_codex_dispatch():
    # Reconciliation: the Claude skill dispatches .claude/agents personas via the Agent tool;
    # it explicitly does NOT render Codex dispatch briefs (the Codex plugin owns that).
    body = CAIRN_INTENT.read_text()
    assert "Codex" in body, (
        "cairn-intent must name the Codex boundary to avoid duplicating it"
    )
