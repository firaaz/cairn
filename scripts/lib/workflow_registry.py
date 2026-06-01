"""Cairn workflow registry loading and validation."""

from __future__ import annotations

from pathlib import Path

import yaml

CAIRN_INTENT_NODE_IDS = [
    "load-or-form-intent",
    "intent-challenge",
    "construct",
    "close-review",
    "close",
]

CAIRN_INTENT_FRESH_AGENT_RUNS = [
    ("cairn-intent-challenge", ["intent-challenge"]),
    ("cairn-intent-close-review", ["close-review"]),
]
CAIRN_INTENT_DYNAMIC_RUNS = CAIRN_INTENT_FRESH_AGENT_RUNS


class WorkflowRegistryError(ValueError):
    """Raised when a workflow registry document is malformed."""


def load_workflow(path: str | Path) -> dict:
    """Load and validate a single workflow registry YAML document."""
    workflow_path = Path(path)
    try:
        data = yaml.safe_load(workflow_path.read_text())
    except OSError as exc:
        raise WorkflowRegistryError(f"{workflow_path}: unreadable: {exc}") from exc
    except yaml.YAMLError as exc:
        raise WorkflowRegistryError(f"{workflow_path}: invalid YAML: {exc}") from exc

    errors = validate_workflow_document(data)
    if errors:
        joined = "; ".join(errors)
        raise WorkflowRegistryError(f"{workflow_path}: {joined}")
    return data


def load_registry(root: str | Path) -> list[dict]:
    """Load every workflow YAML document in a registry directory."""
    registry_root = Path(root)
    workflows = []
    for path in sorted(registry_root.glob("*.yaml")):
        workflows.append(load_workflow(path))
    return workflows


def nodes_by_id(workflow: dict) -> dict[str, dict]:
    """Return workflow nodes keyed by id."""
    result: dict[str, dict] = {}
    for node in workflow.get("nodes", []):
        if isinstance(node, dict) and isinstance(node.get("id"), str):
            result[node["id"]] = node
    return result


def validate_workflow_document(data) -> list[str]:
    """Return schema errors for a workflow document."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["workflow document must be a mapping"]

    for field in ("schema_version", "id", "name", "nodes"):
        if field not in data:
            errors.append(f"missing required top-level field: {field}")

    if "id" in data and not _non_empty_string(data["id"]):
        errors.append("workflow id must be a non-empty string")
    if "name" in data and not _non_empty_string(data["name"]):
        errors.append("workflow name must be a non-empty string")
    if "nodes" in data and not isinstance(data["nodes"], list):
        errors.append("nodes must be a list")

    nodes = data.get("nodes") if isinstance(data.get("nodes"), list) else []
    seen: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}] must be a mapping")
            continue
        node_id = node.get("id")
        if not _non_empty_string(node_id):
            errors.append(f"nodes[{index}] missing non-empty id")
        elif node_id in seen:
            errors.append(f"duplicate node id: {node_id}")
        else:
            seen.add(node_id)
        errors.extend(_validate_node_contract(node, index))

    return errors


def validate_cairn_intent_workflow(workflow: dict) -> list[str]:
    """Return cairn-intent domain-specific validation errors."""
    errors = validate_workflow_document(workflow)
    if errors:
        return errors

    if workflow.get("id") != "cairn-intent":
        errors.append("cairn-intent validator requires workflow id 'cairn-intent'")

    node_ids = [node["id"] for node in workflow.get("nodes", [])]
    if node_ids != CAIRN_INTENT_NODE_IDS:
        errors.append(
            "cairn-intent nodes must be ordered as "
            + ", ".join(CAIRN_INTENT_NODE_IDS)
        )

    nodes = nodes_by_id(workflow)
    for node_id in ("intent-challenge", "close-review"):
        node = nodes.get(node_id)
        if node is None:
            errors.append(f"missing required decorrelation node: {node_id}")
            continue
        execution = node.get("execution", {})
        if execution.get("executor") != "fresh_agent":
            errors.append(f"{node_id}: executor must be fresh_agent")
        if execution.get("context") != "fresh":
            errors.append(f"{node_id}: context must be fresh")
        if execution.get("same_context_fallback") is not False:
            errors.append(f"{node_id}: same_context_fallback must be false")

    construct = nodes.get("construct", {})
    if construct.get("execution", {}).get("executor") != "conversation":
        errors.append("construct must remain a conversation node")

    _validate_cairn_intent_executor_runs(
        errors,
        "Claude dynamic",
        _dynamic_runs(workflow),
    )
    _validate_cairn_intent_executor_runs(
        errors,
        "Codex",
        _codex_agent_runs(workflow),
    )

    guards = workflow.get("guards", [])
    for guard in (
        "role_guard",
        "premise_guard",
        "atomicity_guard",
        "reversibility-guard",
    ):
        if guard not in guards:
            errors.append(f"cairn-intent must keep guard primitive: {guard}")

    return errors


def _validate_node_contract(node: dict, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"nodes[{index}]"

    role = node.get("role")
    if not isinstance(role, dict):
        errors.append(f"{prefix}.role must be a mapping")
    else:
        for field in ("name", "charter"):
            if not _non_empty_string(role.get(field)):
                errors.append(f"{prefix}.role.{field} must be a non-empty string")

    if not _non_empty_string(node.get("prompt")):
        errors.append(f"{prefix}.prompt must be a non-empty string")
    if not _non_empty_string_list(node.get("allowed_inputs")):
        errors.append(f"{prefix}.allowed_inputs must be a non-empty string list")

    envelope = node.get("write_envelope")
    if not isinstance(envelope, dict):
        errors.append(f"{prefix}.write_envelope must be a mapping")
    else:
        if not _non_empty_string(envelope.get("mode")):
            errors.append(f"{prefix}.write_envelope.mode must be a non-empty string")
        if not _non_empty_string_list(envelope.get("paths")):
            errors.append(f"{prefix}.write_envelope.paths must be a non-empty list")

    evidence = node.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{prefix}.evidence must be a non-empty list")
    else:
        for evidence_index, requirement in enumerate(evidence):
            errors.extend(
                _validate_evidence_requirement(requirement, prefix, evidence_index)
            )

    for output_field in ("pass_output", "fail_output"):
        output = node.get(output_field)
        if not isinstance(output, dict):
            errors.append(f"{prefix}.{output_field} must be a mapping")
            continue
        if not _non_empty_string(output.get("status")):
            errors.append(f"{prefix}.{output_field}.status must be non-empty")
        if not _non_empty_string_list(output.get("fields")):
            errors.append(f"{prefix}.{output_field}.fields must be non-empty")

    execution = node.get("execution")
    if not isinstance(execution, dict):
        errors.append(f"{prefix}.execution must be a mapping")
    else:
        if not _non_empty_string(execution.get("executor")):
            errors.append(f"{prefix}.execution.executor must be non-empty")
        if not _non_empty_string(execution.get("context")):
            errors.append(f"{prefix}.execution.context must be non-empty")

    return errors


def _validate_evidence_requirement(requirement, prefix: str, index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(requirement, dict):
        return [f"{prefix}.evidence[{index}] must be a mapping"]
    for field in ("id", "description"):
        if not _non_empty_string(requirement.get(field)):
            errors.append(
                f"{prefix}.evidence[{index}].{field} must be a non-empty string"
            )
    if requirement.get("required") is not True:
        errors.append(f"{prefix}.evidence[{index}].required must be true")
    return errors


def _dynamic_runs(workflow: dict) -> list:
    return _executor_runs(workflow, "claude_dynamic_workflows")


def _codex_agent_runs(workflow: dict) -> list:
    return _executor_runs(workflow, "codex_agents")


def _executor_runs(workflow: dict, executor_key: str) -> list:
    executors = workflow.get("executors", {})
    if not isinstance(executors, dict):
        return []
    executor = executors.get(executor_key, {})
    if not isinstance(executor, dict):
        return []
    runs = executor.get("runs", [])
    if not isinstance(runs, list):
        return []
    return runs


def _validate_cairn_intent_executor_runs(
    errors: list[str], label: str, runs: list
) -> None:
    expected_runs = [
        {"id": run_id, "nodes": node_ids}
        for run_id, node_ids in CAIRN_INTENT_FRESH_AGENT_RUNS
    ]
    actual_runs = [
        {"id": run.get("id"), "nodes": run.get("nodes")}
        for run in runs
        if isinstance(run, dict)
    ]
    if actual_runs != expected_runs:
        errors.append(
            f"cairn-intent {label} runs must split into "
            "cairn-intent-challenge and cairn-intent-close-review"
        )

    for run in runs:
        if not isinstance(run, dict):
            continue
        run_id = run.get("id", "<unknown>")
        if run.get("human_signoff_after") is not True:
            errors.append(f"{run_id}: {label} run must require sign-off after")
        if "construct" in run.get("nodes", []) or "close" in run.get("nodes", []):
            errors.append(f"{run_id}: {label} run must not include construct/close")


def _non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_string_list(value) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(_non_empty_string(item) for item in value)
