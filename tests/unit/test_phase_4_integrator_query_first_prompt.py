"""Phase 2 RED — compression/lever-Z-substrate-full-pipeline §S6.

Three string-presence assertions on ``.claude/agents/phase-4-integrator.md``
per intent §S4:

  (a) Query-first directive — "cairn-knowledge" + "query".
  (b) Invariant-evidence consumption directive — substrate query for
      invariant Statement / target spec; pair-substring "invariant" +
      "substrate" (or "invariant" + "lookup") guards against accidental
      matches.
  (c) Sweep-notes template scaffold instruction — pre-fill the Statement
      column from substrate query; pair-substring "sweep-notes" +
      "Statement" guards against the existing "sweep-notes.md" mention
      (which is just the write target).

Brittleness accepted (intent §S6).

Expected at Phase 2: FAIL — none of the three directives present today.
"""

from __future__ import annotations

from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
PHASE_4_INTEGRATOR_MD = CAIRN_ROOT / ".claude" / "agents" / "phase-4-integrator.md"


def test_phase_4_integrator_query_first_directive_present():
    """intent §S4(1) — query-first directive."""
    text = PHASE_4_INTEGRATOR_MD.read_text()
    assert "cairn-knowledge" in text, (
        f"intent §S4(1) — phase-4-integrator.md must reference the "
        f"`cairn-knowledge` MCP server; file: {PHASE_4_INTEGRATOR_MD}"
    )
    assert "query" in text.lower(), (
        f"intent §S4(1) — phase-4-integrator.md must contain a query "
        f"directive; file: {PHASE_4_INTEGRATOR_MD}"
    )


def test_phase_4_integrator_invariant_substrate_directive_present():
    """intent §S4(2) — invariant-evidence consumption directive.

    Substrate-derived Statement / target spec for invariants. Pair
    substrings "invariant" + "substrate" stable enough not to bind to
    verbatim phrasing; specific enough that the existing prompt body
    (which mentions "invariant verification" and "invariant evidence"
    but not "substrate") will not vacuously satisfy.
    """
    text = PHASE_4_INTEGRATOR_MD.read_text()
    lower = text.lower()
    assert "invariant" in lower, (
        f"intent §S4(2) — phase-4-integrator.md must mention invariant "
        f"verification; file: {PHASE_4_INTEGRATOR_MD}"
    )
    assert "substrate" in lower, (
        f"intent §S4(2) — phase-4-integrator.md must direct the integrator "
        f"to source invariant Statement / target spec from the substrate "
        f"(e.g., via `lookup` or `cypher` on Invariant records); "
        f"file: {PHASE_4_INTEGRATOR_MD}"
    )


def test_phase_4_integrator_sweep_notes_scaffold_directive_present():
    """intent §S4(3) — sweep-notes template scaffold instruction.

    Pre-fill the Statement column from substrate query results. Pair
    substrings "sweep-notes" + "Statement" — `sweep-notes.md` is already
    mentioned today as a write target; the new bit is naming the
    Statement column specifically (so the scaffold instruction is
    unambiguous about what gets pre-filled).
    """
    text = PHASE_4_INTEGRATOR_MD.read_text()
    assert "sweep-notes" in text.lower(), (
        f"intent §S4(3) — phase-4-integrator.md must mention sweep-notes; "
        f"file: {PHASE_4_INTEGRATOR_MD}"
    )
    assert "Statement" in text, (
        f"intent §S4(3) — phase-4-integrator.md must instruct the integrator "
        f"to pre-fill the `Statement` column of sweep-notes' invariants "
        f"table from substrate query results (case-sensitive: matches the "
        f"column header); file: {PHASE_4_INTEGRATOR_MD}"
    )
