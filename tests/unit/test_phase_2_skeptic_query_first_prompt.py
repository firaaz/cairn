"""Phase 2 RED — compression/lever-Z-substrate-full-pipeline §S6.

String-presence assertion: ``.claude/agents/phase-2-skeptic.md`` MUST
contain the query-first directive (intent §S2). Phase 3 must add prose
naming the ``cairn-knowledge`` MCP server as the canonical-knowledge
read path.

Brittleness of string-presence is explicitly accepted (intent §S6 lesson
from compression/learnings-capture: every Phase-3 cluster must carry a
RED test, including prompt-amendment clusters; string-presence is the
cheapest signal that GREEN cannot vacuously satisfy).

Substring choice rationale: ``cairn-knowledge`` is the MCP server name
shipped by Slice 2 and is unlikely to drift. Pairing it with ``query``
guards against accidental matches (e.g., a passing reference rather
than a directive).

Expected at Phase 2: FAIL — no query-first directive in the file today.
"""

from __future__ import annotations

from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
PHASE_2_SKEPTIC_MD = CAIRN_ROOT / ".claude" / "agents" / "phase-2-skeptic.md"


def test_phase_2_skeptic_query_first_directive_present():
    """intent §S2 — phase-2-skeptic.md mentions cairn-knowledge MCP query.

    Stable substrings:
      - "cairn-knowledge" — the MCP server name (shipped Slice 2)
      - "query" — the directive verb

    Both must appear in the file body. Exact phrasing is implementer
    choice (intent §S2 explicitly: "Phase-3 may rephrase as long as
    semantics are preserved").
    """
    text = PHASE_2_SKEPTIC_MD.read_text()
    assert "cairn-knowledge" in text, (
        f"intent §S2 — phase-2-skeptic.md must reference the "
        f"`cairn-knowledge` MCP server in its query-first directive; "
        f"file: {PHASE_2_SKEPTIC_MD}"
    )
    assert "query" in text.lower(), (
        f"intent §S2 — phase-2-skeptic.md must contain a query directive; "
        f"file: {PHASE_2_SKEPTIC_MD}"
    )
