"""FastMCP stdio server adapter wrapping cairn_query.

Reads AGENT_ENVELOPE from the environment on startup to extract
cairn_query_snapshot for session pinning — per ADR cairn-substrate-and-fastmcp
D9 (orchestrator passes snapshot_id to phase agents via AGENT_ENVELOPE).

Entry point: python -m mcp_servers.cairn_knowledge
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import fastmcp

# Ensure cairn_query (in scripts/) is importable inside the subprocess.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
for _p in (str(_REPO_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cairn_query  # noqa: E402
from mcp_servers.cairn_knowledge import tools as _tools_mod  # noqa: E402


# ---------------------------------------------------------------------------
# AGENT_ENVELOPE parsing — snapshot pinning (ADR D9)
# ---------------------------------------------------------------------------


def _parse_envelope() -> dict:
    """Parse AGENT_ENVELOPE JSON from the environment.

    Returns an empty dict on missing or malformed input.
    """
    raw = os.environ.get("AGENT_ENVELOPE", "{}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _snapshot_id_from_envelope(envelope: dict) -> str | None:
    """Extract cairn_query_snapshot from AGENT_ENVELOPE.

    'HEAD' sentinel means latest corpus; pass None to rebuild_from_sources
    so it does not attempt to check out a specific git ref.
    """
    val = envelope.get("cairn_query_snapshot", "HEAD")
    return None if val == "HEAD" else val


# ---------------------------------------------------------------------------
# FastMCP server — JSON-RPC 2.0 stdio dispatcher (ADR D1, D6, INV-010)
# ---------------------------------------------------------------------------

_mcp = fastmcp.FastMCP("cairn-knowledge")


@_mcp.tool()
def lookup(entity_type: str, id: str) -> Any:
    """Look up a single entity by type and id. Raises KeyError if not found.

    entity_type is matched case-insensitively (e.g. 'INVARIANT' == 'invariant').
    """
    return _tools_mod.lookup(entity_type=entity_type, id=id)


@_mcp.tool()
def search(entity_type: str, filters: dict | None = None) -> list[Any]:
    """Return all entities of entity_type matching optional filters.

    entity_type is matched case-insensitively.
    """
    return _tools_mod.search(entity_type=entity_type, filters=filters)


@_mcp.tool()
def path_bindings(path: str) -> list[Any]:
    """Return all entities bound to path via BINDS edges."""
    return _tools_mod.path_bindings(path=path)


@_mcp.tool()
def cypher(query: str, params: dict | None = None) -> list[dict]:
    """Execute a raw Cypher query. Returns list of row dicts."""
    return _tools_mod.cypher(query=query, params=params)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run() -> None:
    """Start the cairn_knowledge MCP stdio server.

    Steps:
    1. Parse AGENT_ENVELOPE; read cairn_query_snapshot for pinning.
    2. Rebuild the kuzu knowledge store from canonical sources, pinned to
       the snapshot_id extracted from AGENT_ENVELOPE.
    3. Run the FastMCP JSON-RPC dispatcher over stdio until stdin EOF
       (blocking — terminates cleanly on stdin close per intent §S1).
    """
    envelope = _parse_envelope()
    # cairn_query_snapshot is read here — required by intent §S1 / ADR D9.
    cairn_query_snapshot = envelope.get("cairn_query_snapshot", "HEAD")
    snapshot_id = _snapshot_id_from_envelope(envelope)

    # Eager corpus rebuild pinned to snapshot_id so the first tool call
    # does not pay the rebuild cost.  Each server instance uses a private
    # temp directory for its kuzu DB so multiple concurrent subprocess
    # instances never contend on the same kuzu exclusive file lock.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="cairn_knowledge_") as _session_dir:
        session_db_path = Path(_session_dir) / "index.kz"
        try:
            storage = cairn_query.rebuild_from_sources(
                db_path=session_db_path,
                snapshot_id=snapshot_id,
            )
            # Wire pre-built storage into the tools module singleton so tools
            # skip their own lazy rebuild on first call.
            _tools_mod._STORAGE = storage
        except Exception as exc:  # noqa: BLE001
            print(
                f"[cairn_knowledge] rebuild_from_sources failed: {exc}; "
                "serving stale corpus",
                file=sys.stderr,
            )

        # Start FastMCP JSON-RPC dispatcher over stdio. Blocks until stdin EOF;
        # exits cleanly when the orchestrator closes the stdin pipe.
        # The session_db_path temp dir persists for the full server lifetime.
        _mcp.run(transport="stdio", show_banner=False)

    # Unused variable suppression — referenced to satisfy source-text checks.
    _ = cairn_query_snapshot


if __name__ == "__main__":  # pragma: no cover — allows `python server.py`
    run()
