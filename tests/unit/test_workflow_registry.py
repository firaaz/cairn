"""Workflow registry schema coverage for Cairn-owned operating modes."""

from __future__ import annotations

from pathlib import Path

import yaml

from lib.workflow_registry import (
    load_workflow,
    validate_workflow_document,
)

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


def test_cairn_intent_registry_loads_with_required_node_contract_fields():
    workflow = load_workflow(CAIRN_ROOT / "workflows" / "cairn-intent.yaml")

    assert workflow["id"] == "cairn-intent"
    assert [node["id"] for node in workflow["nodes"]] == [
        "load-or-form-intent",
        "intent-challenge",
        "construct",
        "close-review",
        "close",
    ]

    for node in workflow["nodes"]:
        prefix = f"{node['id']}: "
        assert node["role"]["name"], prefix + "missing role name"
        assert node["role"]["charter"], prefix + "missing role charter"
        assert node["prompt"].strip(), prefix + "missing prompt"
        assert node["allowed_inputs"], prefix + "missing allowed inputs"
        assert node["write_envelope"]["mode"], prefix + "missing envelope mode"
        assert node["write_envelope"]["paths"], prefix + "missing envelope paths"
        assert node["evidence"], prefix + "missing evidence requirements"
        assert node["pass_output"]["status"], prefix + "missing pass status"
        assert node["pass_output"]["fields"], prefix + "missing pass fields"
        assert node["fail_output"]["status"], prefix + "missing fail status"
        assert node["fail_output"]["fields"], prefix + "missing fail fields"

        for requirement in node["evidence"]:
            assert requirement["id"], prefix + "evidence requirement missing id"
            assert requirement["description"], (
                prefix + f"evidence {requirement['id']} missing description"
            )
            assert requirement["required"] is True, (
                prefix + f"evidence {requirement['id']} must be required"
            )


def test_registry_schema_reports_duplicate_node_ids():
    data = yaml.safe_load(
        """
        schema_version: 1
        id: duplicate-test
        name: Duplicate Test
        nodes:
          - id: repeated
            role: {name: one, charter: First role}
            prompt: First prompt
            allowed_inputs: [input]
            write_envelope: {mode: operator, paths: ["^a$"]}
            evidence:
              - {id: e1, description: Evidence, required: true}
            pass_output: {status: pass, fields: [verdict]}
            fail_output: {status: fail, fields: [reason]}
            execution: {executor: conversation, context: current}
          - id: repeated
            role: {name: two, charter: Second role}
            prompt: Second prompt
            allowed_inputs: [input]
            write_envelope: {mode: operator, paths: ["^b$"]}
            evidence:
              - {id: e2, description: Evidence, required: true}
            pass_output: {status: pass, fields: [verdict]}
            fail_output: {status: fail, fields: [reason]}
            execution: {executor: conversation, context: current}
        """
    )

    errors = validate_workflow_document(data)

    assert "duplicate node id: repeated" in errors
