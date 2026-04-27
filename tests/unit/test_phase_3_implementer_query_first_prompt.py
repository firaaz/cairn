"""Phase 2 RED — compression/lever-Z-substrate-full-pipeline §S6.

String-presence assertion: ``.claude/agents/phase-3-implementer.md`` MUST
contain the query-first directive (intent §S3). Same pattern as
``test_phase_2_skeptic_query_first_prompt.py``.

Expected at Phase 2: FAIL — no query-first directive in the file today.
"""

from __future__ import annotations

from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
PHASE_3_IMPLEMENTER_MD = CAIRN_ROOT / ".claude" / "agents" / "phase-3-implementer.md"


def test_phase_3_implementer_query_first_directive_present():
    """intent §S3 — phase-3-implementer.md mentions cairn-knowledge MCP query.

    Same substring discipline as the phase-2-skeptic prompt test.
    """
    text = PHASE_3_IMPLEMENTER_MD.read_text()
    assert "cairn-knowledge" in text, (
        f"intent §S3 — phase-3-implementer.md must reference the "
        f"`cairn-knowledge` MCP server in its query-first directive; "
        f"file: {PHASE_3_IMPLEMENTER_MD}"
    )
    assert "query" in text.lower(), (
        f"intent §S3 — phase-3-implementer.md must contain a query "
        f"directive; file: {PHASE_3_IMPLEMENTER_MD}"
    )
