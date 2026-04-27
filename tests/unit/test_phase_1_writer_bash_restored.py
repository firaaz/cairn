"""Phase 2 RED — compression/lever-Z-fixup §S1.

Asserts that ``.claude/agents/phase-1-writer.md`` frontmatter ``tools:`` line
restores ``Bash`` (alongside ``Write`` and ``Edit``) so the documented
Phase-1 Bash-heredoc escape (used by the orchestrator's phase-1-writer
subagent to write ``intent.md`` and ``.claude/features/<feature>.yaml``
under Claude Code's outer ``.claude/**`` sensitive-file Write gate) is
reachable again.

Negative regression: ``Grep`` and ``Glob`` MUST remain absent from the
same line — the Slice-2-fixup canonical-knowledge frontmatter hardening
stays in place. Only ``Bash`` is restored.

Per ``.claude/current-slice/intent.md`` §S1 + §S5, ADR
``cairn-substrate-and-fastmcp`` D8 (defense-in-depth layered model).

Expected at Phase 2 (RED): FAILS — current line 4 reads
``tools: Write, Edit`` and ``Bash`` is absent.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_FILE = CAIRN_ROOT / ".claude" / "agents" / "phase-1-writer.md"


def _read_frontmatter() -> str:
    text = AGENT_FILE.read_text()
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, (
        f"phase-1-writer.md missing YAML frontmatter; got first 80 chars: {text[:80]!r}"
    )
    return m.group(1)


def _tools_field(frontmatter: str) -> list[str]:
    for line in frontmatter.splitlines():
        if line.startswith("tools:"):
            raw = line.split(":", 1)[1].strip()
            return [t.strip() for t in raw.split(",") if t.strip()]
    pytest.fail(
        f"phase-1-writer.md frontmatter has no `tools:` line; got {frontmatter!r}"
    )
    return []  # unreachable


def test_s1_tools_includes_bash():
    """intent §S1 — `Bash` MUST be in the phase-1-writer `tools:` list.

    Restoration unblocks the ``.claude/**`` Bash-heredoc escape that the
    orchestrator-driven phase-1-writer subagent depends on for writing
    ``intent.md`` and ``.claude/features/<feature>.yaml``.
    """
    fm = _read_frontmatter()
    tools = _tools_field(fm)
    assert "Bash" in tools, (
        f"intent §S1 — `Bash` must be present in phase-1-writer `tools:` "
        f"line (Slice-2-fixup over-hardening reversal); got {tools!r}"
    )


def test_s1_tools_keeps_write_and_edit():
    """intent §S1 — `Write` and `Edit` MUST remain in the `tools:` list.

    These are the primary authoring tools; restoring `Bash` does not displace
    them. Co-asserted to catch a destructive rewrite of the line.
    """
    fm = _read_frontmatter()
    tools = _tools_field(fm)
    for required in ("Write", "Edit"):
        assert required in tools, (
            f"intent §S1 — `{required}` must remain in phase-1-writer "
            f"`tools:` line; got {tools!r}"
        )


def test_s1_tools_excludes_grep_and_glob():
    """intent §S1 negative regression — `Grep` and `Glob` MUST stay absent.

    Slice-2-fixup §S3 dropped Grep/Glob from this frontmatter as part of the
    canonical-knowledge defense-in-depth outer-gate hardening. This slice
    restores ONLY `Bash`; restoring Grep/Glob would re-open the
    canonical-knowledge frontmatter bypass and is named as a hard non-goal in
    intent.md (Hard non-goals: "Phase-1-writer frontmatter additions beyond
    `Bash` (Grep/Glob restoration would re-open canonical-knowledge
    frontmatter bypass)").
    """
    fm = _read_frontmatter()
    tools = _tools_field(fm)
    for forbidden in ("Grep", "Glob"):
        assert forbidden not in tools, (
            f"intent §S1 hard non-goal — `{forbidden}` must NOT be present "
            f"in phase-1-writer `tools:` (Slice-2-fixup hardening "
            f"preserved); got {tools!r}"
        )
