"""Codex agent workflow mapping for Cairn registry nodes."""

from __future__ import annotations

import json
import shlex

from lib.workflow_registry import (
    WorkflowRegistryError,
    nodes_by_id,
    validate_cairn_intent_workflow,
    validate_workflow_document,
)

_HOOK_FALLBACK_NOTE = (
    "Codex plugin hooks run automatically when the plugin is loaded and trusted. "
    "Keep explicit guard commands as fallback/manual evidence, and run them for "
    "non-hooked premise and atomicity gates."
)


def plan_codex_agent_runs(workflow: dict) -> list[dict]:
    """Return Codex spawn-agent runs declared by a workflow registry document."""
    _raise_for_invalid_workflow(workflow)
    executor = _codex_executor(workflow)
    runs = executor["runs"]
    return [
        {
            "id": run["id"],
            "nodes": list(run["nodes"]),
            "human_signoff_after": run["human_signoff_after"],
            "before": run.get("before", ""),
            "after": run.get("after", ""),
            "spawn_agent": {
                "agent_type": "worker",
                "fork_context": False,
            },
            "guard_commands": render_codex_guard_commands(workflow, run["id"]),
        }
        for run in runs
    ]


def render_codex_agent_prompt(workflow: dict, run_id: str) -> str:
    """Render the prompt sent as the Codex worker agent message for one run."""
    run = _find_run(workflow, run_id)
    nodes = nodes_by_id(workflow)
    node_sections = [_render_node_prompt(nodes[node_id]) for node_id in run["nodes"]]
    return "\n\n".join(
        [
            f"Run Cairn workflow stage `{run_id}` for registry `{workflow['id']}`.",
            "You are a fresh Codex worker agent for this bounded stage. Do not "
            "continue into construction or close; the human sign-off boundary "
            "after this run is mandatory.",
            "Runtime constraints: fork_context is false, so use only the inputs "
            "listed in the node contract and live repository inspection. Do not "
            "request same-context fallback.",
            f"Before: {run.get('before', '')}",
            f"After: {run.get('after', '')}",
            *node_sections,
        ]
    )


def render_codex_dispatch_brief(workflow: dict, run_id: str) -> str:
    """Render a reviewable Codex dispatch packet for one fresh-agent run."""
    run = _find_run(workflow, run_id)
    packet = {
        "spawn_agent": {
            "agent_type": "worker",
            "fork_context": False,
            "message": render_codex_agent_prompt(workflow, run_id),
        }
    }
    commands = render_codex_guard_commands(workflow, run_id)
    return "\n".join(
        [
            f"Codex dispatch brief for `{run_id}`.",
            "Call `spawn_agent` with this packet:",
            json.dumps(packet, indent=2, sort_keys=True),
            "",
            "Guard evidence and fallback commands:",
            _HOOK_FALLBACK_NOTE,
            *[f"- {command}" for command in commands],
            "",
            "Human sign-off after run: "
            + ("required" if run["human_signoff_after"] else "not required"),
        ]
    )


def render_codex_guard_commands(workflow: dict, run_id: str) -> list[str]:
    """Return explicit guard commands for fallback/manual evidence."""
    run = _find_run(workflow, run_id)
    nodes = nodes_by_id(workflow)
    commands: list[str] = []
    if "intent-challenge" in run["nodes"]:
        commands.extend(
            [
                "uv run python checks/premise_guard.py <intent_path>",
                "uv run python checks/atomicity_guard.py <intent_path>",
            ]
        )
    for node_id in run["nodes"]:
        commands.append(_write_envelope_command(nodes[node_id]))
    commands.append(
        "printf '%s\\n' "
        '\'{"tool_name":"Bash",'
        '"tool_input":{"command":"<candidate command>"}}\' '
        "| bash checks/reversibility-guard.sh"
    )
    return commands


def _render_node_prompt(node: dict) -> str:
    evidence_lines = [
        f"- {item['id']}: {item['description']}" for item in node["evidence"]
    ]
    pass_json = _output_json_example(node["pass_output"])
    fail_json = _output_json_example(node["fail_output"])
    return "\n".join(
        [
            f"## Node `{node['id']}`",
            f"Role: {node['role']['name']}",
            f"Charter: {node['role']['charter']}",
            "",
            "Prompt:",
            node["prompt"].strip(),
            "",
            "Allowed inputs:",
            *[f"- {item}" for item in node["allowed_inputs"]],
            "",
            "Write envelope:",
            f"- mode: {node['write_envelope']['mode']}",
            *[f"- path: {item}" for item in node["write_envelope"]["paths"]],
            "",
            "Evidence requirements:",
            *evidence_lines,
            "",
            f"Pass output fields: {', '.join(node['pass_output']['fields'])}",
            f"Fail output fields: {', '.join(node['fail_output']['fields'])}",
            "",
            "Final response must be JSON with a status matching this node's "
            "pass/fail contract. Use exactly one of these status envelopes:",
            pass_json,
            fail_json,
        ]
    )


def _output_json_example(output: dict) -> str:
    payload = {"status": output["status"]}
    for field in output["fields"]:
        payload[field] = f"<{field}>"
    return json.dumps(payload, indent=2)


def _write_envelope_command(node: dict) -> str:
    patterns_json = json.dumps(node["write_envelope"]["paths"])
    code = (
        "import json, re, subprocess, sys; "
        f"patterns=json.loads({patterns_json!r}); "
        "changed=set(subprocess.check_output("
        "['git','diff','--name-only'], text=True).splitlines()); "
        "changed.update(subprocess.check_output("
        "['git','ls-files','--others','--exclude-standard'], "
        "text=True).splitlines()); "
        "bad=[path for path in sorted(changed) "
        "if not any(re.fullmatch(pattern, path) for pattern in patterns)]; "
        "print('write envelope OK' if not bad "
        "else 'write envelope violation: ' + ', '.join(bad)); "
        "sys.exit(1 if bad else 0)"
    )
    return "uv run python -c " + shlex.quote(code)


def _find_run(workflow: dict, run_id: str) -> dict:
    _raise_for_invalid_workflow(workflow)
    for run in _codex_executor(workflow)["runs"]:
        if run.get("id") == run_id:
            return run
    raise WorkflowRegistryError(f"unknown Codex agent run: {run_id}")


def _codex_executor(workflow: dict) -> dict:
    executors = workflow.get("executors", {})
    if not isinstance(executors, dict):
        raise WorkflowRegistryError("workflow declares no executors")
    codex = executors.get("codex_agents", {})
    if not isinstance(codex, dict) or not codex.get("runs"):
        raise WorkflowRegistryError("workflow declares no Codex agent runs")
    policy = codex.get("dispatch_policy", {})
    if not isinstance(policy, dict):
        raise WorkflowRegistryError("Codex executor dispatch_policy must be a mapping")
    if policy.get("tool", "spawn_agent") != "spawn_agent":
        raise WorkflowRegistryError("Codex executor must dispatch with spawn_agent")
    if policy.get("agent_type", "worker") != "worker":
        raise WorkflowRegistryError("Codex executor agent_type must be worker")
    if policy.get("fork_context", False) is not False:
        raise WorkflowRegistryError("Codex executor fork_context must be false")
    return codex


def _raise_for_invalid_workflow(workflow: dict) -> None:
    if workflow.get("id") != "cairn-intent":
        errors = validate_workflow_document(workflow)
        if errors:
            raise WorkflowRegistryError("; ".join(errors))
        raise WorkflowRegistryError("Codex executor is scoped to cairn-intent")
    errors = validate_cairn_intent_workflow(workflow)
    if errors:
        raise WorkflowRegistryError("; ".join(errors))
    _codex_executor(workflow)
