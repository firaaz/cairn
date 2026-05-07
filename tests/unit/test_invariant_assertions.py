"""Phase 2 validation tests for SLICE-010 — D2 code↔invariant binding.

Tests cover:
- Assertion parser: extracting invariant-check blocks from ARCHITECTURE.md
- Assertion types: grep, file-exists, test-ref (v1), plus ast/custom (v2 skip)
- Check D: per-invariant assertion execution with PASS/FAIL and evidence
- Check E: warning for invariants lacking assertion blocks

Tests are mechanism-agnostic — any Phase 3 implementation satisfying the
intent.md specification passes.  Tests exercise the validator through
subprocess for consistent testing of exit codes, stdout, and stderr.

Ambiguity resolutions (see validation/approach.md for full list):
  A1 — type-specific fields: grep needs pattern+target+expect; file-exists
       needs target; test-ref needs pattern (test path).
  A2 — test-ref validates file existence only, not function existence.
  A3 — check D reports ALL failing invariants, not just the first.
  A5 — regex patterns avoid backslash sequences pending Phase 3 convention.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

from validate_architecture import parse_assertion_blocks, parse_invariants


CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = CAIRN_ROOT / "scripts" / "validate_architecture.py"


# --- Fixtures ---------------------------------------------------------------


def _run_validator(
    cwd: Path, env_overrides: dict | None = None
) -> subprocess.CompletedProcess:
    """Run the validator against a project directory."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_adr(adr_dir: Path, adr_id: str, num: str, inv_ids: list[str]) -> None:
    """Create a minimal ADR file that passes checks A/B/C."""
    inv_list = ", ".join(inv_ids)
    (adr_dir / f"{num}-fixture-{adr_id.lower()}.md").write_text(
        textwrap.dedent(f"""\
            ---
            id: {adr_id}
            status: accepted
            firmness: firm
            supersedes: []
            supersedes-sections: []
            superseded-by: null
            topic: process
            invariants-touched: [{inv_list}]
            date: 2026-04-14
            ---

            # {adr_id}: Fixture Decision

            ## Status
            Accepted

            ## Context
            Fixture ADR for SLICE-010 Phase 2 tests.

            ## Decision
            Fixture.

            ## Consequences
            - Paired with invariant(s) {inv_list}.
        """)
    )
    return f"{num}-fixture-{adr_id.lower()}.md"


def _assertion_block(inv_id: str, assertion: dict) -> str:
    """Render an invariant-check fenced block for ARCHITECTURE.md.

    Patterns are rendered single-quoted so backslash escapes (e.g. ``\\.claude/``)
    arrive at the YAML parser verbatim — double-quoted YAML treats ``\\.`` as
    an unknown escape and errors. See M3 Task 3.
    """
    lines = [f"```invariant-check {inv_id}"]
    if "type" in assertion:
        lines.append(f"type: {assertion['type']}")
    if "pattern" in assertion:
        lines.append(f"pattern: '{assertion['pattern']}'")
    if "target" in assertion:
        lines.append(f'target: "{assertion["target"]}"')
    if "expect" in assertion:
        lines.append(f"expect: {assertion['expect']}")
    if "description" in assertion:
        lines.append(f'description: "{assertion["description"]}"')
    lines.append("```")
    return "\n".join(lines)


def _make_project(
    root: Path,
    invariants: list[dict],
    extra_files: dict[str, str] | None = None,
) -> None:
    """Create a test project with ARCHITECTURE.md, ADRs, and optional assertions.

    Each invariant dict:
        id: str            — e.g. "INV-001"
        text: str          — invariant text
        adr_id: str        — e.g. "ADR-901"
        adr_num: str       — e.g. "901" (for ADR filename)
        assertion: dict|None — keys: type, pattern, target, expect, description
    """
    docs = root / "docs"
    adr_dir = docs / "adr"
    adr_dir.mkdir(parents=True)

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
            arch_lines.append(_assertion_block(inv["id"], inv["assertion"]))
            arch_lines.append("")

    arch_lines.extend(
        [
            "## Boundaries",
            "",
            "Not declared for this fixture.",
            "",
            "## Data Ownership",
            "",
            "No runtime data.",
            "",
        ]
    )
    (docs / "ARCHITECTURE.md").write_text("\n".join(arch_lines))

    # --- Create ADR files + index ---
    index_lines = ["# ADR Index", ""]
    for inv in invariants:
        fname = _make_adr(adr_dir, inv["adr_id"], inv["adr_num"], [inv["id"]])
        index_lines.append(f"- [{inv['adr_id']}]({fname})")
    (adr_dir / "index.md").write_text("\n".join(index_lines) + "\n")

    # --- Create extra files needed by assertions ---
    if extra_files:
        for rel_path, content in extra_files.items():
            p = root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)


# === Parser tests (observable through check D output) ========================


class TestAssertionParser:
    """Verify the parser extracts and acts on invariant-check blocks."""

    def test_single_assertion_block_recognized(self, tmp_path):
        """One invariant-check block → check D runs it."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Fixture invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "exists",
                        "description": "ARCHITECTURE.md exists",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_multiple_assertion_blocks_all_checked(self, tmp_path):
        """Two invariant-check blocks → both are parsed and executed."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "First invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "exists",
                        "description": "ARCHITECTURE.md exists",
                    },
                },
                {
                    "id": "INV-002",
                    "text": "Second invariant.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/adr/index.md",
                        "expect": "exists",
                        "description": "ADR index exists",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_assertion_fields_drive_correct_execution(self, tmp_path):
        """Grep assertion with all five fields executes correctly."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Grep invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "System:",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "match",
                        "description": "ARCHITECTURE.md contains System line",
                    },
                }
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# === Assertion type: grep ====================================================


class TestGrepAssertion:
    """Tests for the grep assertion type."""

    def test_grep_match_found_passes(self, tmp_path):
        """grep + expect: match passes when pattern is found in target."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Has marker.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "UNIQUE_MARKER_ABC",
                        "target": "src/example.py",
                        "expect": "match",
                        "description": "Pattern found in source",
                    },
                }
            ],
            extra_files={"src/example.py": "# UNIQUE_MARKER_ABC\nprint('hello')\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_grep_match_not_found_fails(self, tmp_path):
        """grep + expect: match fails when pattern NOT found in target."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Should have pattern.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "MISSING_PATTERN_XYZ",
                        "target": "src/example.py",
                        "expect": "match",
                        "description": "Pattern must exist",
                    },
                }
            ],
            extra_files={"src/example.py": "# nothing here\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0, (
            f"Expected nonzero exit when grep match not found.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "INV-001" in result.stdout + result.stderr, (
            f"Output should name the failing invariant.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_grep_no_match_absent_passes(self, tmp_path):
        """grep + expect: no-match passes when pattern NOT found."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "No forbidden pattern.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "FORBIDDEN_TOKEN",
                        "target": "src/example.py",
                        "expect": "no-match",
                        "description": "Forbidden token must not appear",
                    },
                }
            ],
            extra_files={"src/example.py": "# clean code\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_grep_no_match_present_fails(self, tmp_path):
        """grep + expect: no-match fails when pattern IS found."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "No forbidden pattern.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "FORBIDDEN_TOKEN",
                        "target": "src/example.py",
                        "expect": "no-match",
                        "description": "Forbidden token must not appear",
                    },
                }
            ],
            extra_files={"src/example.py": "# FORBIDDEN_TOKEN is here\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0, (
            f"Expected nonzero exit when no-match finds the pattern.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_grep_uses_regex_not_literal(self, tmp_path):
        """grep pattern is a Python re regex, not a plain string."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Regex invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "def .+validate",
                        "target": "src/example.py",
                        "expect": "match",
                        "description": "Has a validate function",
                    },
                }
            ],
            extra_files={
                "src/example.py": "def my_validate(x):\n    pass\n",
            },
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_grep_target_glob_multiple_files(self, tmp_path):
        """grep target glob matches multiple files; pattern in any one passes."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Pattern in any source.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "MARKER",
                        "target": "src/*.py",
                        "expect": "match",
                        "description": "At least one source file has MARKER",
                    },
                }
            ],
            extra_files={
                "src/a.py": "# no marker here\n",
                "src/b.py": "# MARKER present\n",
            },
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# === Assertion type: file-exists =============================================


class TestFileExistsAssertion:
    """Tests for the file-exists assertion type."""

    def test_file_exists_found_passes(self, tmp_path):
        """file-exists passes when target resolves to ≥1 file."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Feature file exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "src/feature.py",
                        "expect": "exists",
                        "description": "Feature module exists",
                    },
                }
            ],
            extra_files={"src/feature.py": "# feature\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_file_exists_not_found_fails(self, tmp_path):
        """file-exists fails when target resolves to no files."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Feature file exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "src/nonexistent.py",
                        "expect": "exists",
                        "description": "Feature module exists",
                    },
                }
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0, (
            f"Expected nonzero exit when file-exists target not found.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "INV-001" in result.stdout + result.stderr

    def test_file_exists_glob_pattern(self, tmp_path):
        """file-exists target can be a glob matching multiple files."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Has Python files.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "src/*.py",
                        "expect": "exists",
                        "description": "At least one Python file in src/",
                    },
                }
            ],
            extra_files={"src/main.py": "# main\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# === Assertion type: test-ref ================================================


class TestTestRefAssertion:
    """Tests for the test-ref assertion type."""

    def test_ref_file_exists_passes(self, tmp_path):
        """test-ref passes when the referenced test file exists."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Tested invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "test-ref",
                        "pattern": "tests/unit/test_invariant.py",
                        "expect": "pass",
                        "description": "Invariant has a test file",
                    },
                }
            ],
            extra_files={
                "tests/unit/test_invariant.py": "def test_it(): pass\n",
            },
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_ref_file_not_found_fails(self, tmp_path):
        """test-ref fails when the referenced test file does not exist."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Tested invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "test-ref",
                        "pattern": "tests/unit/test_nonexistent.py",
                        "expect": "pass",
                        "description": "Invariant has a test file",
                    },
                }
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0, (
            f"Expected nonzero exit when test-ref target not found.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "INV-001" in result.stdout + result.stderr


# === Assertion types: v2-reserved (ast, custom) ==============================


class TestV2ReservedTypes:
    """ast and custom are recognized but skipped with a warning."""

    def test_ast_type_skipped_with_warning(self, tmp_path):
        """type: ast → skip-warning, not failure."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "AST-checked invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "ast",
                        "pattern": "some_ast_check",
                        "target": "src/example.py",
                        "expect": "match",
                        "description": "AST check (v2)",
                    },
                }
            ],
            extra_files={"src/example.py": "# placeholder\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"ast type must not cause failure.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert any(
            kw in combined.lower()
            for kw in ("skip", "warning", "ast", "v2", "reserved")
        ), (
            f"Expected skip/warning for ast type.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_custom_type_skipped_with_warning(self, tmp_path):
        """type: custom → skip-warning, not failure."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Custom-checked invariant.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "custom",
                        "pattern": "some_custom_check",
                        "target": "src/example.py",
                        "expect": "match",
                        "description": "Custom check (v2)",
                    },
                }
            ],
            extra_files={"src/example.py": "# placeholder\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"custom type must not cause failure.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert any(
            kw in combined.lower()
            for kw in ("skip", "warning", "custom", "v2", "reserved")
        ), (
            f"Expected skip/warning for custom type.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# === Check D: assertion execution ============================================


class TestCheckD:
    """Tests for Check D — per-invariant assertion execution."""

    def test_all_pass_exits_zero(self, tmp_path):
        """All firm invariants' assertions pass → exit 0."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "File exists.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "exists",
                        "description": "ARCHITECTURE.md present",
                    },
                },
                {
                    "id": "INV-002",
                    "text": "Pattern present.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                    "assertion": {
                        "type": "grep",
                        "pattern": "Architecture",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "match",
                        "description": "Has Architecture heading",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_failure_names_invariant(self, tmp_path):
        """Check D failure output includes the failing invariant ID."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Must have file.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "nonexistent/file.py",
                        "expect": "exists",
                        "description": "Required file exists",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "INV-001" in combined, (
            f"Check D failure must name the invariant.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_failure_shows_evidence(self, tmp_path):
        """Check D failure output includes evidence (file ref or description)."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Must have pattern.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "grep",
                        "pattern": "ABSENT_MARKER",
                        "target": "src/example.py",
                        "expect": "match",
                        "description": "Source must contain ABSENT_MARKER",
                    },
                }
            ],
            extra_files={"src/example.py": "# no marker\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        has_evidence = (
            any(
                kw in combined
                for kw in (
                    "ABSENT_MARKER",
                    "src/example.py",
                    "example.py",
                    "FAIL",
                )
            )
            or "no match" in combined.lower()
        )
        assert has_evidence, (
            f"Check D failure must show evidence.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_multiple_failures_all_reported(self, tmp_path):
        """Check D reports all failing invariants, not just the first."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "First failing.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "missing1.py",
                        "expect": "exists",
                        "description": "First missing file",
                    },
                },
                {
                    "id": "INV-002",
                    "text": "Second failing.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                    "assertion": {
                        "type": "file-exists",
                        "target": "missing2.py",
                        "expect": "exists",
                        "description": "Second missing file",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "INV-001" in combined, f"Should report INV-001.\n{combined}"
        assert "INV-002" in combined, f"Should report INV-002.\n{combined}"

    def test_abc_failure_short_circuits_before_d(self, tmp_path):
        """A/B/C failure short-circuits; check D does not run."""
        docs = tmp_path / "docs"
        adr_dir = docs / "adr"
        adr_dir.mkdir(parents=True)

        # Invariant references ADR-999 which does not exist → check A/B fails
        (docs / "ARCHITECTURE.md").write_text(
            textwrap.dedent("""\
            # Architecture

            System: fixture

            ## Invariants

            **INV-001** References nonexistent ADR. (ADR-999)

            ```invariant-check INV-001
            type: file-exists
            target: "docs/ARCHITECTURE.md"
            expect: exists
            description: "Would pass if check D ran"
            ```

            ## Boundaries

            Not declared.

            ## Data Ownership

            None.
        """)
        )
        (adr_dir / "index.md").write_text("# ADR Index\n")

        result = _run_validator(tmp_path)
        assert result.returncode != 0, "A/B/C should fail before check D runs"


# === Check E: missing assertion warning ======================================


class TestCheckE:
    """Tests for Check E — warning for invariants with no assertion block."""

    def test_missing_assertion_produces_warning(self, tmp_path):
        """Invariant without assertion block → check E warning on stderr."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "No assertion block.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    # No assertion key
                },
            ],
        )
        result = _run_validator(tmp_path)
        # Check E is a warning, NOT a hard failure
        assert result.returncode == 0, (
            f"Missing assertion should warn, not fail.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        combined = result.stdout + result.stderr
        assert "INV-001" in combined, (
            f"Check E should mention the invariant.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        has_warning = any(
            kw in combined.lower()
            for kw in (
                "no machine-checkable assertion",
                "no assertion",
                "missing assertion",
                "warning",
                "check e",
            )
        )
        assert has_warning, (
            f"Check E should produce warning text.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_present_assertion_no_warning(self, tmp_path):
        """Invariant with assertion block → no check E warning."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Has assertion.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "exists",
                        "description": "File present",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        has_missing_warning = any(
            kw in combined.lower()
            for kw in (
                "no machine-checkable assertion",
                "no assertion",
                "missing assertion",
            )
        )
        assert not has_missing_warning, (
            f"INV-001 has an assertion; check E should not warn.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    def test_warning_does_not_fail_validator(self, tmp_path):
        """Multiple invariants missing assertions → warnings, exit 0."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "No assertion.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                },
                {
                    "id": "INV-002",
                    "text": "Also no assertion.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"Check E is warning-only; must not cause failure.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# === End-to-end verification (maps to intent.md Verification §) =============


class TestEndToEnd:
    """End-to-end tests matching intent.md verification items V1–V4."""

    def test_v1_all_types_pass(self, tmp_path):
        """V1 — validator exits 0 with grep + file-exists + test-ref all passing."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "File present.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "exists",
                        "description": "Architecture doc exists",
                    },
                },
                {
                    "id": "INV-002",
                    "text": "Pattern found.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                    "assertion": {
                        "type": "grep",
                        "pattern": "## Invariants",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "match",
                        "description": "Has invariants section",
                    },
                },
                {
                    "id": "INV-003",
                    "text": "Test exists.",
                    "adr_id": "ADR-903",
                    "adr_num": "903",
                    "assertion": {
                        "type": "test-ref",
                        "pattern": "tests/test_example.py",
                        "expect": "pass",
                        "description": "Has test file",
                    },
                },
            ],
            extra_files={"tests/test_example.py": "def test_it(): pass\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "ALL CHECKS PASSED" in result.stdout

    def test_v2_broken_assertion_exits_nonzero(self, tmp_path):
        """V2 — broken test-ref → exit 1 with failing invariant named."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "Correct.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "file-exists",
                        "target": "docs/ARCHITECTURE.md",
                        "expect": "exists",
                        "description": "Passes",
                    },
                },
                {
                    "id": "INV-002",
                    "text": "Broken.",
                    "adr_id": "ADR-902",
                    "adr_num": "902",
                    "assertion": {
                        "type": "test-ref",
                        "pattern": "tests/nonexistent_test.py",
                        "expect": "pass",
                        "description": "Deliberately broken test-ref",
                    },
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode != 0
        assert "INV-002" in result.stdout + result.stderr, (
            "Should name the failing invariant"
        )

    def test_v3_no_assertion_block_warns_not_fails(self, tmp_path):
        """V3 — invariant with no assertion block → warning, exit 0."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "No assertion.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                },
            ],
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0
        assert "INV-001" in result.stdout + result.stderr

    def test_v4_ast_type_warns_not_fails(self, tmp_path):
        """V4 — type: ast → skip-warning, exit 0."""
        _make_project(
            tmp_path,
            [
                {
                    "id": "INV-001",
                    "text": "AST check.",
                    "adr_id": "ADR-901",
                    "adr_num": "901",
                    "assertion": {
                        "type": "ast",
                        "pattern": "check",
                        "target": "src/*.py",
                        "expect": "match",
                        "description": "v2 AST check",
                    },
                }
            ],
            extra_files={"src/example.py": "# placeholder\n"},
        )
        result = _run_validator(tmp_path)
        assert result.returncode == 0


# === Cairn self-dogfood regression ===========================================


class TestCairnSelfDogfood:
    """Validator must still pass on cairn's own substrate after D/E additions."""

    def test_cairn_self_validation_still_passes(self):
        """Regression: cairn's own ARCHITECTURE.md passes with check D/E present."""
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(CAIRN_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "ALL CHECKS PASSED" in result.stdout


# === SLICE-011: Assertion block coverage for all firm invariants ==============
#
# These tests verify that every invariant in cairn's own ARCHITECTURE.md carries
# a machine-checkable assertion block, completing the D2 defense commitment.
# Baseline: INV-001 through INV-008 (INV-008 added by compression/slice-3
# observability-and-close-slice — slice-close-contract).
#
# M4 cairn-shrink (2026-05-07): INV-008 retired; its binding block intentionally
# absent. RETIRED_INVARIANT_IDS exempts it from the assertion-block requirement.


EXPECTED_INVARIANT_IDS = {f"INV-{n:03d}" for n in range(1, 11)}
# Retired invariants: prose marker present in ARCHITECTURE.md but no binding block.
RETIRED_INVARIANT_IDS = {"INV-008", "INV-009", "INV-010"}
V1_ASSERTION_TYPES = {
    "grep",
    "file-exists",
    "test-ref",
    "git-log-walk",
    "structural-parser",
}


def _read_cairn_architecture() -> str:
    """Read cairn's own ARCHITECTURE.md."""
    return (CAIRN_ROOT / "docs" / "ARCHITECTURE.md").read_text()


class TestSlice011AssertionCoverage:
    """Every firm invariant (INV-001 through INV-008) must have an assertion block."""

    def test_all_seven_invariants_have_assertion_blocks(self):
        """Each non-retired invariant (INV-001..INV-010 minus RETIRED) has a block."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        required = EXPECTED_INVARIANT_IDS - RETIRED_INVARIANT_IDS
        missing = required - set(blocks.keys())
        assert not missing, f"Invariants missing assertion blocks: {sorted(missing)}"

    def test_no_extra_assertion_blocks(self):
        """No assertion blocks for non-existent invariants."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        extra = set(blocks.keys()) - EXPECTED_INVARIANT_IDS
        assert not extra, f"Assertion blocks for unknown invariants: {sorted(extra)}"

    def test_all_assertions_use_v1_types(self):
        """Every assertion block uses grep, file-exists, or test-ref (not custom/ast)."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        for inv_id, assertion in blocks.items():
            atype = assertion.get("type", "")
            assert atype in V1_ASSERTION_TYPES, (
                f"{inv_id} uses type '{atype}', expected one of {V1_ASSERTION_TYPES}"
            )

    def test_every_assertion_has_required_fields(self):
        """Each assertion block has type and description at minimum."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        for inv_id, assertion in blocks.items():
            assert "type" in assertion, f"{inv_id} missing 'type' field"
            assert "description" in assertion, f"{inv_id} missing 'description' field"

    def test_grep_assertions_have_pattern_and_target(self):
        """Grep assertions must have pattern, target, and expect fields."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        for inv_id, assertion in blocks.items():
            if assertion.get("type") == "grep":
                assert "pattern" in assertion, f"{inv_id} grep missing 'pattern'"
                assert "target" in assertion, f"{inv_id} grep missing 'target'"
                assert "expect" in assertion, f"{inv_id} grep missing 'expect'"

    def test_file_exists_assertions_have_target(self):
        """File-exists assertions must have a target field."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        for inv_id, assertion in blocks.items():
            if assertion.get("type") == "file-exists":
                assert "target" in assertion, f"{inv_id} file-exists missing 'target'"

    def test_test_ref_assertions_have_pattern(self):
        """Test-ref assertions must have a pattern field (test file path)."""
        arch_text = _read_cairn_architecture()
        blocks = parse_assertion_blocks(arch_text)
        for inv_id, assertion in blocks.items():
            if assertion.get("type") == "test-ref":
                assert "pattern" in assertion, f"{inv_id} test-ref missing 'pattern'"

    def test_invariant_count_unchanged(self):
        """ARCHITECTURE.md has exactly the firm-invariant set (INV-001..INV-008)."""
        arch_text = _read_cairn_architecture()
        invariants = parse_invariants(arch_text)
        inv_ids = {f"INV-{inv['inv_num']:03d}" for inv in invariants}
        assert inv_ids == EXPECTED_INVARIANT_IDS, (
            f"Expected {sorted(EXPECTED_INVARIANT_IDS)}, got {sorted(inv_ids)}"
        )


class TestSlice011ZeroWarnings:
    """Validator produces zero Check E warnings and zero Check D failures."""

    def test_zero_check_e_warnings(self):
        """No 'Check E' warnings in stderr when all assertion blocks present."""
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(CAIRN_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        check_e_lines = [
            line
            for line in result.stderr.splitlines()
            if "Check E" in line or "no machine-checkable assertion" in line.lower()
        ]
        assert not check_e_lines, (
            "Check E warnings found (expected zero):\n" + "\n".join(check_e_lines)
        )

    def test_zero_check_d_failures(self):
        """No Check D failures — all assertions pass against current codebase."""
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(CAIRN_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Validator should exit 0 with all assertions passing.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        check_d_lines = [
            line
            for line in (result.stdout + result.stderr).splitlines()
            if "Check D" in line and "FAIL" in line
        ]
        assert not check_d_lines, "Check D failures found:\n" + "\n".join(check_d_lines)


class TestSlice011Falsification:
    """Falsification: for each assertion, corrupting expected state causes Check D failure.

    Tests are data-driven — they read assertion blocks from cairn's own ARCHITECTURE.md
    and synthesize type-specific corruptions. If no assertion blocks exist, the
    test_assertions_exist_to_falsify guard catches it.
    """

    def _get_assertions(self):
        """Parse assertion blocks from cairn's ARCHITECTURE.md."""
        arch_text = _read_cairn_architecture()
        return parse_assertion_blocks(arch_text)

    def test_assertions_exist_to_falsify(self):
        """Guard: at least 7 assertion blocks must exist for falsification to be meaningful."""
        blocks = self._get_assertions()
        assert len(blocks) >= 7, (
            f"Only {len(blocks)} assertion blocks found; need 7 for full falsification coverage"
        )

    def test_falsify_grep_match_by_removing_pattern(self, tmp_path):
        """For each grep+match assertion, removing the pattern from target causes Check D failure."""
        blocks = self._get_assertions()
        grep_match_blocks = {
            inv_id: a
            for inv_id, a in blocks.items()
            if a.get("type") == "grep" and a.get("expect") == "match"
        }
        if not grep_match_blocks:
            assert False, "No grep+match assertions found to falsify"

        for inv_id, assertion in grep_match_blocks.items():
            target = assertion.get("target", "")
            inv_fixture = {
                "id": inv_id,
                "text": f"Falsification test for {inv_id}.",
                "adr_id": "ADR-901",
                "adr_num": "901",
                "assertion": dict(assertion),
            }
            test_dir = tmp_path / f"falsify-grep-{inv_id}"
            test_dir.mkdir()
            _make_project(
                test_dir,
                [inv_fixture],
                extra_files={target: "# deliberately empty — pattern absent\n"},
            )
            result = _run_validator(test_dir)
            assert result.returncode != 0, (
                f"Falsification failed for {inv_id}: validator should reject "
                f"when grep pattern is absent from {target}.\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
            assert inv_id in result.stdout + result.stderr, (
                f"Failure output should name {inv_id}"
            )

    def test_falsify_grep_no_match_by_adding_pattern(self, tmp_path):
        """For each grep+no-match assertion, adding the pattern causes Check D failure."""
        blocks = self._get_assertions()
        grep_nomatch_blocks = {
            inv_id: a
            for inv_id, a in blocks.items()
            if a.get("type") == "grep" and a.get("expect") == "no-match"
        }
        if not grep_nomatch_blocks:
            return

        for inv_id, assertion in grep_nomatch_blocks.items():
            target = assertion.get("target", "")
            pattern = assertion.get("pattern", "")
            inv_fixture = {
                "id": inv_id,
                "text": f"Falsification test for {inv_id}.",
                "adr_id": "ADR-901",
                "adr_num": "901",
                "assertion": dict(assertion),
            }
            test_dir = tmp_path / f"falsify-nomatch-{inv_id}"
            test_dir.mkdir()
            _make_project(
                test_dir,
                [inv_fixture],
                extra_files={target: f"# {pattern} — deliberately injected\n"},
            )
            result = _run_validator(test_dir)
            assert result.returncode != 0, (
                f"Falsification failed for {inv_id}: validator should reject "
                f"when no-match pattern is present in {target}.\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

    def test_falsify_file_exists_by_removing_file(self, tmp_path):
        """For each file-exists assertion, omitting the target causes Check D failure."""
        blocks = self._get_assertions()
        file_exists_blocks = {
            inv_id: a for inv_id, a in blocks.items() if a.get("type") == "file-exists"
        }
        if not file_exists_blocks:
            return

        for inv_id, assertion in file_exists_blocks.items():
            target = assertion.get("target", "")
            inv_fixture = {
                "id": inv_id,
                "text": f"Falsification test for {inv_id}.",
                "adr_id": "ADR-901",
                "adr_num": "901",
                "assertion": dict(assertion),
            }
            test_dir = tmp_path / f"falsify-file-exists-{inv_id}"
            test_dir.mkdir()
            _make_project(test_dir, [inv_fixture])
            result = _run_validator(test_dir)
            assert result.returncode != 0, (
                f"Falsification failed for {inv_id}: validator should reject "
                f"when target file '{target}' is missing.\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
            assert inv_id in result.stdout + result.stderr, (
                f"Failure output should name {inv_id}"
            )

    def test_falsify_test_ref_by_removing_test_file(self, tmp_path):
        """For each test-ref assertion, omitting the test file causes Check D failure."""
        blocks = self._get_assertions()
        test_ref_blocks = {
            inv_id: a for inv_id, a in blocks.items() if a.get("type") == "test-ref"
        }
        if not test_ref_blocks:
            return

        for inv_id, assertion in test_ref_blocks.items():
            test_path = assertion.get("pattern", "")
            inv_fixture = {
                "id": inv_id,
                "text": f"Falsification test for {inv_id}.",
                "adr_id": "ADR-901",
                "adr_num": "901",
                "assertion": dict(assertion),
            }
            test_dir = tmp_path / f"falsify-test-ref-{inv_id}"
            test_dir.mkdir()
            _make_project(test_dir, [inv_fixture])
            result = _run_validator(test_dir)
            assert result.returncode != 0, (
                f"Falsification failed for {inv_id}: validator should reject "
                f"when test file '{test_path}' is missing.\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
            assert inv_id in result.stdout + result.stderr, (
                f"Failure output should name {inv_id}"
            )
