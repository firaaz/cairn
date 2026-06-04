"""Cairn-intent workflow invariants from intent-management-loop D2/D9."""

from __future__ import annotations

import re
from pathlib import Path

from lib.workflow_registry import (
    load_workflow,
    nodes_by_id,
    validate_cairn_intent_workflow,
)

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


def _path_is_permitted(patterns: list[str], path: str) -> bool:
    return any(re.search(pattern, path) for pattern in patterns)


def test_cairn_intent_has_challenge_and_review_nodes_with_no_same_context_fallback():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")
    nodes = nodes_by_id(workflow)

    assert "intent-challenge" in nodes
    assert "close-review" in nodes

    for node_id in ("intent-challenge", "close-review"):
        execution = nodes[node_id]["execution"]
        assert execution["executor"] == "fresh_agent"
        assert execution["context"] == "fresh"
        assert execution["same_context_fallback"] is False


def test_cairn_intent_keeps_construction_out_of_fresh_agent_runs():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")
    nodes = nodes_by_id(workflow)
    claude_runs = workflow["executors"]["claude_dynamic_workflows"]["runs"]
    codex_runs = workflow["executors"]["codex_agents"]["runs"]

    assert nodes["construct"]["execution"]["executor"] == "conversation"
    for runs in (claude_runs, codex_runs):
        assert all("construct" not in run["nodes"] for run in runs)
        assert all("close" not in run["nodes"] for run in runs)


def test_cairn_intent_close_observations_use_dated_operator_field_notes():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")
    close_paths = nodes_by_id(workflow)["close"]["write_envelope"]["paths"]

    assert _path_is_permitted(
        close_paths,
        "docs/operator-field-notes-2026-06-02.md",
    )
    assert not _path_is_permitted(close_paths, "docs/dogfood-log.md")


def test_cairn_intent_splits_all_fresh_agent_executors_at_human_signoff_boundaries():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")
    claude_runs = workflow["executors"]["claude_dynamic_workflows"]["runs"]
    codex_runs = workflow["executors"]["codex_agents"]["runs"]

    for runs in (claude_runs, codex_runs):
        assert [run["id"] for run in runs] == [
            "cairn-intent-challenge",
            "cairn-intent-close-review",
        ]
        assert [run["nodes"] for run in runs] == [
            ["intent-challenge"],
            ["close-review"],
        ]
        assert all(run["human_signoff_after"] is True for run in runs)


def test_cairn_intent_domain_validation_rejects_transport_specific_fresh_nodes():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")
    nodes = nodes_by_id(workflow)
    nodes["intent-challenge"]["execution"]["executor"] = "claude_dynamic_workflow"

    errors = validate_cairn_intent_workflow(workflow)

    assert "intent-challenge: executor must be fresh_agent" in errors


def test_cairn_intent_domain_validation_rejects_codex_construct_runs():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")
    workflow["executors"]["codex_agents"]["runs"][0]["nodes"].append("construct")

    errors = validate_cairn_intent_workflow(workflow)

    assert (
        "cairn-intent-challenge: Codex run must not include construct/close" in errors
    )


def test_cairn_intent_domain_validation_passes():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    assert validate_cairn_intent_workflow(workflow) == []
