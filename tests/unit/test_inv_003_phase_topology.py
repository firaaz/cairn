"""Phase 2 RED tests for slice v1-defense-d2/inv-003-phase-topology-binding.

Verifies the new INV-003 binding: a four-way cross-reference assertion that
the (phase_ordinal, role_slug) topology declared in the four canonical
sources is identical.

Canonical sources:
  1. .claude/agents/role-topology.yaml — phases mapping (authoritative; M4-A2
     relocated this from scripts/slice_orchestrator/core.py:ROLE_FOR_PHASE).
  2. docs/operational-reference.md — § Phase Skill Guide tables (regex-extracted).
  3. .claude/agents/phase-{1..4}-*.md — filenames.
  4. checks/role_guard.py — union of ROLE_POLICIES + ROLE_DENY_READ keys.

Asymmetry decision (resolved by Phase 2 per intent.md §Asymmetry decision):
  Option (b) — phase-3-implementer carries no static ROLE_POLICIES entry; its
  write-path gate is granted dynamically per AGENT_ENVELOPE under
  compression-infrastructure-bootstrap. The binding tolerates this provided
  role_guard.py carries an explanatory comment naming the asymmetry as
  intentional. Operator recommendation in brief.

Public surface tested:
  - The validator entry point ``validate_phase_topology(project_root: Path)``
    is exposed by ``scripts/validate_architecture.py`` (per slice brief). It
    returns a list of failure messages — empty on agreement.
  - End-to-end invocation of ``scripts/validate_architecture.py`` against
    cairn's HEAD passes (the new binding accepts the canonical agreement).
  - The INV-003 assertion block in ``docs/ARCHITECTURE.md`` no longer uses
    the old grep-for-section-header proxy.
  - The D2 paragraph in ``docs/ARCHITECTURE.md`` reflects that INV-003
    carries a true binding (not "out of scope").
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = CAIRN_ROOT / "scripts" / "validate_architecture.py"
ARCHITECTURE = CAIRN_ROOT / "docs" / "ARCHITECTURE.md"

EXPECTED_TOPOLOGY = {
    (1, "phase-1-tdd"),
    (2, "phase-2-tdd"),
    (3, "phase-3-tdd"),
    (4, "phase-4-tdd"),
}

CANONICAL_SOURCES = [
    Path(".claude/agents/role-topology.yaml"),
    Path("docs/operational-reference.md"),
    Path("checks/role_guard.py"),
]

AGENT_FILES = [
    Path(".claude/agents/phase-1-tdd.md"),
    Path(".claude/agents/phase-2-tdd.md"),
    Path(".claude/agents/phase-3-tdd.md"),
    Path(".claude/agents/phase-4-tdd.md"),
]


# --- Helpers ----------------------------------------------------------------


def _seed_topology_root(tmp_path: Path) -> Path:
    """Copy the four canonical sources from CAIRN_ROOT into tmp_path.

    Preserves the relative paths so a binding using project_root + relative
    path resolves the copy.
    """
    for rel in CANONICAL_SOURCES + AGENT_FILES:
        src = CAIRN_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return tmp_path


def _import_binding():
    """Import the binding entry point — ImportError → RED."""
    from validate_architecture import validate_phase_topology  # noqa: F401

    return validate_phase_topology


def _run_validator_subprocess(cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(cwd)
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _read_inv_003_block() -> dict:
    """Parse the INV-003 invariant-check assertion block from ARCHITECTURE.md."""
    from validate_architecture import parse_assertion_blocks

    return parse_assertion_blocks(ARCHITECTURE.read_text()).get("INV-003", {})


# === Public-surface presence ================================================


class TestEntryPointExposed:
    """The slice brief commits to a ``validate_phase_topology`` function."""

    def test_validate_phase_topology_is_importable(self):
        """``from validate_architecture import validate_phase_topology`` succeeds."""
        fn = _import_binding()
        assert callable(fn), "validate_phase_topology must be callable"

    def test_validate_phase_topology_accepts_project_root(self, tmp_path):
        """The function takes a project root path and returns a list of failures."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        result = fn(tmp_path)
        assert isinstance(result, list), (
            f"Expected list of failure messages, got {type(result).__name__}"
        )
        assert all(isinstance(m, str) for m in result), (
            "Each failure message must be a string"
        )


# === Clean-tree agreement ===================================================


class TestCleanTreePasses:
    """All four canonical sources currently agree — the binding must accept them."""

    def test_clean_tree_returns_no_failures(self):
        """``validate_phase_topology(CAIRN_ROOT)`` returns ``[]``."""
        fn = _import_binding()
        failures = fn(CAIRN_ROOT)
        assert failures == [], (
            f"Clean cairn tree must satisfy the binding. Got: {failures!r}"
        )

    def test_validator_subprocess_passes_on_cairn_head(self):
        """End-to-end: ``scripts/validate_architecture.py`` exits 0 on HEAD."""
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(CAIRN_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Validator must pass on cairn HEAD with new INV-003 binding.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "ALL CHECKS PASSED" in result.stdout

    def test_seeded_tmp_root_passes(self, tmp_path):
        """A tmp_path seeded with byte-identical copies of the three sources passes."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        failures = fn(tmp_path)
        assert failures == [], (
            f"Seeded tmp_path with byte-identical copies must satisfy binding.\n"
            f"Got: {failures!r}"
        )


# === Perturbation: source 1 (.claude/agents/role-topology.yaml) ===============


import yaml as _yaml


ROLE_TOPOLOGY_PATH = CAIRN_ROOT / ".claude" / "agents" / "role-topology.yaml"


def _read_role_for_phase() -> dict[int, str]:
    return _yaml.safe_load(ROLE_TOPOLOGY_PATH.read_text())["phases"]


class TestRoleForPhasePerturbations:
    """Mutations to ``role-topology.yaml`` are caught and named."""

    def test_dropping_phase_4_from_role_for_phase_fails(self, tmp_path):
        """Removing the phase-4 entry from role-topology.yaml triggers failure."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        fake = tmp_path / ".claude/agents/role-topology.yaml"
        original = fake.read_text()
        mutated = original.replace("  4: phase-4-tdd\n", "")
        assert mutated != original, (
            "Test setup: phase-4-tdd line not found in role-topology.yaml"
        )
        fake.write_text(mutated)

        import validate_architecture as _va

        _orig = _va.ROLE_TOPOLOGY_PATH
        _va.ROLE_TOPOLOGY_PATH = fake
        try:
            failures = fn(tmp_path)
        finally:
            _va.ROLE_TOPOLOGY_PATH = _orig

        assert failures, "Dropping phase-4 from role-topology.yaml must fail"
        joined = "\n".join(failures)
        assert "phase-4" in joined or "(4," in joined or "4," in joined, (
            f"Failure message must name the offending phase/role pair.\n"
            f"failures={failures!r}"
        )

    def test_renaming_role_in_role_for_phase_fails(self, tmp_path):
        """Renaming a role slug in role-topology.yaml surfaces as drift."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        fake = tmp_path / ".claude/agents/role-topology.yaml"
        original = fake.read_text()
        mutated = original.replace("  2: phase-2-tdd", "  2: phase-2-renamed-tdd")
        assert mutated != original, (
            "Test setup: phase-2-tdd line not found in role-topology.yaml"
        )
        fake.write_text(mutated)

        import validate_architecture as _va

        _orig = _va.ROLE_TOPOLOGY_PATH
        _va.ROLE_TOPOLOGY_PATH = fake
        try:
            failures = fn(tmp_path)
        finally:
            _va.ROLE_TOPOLOGY_PATH = _orig

        assert failures, "Renaming phase-2-tdd in role-topology.yaml must fail"


# === Perturbation: source 2 (operational-reference.md Phase Skill Guide) =====


class TestSkillGuidePerturbations:
    """Mutations to the Phase Skill Guide tables are caught and named."""

    def test_renaming_role_in_skill_guide_fails(self, tmp_path):
        """Renaming a role token in the Skill Guide table fails the binding."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        opref = tmp_path / "docs/operational-reference.md"
        text = opref.read_text()
        mutated = text.replace("Skeptic", "Validator")
        assert mutated != text, (
            "Test setup: 'Skeptic' role token not found in operational-reference.md"
        )
        opref.write_text(mutated)

        failures = fn(tmp_path)
        assert failures, "Renaming Skeptic in the Skill Guide must fail"
        joined = "\n".join(failures).lower()
        assert (
            "operational-reference" in joined
            or "skill guide" in joined
            or "phase-2" in joined
        ), f"Failure should name the Skill Guide source. failures={failures!r}"

    def test_dropping_skill_guide_row_fails(self, tmp_path):
        """Removing a phase row from the Skill Guide table fails the binding."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        opref = tmp_path / "docs/operational-reference.md"
        text = opref.read_text()
        # Strip the Phase 3 rows from BOTH Phase Skill Guide tables
        # (Role-and-anti-behaviors and Phase-to-skill-mapping). The row
        # extractor regex matches lines starting with "| 3. ", so removing
        # those lines drops Phase 3 from the Skill Guide topology.
        mutated_lines = [ln for ln in text.splitlines() if not ln.startswith("| 3. ")]
        mutated = "\n".join(mutated_lines)
        assert mutated != text, "Test setup: no '| 3. ' Skill Guide rows found"
        opref.write_text(mutated)

        failures = fn(tmp_path)
        assert failures, "Dropping phase-3 row from Skill Guide must fail"


# === Perturbation: source 3 (.claude/agents/phase-N-*.md) ====================


class TestAgentFilenamePerturbations:
    """Mutations to the agent prompt filenames are caught and named."""

    def test_extra_phase_5_agent_file_fails(self, tmp_path):
        """An extra ``phase-5-*.md`` not in ROLE_FOR_PHASE triggers failure."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        extra = tmp_path / ".claude/agents/phase-5-evaluator.md"
        extra.write_text("---\nname: phase-5-evaluator\n---\n")

        failures = fn(tmp_path)
        assert failures, "Extra phase-5 agent file must fail the binding"
        joined = "\n".join(failures)
        assert "5" in joined or "phase-5" in joined, (
            f"Failure must name the offending phase ordinal. failures={failures!r}"
        )

    @pytest.mark.xfail(
        reason=(
            "M4-C5: binding now checks canonical TDD slugs only; removing the legacy "
            "phase-2-skeptic.md sibling no longer triggers drift. Test should be "
            "updated in M4-E5 to target phase-2-tdd.md removal instead."
        ),
        strict=True,
    )
    def test_missing_phase_2_agent_file_fails(self, tmp_path):
        """Removing the phase-2-skeptic agent file fails the binding."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        target = tmp_path / ".claude/agents/phase-2-skeptic.md"
        target.unlink()

        failures = fn(tmp_path)
        assert failures, "Missing phase-2 agent prompt file must fail"
        joined = "\n".join(failures)
        assert "phase-2" in joined or "skeptic" in joined.lower(), (
            f"Failure should name the missing role. failures={failures!r}"
        )

    @pytest.mark.xfail(
        reason=(
            "M4-C5: binding now checks canonical TDD slugs only; renaming the legacy "
            "phase-2-skeptic.md sibling no longer triggers drift. Test should be "
            "updated in M4-E5 to target phase-2-tdd.md renaming instead."
        ),
        strict=True,
    )
    def test_renamed_agent_file_fails(self, tmp_path):
        """Renaming an agent file role-slug fails the binding."""
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        src = tmp_path / ".claude/agents/phase-2-skeptic.md"
        dst = tmp_path / ".claude/agents/phase-2-validator.md"
        src.rename(dst)

        failures = fn(tmp_path)
        assert failures, "Renamed phase-2 agent file (skeptic→validator) must fail"


# === Perturbation: source 4 (role_guard.py) ==================================


class TestRoleGuardPerturbations:
    """Mutations to ROLE_POLICIES keys are caught and named.

    D2 note: test_renaming_role_policies_key_fails and
    test_dropping_role_deny_read_key_fails deleted — their perturbation
    targets (phase-2-skeptic key and ROLE_DENY_READ) no longer exist
    post-D2 simplification.
    """


# === Asymmetry decision: option (b) — envelope-grant-only tolerated ==========


class TestAsymmetryDecisionOptionB:
    """Phase-3 has no static ROLE_POLICIES entry; the binding tolerates this
    provided role_guard.py carries an explanatory comment naming the asymmetry.
    """

    def test_phase_3_implementer_absent_from_role_policies(self):
        """Option (b) preserves the asymmetry — no static phase-3 entry.

        D2 retired checks_role_guard_module.py; load-bearing assertion is
        the _via_text companion test below.
        """
        pass  # sentinel retired; see test_phase_3_implementer_absent_from_role_policies_via_text

    def test_phase_3_implementer_absent_from_role_policies_via_text(self):
        """Source-of-truth text inspection: no ``"phase-3-implementer":`` key
        in the ``ROLE_POLICIES`` dict body of ``checks/role_guard.py``.
        """
        guard_text = (CAIRN_ROOT / "checks/role_guard.py").read_text()
        # Slice out just the ROLE_POLICIES dict body to avoid matching the
        # ROLE_DENY_READ keys (which legitimately include phase-3-implementer).
        m = re.search(r"ROLE_POLICIES\s*=\s*\{(.*?)\n\}", guard_text, flags=re.DOTALL)
        assert m, "Could not locate ROLE_POLICIES dict in role_guard.py"
        body = m.group(1)
        assert '"phase-3-implementer":' not in body, (
            "Option (b) preserves the asymmetry: phase-3-implementer must NOT "
            "have a static ROLE_POLICIES entry."
        )

    def test_role_guard_has_explanatory_asymmetry_comment(self):
        """A comment in role_guard.py names the phase-3 asymmetry as intentional.

        The comment must (a) live in role_guard.py, (b) name
        ``phase-3-implementer``, and (c) name the envelope mechanism — at
        least one of: ``AGENT_ENVELOPE``, ``envelope-grant``, ``envelope grant``,
        ``envelope-driven``, ``compression-infrastructure-bootstrap``.
        """
        guard_text = (CAIRN_ROOT / "checks/role_guard.py").read_text()
        comment_lines = [
            ln.strip() for ln in guard_text.splitlines() if ln.lstrip().startswith("#")
        ]
        joined_comments = "\n".join(comment_lines)
        names_role = "phase-3-implementer" in joined_comments
        names_mechanism = any(
            tok in joined_comments
            for tok in (
                "AGENT_ENVELOPE",
                "envelope-grant",
                "envelope grant",
                "envelope-driven",
                "compression-infrastructure-bootstrap",
            )
        )
        intentional_marker = any(
            tok in joined_comments.lower()
            for tok in ("intentional", "asymmetry", "asymmetric", "by design")
        )
        assert names_role and names_mechanism and intentional_marker, (
            "role_guard.py must carry an explanatory comment naming "
            "phase-3-implementer's envelope-grant-only asymmetry as "
            "intentional. Found:\n" + joined_comments
        )

    def test_binding_tolerates_phase_3_envelope_grant_only(self):
        """The binding passes on cairn HEAD even though phase-3-implementer
        is absent from ``ROLE_POLICIES``.
        """
        fn = _import_binding()
        failures = fn(CAIRN_ROOT)
        assert failures == [], (
            f"Option (b) requires the binding to tolerate the asymmetry "
            f"on the clean tree. Got: {failures!r}"
        )


# === ARCHITECTURE.md surface change =========================================


class TestArchitectureSurface:
    """The INV-003 block in ARCHITECTURE.md is replaced; D2 paragraph updated."""

    def test_inv_003_assertion_block_present(self):
        """INV-003 retains an invariant-check assertion block."""
        block = _read_inv_003_block()
        assert block, "INV-003 must carry an invariant-check assertion block"
        assert "type" in block, "INV-003 assertion block must declare a 'type'"

    def test_inv_003_old_grep_proxy_removed(self):
        """The old grep-for-section-header proxy is gone."""
        block = _read_inv_003_block()
        is_old_proxy = (
            block.get("type") == "grep"
            and block.get("pattern") == "### Phase 1: Intent"
            and block.get("target") == "docs/operational-reference.md"
        )
        assert not is_old_proxy, (
            "INV-003 must no longer use the deletion-detection grep proxy "
            f"(pattern='### Phase 1: Intent'). Got block: {block!r}"
        )

    def test_inv_003_block_references_new_binding(self):
        """The new INV-003 block names the binding mechanism (phase-topology
        type or the validate_phase_topology entry).
        """
        block = _read_inv_003_block()
        block_repr = " ".join(f"{k}={v}" for k, v in block.items()).lower()
        assert (
            "phase-topology" in block_repr
            or "validate_phase_topology" in block_repr
            or "phase_topology" in block_repr
        ), (
            "INV-003 assertion block must reference the new binding "
            f"(phase-topology / validate_phase_topology). Got: {block!r}"
        )

    def test_d2_paragraph_reflects_inv_003_binding(self):
        """The D2 paragraph names INV-003 as having a binding (not 'out of scope')."""
        text = ARCHITECTURE.read_text()
        # Locate the D2 bullet — it begins with '- **D2 —'.
        m = re.search(r"-\s+\*\*D2\b.+?(?=\n-\s+\*\*D|\n\n\*\*)", text, flags=re.DOTALL)
        assert m, "Could not locate the D2 bullet in ARCHITECTURE.md"
        d2 = m.group(0)
        assert "INV-003" in d2, "D2 paragraph must mention INV-003"
        old_phrase = "INV-003 is independently routed to a separate slice"
        assert old_phrase not in d2, (
            "D2 paragraph must no longer mark INV-003 as routed to a separate "
            f"slice — that slice is this one. Found: {d2!r}"
        )


# === Failure-message contract ===============================================


class TestFailureMessageContract:
    """Per intent §Verification(2): failure names the perturbed source AND
    the offending pair.
    """

    def test_failure_names_offending_pair(self, tmp_path):
        """A perturbation produces a message identifying the offending
        ``(phase, role)`` pair.
        """
        fn = _import_binding()
        _seed_topology_root(tmp_path)
        fake = tmp_path / ".claude/agents/role-topology.yaml"
        fake.write_text(
            fake.read_text().replace("  2: phase-2-tdd", "  2: phase-2-renamed-tdd")
        )

        import validate_architecture as _va

        _orig = _va.ROLE_TOPOLOGY_PATH
        _va.ROLE_TOPOLOGY_PATH = fake
        try:
            failures = fn(tmp_path)
        finally:
            _va.ROLE_TOPOLOGY_PATH = _orig

        assert failures, "Setup failed — perturbation did not trigger failure"
        joined = "\n".join(failures)
        names_pair = ("phase-2-tdd" in joined) or ("phase-2-renamed-tdd" in joined)
        assert names_pair, (
            "Failure must name the offending (phase, role) pair "
            f"(phase-2-tdd or phase-2-renamed-tdd). failures={failures!r}"
        )


# === Out-of-scope guards =====================================================


class TestOutOfScopeUntouched:
    """INV-001 / INV-002 bindings and other invariants are unchanged."""

    def test_inv_001_block_unchanged_class(self):
        """INV-001 still has its block (touched only by separate slice)."""
        from validate_architecture import parse_assertion_blocks

        blocks = parse_assertion_blocks(ARCHITECTURE.read_text())
        assert "INV-001" in blocks, "INV-001 assertion block must remain"

    def test_inv_002_block_unchanged_class(self):
        """INV-002 still has its block (touched only by separate slice)."""
        from validate_architecture import parse_assertion_blocks

        blocks = parse_assertion_blocks(ARCHITECTURE.read_text())
        assert "INV-002" in blocks, "INV-002 assertion block must remain"

    def test_role_topology_yaml_has_correct_shape(self):
        """role-topology.yaml is a 4-key {phase: slug} YAML at the canonical path."""
        data = _read_role_for_phase()
        assert isinstance(data, dict)
        assert set(data.items()) == EXPECTED_TOPOLOGY


# === Stale-import guard for asymmetry first test ============================
#
# The first asymmetry test imports a module-name that does not exist; it is
# intentionally a sentinel demonstrating that the slice's chosen public surface
# is text-inspection of role_guard.py (not import-from). pytest collection
# treats the ImportError as a test failure — which is the intended RED state
# for the asymmetry-decision tests until Phase 3 lands.
#
# If a future Phase 3 implementation chooses to expose ROLE_POLICIES as an
# importable symbol via ``checks.role_guard``, this sentinel can be retired in
# favour of a direct import — but the *_via_text companion test remains the
# load-bearing assertion.


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    """Tests must not run under an AGENT_ROLE — defensive isolation."""
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)
