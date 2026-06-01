"""Claude dynamic workflow mapping for Cairn workflow registry nodes."""

from __future__ import annotations

import json

from lib.workflow_registry import (
    WorkflowRegistryError,
    nodes_by_id,
    validate_cairn_intent_workflow,
    validate_workflow_document,
)


def plan_claude_dynamic_runs(workflow: dict) -> list[dict]:
    """Return the dynamic workflow runs declared by a workflow registry document."""
    _raise_for_invalid_workflow(workflow)
    runs = workflow["executors"]["claude_dynamic_workflows"]["runs"]
    return [
        {
            "id": run["id"],
            "nodes": list(run["nodes"]),
            "human_signoff_after": run["human_signoff_after"],
            "before": run.get("before", ""),
            "after": run.get("after", ""),
        }
        for run in runs
    ]


def render_dynamic_workflow_prompt(workflow: dict, run_id: str) -> str:
    """Render the prompt used to ask Claude Code to run one dynamic workflow stage."""
    run = _find_run(workflow, run_id)
    nodes = nodes_by_id(workflow)
    node_sections = [_render_node_prompt(nodes[node_id]) for node_id in run["nodes"]]
    return "\n\n".join(
        [
            f"Run Cairn workflow stage `{run_id}` for registry `{workflow['id']}`.",
            "Use Claude Code dynamic workflows only for this bounded stage. "
            "Do not continue into construction or close; the human sign-off "
            "boundary after this run is mandatory.",
            "Workflow runtime constraints: no mid-run user input; the workflow "
            "script coordinates agents; agents perform file and shell work.",
            f"Before: {run.get('before', '')}",
            f"After: {run.get('after', '')}",
            *node_sections,
        ]
    )


def render_dynamic_workflow_script_draft(workflow: dict, run_id: str) -> str:
    """Render a reviewable JavaScript draft for one dynamic workflow run.

    The draft is intentionally not written under .claude/workflows/. The registry
    save policy requires reviewing and dogfooding a generated script before it
    becomes a reusable project workflow.
    """
    run = _find_run(workflow, run_id)
    nodes = nodes_by_id(workflow)
    contract_nodes = [nodes[node_id] for node_id in run["nodes"]]
    payload = {
        "workflow": workflow["id"],
        "run": {
            "id": run["id"],
            "nodes": run["nodes"],
            "human_signoff_after": run["human_signoff_after"],
        },
        "save_policy": workflow["executors"]["claude_dynamic_workflows"].get(
            "save_policy", ""
        ),
        "nodes": contract_nodes,
    }
    payload_json = json.dumps(payload, indent=2, sort_keys=True)
    return f"""/*
Generated Cairn dynamic workflow draft for {run_id}.

Review and dogfood this generated script before saving it under .claude/workflows/.
Agents perform all file and shell work; this script is orchestration-only.
*/

const cairnRunContract = {payload_json};

function buildPrompt(node) {{
  return [
    `Cairn node: ${{node.id}}`,
    `Role: ${{node.role.name}}`,
    `Charter: ${{node.role.charter}}`,
    `Prompt:\\n${{node.prompt}}`,
    `Allowed inputs: ${{node.allowed_inputs.join(", ")}}`,
    `Write envelope: ${{node.write_envelope.paths.join(", ")}}`,
    `Evidence: ${{node.evidence.map((item) => item.id).join(", ")}}`,
    `Pass output: ${{node.pass_output.status}}`,
    `Fail output: ${{node.fail_output.status}}`,
  ].join("\\n\\n");
}}

export default async function run(runtime) {{
  const results = [];
  for (const node of cairnRunContract.nodes) {{
    results.push(await runtime.runAgent({{
      name: node.role.name,
      prompt: buildPrompt(node),
    }}));
  }}
  return {{
    workflow: cairnRunContract.workflow,
    run: cairnRunContract.run.id,
    humanSignoffRequired: cairnRunContract.run.human_signoff_after,
    results,
  }};
}}
"""


def _render_node_prompt(node: dict) -> str:
    evidence_lines = [
        f"- {item['id']}: {item['description']}" for item in node["evidence"]
    ]
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
            *[f"- {item}" for item in node["write_envelope"]["paths"]],
            "",
            "Evidence requirements:",
            *evidence_lines,
            "",
            f"Pass output: {node['pass_output']['status']} "
            f"({', '.join(node['pass_output']['fields'])})",
            f"Fail output: {node['fail_output']['status']} "
            f"({', '.join(node['fail_output']['fields'])})",
        ]
    )


def _find_run(workflow: dict, run_id: str) -> dict:
    _raise_for_invalid_workflow(workflow)
    for run in workflow["executors"]["claude_dynamic_workflows"]["runs"]:
        if run.get("id") == run_id:
            return run
    raise WorkflowRegistryError(f"unknown Claude dynamic workflow run: {run_id}")


def _raise_for_invalid_workflow(workflow: dict) -> None:
    if workflow.get("id") == "cairn-intent":
        errors = validate_cairn_intent_workflow(workflow)
    else:
        errors = validate_workflow_document(workflow)
    if errors:
        raise WorkflowRegistryError("; ".join(errors))
    executors = workflow.get("executors", {})
    claude = executors.get("claude_dynamic_workflows", {})
    runs = claude.get("runs", [])
    if not runs:
        raise WorkflowRegistryError("workflow declares no Claude dynamic workflow runs")
