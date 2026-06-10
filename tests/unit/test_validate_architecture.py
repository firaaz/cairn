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
        if broken_ref:
            refs_str = broken_ref
        else:
            own_adr = f"ADR-{900 + i:03d}"
            if i == 1 and adrs > invariants:
                extras = [f"ADR-{900 + j:03d}" for j in range(invariants + 1, adrs + 1)]
                refs_str = ", ".join([own_adr, *extras])
            else:
                refs_str = own_adr
        arch_lines.append(
            f"**INV-{i:03d}** Fixture invariant {i} for symlink resolution testing. ({refs_str})"
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
                carrier: rationale-only
                firmness: firm
                supersedes: []
                supersedes-sections: []
                superseded-by: null
                topic: process
                invariants-touched: [INV-{i:03d}]
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


# --- Phase 2 (SLICE-018): flat-slug ADR recognition -----------------------
#
# The tests below exercise the behaviors declared in SLICE-018 intent.md
# §Verification V2–V6 and V10. V1 (legacy + commentary parity on live
# corpus) is covered by test_v1_cairn_self_dogfood_baseline above: the
# current ARCHITECTURE.md includes commentary inside invariant
# parentheticals (e.g. `(phase-lock-and-role-declaration; confirmed by phase-pipeline-evaluation)` on INV-003,
# `(context-discipline-protocol; dedicated ADR pending ...)` on INV-004), so that test is the
# whole-corpus regression guard for intent's "at parity with current
# behavior" clause on commentary handling. V7 (project-root resolution
# unchanged) is covered by V1–V6. V8/V9 are Phase 3 run-time checks, not
# Phase 2 unit tests.


def _make_flat_slug_project(
    root: Path,
    *,
    adrs: list[dict],
    invariants: list[dict],
) -> None:
    """Build a minimal substrate for flat-slug parsing tests.

    ADR spec keys: id, filename, status (default "accepted"),
    firmness (default "firm"), superseded_by (default None, else the
    successor id), invariants_touched (default []).

    Invariant spec keys: id, refs (literal parenthetical content), text
    (default fixture boilerplate).
    """
    docs = root / "docs"
    adr_dir = docs / "adr"
    adr_dir.mkdir(parents=True)

    arch_lines = [
        "# Architecture",
        "",
        "System: flat-slug fixture",
        "",
        "## Invariants",
        "",
    ]
    for inv in invariants:
        inv_id = inv["id"]
        refs = inv["refs"]
        text = inv.get(
            "text",
            f"Fixture invariant {inv_id} for flat-slug parsing tests.",
        )
        arch_lines.append(f"**{inv_id}** {text} ({refs})")
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
    for adr in adrs:
        filename = adr["filename"]
        id_field = adr["id"]
        status = adr.get("status", "accepted")
        firmness = adr.get("firmness", "firm")
        superseded_by = adr.get("superseded_by")
        invariants_touched = adr.get("invariants_touched", [])
        inv_list = (
            "[" + ", ".join(invariants_touched) + "]" if invariants_touched else "[]"
        )
        superseded_val = superseded_by if superseded_by else "null"
        body = textwrap.dedent(
            f"""\
            ---
            id: {id_field}
            status: {status}
            carrier: rationale-only
            firmness: {firmness}
            supersedes: []
            supersedes-sections: []
            superseded-by: {superseded_val}
            topic: process
            invariants-touched: {inv_list}
            date: 2026-04-16
            ---

            # {id_field}: Fixture ADR

            ## Status
            {status.title()}

            ## Context
            Fixture ADR for Phase 2 flat-slug parsing tests.

            ## Decision
            Fixture decision.

            ## Consequences
            - Fixture consequences.
            """
        )
        (adr_dir / filename).write_text(body)
        index_lines.append(f"- [{id_field}]({filename})")
    (adr_dir / "index.md").write_text("\n".join(index_lines) + "\n")


def _run_in(tmp_path: Path) -> subprocess.CompletedProcess:
    return _run(
        VALIDATOR,
        cwd=tmp_path,
        env_overrides={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )


def test_flat_slug_adr_recognized_and_referenced(tmp_path):
    """V2 — A flat-slug ADR `id: foo-scheme` referenced via `(foo-scheme)` resolves."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "foo-scheme",
                "filename": "foo-scheme.md",
                "invariants_touched": ["INV-001"],
            },
        ],
        invariants=[{"id": "INV-001", "refs": "foo-scheme"}],
    )
    result = _run_in(tmp_path)
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "ALL CHECKS PASSED" in result.stdout
    assert "Invariants verified: 1" in result.stdout
    assert "ADR files checked: 1" in result.stdout, (
        f"Flat-slug ADR must be discovered. A count of 0 means the validator "
        f"did not widen discovery beyond legacy NNN-slug.md filenames.\n"
        f"stdout:\n{result.stdout}"
    )


def test_flat_slug_accepted_firm_without_invariant_fails_check_b(tmp_path):
    """V3 — An accepted+firm flat-slug ADR uncovered by invariants → Check B error."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "bootstrap-exception",
                "filename": "001-legacy.md",
                "invariants_touched": ["INV-001"],
            },
            {
                "id": "foo-scheme",
                "filename": "foo-scheme.md",
                # intentionally NOT referenced by any invariant
            },
        ],
        invariants=[{"id": "INV-001", "refs": "bootstrap-exception"}],
    )
    result = _run_in(tmp_path)
    assert result.returncode != 0, (
        f"Accepted+firm flat-slug ADR without invariant coverage must fail.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "foo-scheme" in result.stdout, (
        f"Check B error must name the uncovered flat-slug id verbatim.\n"
        f"stdout:\n{result.stdout}"
    )


def test_flat_slug_soft_without_invariant_no_check_b(tmp_path):
    """V3-neg — A soft flat-slug ADR uncovered by invariants does NOT fire Check B."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "bootstrap-exception",
                "filename": "001-legacy.md",
                "invariants_touched": ["INV-001"],
            },
            {
                "id": "soft-scheme",
                "filename": "soft-scheme.md",
                "firmness": "soft",
            },
        ],
        invariants=[{"id": "INV-001", "refs": "bootstrap-exception"}],
    )
    result = _run_in(tmp_path)
    assert result.returncode == 0, (
        f"Soft flat-slug ADRs are not required to have invariant coverage.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ALL CHECKS PASSED" in result.stdout
    # Anti-vacuous-pass guard: the soft-scheme flat-slug file must actually
    # be discovered by the validator for this test's negative claim (no
    # Check B) to have semantic content. A count of 1 (only legacy bootstrap-exception
    # discovered) means this test was passing for the wrong reason.
    assert "ADR files checked: 2" in result.stdout, (
        f"Both legacy and flat-slug ADRs must be discovered.\nstdout:\n{result.stdout}"
    )


def test_flat_slug_superseded_reference_fails_check_c(tmp_path):
    """V4 — An invariant referencing a superseded flat-slug ADR → Check C error."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "old-scheme",
                "filename": "old-scheme.md",
                "superseded_by": "new-scheme",
                "invariants_touched": ["INV-001"],
            },
            {
                "id": "new-scheme",
                "filename": "new-scheme.md",
                "invariants_touched": ["INV-002"],
            },
        ],
        invariants=[
            {"id": "INV-001", "refs": "old-scheme"},
            {"id": "INV-002", "refs": "new-scheme"},
        ],
    )
    result = _run_in(tmp_path)
    assert result.returncode != 0, (
        f"Reference to a superseded flat-slug ADR must fail.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "old-scheme" in result.stdout, (
        f"Check C error must name the superseded flat-slug id verbatim.\n"
        f"stdout:\n{result.stdout}"
    )
    # Anti-vacuous-pass guard: intent specifies Check C ("reference to a
    # superseded ADR") should fire here, not Check A ("unknown reference").
    # Currently the fixture's "old-scheme" is unknown to the validator and
    # produces a Check A error that coincidentally contains "old-scheme" —
    # which would satisfy the assertion above for the wrong reason. Pin to
    # the supersession concept to force Phase 3 to discover the flat-slug
    # ADR and route the error through Check C.
    assert "supersed" in result.stdout.lower(), (
        f"Expected Check C (superseded-reference) wording, not Check A.\n"
        f"stdout:\n{result.stdout}"
    )


def test_unknown_flat_slug_token_fails_check_a(tmp_path):
    """V5 — A reference token matching no ADR id → Check A error with token verbatim."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "bootstrap-exception",
                "filename": "001-legacy.md",
                "invariants_touched": ["INV-002"],
            },
        ],
        invariants=[
            {"id": "INV-001", "refs": "no-such-adr"},
            {"id": "INV-002", "refs": "bootstrap-exception"},
        ],
    )
    result = _run_in(tmp_path)
    assert result.returncode != 0, (
        f"Unknown reference token must fail Check A.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "no-such-adr" in result.stdout, (
        f"Check A error must name the unknown token verbatim.\nstdout:\n{result.stdout}"
    )
    assert "INV-001" in result.stdout, (
        f"Check A error must name the invariant carrying the bad reference.\n"
        f"stdout:\n{result.stdout}"
    )


def test_flat_slug_not_addressable_via_synthetic_adr_nnn(tmp_path):
    """V5-alias — A flat-slug ADR cannot be reached via a synthesized ADR-NNN token."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "foo-scheme",
                "filename": "foo-scheme.md",
                "invariants_touched": ["INV-002"],
            },
        ],
        invariants=[
            {"id": "INV-001", "refs": "ADR-999"},
            {"id": "INV-002", "refs": "foo-scheme"},
        ],
    )
    result = _run_in(tmp_path)
    assert result.returncode != 0, (
        f"Flat-slug ADRs must not be aliased to synthesized ADR-NNN tokens.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ADR-999" in result.stdout, (
        f"Check A error must name the unresolved ADR-NNN token verbatim.\n"
        f"stdout:\n{result.stdout}"
    )


def test_assertion_blocks_run_on_mixed_corpus(tmp_path):
    """V6 — Check D/E assertion execution is unchanged on a mixed legacy + flat-slug corpus."""
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "bootstrap-exception",
                "filename": "001-legacy.md",
                "invariants_touched": ["INV-001"],
            },
            {
                "id": "foo-scheme",
                "filename": "foo-scheme.md",
                "invariants_touched": ["INV-002"],
            },
        ],
        invariants=[
            {"id": "INV-001", "refs": "bootstrap-exception"},
            {"id": "INV-002", "refs": "foo-scheme"},
        ],
    )
    target = tmp_path / "docs" / "target.txt"
    target.write_text("fixture target\n")
    arch_path = tmp_path / "docs" / "ARCHITECTURE.md"
    arch_path.write_text(
        arch_path.read_text()
        + "\n```invariant-check INV-002\n"
        + "type: file-exists\n"
        + 'target: "docs/target.txt"\n'
        + 'description: "Fixture assertion for Check D"\n'
        + "```\n"
    )
    result = _run_in(tmp_path)
    assert result.returncode == 0, (
        f"Mixed corpus with a resolvable assertion must pass.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ALL CHECKS PASSED" in result.stdout
    assert "ADR files checked: 2" in result.stdout, (
        f"Both the legacy and flat-slug ADRs must be discovered.\n"
        f"stdout:\n{result.stdout}"
    )


def test_inv005_style_identifier_scheme_parenthetical_fixture(tmp_path):
    """V10 — Fixture rewrites INV-005's parenthetical from `(feature-slice-model)` to `(identifier-scheme)`.

    Proves the validator accepts the INV-005 re-point path before
    ARCHITECTURE.md itself is edited — that edit is out of this slice's
    envelope.
    """
    _make_flat_slug_project(
        tmp_path,
        adrs=[
            {
                "id": "identifier-scheme",
                "filename": "identifier-scheme.md",
                "invariants_touched": ["INV-005"],
            },
        ],
        invariants=[
            {
                "id": "INV-005",
                "refs": "identifier-scheme",
                "text": "Cross-referenceable entities carry a two-field identity model.",
            },
        ],
    )
    result = _run_in(tmp_path)
    assert result.returncode == 0, (
        f"INV-005 with (identifier-scheme) parenthetical must validate cleanly.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ALL CHECKS PASSED" in result.stdout
    assert "ADR files checked: 1" in result.stdout, (
        f"The flat-slug identifier-scheme ADR must be discovered.\n"
        f"stdout:\n{result.stdout}"
    )
