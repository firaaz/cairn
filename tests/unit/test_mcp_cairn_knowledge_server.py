"""Phase 2 RED — compression/lever-Y-mcp-substrate V2.

`mcp_servers.cairn_knowledge` ships a FastMCP stdio server adapter wrapping
`scripts/cairn_query/`. Its module entry (`python -m mcp_servers.cairn_knowledge`)
MUST start a stdio server registering exactly four tools:
``lookup``, ``search``, ``path_bindings``, ``cypher`` — per ADR
``cairn-substrate-and-fastmcp`` D6 and intent.md S1.

Expected at Phase 2: FAILS — ``mcp_servers/cairn_knowledge/`` does not exist.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent

# Repo-root path for ``import mcp_servers...`` (pyproject pythonpath only adds
# ``scripts``; the mcp_servers package lives at repo root per intent §S1).
if str(CAIRN_ROOT) not in sys.path:
    sys.path.insert(0, str(CAIRN_ROOT))


EXPECTED_TOOL_NAMES = {"lookup", "search", "path_bindings", "cypher"}


def test_v2_package_layout_exists():
    """Intent §S1 — new package ``mcp_servers/cairn_knowledge/`` exists."""
    pkg = CAIRN_ROOT / "mcp_servers" / "cairn_knowledge"
    assert pkg.is_dir(), f"package missing: {pkg}"
    assert (pkg / "__init__.py").is_file(), "package __init__.py missing"
    assert (pkg / "server.py").is_file(), "server.py missing per intent §S1"
    assert (pkg / "tools.py").is_file(), "tools.py missing per intent §S1"
    assert (pkg / "__main__.py").is_file(), (
        "__main__.py missing — intent §S1 requires `python -m mcp_servers.cairn_knowledge`"
    )


def test_v2_tools_module_imports_and_lists_four_tools():
    """Intent §S1 — tools.py exposes exactly the four read-only MCP tools."""
    mod = importlib.import_module("mcp_servers.cairn_knowledge.tools")
    # Tool registry surface: either a TOOLS list/dict or four module-level
    # callables matching the names. Skeptic accepts any of these forms.
    found: set[str] = set()
    if hasattr(mod, "TOOLS"):
        registry = mod.TOOLS
        if isinstance(registry, dict):
            found = set(registry.keys())
        else:
            for entry in registry:
                name = getattr(entry, "name", None) or getattr(entry, "__name__", None)
                if name:
                    found.add(name)
    else:
        for name in EXPECTED_TOOL_NAMES:
            if hasattr(mod, name):
                found.add(name)
    assert found == EXPECTED_TOOL_NAMES, (
        f"intent §S1 — tools must be exactly {sorted(EXPECTED_TOOL_NAMES)}; "
        f"found {sorted(found)!r}"
    )


def test_v2_module_main_subprocess_starts_stdio_server():
    """Intent §S1 — `python -m mcp_servers.cairn_knowledge` boots a stdio server.

    Black-box: spawn the subprocess with stdio piped, send no input, allow it
    a short window to come up, then SIGTERM. We only assert the process
    started without an immediate import/boot crash.
    """
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_servers.cairn_knowledge"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=CAIRN_ROOT,
        env={
            **os.environ,
            "AGENT_ENVELOPE": '{"paths":[],"cairn_query_snapshot":"HEAD"}',
        },
    )
    try:
        # Give it ~1s to crash on import; if it's still running, we trust the
        # stdio loop is up. Real protocol-level handshake is integration scope.
        try:
            stdout, stderr = proc.communicate(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=2.0)
            # Process was alive at timeout → did not crash on boot. PASS.
            return
        # Process exited within 1s — failure mode for a stdio server.
        pytest.fail(
            f"`python -m mcp_servers.cairn_knowledge` exited rc={proc.returncode} "
            f"within 1s; stderr={stderr.decode(errors='replace')!r}"
        )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=2.0)


def test_v2_server_module_has_envelope_snapshot_pinning_hook():
    """Intent §S1 — server reads ``cairn_query_snapshot`` from AGENT_ENVELOPE
    and pins the session by passing it to ``rebuild_from_sources``.

    Skeptic asserts the contract by reference: ``server.py`` source must
    mention both ``AGENT_ENVELOPE`` and ``cairn_query_snapshot`` so the wiring
    is observable from a public-interface review.
    """
    server_src = (
        CAIRN_ROOT / "mcp_servers" / "cairn_knowledge" / "server.py"
    ).read_text()
    assert "AGENT_ENVELOPE" in server_src, (
        "intent §S1 — server.py must consume AGENT_ENVELOPE for snapshot pinning"
    )
    assert "cairn_query_snapshot" in server_src, (
        "intent §S1 — server.py must read cairn_query_snapshot from envelope"
    )
