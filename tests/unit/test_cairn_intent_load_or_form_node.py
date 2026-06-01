"""Coverage for the cairn-intent workflow's load-or-form-intent node — the carrier's
unconditional fallback (ADR using-cairn-carrier-contract D4).

test_cairn_intent_workflow.py pins workflow topology; it does not assert that load-or-form runs
in-conversation and REQUIRES the intent-pointer evidence. That gap matters: a silent (non-firing)
carrier must not be able to strand the loop — Step 1 resolves the intent on disk regardless. This
test closes the gap the close-review of the deferred-carrier approach identified.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW = CAIRN_ROOT / "workflows" / "cairn-intent.yaml"


def _node(node_id: str) -> dict:
    workflow = yaml.safe_load(WORKFLOW.read_text())
    return {node["id"]: node for node in workflow["nodes"]}[node_id]


def test_load_or_form_runs_in_conversation_not_a_fresh_agent():
    assert _node("load-or-form-intent")["execution"]["executor"] == "conversation"


def test_load_or_form_requires_intent_pointer_evidence():
    evidence = {e["id"]: e for e in _node("load-or-form-intent")["evidence"]}
    assert evidence["intent-pointer"]["required"] is True


def test_load_or_form_has_no_carrier_dependency():
    # Inputs are the conversation + handoff + intent file on disk — not a carrier signal.
    inputs = " ".join(_node("load-or-form-intent")["allowed_inputs"]).lower()
    assert "handoff" in inputs
    assert "carrier" not in inputs
