"""RED tests for M3 fix: INV-003 topology ignores legacy-slug sibling agent defs.

Tracks the M2 change: cairn-tdd-feature skill introduced phase-{1..4}-tdd.md
agents. M4-A2 promoted these to canonical and demoted the legacy
phase-{1..4}-{writer,skeptic,implementer,integrator}.md to siblings. The
topology binding must tolerate these siblings without flagging drift.

Out-of-scope guard: phase-5-foo.md MUST still fail (no phase-5 in role-topology.yaml).

Public surface (existing): scripts/validate_architecture.validate_phase_topology
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parents[2]


def _seed_canonical_only(tmp_path: Path) -> Path:
    """Copy the four canonical agent files + the three other canonical sources."""
    canonical_sources = [
        Path(".claude/agents/role-topology.yaml"),
        Path("docs/operational-reference.md"),
        Path("checks/role_guard.py"),
    ]
    canonical_agents = [
        Path(".claude/agents/phase-1-tdd.md"),
        Path(".claude/agents/phase-2-tdd.md"),
        Path(".claude/agents/phase-3-tdd.md"),
        Path(".claude/agents/phase-4-tdd.md"),
    ]
    for rel in canonical_sources + canonical_agents:
        src = CAIRN_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return tmp_path


def test_clean_tree_with_tdd_siblings_passes():
    """Live cairn HEAD: legacy-slug agent siblings exist and must not break the binding."""
    from validate_architecture import validate_phase_topology

    failures = validate_phase_topology(CAIRN_ROOT)
    assert failures == [], (
        f"phase-*-tdd.md siblings must not trigger phase-topology drift.\n"
        f"failures={failures!r}"
    )


def test_phase_1_legacy_sibling_alone_does_not_fail(tmp_path):
    """Adding a phase-1-writer.md to a clean topology does not fail the binding."""
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    sibling = tmp_path / ".claude/agents/phase-1-writer.md"
    sibling.write_text("---\nname: phase-1-writer\n---\n")

    # role-topology.yaml lookup uses module-level path; redirect to seeded copy.
    import validate_architecture as _va

    _orig = _va.ROLE_TOPOLOGY_PATH
    _va.ROLE_TOPOLOGY_PATH = tmp_path / ".claude/agents/role-topology.yaml"
    try:
        failures = validate_phase_topology(tmp_path)
    finally:
        _va.ROLE_TOPOLOGY_PATH = _orig
    assert failures == [], (
        f"phase-1-writer sibling alone must not fail the binding. failures={failures!r}"
    )


def test_all_four_legacy_siblings_do_not_fail(tmp_path):
    """All four legacy-slug siblings together do not fail the binding."""
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    for n, role in [
        (1, "writer"),
        (2, "skeptic"),
        (3, "implementer"),
        (4, "integrator"),
    ]:
        sibling = tmp_path / f".claude/agents/phase-{n}-{role}.md"
        sibling.write_text(f"---\nname: phase-{n}-{role}\n---\n")

    import validate_architecture as _va

    _orig = _va.ROLE_TOPOLOGY_PATH
    _va.ROLE_TOPOLOGY_PATH = tmp_path / ".claude/agents/role-topology.yaml"
    try:
        failures = validate_phase_topology(tmp_path)
    finally:
        _va.ROLE_TOPOLOGY_PATH = _orig
    assert failures == [], f"Four legacy siblings must not fail. failures={failures!r}"


def test_phase_5_evaluator_still_fails(tmp_path):
    """Out-of-scope guard: a phase-5-* file (not in role-topology.yaml) must still fail."""
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    extra = tmp_path / ".claude/agents/phase-5-evaluator.md"
    extra.write_text("---\nname: phase-5-evaluator\n---\n")

    import validate_architecture as _va

    _orig = _va.ROLE_TOPOLOGY_PATH
    _va.ROLE_TOPOLOGY_PATH = tmp_path / ".claude/agents/role-topology.yaml"
    try:
        failures = validate_phase_topology(tmp_path)
    finally:
        _va.ROLE_TOPOLOGY_PATH = _orig
    assert failures, "Extra phase-5-evaluator.md must still fail the binding"
    joined = "\n".join(failures)
    assert "5" in joined or "phase-5" in joined, (
        f"Failure must name the offending phase. failures={failures!r}"
    )


def test_canonical_role_slug_replaced_by_legacy_variant_still_fails(tmp_path):
    """If phase-2-tdd.md is REMOVED but phase-2-skeptic.md exists, the binding must fail.

    The legacy sibling does NOT replace the canonical role; missing canonical files
    are still drift.
    """
    from validate_architecture import validate_phase_topology

    _seed_canonical_only(tmp_path)
    (tmp_path / ".claude/agents/phase-2-tdd.md").unlink()
    (tmp_path / ".claude/agents/phase-2-skeptic.md").write_text(
        "---\nname: phase-2-skeptic\n---\n"
    )

    import validate_architecture as _va

    _orig = _va.ROLE_TOPOLOGY_PATH
    _va.ROLE_TOPOLOGY_PATH = tmp_path / ".claude/agents/role-topology.yaml"
    try:
        failures = validate_phase_topology(tmp_path)
    finally:
        _va.ROLE_TOPOLOGY_PATH = _orig
    assert failures, (
        "Removing phase-2-tdd.md must still fail even when phase-2-skeptic.md exists"
    )


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)
