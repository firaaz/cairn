"""Structure contract for the intent-challenge subagent, pinned to the
cairn-intent workflow node so the agent prose can never drift from the machine
contract the executors render.

The semantic challenge itself (does the source MEAN what the intent claims) is
the agent's LLM judgment, verified in the Trial-E integration per ADR
intent-management-loop D9 — not here. This test pins only the mechanical
surface: the two verdict envelopes, the evidence ids, the report-only write
path, and the explicit slice-#25 obligation.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_PATH = CAIRN_ROOT / ".claude" / "agents" / "intent-challenge.md"
WORKFLOW_PATH = CAIRN_ROOT / "workflows" / "cairn-intent.yaml"


def _node() -> dict:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text())
    return {node["id"]: node for node in workflow["nodes"]}["intent-challenge"]


def _frontmatter_and_body(text: str) -> tuple[dict, str]:
    assert text.startswith("---\n"), "agent file must open with YAML frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    return yaml.safe_load(frontmatter), body


def test_agent_file_exists():
    assert AGENT_PATH.is_file()


def test_frontmatter_name_is_intent_challenge():
    frontmatter, _ = _frontmatter_and_body(AGENT_PATH.read_text())
    assert frontmatter["name"] == "intent-challenge"


def test_tools_grant_write_and_body_constrains_it_to_the_report_path():
    frontmatter, body = _frontmatter_and_body(AGENT_PATH.read_text())
    # The node is write_envelope.mode == report-only with a single path, but a
    # Claude subagent needs the Write tool to emit that one report.
    assert "Write" in frontmatter["tools"]
    report_path = _node()["write_envelope"]["paths"][0]
    assert report_path in body, "body must name the single allowed report path"


def test_body_pins_both_verdict_envelopes_from_the_node_contract():
    body = AGENT_PATH.read_text()
    node = _node()
    assert node["pass_output"]["status"] in body
    assert node["fail_output"]["status"] in body
    for field in node["pass_output"]["fields"] + node["fail_output"]["fields"]:
        assert field in body, f"verdict field absent from agent body: {field}"


def test_body_names_all_required_evidence_ids():
    body = AGENT_PATH.read_text()
    for item in _node()["evidence"]:
        assert item["id"] in body, f"evidence id absent: {item['id']}"


def test_body_carries_the_slice25_semantic_obligation():
    body = AGENT_PATH.read_text().lower()
    # The agent owns exactly the gap premise_guard cannot: a verbatim-grounded
    # quote whose label/claim misrepresents the source.
    assert "slice-#25" in body or "slice #25" in body
    assert "premise_guard" in body
    assert "label" in body
