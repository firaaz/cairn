"""Four read-only MCP tools wrapping scripts/cairn_query.

Tool registry: TOOLS dict (keys = tool names, values = callables).
Each tool manages its own KuzuStorage via lazy module-level singleton.

ADR cairn-substrate-and-fastmcp D15 compliant: operator memory paths are
never referenced from this module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure cairn_query (in scripts/) is importable when this module is loaded
# outside the pytest process (e.g. inside the MCP server subprocess).
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
for _p in (str(_REPO_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cairn_query  # noqa: E402
from cairn_query.storage import KuzuStorage  # noqa: E402

_DEFAULT_DB_PATH: Path = cairn_query.DEFAULT_DB_PATH
_STORAGE: KuzuStorage | None = None


def _get_storage() -> KuzuStorage:
    """Lazily build (or reuse) the module-level KuzuStorage singleton."""
    global _STORAGE
    if _STORAGE is None:
        _STORAGE = cairn_query.rebuild_from_sources(db_path=_DEFAULT_DB_PATH)
    return _STORAGE


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def lookup(entity_type: str, id: str) -> Any:
    """Look up a single entity by type and id. Raises KeyError if missing.

    entity_type is matched case-insensitively (e.g. 'INVARIANT' == 'invariant').
    """
    return cairn_query.lookup(_get_storage(), entity_type.lower(), id)


def search(entity_type: str, filters: dict | None = None) -> list[Any]:
    """Return all entities of entity_type matching optional filters.

    entity_type is matched case-insensitively.
    """
    return cairn_query.search(_get_storage(), entity_type.lower(), filters)


def path_bindings(path: str) -> list[Any]:
    """Return all entities bound to path via BINDS edges."""
    return cairn_query.path_bindings(_get_storage(), path)


def cypher(query: str, params: dict | None = None) -> list[dict]:
    """Execute a raw Cypher query. Returns list of row dicts."""
    return cairn_query.cypher(_get_storage(), query, params)


# ---------------------------------------------------------------------------
# Tool registry (dict form accepted by test_v2_tools_module_imports_and_lists_four_tools)
# ---------------------------------------------------------------------------

TOOLS: dict[str, Any] = {
    "lookup": lookup,
    "search": search,
    "path_bindings": path_bindings,
    "cypher": cypher,
}
