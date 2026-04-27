"""Phase 2 RED — compression/lever-Y-mcp-substrate V7.

`.claude/agents/phase-1-writer.md` MUST:
  - Frontmatter `tools:` no longer contains `Read` or `Bash`
    (defense-in-depth outer gate per ADR D8 layered model).
  - Prompt body lists the four MCP tools by name (lookup, search,
    path_bindings, cypher) and directs query-first behavior.

Per intent.md §S5 + V7.

Expected at Phase 2: FAILS — the agent file currently lists Read & Bash
in `tools:` and has no MCP-tool guidance.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_FILE = CAIRN_ROOT / ".claude" / "agents" / "phase-1-writer.md"


def _read_frontmatter_and_body():
    text = AGENT_FILE.read_text()
    m = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    assert m, (
        f"phase-1-writer.md missing YAML frontmatter; got first 80 chars: {text[:80]!r}"
    )
    return m.group(1), m.group(2)


def _tools_field(frontmatter: str) -> list[str]:
    for line in frontmatter.splitlines():
        if line.startswith("tools:"):
            raw = line.split(":", 1)[1].strip()
            return [t.strip() for t in raw.split(",") if t.strip()]
    pytest.fail(
        f"phase-1-writer.md frontmatter has no `tools:` line; got {frontmatter!r}"
    )
    return []  # unreachable


def test_v7_tools_frontmatter_excludes_read_and_bash():
    """intent §S5 — Read removed from agent's tools list.

    Post-`compression/lever-Z-fixup` §S1: `Bash` was restored to this
    frontmatter to unblock the documented `.claude/**` Bash-heredoc escape
    used by the orchestrator's phase-1-writer subagent. The original V7
    `Bash not in tools` assertion was inverted by S1 and dropped per
    operator-routed envelope expansion (see
    `.claude/current-slice/integration/envelope-expansions.log`,
    2026-04-27 entry). `Read` remains absent — Slice-2-fixup hardening
    plus L-Z-fixup intent §S1 hard non-goal preserve that.
    """
    fm, _ = _read_frontmatter_and_body()
    tools = _tools_field(fm)
    assert "Read" not in tools, (
        f"intent §S5 — `Read` must be removed from phase-1-writer tools; got {tools!r}"
    )


def test_v7_tools_frontmatter_keeps_authoring_tools():
    """Write/Edit remain available.

    Parent slice (compression/lever-Y-mcp-substrate) §S5 originally also
    required Grep/Glob to remain. Superseded by fixup slice
    (compression/lever-Y-mcp-substrate-fixup) §S3, which mandates dropping
    Grep/Glob from this frontmatter — the parent slice's READ_CLASS_TOOLS
    was Read-only, so the outer-gate Grep/Glob entries had no inner-gate
    counterpart and were a substrate defect. Write/Edit assertion stays.
    """
    fm, _ = _read_frontmatter_and_body()
    tools = _tools_field(fm)
    for required in ("Write", "Edit"):
        assert required in tools, (
            f"Write/Edit must remain in phase-1-writer tools; got {tools!r}"
        )


def test_v7_prompt_body_lists_four_mcp_tools_by_name():
    """intent §S5/V7 — prompt body names lookup, search, path_bindings, cypher."""
    _, body = _read_frontmatter_and_body()
    for tool_name in ("lookup", "search", "path_bindings", "cypher"):
        assert tool_name in body, (
            f"intent §S5 — prompt body must mention MCP tool `{tool_name}`; missing"
        )


def test_v7_prompt_body_references_cairn_knowledge_mcp_server():
    """intent §S5 — query-first directive references the cairn-knowledge server."""
    _, body = _read_frontmatter_and_body()
    assert "cairn-knowledge" in body or "cairn_knowledge" in body, (
        "intent §S5 — prompt body must reference the cairn-knowledge MCP server name"
    )


def test_v7_prompt_body_directs_query_first():
    """intent §S5 — body explicitly directs query-first usage."""
    _, body = _read_frontmatter_and_body()
    lower = body.lower()
    assert "query" in lower and ("mcp" in lower or "cairn-knowledge" in lower), (
        "intent §S5 — prompt body must direct query-first behavior over MCP"
    )


def test_v7_p2_no_preempt_refusal_directive_preserved():
    """intent §S5 — existing P1/P2 directives kept verbatim (escape hatches)."""
    _, body = _read_frontmatter_and_body()
    assert "P2" in body, "P2 escape hatch directive must be preserved"
    assert "P1" in body, "P1 heredoc-escape directive must be preserved"


def test_v7_mcp_json_registers_cairn_knowledge_server():
    """intent §S2 — `.mcp.json` at repo root registers the cairn-knowledge stdio server."""
    import json

    mcp_json = CAIRN_ROOT / ".mcp.json"
    assert mcp_json.exists(), "intent §S2 — .mcp.json must exist at repo root"
    data = json.loads(mcp_json.read_text())
    servers = data.get("mcpServers") or {}
    assert "cairn-knowledge" in servers, (
        f"intent §S2 — `cairn-knowledge` server must be registered; got {list(servers)!r}"
    )
    entry = servers["cairn-knowledge"]
    args = entry.get("args") or []
    assert "mcp_servers.cairn_knowledge" in args or any(
        "mcp_servers.cairn_knowledge" in str(a) for a in args
    ), (
        f"intent §S2 — `.mcp.json` must launch `python -m mcp_servers.cairn_knowledge`; "
        f"got args={args!r}"
    )
