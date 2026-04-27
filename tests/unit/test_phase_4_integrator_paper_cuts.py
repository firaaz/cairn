"""Phase 2 RED — compression/lever-Z-fixup §S4.b.

Asserts that ``.claude/agents/phase-4-integrator.md`` gains three
clarifications surfaced as rough edges during Lever-Z's Phase-4 dogfood:

  1. ``lookup``'s required ``entity_type`` parameter is named explicitly
     in connection with `lookup`.
  2. Typed-record attribute access pattern (``record.statement`` or
     equivalent attribute-access form) is documented (substrate query
     results are pydantic models; subscript-style access raises
     ``KeyError``).
  3. The cairn-knowledge MCP server's stdio-only transport constraint is
     called out explicitly (per ADR ``cairn-substrate-and-fastmcp`` D6),
     so in-process audit paths know to call ``tools.py`` callables
     directly rather than importing the server module.

Brittle by design — every Phase-3 cluster carries a RED test, including
prompt/doc-amendment clusters (cluster-RED-test discipline per
``compression/learnings-capture`` retry).

Per ``.claude/current-slice/intent.md`` §S4.b + §S5.

Expected at Phase 2 (RED): FAILS — none of the three clarifications are
present in the current agent file.
"""

from __future__ import annotations

from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_FILE = CAIRN_ROOT / ".claude" / "agents" / "phase-4-integrator.md"


def _read_body() -> str:
    return AGENT_FILE.read_text()


def test_s4b_lookup_entity_type_parameter_named():
    """intent §S4.b clarification 1 — `entity_type` named with `lookup`.

    Stable signal: both tokens `lookup` and `entity_type` MUST appear in
    the agent body. (Phase-3 retains prose-shape latitude; the test does
    not assert proximity, only co-presence.)
    """
    body = _read_body()
    assert "lookup" in body, (
        "intent §S4.b clarification 1 — `lookup` must remain named in the "
        "phase-4-integrator agent body"
    )
    assert "entity_type" in body, (
        "intent §S4.b clarification 1 — `entity_type` parameter must be "
        "named explicitly in the phase-4-integrator agent body so callers "
        "do not omit the required argument"
    )


def test_s4b_typed_record_attribute_access_pattern_named():
    """intent §S4.b clarification 2 — attribute-access pattern documented.

    Stable signal: at least one of the canonical attribute-access tokens
    appears in the body. The intent specifically calls out
    ``record.statement`` as a reference; we accept ``record.<attr>``
    style or equivalent attribute-access prose tokens to give Phase-3
    rephrasing room.
    """
    body = _read_body()
    candidates = (
        "record.statement",
        "record.",
        "attribute access",
        "attribute-access",
    )
    matches = [tok for tok in candidates if tok in body]
    assert matches, (
        "intent §S4.b clarification 2 — phase-4-integrator agent body must "
        "name the typed-record attribute-access pattern (e.g. "
        "`record.statement`) so callers do not subscript pydantic models "
        f"and hit KeyError; expected at least one of {candidates!r}"
    )


def test_s4b_stdio_constraint_named_in_cairn_knowledge_context():
    """intent §S4.b clarification 3 — stdio constraint flagged with cairn-knowledge.

    Stable signal: tokens `stdio` AND (`cairn-knowledge` or
    `cairn_knowledge`) BOTH appear in the agent body, so the in-process
    audit caveat (use `tools.py` callables directly, not the MCP server
    module) is reachable.
    """
    body = _read_body()
    assert "stdio" in body, (
        "intent §S4.b clarification 3 — `stdio` must be named in the "
        "phase-4-integrator agent body so in-process audit paths know "
        "the cairn-knowledge MCP server cannot be invoked in-process"
    )
    assert "cairn-knowledge" in body or "cairn_knowledge" in body, (
        "intent §S4.b clarification 3 — `cairn-knowledge` must remain "
        "named alongside the stdio constraint so the audit-caveat reader "
        "associates the constraint with the right server"
    )
