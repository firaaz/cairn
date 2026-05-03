"""Phase 2 RED tests for slice v1-defense-d2/inv-002-binding-implementation.

Pins the new ``structural-parser`` validator type bound to INV-002 sub-clause
(a) per ADR ``invariant-binding-strategy`` D4. Tests bypass
``parse_assertion_blocks`` and feed nested assertion dicts directly to
``_run_assertion`` so they remain stable across whatever parser-upgrade
strategy Phase 3 selects (line-based, yaml.safe_load, or sibling-schema-file).

Pinned public surface:

  - ``scripts/validate_architecture._run_assertion`` dispatcher accepts
    ``type: structural-parser`` (new branch).
  - ``tests/unit/test_invariant_assertions.V1_ASSERTION_TYPES`` allowlist
    includes ``"structural-parser"``.
  - Placeholder ``binding-effective-from: <pending-slice-close-sha>`` ⇒
    no-op-with-notice (D3 grandfathering, mirrors INV-001 walker).
  - Required-section absent ⇒ failure naming the section.
  - Forbidden literal section ⇒ failure naming the section.
  - Forbidden ``^##\\s+(Lessons|Reflection|Notes)\\b`` regex section ⇒ failure.
  - Forbidden content regex (first-person + test-tally) ⇒ failure.
  - Token budget byte-approximation: ``ceil(len(file_bytes)/4)`` against
    ``warn-at: 360`` (warn) and ``fail-at: 440`` (fail) per D7.
  - Live ``.claude/handoff.md`` (under the schema cap) passes the
    structural-parser check on a non-placeholder SHA.

Anti-revert guards (slice-1 ``phase_3_revert_under_red_pressure`` lesson):
no test relies on the legacy ``Token budget: 150 to 400 tokens`` grep proxy
or any other pre-binding shape; reverting Phase 3's allowlist or dispatcher
edits breaks these tests independently of any other pinning test.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


CAIRN_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = CAIRN_ROOT / "scripts" / "validate_architecture.py"
PLACEHOLDER_SHA = "<pending-slice-close-sha>"


# --- Defensive isolation ----------------------------------------------------


@pytest.fixture(autouse=True)
def _no_agent_role_env(monkeypatch):
    """Tests must not run under an AGENT_ROLE — defensive isolation."""
    monkeypatch.delenv("AGENT_ROLE", raising=False)
    monkeypatch.delenv("AGENT_ENVELOPE", raising=False)


# --- Helpers ----------------------------------------------------------------


def _well_formed_handoff_text() -> str:
    """Synthesize a handoff body that satisfies every required-section + forbidden check."""
    return (
        "---\n"
        "slice: demo/slice-x\n"
        "phase: 4-integration\n"
        "branch: demo\n"
        "as-of: 2026-05-03 deadbeef\n"
        "---\n\n"
        "## State\n"
        "Pipeline at phase 4 integration; sweep notes drafted.\n\n"
        "## Next\n"
        "Run /close-slice to trigger DC-3.\n\n"
        "## Blocked / Pending\n"
        "- nothing pending\n\n"
        "## Pointers\n"
        "- `docs/ARCHITECTURE.md` — invariant set\n"
    )


def _make_assertion(**overrides) -> dict:
    """Construct a structural-parser assertion dict matching ADR D4 schema.

    Tests pass this directly to _run_assertion to avoid coupling on the
    parse_assertion_blocks shape (Phase 3 may upgrade the parser to
    yaml.safe_load; tests here remain stable).
    """
    base = {
        "type": "structural-parser",
        "target": ".claude/handoff.md",
        "required-sections": ["State", "Next", "Blocked / Pending", "Pointers"],
        "optional-sections": ["Features"],
        "forbidden-sections": {
            "literal": [
                "What This Session Was About",
                "What Was Accomplished",
                "Surprises or Discoveries",
                "Self-Check",
            ],
            "regex": [r"^##\s+(Lessons|Reflection|Notes)\b"],
        },
        "forbidden-content": {
            "regex": [
                r"I (was|am|will|just) ",
                r"\d+\s*/\s*\d+\s+(passed|failed|tests)",
            ],
        },
        "token-budget": {
            "approximation": "bytes-per-token-4",
            "warn-at": 360,
            "fail-at": 440,
        },
        "binding-effective-from": "0123456789abcdef0123456789abcdef01234567",
        "description": "INV-002(a) handoff structural binding per ADR D4",
    }
    base.update(overrides)
    return base


def _write_handoff(tmp_path: Path, body: str) -> Path:
    target = tmp_path / ".claude" / "handoff.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)
    return target


# === T1 — V1 allowlist includes structural-parser ===========================


def test_v1_assertion_types_allowlist_includes_structural_parser():
    """Slice-1 left a hardcoded allowlist; the new type must join it.

    Brief landmine #1: tests/unit/test_invariant_assertions.py:1116
    ``V1_ASSERTION_TYPES`` set must gain ``"structural-parser"`` so
    ``test_all_assertions_use_v1_types`` does not regress when INV-002's
    block flips.
    """
    from test_invariant_assertions import V1_ASSERTION_TYPES

    assert "structural-parser" in V1_ASSERTION_TYPES, (
        "V1_ASSERTION_TYPES must allow 'structural-parser' once Phase 3 "
        "lands the new validator type. Current set: "
        f"{sorted(V1_ASSERTION_TYPES)}"
    )


# === T2 — Dispatcher routes structural-parser ===============================


def test_run_assertion_dispatches_structural_parser(tmp_path, monkeypatch):
    """`_run_assertion` recognises ``type: structural-parser`` (new branch).

    Pre-Phase 3 the dispatcher returns ``None`` for unknown types — so
    feeding a CLEARLY violating handoff and seeing ``None`` is the RED
    signal: the new branch isn't wired yet. Once wired, the violation
    must surface as a non-None failure message.
    """
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    _write_handoff(tmp_path, "no headings, just prose\n")
    assertion = _make_assertion()

    result = _run_assertion(tmp_path, "INV-002", assertion)
    assert result is not None, (
        "Structural-parser dispatch missing: a handoff with zero required "
        "sections must produce a failure message, not None. Phase 3 must "
        "register the new branch in _run_assertion."
    )
    assert "INV-002" in result


# === T3 — Placeholder SHA → no-op-with-notice ===============================


def test_placeholder_effective_from_is_noop_with_notice(tmp_path, capsys, monkeypatch):
    """``binding-effective-from: <pending-slice-close-sha>`` ⇒ no failure + notice."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    _write_handoff(tmp_path, "no required sections at all\n")
    assertion = _make_assertion(**{"binding-effective-from": PLACEHOLDER_SHA})

    result = _run_assertion(tmp_path, "INV-002", assertion)
    assert result is None, f"Placeholder SHA must yield no-op (None). Got: {result!r}"
    captured = capsys.readouterr()
    haystack = (captured.out + captured.err).lower()
    assert "binding pending" in haystack or "placeholder" in haystack, (
        "Structural-parser must emit a placeholder/pending notice on "
        f"<pending-slice-close-sha>. stdout={captured.out!r} stderr={captured.err!r}"
    )


# === T4 — Required section missing ⇒ failure naming section =================


@pytest.mark.parametrize(
    "missing_section",
    ["State", "Next", "Blocked / Pending", "Pointers"],
)
def test_required_section_missing_fails(tmp_path, missing_section, monkeypatch):
    """Each required section absent triggers a failure citing the section."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text()
    body = body.replace(f"## {missing_section}\n", "")
    _write_handoff(tmp_path, body)

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is not None, (
        f"Removing required section '{missing_section}' must fail."
    )
    assert missing_section in result, (
        f"Failure must name missing section '{missing_section}'. Got: {result!r}"
    )


# === T5 — Forbidden literal section ⇒ failure ===============================


@pytest.mark.parametrize(
    "forbidden_literal",
    [
        "What This Session Was About",
        "What Was Accomplished",
        "Surprises or Discoveries",
        "Self-Check",
    ],
)
def test_forbidden_literal_section_fails(tmp_path, forbidden_literal, monkeypatch):
    """A forbidden ATX heading triggers a failure citing the heading."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text() + f"\n## {forbidden_literal}\nbody\n"
    _write_handoff(tmp_path, body)

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is not None, (
        f"Forbidden literal section '{forbidden_literal}' must fail."
    )
    assert forbidden_literal in result, (
        f"Failure must echo offending heading. Got: {result!r}"
    )


# === T6 — Forbidden regex section (Lessons/Reflection/Notes) ⇒ failure ======


@pytest.mark.parametrize("heading", ["Lessons", "Reflection", "Notes"])
def test_forbidden_regex_section_fails(tmp_path, heading, monkeypatch):
    """ATX headings matching the regex class trigger failure."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text() + f"\n## {heading}\nbody\n"
    _write_handoff(tmp_path, body)

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is not None, f"Forbidden regex-class section '{heading}' must fail."
    assert heading in result, (
        f"Failure must cite offending heading text. Got: {result!r}"
    )


# === T7 — Forbidden content regex (first-person) ⇒ failure ==================


def test_forbidden_first_person_content_fails(tmp_path, monkeypatch):
    """Body text matching ``I (was|am|will|just) `` triggers failure."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text().replace(
        "Pipeline at phase 4 integration; sweep notes drafted.",
        "I just finished implementing the structural parser.",
    )
    _write_handoff(tmp_path, body)

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is not None, "First-person content regex must fail."


# === T8 — Forbidden content regex (test tally) ⇒ failure ====================


def test_forbidden_test_tally_content_fails(tmp_path, monkeypatch):
    """Body text matching test-tally regex triggers failure."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text().replace(
        "Pipeline at phase 4 integration; sweep notes drafted.",
        "Suite at 12/15 passed.",
    )
    _write_handoff(tmp_path, body)

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is not None, "Test-tally content regex must fail."


# === T9 — Token budget fail-at threshold ====================================


def test_token_budget_fail_at_440(tmp_path, monkeypatch):
    """File of size > fail-at × 4 bytes triggers token-budget failure.

    Bytes-per-token-4: fail-at 440 tokens ⇒ ~1760 bytes.
    Phase 3 implementation is ``ceil(len(bytes)/4) > fail-at``.
    """
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text()
    pad_target_bytes = 440 * 4 + 200  # comfortably over fail-at
    needed = pad_target_bytes - len(body.encode("utf-8"))
    body = body + ("padding line\n" * max(1, needed // len("padding line\n") + 1))
    _write_handoff(tmp_path, body)

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is not None, (
        "Token budget fail-at threshold must produce a failure message."
    )
    haystack = result.lower()
    assert "token" in haystack or "budget" in haystack, (
        f"Failure must mention token budget. Got: {result!r}"
    )


# === T10 — Token budget warn-at threshold (warn, not fail) ==================


def test_token_budget_warn_at_360_does_not_fail(tmp_path, capsys, monkeypatch):
    """File between warn-at and fail-at warns but does not fail (None return)."""
    from validate_architecture import _run_assertion

    monkeypatch.chdir(tmp_path)
    body = _well_formed_handoff_text()
    target_bytes = 360 * 4 + 80  # > warn-at*4 (1440) but < fail-at*4 (1760)
    needed = target_bytes - len(body.encode("utf-8"))
    body = body + ("x" * max(0, needed))
    _write_handoff(tmp_path, body)

    assert 360 * 4 < len(body.encode("utf-8")) < 440 * 4, (
        "Fixture must land strictly between warn-at and fail-at byte windows"
    )

    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is None, f"Warn-band must NOT fail (None expected). Got: {result!r}"


# === T11 — Happy path: live cairn .claude/handoff.md passes =================


def test_live_cairn_handoff_passes_structural_parser(tmp_path, monkeypatch):
    """The committed cairn handoff.md must satisfy the structural-parser schema.

    Regression: post-SHA-substitution, the binding will run against the live
    file. If the live file does not conform, the substrate is broken before
    the binding lands. Tests must catch that NOW (Phase 2), not at sweep.
    """
    from validate_architecture import _run_assertion

    live_handoff = CAIRN_ROOT / ".claude" / "handoff.md"
    assert live_handoff.exists(), "live handoff.md missing — substrate broken"

    # Stage the live handoff into a synthetic project root so the verifier
    # is exercised exactly as it would run via the validator.
    target = tmp_path / ".claude" / "handoff.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(live_handoff.read_text())

    monkeypatch.chdir(tmp_path)
    result = _run_assertion(tmp_path, "INV-002", _make_assertion())
    assert result is None, (
        f"Live cairn handoff.md must pass structural-parser. Got: {result!r}\n"
        "If this fails, either Phase 3 mis-specified the schema or the live "
        "handoff has drifted out of conformance — fix the file, not the test."
    )


# === T12 — End-to-end: validator exits 0 with placeholder still set =========


def test_validator_e2e_passes_with_placeholder():
    """Real ARCHITECTURE.md INV-002 block in placeholder state ⇒ validator exits 0.

    Mirrors INV-001 precedent (test_inv_001_git_log_walk.py::
    test_validator_e2e_passes_with_placeholder). Once Phase 3 swaps INV-002's
    block to ``structural-parser`` with the literal ``<pending-slice-close-sha>``,
    no-op-with-notice must keep the validator exit clean. Pre-Phase-3 the
    legacy grep block also exits 0 — this test functions as a regression
    guard during the swap.
    """
    proc = subprocess.run(
        ["uv", "run", "python", "scripts/validate_architecture.py"],
        cwd=str(CAIRN_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        "Validator must exit 0 with placeholder set on INV-002.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
