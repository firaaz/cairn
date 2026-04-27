"""Phase 2 RED — compression/lever-Y-mcp-substrate V3.

Each of the four MCP tools wrapping ``scripts.cairn_query`` MUST return a
typed pydantic record (or list thereof) on valid input over the current
corpus — per intent.md V3 + ADR D6.

Expected at Phase 2: FAILS — ``mcp_servers/cairn_knowledge/tools.py``
does not exist; the rebuild seed/database may also be absent.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
if str(CAIRN_ROOT) not in sys.path:
    sys.path.insert(0, str(CAIRN_ROOT))


@pytest.fixture(scope="module")
def storage(tmp_path_factory):
    """Build the kuzu store from canonical sources via the public API."""
    import cairn_query

    db_path = tmp_path_factory.mktemp("cairn_query_db") / "index.kz"
    return cairn_query.rebuild_from_sources(db_path=db_path)


@pytest.fixture(scope="module")
def tools_mod():
    return importlib.import_module("mcp_servers.cairn_knowledge.tools")


def _resolve_tool(tools_mod, name):
    """Resolve a tool by name from either a TOOLS registry or a callable attr."""
    if hasattr(tools_mod, "TOOLS"):
        reg = tools_mod.TOOLS
        if isinstance(reg, dict) and name in reg:
            return reg[name]
        for entry in reg or []:
            if (
                getattr(entry, "name", None) == name
                or getattr(entry, "__name__", None) == name
            ):
                return entry
    return getattr(tools_mod, name, None)


def _call_tool(tool, *args, **kwargs):
    """Best-effort tool invocation — supports plain callables and FastMCP-decorated objects."""
    if tool is None:
        pytest.fail("tool not registered")
    if callable(tool):
        return tool(*args, **kwargs)
    inner = (
        getattr(tool, "fn", None)
        or getattr(tool, "func", None)
        or getattr(tool, "callable", None)
    )
    if callable(inner):
        return inner(*args, **kwargs)
    pytest.fail(f"tool {tool!r} is not invocable")


def test_v3_lookup_returns_invariant(storage, tools_mod):
    """intent.md V3 — `lookup(INVARIANT, 'INV-008')` returns a populated Invariant."""
    from cairn_query import Invariant

    tool = _resolve_tool(tools_mod, "lookup")
    result = _call_tool(tool, entity_type="INVARIANT", id="INV-008")
    assert isinstance(result, Invariant), (
        f"lookup must return a typed pydantic Invariant; got {type(result).__name__}"
    )
    assert result.id == "INV-008", f"id round-trip failed; got {result.id!r}"


def test_v3_search_returns_typed_list(storage, tools_mod):
    """intent.md V3 — `search(INVARIANT)` returns a non-empty list of Invariant."""
    from cairn_query import Invariant

    tool = _resolve_tool(tools_mod, "search")
    result = _call_tool(tool, entity_type="INVARIANT")
    assert isinstance(result, list)
    assert result, "search(INVARIANT) must return ≥1 Invariant on current corpus"
    assert all(isinstance(e, Invariant) for e in result), (
        "search must return typed pydantic Invariant records"
    )


def test_v3_path_bindings_returns_entities(storage, tools_mod):
    """intent.md V3 — `path_bindings('docs/ARCHITECTURE.md')` returns ≥1 entity."""
    tool = _resolve_tool(tools_mod, "path_bindings")
    result = _call_tool(tool, path="docs/ARCHITECTURE.md")
    assert isinstance(result, list)
    assert result, "path_bindings on docs/ARCHITECTURE.md must return ≥1 entity"


def test_v3_cypher_returns_row_dicts(storage, tools_mod):
    """intent.md V3 — `cypher(...)` returns list of row dicts."""
    tool = _resolve_tool(tools_mod, "cypher")
    rows = _call_tool(
        tool,
        query="MATCH (i:Invariant) RETURN i.id LIMIT 1",
    )
    assert isinstance(rows, list)
    assert rows, "cypher must return non-empty rows on a populated corpus"
    assert all(isinstance(r, dict) for r in rows), (
        "rows must be dicts per cairn_query.cypher contract"
    )


def test_v3_no_operator_memory_in_tool_surface(tools_mod):
    """ADR D15 — operator memory is NEVER reachable from the MCP tool surface.

    Structural check: the tools module source MUST NOT reference operator
    memory paths or the ``memory`` directory under ``~/.claude/projects/``.
    """
    src = (CAIRN_ROOT / "mcp_servers" / "cairn_knowledge" / "tools.py").read_text()
    forbidden = [
        ".claude/projects",
        "/memory/",
        "MEMORY.md",
        "operator-memory",
        "operator_memory",
    ]
    hits = [tok for tok in forbidden if tok in src]
    assert not hits, (
        f"ADR D15 — tools.py must not reference operator memory; found {hits!r}"
    )
