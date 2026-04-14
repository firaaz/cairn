"""Phase 2 validation tests for SLICE-012 — D3 integration gate backstop.

Tests cover:
- Step 3 gate: delegates to validate_architecture.py Check D, gates on result
- Step 4 gate: runs ruff check + pytest in sequence, gates on result
- Exit codes: 0 (all pass), 1 (one or more fail), 2 (missing prerequisites)
- No short-circuit: all checks run even if early checks fail (A2)
- Falsification: planted invariant violation must be caught (ADR-003 D3)

Tests are mechanism-agnostic — any Phase 3 implementation satisfying the
intent.md specification passes.  Tests exercise the script through subprocess
for consistent testing of exit codes and stdout/stderr.

Ambiguity resolutions (see validation/approach.md for full list):
  A2 — All checks run regardless of early failures; no short-circuit.
  A6 — Invocation mechanism for validate_architecture.py is implementation
       detail; tests verify exit codes and output, not call mechanism.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path



CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = CAIRN_ROOT / "scripts" / "integration_gate.py"
VALIDATOR = CAIRN_ROOT / "scripts" / "validate_architecture.py"


# --- Helpers ----------------------------------------------------------------


def _run_gate(
    cwd: Path | None = None,
    env_overrides: dict | None = None,
) -> subprocess.CompletedProcess:
    """Run integration_gate.py and return the result."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(cwd) if cwd else str(CAIRN_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _make_project(
    root: Path,
    invariants: list[dict],
    extra_files: dict[str, str] | None = None,
) -> None:
    """Create a test project with ARCHITECTURE.md, ADRs, and optional files.

    Each invariant dict:
        id: str            — e.g. "INV-001"
        text: str          — invariant text
        adr_id: str        — e.g. "ADR-901"
        adr_num: str       — e.g. "901" (for ADR filename)
        assertion: dict|None — keys: type, pattern, target, expect, description
    """
    docs = root / "docs"
    adr_dir = docs / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)

    # --- Build ARCHITECTURE.md ---
    arch_lines = [
        "# Architecture",
        "",
        "System: fixture project",
        "",
        "## Invariants",
        "",
    ]
    for inv in invariants:
        arch_lines.append(f"**{inv['id']}** {inv['text']} ({inv['adr_id']})")
        arch_lines.append("")
        if inv.get("assertion"):
            a = inv["assertion"]
            block_lines = [f"```invariant-check {inv['id']}"]
            if "type" in a:
                block_lines.append(f"type: {a['type']}")
            if "pattern" in a:
                block_lines.append(f'pattern: "{a["pattern"]}"')
            if "target" in a:
                block_lines.append(f'target: "{a["target"]}"')
            if "expect" in a:
                block_lines.append(f"expect: {a['expect']}")
            if "description" in a:
                block_lines.append(f'description: "{a["description"]}"')
            block_lines.append("```")
            arch_lines.append("\n".join(block_lines))
            arch_lines.append("")

    arch_lines.extend(
        [
            "## Boundaries",
            "",
            "None.",
            "",
            "## Data Ownership",
            "",
            "None.",
            "",
        ]
    )
    (docs / "ARCHITECTURE.md").write_text("\n".join(arch_lines))

    # --- Build ADR files ---
    for inv in invariants:
        inv_list = inv["id"]
        adr_content = textwrap.dedent(f"""\
            ---
            id: {inv["adr_id"]}
            status: accepted
            firmness: firm
            supersedes: []
            supersedes-sections: []
            superseded-by: null
            topic: process
            invariants-touched: [{inv_list}]
            date: 2026-04-14
            ---

            # {inv["adr_id"]}: Fixture Decision

            ## Status
            Accepted

            ## Context
            Fixture ADR for SLICE-012 Phase 2 tests.

            ## Decision
            Fixture.

            ## Consequences
            - Paired with invariant {inv_list}.
        """)
        (adr_dir / f"{inv['adr_num']}-fixture.md").write_text(adr_content)

    # --- Build ADR index ---
    index_lines = ["# ADR Index", ""]
    for inv in invariants:
        index_lines.append(f"- [{inv['adr_id']}](adr/{inv['adr_num']}-fixture.md)")
    (docs / "adr" / "index.md").write_text("\n".join(index_lines))

    # --- Extra files ---
    if extra_files:
        for rel_path, content in extra_files.items():
            p = root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)


# --- Exit code tests --------------------------------------------------------


class TestExitCodes:
    """Basic exit code contract for integration_gate.py."""

    def test_clean_project_exits_0(self, tmp_path):
        """All gates pass on a project with valid invariants → exit 0.

        Requires: validate_architecture.py passes, ruff passes, pytest passes.
        """
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Test file exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "description": "Check that ARCHITECTURE.md exists",
                    },
                }
            ],
            extra_files={
                # A minimal passing test so pytest has something to run
                "tests/__init__.py": "",
                "tests/test_trivial.py": "def test_pass(): assert True\n",
            },
        )
        result = _run_gate(cwd=tmp_path)
        assert result.returncode == 0, (
            f"Expected exit 0 on clean project, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_invariant_failure_exits_1(self, tmp_path):
        """Check D invariant assertion failure → exit 1."""
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "A file that does not exist.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "nonexistent/file.py",
                        "description": "Points to a missing file",
                    },
                }
            ],
        )
        result = _run_gate(cwd=tmp_path)
        assert result.returncode == 1, (
            f"Expected exit 1 for invariant failure, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_ruff_failure_exits_1(self, tmp_path):
        """Ruff lint failure → exit 1."""
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Architecture exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "description": "Check ARCHITECTURE.md exists",
                    },
                }
            ],
            extra_files={
                # Deliberately broken Python that ruff should flag
                "scripts/bad_lint.py": (
                    "import os\nimport sys\n"
                    "# neither os nor sys is used — F401 unused import\n"
                ),
            },
        )
        result = _run_gate(cwd=tmp_path)
        assert result.returncode == 1, (
            f"Expected exit 1 for ruff failure, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_pytest_failure_exits_1(self, tmp_path):
        """Pytest test failure → exit 1."""
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Architecture exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "description": "Check ARCHITECTURE.md exists",
                    },
                }
            ],
            extra_files={
                "tests/__init__.py": "",
                "tests/test_failing.py": "def test_fail(): assert False\n",
            },
        )
        result = _run_gate(cwd=tmp_path)
        assert result.returncode == 1, (
            f"Expected exit 1 for pytest failure, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# --- Output format tests ---------------------------------------------------


class TestOutputFormat:
    """Integration gate logs each sub-check with pass/fail."""

    def test_output_shows_pass_fail_per_check(self, tmp_path):
        """Each sub-check (Step 3, Step 4a ruff, Step 4b pytest) is logged."""
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Architecture exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "description": "Check ARCHITECTURE.md exists",
                    },
                }
            ],
            extra_files={
                "tests/__init__.py": "",
                "tests/test_trivial.py": "def test_pass(): assert True\n",
            },
        )
        result = _run_gate(cwd=tmp_path)
        combined = result.stdout + result.stderr
        # The output must mention pass/fail status for each gate component.
        # We check for the presence of "pass" or "fail" (case-insensitive)
        # as a minimum; the exact format is Phase 3's choice.
        combined_lower = combined.lower()
        assert "pass" in combined_lower or "fail" in combined_lower, (
            f"Expected pass/fail indicators in output.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# --- No short-circuit tests (A2) -------------------------------------------


class TestNoShortCircuit:
    """All checks run even if earlier checks fail (A2)."""

    def test_all_checks_run_on_step3_failure(self, tmp_path):
        """When Step 3 (invariant check) fails, Step 4 still runs.

        Evidence: output mentions results from all gates, not just the first
        failure.
        """
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Missing file invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "nonexistent/file.py",
                        "description": "Will fail — file does not exist",
                    },
                }
            ],
            extra_files={
                "tests/__init__.py": "",
                "tests/test_trivial.py": "def test_pass(): assert True\n",
            },
        )
        result = _run_gate(cwd=tmp_path)
        assert result.returncode == 1
        combined = result.stdout + result.stderr
        combined_lower = combined.lower()
        # Step 3 failed, but Step 4 should still have run.
        # Evidence: pytest output or ruff output appears in the combined output.
        # We look for indicators that additional checks were attempted.
        has_additional_check = (
            "ruff" in combined_lower
            or "pytest" in combined_lower
            or "test" in combined_lower
        )
        assert has_additional_check, (
            f"Expected evidence that Step 4 ran after Step 3 failure.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# --- Prerequisite detection tests -------------------------------------------


class TestPrerequisites:
    """Exit code 2 when mandatory tools are missing."""

    def test_missing_ruff_exits_2(self, tmp_path):
        """When ruff is not on PATH, integration gate exits 2."""
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Architecture exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "description": "Check ARCHITECTURE.md exists",
                    },
                }
            ],
        )
        # Run with a PATH that excludes ruff
        env = {"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "")}
        result = _run_gate(cwd=tmp_path, env_overrides=env)
        assert result.returncode == 2, (
            f"Expected exit 2 for missing ruff, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# --- Falsification test (ADR-003 D3 requirement) ---------------------------


class TestFalsification:
    """D3 falsification: planted invariant violation that integration gate MUST catch.

    ADR-003 requires a pre-specified calibration case that, if the check
    does not flag, causes D3 to be rejected at Phase 4.
    """

    def test_planted_invariant_violation_caught(self, tmp_path):
        """Falsification: create a failing invariant-check block.

        Setup:
          - Project with one invariant whose file-exists assertion points
            to a nonexistent file
          - Otherwise valid project structure

        Expected: integration_gate.py exits 1 with the failing invariant
        named in the output.

        If this test does not pass, D3 is rejected per ADR-003.
        """
        _make_project(
            tmp_path,
            invariants=[
                {
                    "id": "INV-901",
                    "text": "Valid invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "description": "Check ARCHITECTURE.md — will pass",
                    },
                },
                {
                    "id": "INV-902",
                    "text": "Planted violation — references nonexistent file.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                    "assertion": {
                        "type": "file-exists",
                        "target": "scripts/does_not_exist.py",
                        "description": "Planted failure — file missing",
                    },
                },
            ],
            extra_files={
                "tests/__init__.py": "",
                "tests/test_trivial.py": "def test_pass(): assert True\n",
            },
        )
        result = _run_gate(cwd=tmp_path)
        assert result.returncode == 1, (
            f"FALSIFICATION FAILURE: planted invariant violation not detected. "
            f"Exit code: {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "INV-902" in combined, (
            f"FALSIFICATION FAILURE: failing invariant not named in output.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
