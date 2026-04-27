"""Phase 2 RED — compression/lever-Z-fixup §S2.

Asserts the consumer-migration doc ``docs/upgrading-from-pre-compression.md``
exists and enumerates the five wiring deltas a consumer must apply
post-merge to make the new compression-feature wiring functional in an
existing project consuming cairn via ``.slice-system → .`` symlink.

Brittle by design — the cluster-RED-test discipline from
``compression/learnings-capture`` retry: a cluster whose Phase-3 surface is
prose-only must still carry a RED test (cheap signal that GREEN cannot
vacuously satisfy).

Per ``.claude/current-slice/intent.md`` §S2 + §S5.

Expected at Phase 2 (RED): FAILS — the file does not yet exist.
"""

from __future__ import annotations

from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
DOC_PATH = CAIRN_ROOT / "docs" / "upgrading-from-pre-compression.md"


def test_s2_doc_exists():
    """intent §S2 — the consumer-migration doc MUST exist."""
    assert DOC_PATH.is_file(), (
        f"intent §S2 — `docs/upgrading-from-pre-compression.md` must exist; "
        f"missing at {DOC_PATH}"
    )


def test_s2_doc_names_five_wiring_delta_topics():
    """intent §S2 — the doc MUST cover the five named wiring-delta topics.

    Topics are anchored by stable substring tokens (case-insensitive) drawn
    from intent.md §S2's enumerated list:

      1. Hook registration in `.claude/settings.json`
      2. MCP server registration in `.mcp.json` (cairn-knowledge stdio)
      3. Python dependencies (`pydantic`, `kuzu`, `mistune`, `typer`,
         `fastmcp`) under cairn's venv vs vendored
      4. Agent + slash-command discoverability (Claude Code reads from
         consumer's `.claude/agents/` and `.claude/commands/`)
      5. CLAUDE.md updates for retired stdlib-only and Rust-mapping
         constraints

    Stable token chosen per topic (the test asserts presence of the token
    string, not a specific section-header form, to keep brittleness
    bounded to load-bearing semantics).
    """
    body = DOC_PATH.read_text()
    lower = body.lower()
    required_tokens = (
        ".claude/settings.json",  # delta 1: hook registration target
        ".mcp.json",  # delta 2: MCP server registration target
        "pydantic",  # delta 3: representative substrate dep
        ".claude/agents",  # delta 4: agent discoverability path
        "claude.md",  # delta 5: CLAUDE.md surgery topic
    )
    missing = [t for t in required_tokens if t.lower() not in lower]
    assert not missing, (
        f"intent §S2 — consumer-migration doc must name all five wiring "
        f"deltas via stable tokens; missing tokens: {missing!r}"
    )


def test_s2_doc_includes_five_verify_snippets():
    """intent §S2 — each of the five deltas carries a "Verify" snippet.

    intent.md: "5 numbered sections (one per delta), each ≤200 words, with
    a 'Verify' snippet (a one-line shell command or grep that confirms the
    delta landed)."

    Test asserts the literal token `Verify` appears at least 5 times in the
    doc body (one per delta). The snippet itself can be a fenced shell
    block, an inline `grep`, or a one-line command — Phase-3 retains
    prose-shape latitude — but the count of ``Verify`` markers is the
    load-bearing signal.
    """
    body = DOC_PATH.read_text()
    count = body.count("Verify")
    assert count >= 5, (
        f"intent §S2 — doc must include >=5 'Verify' snippet markers (one "
        f"per wiring delta); found {count} occurrences"
    )


def test_s2_doc_names_cairn_knowledge_stdio_constraint():
    """intent §S2 delta 2 — the doc MUST flag cairn-knowledge as stdio.

    Stable token: substring `stdio` co-located with `cairn-knowledge`.
    Intent §S2 delta 2 explicitly names this constraint and the
    PYTHONPATH-vs-symlink open question.
    """
    body = DOC_PATH.read_text().lower()
    assert "stdio" in body, (
        "intent §S2 delta 2 — doc must name the `stdio` transport "
        "constraint of the cairn-knowledge MCP server"
    )
    assert "cairn-knowledge" in body or "cairn_knowledge" in body, (
        "intent §S2 delta 2 — doc must reference the `cairn-knowledge` "
        "MCP server by name"
    )


def test_s2_doc_names_retired_constraints():
    """intent §S2 delta 5 — doc names both retired CLAUDE.md constraints.

    intent.md §S2 delta 5 enumerates: stdlib-only target (retired by ADR
    `cairn-substrate-and-fastmcp` D3) and Rust-mapping end-of-v1 target
    (retired by ADR D4). Both need to be reachable from the doc body so
    consumers know which CLAUDE.md lines to revisit.
    """
    body = DOC_PATH.read_text().lower()
    assert "stdlib" in body, (
        "intent §S2 delta 5 — doc must reference the retired `stdlib-only` "
        "constraint by name"
    )
    assert "rust" in body, (
        "intent §S2 delta 5 — doc must reference the retired Rust-mapping "
        "end-of-v1 target by name"
    )
