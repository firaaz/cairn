"""Claude dynamic workflow executor mapping for Cairn registry nodes."""

from __future__ import annotations

from pathlib import Path

from lib.claude_workflow_executor import (
    plan_claude_dynamic_runs,
    render_dynamic_workflow_prompt,
    render_dynamic_workflow_script_draft,
)
from lib.workflow_registry import load_workflow

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


def test_executor_maps_only_decorrelation_nodes_to_dynamic_workflows():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    runs = plan_claude_dynamic_runs(workflow)

    assert [run["id"] for run in runs] == [
        "cairn-intent-challenge",
        "cairn-intent-close-review",
    ]
    assert runs[0]["nodes"] == ["intent-challenge"]
    assert runs[1]["nodes"] == ["close-review"]


def test_challenge_prompt_preserves_node_contract():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    prompt = render_dynamic_workflow_prompt(workflow, "cairn-intent-challenge")

    assert "intent-challenge" in prompt
    assert "intent-challenger" in prompt
    assert "Allowed inputs" in prompt
    assert ".claude/skill-runs/<feature>/intent.md" in prompt
    assert "Write envelope" in prompt
    assert "^\\.claude/skill-runs/[^/]+/intent-challenge\\.md$" in prompt
    assert "premise-source-checks" in prompt
    assert "challenge-pass" in prompt
    assert "challenge-blocked" in prompt


def test_script_draft_is_orchestration_only_and_mentions_save_policy():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    script = render_dynamic_workflow_script_draft(workflow, "cairn-intent-close-review")

    assert "cairn-intent-close-review" in script
    assert "close-review" in script
    assert "close-reviewer" in script
    assert ".claude/workflows/" in script
    assert "Agents perform all file and shell work" in script
    assert "require(" not in script
    assert "import fs" not in script
    assert "child_process" not in script
