"""Codex agent executor mapping for Cairn registry nodes."""

from __future__ import annotations

from pathlib import Path

from lib.codex_workflow_executor import (
    plan_codex_agent_runs,
    render_codex_agent_prompt,
    render_codex_dispatch_brief,
    render_codex_guard_commands,
)
from lib.workflow_registry import load_workflow

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


def test_codex_executor_maps_only_fresh_agent_decorrelation_nodes():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    runs = plan_codex_agent_runs(workflow)

    assert [run["id"] for run in runs] == [
        "cairn-intent-challenge",
        "cairn-intent-close-review",
    ]
    assert runs[0]["nodes"] == ["intent-challenge"]
    assert runs[1]["nodes"] == ["close-review"]
    assert all(run["spawn_agent"]["agent_type"] == "worker" for run in runs)
    assert all(run["spawn_agent"]["fork_context"] is False for run in runs)


def test_codex_prompt_preserves_node_contract_and_json_statuses():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    prompt = render_codex_agent_prompt(workflow, "cairn-intent-challenge")

    assert "intent-challenge" in prompt
    assert "intent-challenger" in prompt
    assert "Allowed inputs" in prompt
    assert ".claude/skill-runs/<feature>/intent.md" in prompt
    assert "Write envelope" in prompt
    assert "^\\.claude/skill-runs/[^/]+/intent-challenge\\.md$" in prompt
    assert "Evidence requirements" in prompt
    assert "premise-source-checks" in prompt
    assert "semantic-counterfactual-search" in prompt
    assert "Final response must be JSON" in prompt
    assert '"status": "challenge-pass"' in prompt
    assert '"status": "challenge-blocked"' in prompt


def test_codex_dispatch_brief_names_spawn_agent_worker_without_context_fork():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    brief = render_codex_dispatch_brief(workflow, "cairn-intent-close-review")

    assert "spawn_agent" in brief
    assert '"agent_type": "worker"' in brief
    assert '"fork_context": false' in brief
    assert "close-review" in brief
    assert "close-review-pass" in brief
    assert "close-review-blocked" in brief


def test_codex_dispatch_brief_names_automatic_hooks_and_guard_evidence():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    brief = render_codex_dispatch_brief(workflow, "cairn-intent-challenge")

    assert "Guard evidence and fallback commands:" in brief
    assert (
        "Codex plugin hooks run automatically when the plugin is loaded and trusted"
        in brief
    )
    assert "no plugin.json hooks registration field" not in brief
    assert "instead of claiming hook parity" not in brief
    assert "checks/premise_guard.py" in brief
    assert "checks/atomicity_guard.py" in brief
    assert "checks/reversibility-guard.sh" in brief


def test_codex_guard_fallback_commands_include_challenge_stage_gates():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    commands = render_codex_guard_commands(workflow, "cairn-intent-challenge")

    assert any("checks/premise_guard.py" in command for command in commands)
    assert any("checks/atomicity_guard.py" in command for command in commands)
    assert any("write envelope" in command for command in commands)
    assert any("checks/reversibility-guard.sh" in command for command in commands)
