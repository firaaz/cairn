"""Phase 2 validation tests for SLICE-001 — validator project root resolution.

Verifies intent.md V1-V6: the substrate validator must resolve "project
root" to the caller's intended target across four calling contexts, and
must fail loudly rather than silently fall back to a wrong target.

Tests are mechanism-agnostic — assertions cover observable behavior, not
a specific resolution chain. Any Phase 3 implementation satisfying the
resolution contract passes, whether it is the minimal fix (drop
.resolve() from __file__) or a multi-mechanism chain (env → git →
fallback).
"""

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = CAIRN_ROOT / "scripts" / "validate_architecture.py"


# --- Fixtures --------------------------------------------------------------


def _make_consumer_project(
    root: Path,
    *,
    invariants: int,
    adrs: int,
    broken_ref: str | None = None,
) -> None:
    """Create a minimal consumer-project substrate under root.

    invariants: count declared in docs/ARCHITECTURE.md.
    adrs:       count placed under docs/adr/.
    broken_ref: if set, every invariant references this ADR ID instead of
                its paired fixture ADR, breaking Check A.
    """
    docs = root / "docs"
    adr_dir = docs / "adr"
    adr_dir.mkdir(parents=True)

    arch_lines = [
        "# Architecture",
        "",
        "System: fixture consumer project",
        "",
        "## Invariants",
        "",
    ]
    for i in range(1, invariants + 1):
        target_adr = broken_ref if broken_ref else f"ADR-{900 + i:03d}"
        arch_lines.append(
            f"**TMP-{i:03d}** Fixture invariant {i} for symlink resolution testing. ({target_adr})"
        )
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

    index_lines = ["# ADR Index", ""]
    for i in range(1, adrs + 1):
        adr_id = f"ADR-{900 + i:03d}"
        adr_num = f"{900 + i:03d}"
        adr_file = adr_dir / f"{adr_num}-fixture-decision-{i}.md"
        adr_file.write_text(
            textwrap.dedent(
                f"""\
                ---
                id: {adr_id}
                status: accepted
                firmness: firm
                supersedes: []
                supersedes-sections: []
                superseded-by: null
                topic: process
                invariants-touched: [TMP-{i:03d}]
                date: 2026-04-11
                ---

                # {adr_id}: Fixture Decision {i}

                ## Status
                Accepted

                ## Context
                Fixture ADR for Phase 2 resolution tests.

                ## Decision
                Fixture decision.

                ## Consequences
                - Creates paired invariant TMP-{i:03d}.
                """
            )
        )
        index_lines.append(f"- [{adr_id}]({adr_num}-fixture-decision-{i}.md)")
    (adr_dir / "index.md").write_text("\n".join(index_lines) + "\n")


def _symlink_slice_system(consumer_root: Path) -> None:
    os.symlink(CAIRN_ROOT, consumer_root / ".slice-system")


def _run(
    script_path: Path,
    cwd: Path,
    env_overrides: dict | None = None,
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _parse_invariant_count(stdout: str) -> int | None:
    match = re.search(r"Invariants verified:\s+(\d+)", stdout)
    return int(match.group(1)) if match else None


# --- V1: Cairn self-dogfood baseline --------------------------------------


def test_v1_cairn_self_dogfood_baseline():
    """V1 — Validator run from cairn's own repo root must still pass.

    Regression guard: the fix must not break self-validation, which /status
    relies on. Asserts exit 0 and success string only — does not bind to
    cairn's current 1-invariant/1-ADR count, so cairn's substrate can
    grow without breaking this test.
    """
    result = _run(VALIDATOR, cwd=CAIRN_ROOT)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "ALL CHECKS PASSED" in result.stdout


# --- V2: Consumer via symlink, CLAUDE_PROJECT_DIR set ---------------------


def test_v2_consumer_via_symlink_with_env_var(tmp_path):
    """V2 — Consumer via .slice-system symlink with CLAUDE_PROJECT_DIR set.

    Fixture has 2 invariants / 3 ADRs. Cairn has 1/1. Parsing the
    validator's `Invariants verified: N` line proves which substrate was
    read: 2 = tmp (correct), 1 = cairn (false-green, the bug).
    """
    _make_consumer_project(tmp_path, invariants=2, adrs=3)
    _symlink_slice_system(tmp_path)

    result = _run(
        tmp_path / ".slice-system" / "scripts" / "validate_architecture.py",
        cwd=tmp_path,
        env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "ALL CHECKS PASSED" in result.stdout
    count = _parse_invariant_count(result.stdout)
    assert count == 2, (
        f"Expected 2 invariants from tmp fixture, got {count}. "
        f"A count of 1 means the validator silently read cairn's substrate.\n"
        f"stdout:\n{result.stdout}"
    )


# --- V3: Consumer via symlink, no env var --------------------------------


def test_v3_consumer_via_symlink_no_env_var(tmp_path):
    """V3 — Consumer via symlink, CLAUDE_PROJECT_DIR unset, git-initialized.

    Exercises the mechanism chain without the env-var shortcut. git init
    is present so any git-rev-parse-based mechanism can succeed, but the
    minimal-fix mechanism (drop .resolve()) also passes because
    __file__.parent.parent from tmp/.slice-system/scripts/*.py yields tmp.
    """
    _make_consumer_project(tmp_path, invariants=2, adrs=3)
    _symlink_slice_system(tmp_path)
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)

    result = _run(
        tmp_path / ".slice-system" / "scripts" / "validate_architecture.py",
        cwd=tmp_path,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "ALL CHECKS PASSED" in result.stdout
    count = _parse_invariant_count(result.stdout)
    assert count == 2, (
        f"Expected 2 invariants from tmp fixture, got {count}.\n"
        f"stdout:\n{result.stdout}"
    )


# --- V4: Consumer invoked from subdirectory -------------------------------


def test_v4_consumer_invoked_from_subdirectory(tmp_path):
    """V4 — Validator invoked from a subdirectory of the consumer repo.

    Resolution must still yield the consumer repo root, not the
    subdirectory and not cairn's install.
    """
    _make_consumer_project(tmp_path, invariants=2, adrs=3)
    _symlink_slice_system(tmp_path)
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)

    subdir = tmp_path / "src" / "submod"
    subdir.mkdir(parents=True)

    result = _run(
        tmp_path / ".slice-system" / "scripts" / "validate_architecture.py",
        cwd=subdir,
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "ALL CHECKS PASSED" in result.stdout
    count = _parse_invariant_count(result.stdout)
    assert count == 2, (
        f"Expected 2 invariants from tmp fixture, got {count}.\n"
        f"stdout:\n{result.stdout}"
    )


# --- V5: Consumer with deliberately broken substrate ---------------------


def test_v5_consumer_with_broken_substrate(tmp_path):
    """V5 — Consumer substrate is broken (invariants reference nonexistent ADR-999).

    Validator must report tmp's failure. If it silently read cairn's
    substrate, it would exit 0 because cairn's substrate is consistent —
    the false-green this slice exists to prevent.
    """
    _make_consumer_project(tmp_path, invariants=2, adrs=3, broken_ref="ADR-999")
    _symlink_slice_system(tmp_path)
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)

    result = _run(
        tmp_path / ".slice-system" / "scripts" / "validate_architecture.py",
        cwd=tmp_path,
    )

    assert result.returncode != 0, (
        f"Expected nonzero exit on broken tmp substrate. A zero exit means "
        f"the validator silently read cairn's (consistent) substrate.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ALL CHECKS PASSED" not in result.stdout

    combined = result.stdout + result.stderr
    tmp_markers = ("TMP-", "ADR-9")
    assert any(m in combined for m in tmp_markers), (
        f"No tmp-specific identifier found in output. The failure may not "
        f"reference the tmp substrate.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# --- V6: Resolution failure, no viable project root ----------------------


def test_v6_resolution_failure_no_viable_root(tmp_path):
    """V6 — No CLAUDE_PROJECT_DIR, cwd outside a git repo, .slice-system in
    a directory with no docs/ of its own.

    The validator MUST fail loudly rather than silently fall back to
    reading cairn's own substrate. Per ambiguity A1 we test the property,
    not the diagnostic wording: any nonzero exit plus the absence of
    false-green is sufficient.

    Anti-leak assertion: cairn has 1 invariant. If the validator's
    fallback silently reads cairn's root, stdout would contain
    `Invariants verified: 1`. We assert that string is not present.
    """
    _symlink_slice_system(tmp_path)
    assert not (tmp_path / "docs").exists()
    assert not (tmp_path / ".git").exists()

    result = _run(
        tmp_path / ".slice-system" / "scripts" / "validate_architecture.py",
        cwd=tmp_path,
    )

    assert result.returncode != 0, (
        f"Expected nonzero exit on resolution failure. A zero exit almost "
        f"certainly means the validator fell back to cairn's root.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ALL CHECKS PASSED" not in result.stdout, (
        f"Expected no false-green, but validator reported success.\n"
        f"stdout:\n{result.stdout}"
    )
    assert "Invariants verified: 1" not in result.stdout, (
        f"Validator silently read cairn's substrate (count=1 matches cairn).\n"
        f"stdout:\n{result.stdout}"
    )
