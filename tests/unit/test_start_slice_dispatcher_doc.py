"""Phase 2 RED — substrate/start-slice-pythonpath-paper-cut.

Asserts that operator-facing documentation never quotes the bare dispatcher
line ``python -m slice_orchestrator``: copy-paste of that line into a fresh
shell at repo root raises ``ModuleNotFoundError`` because the package lives
under ``scripts/slice_orchestrator/`` and is not installed into the project
venv. The canonical working form is::

    PYTHONPATH=scripts uv run python -m slice_orchestrator

Per ``.claude/current-slice/intent.md`` §Specification: every occurrence of
the substring ``python -m slice_orchestrator`` in the four envelope files
must be preceded (in the same line, immediately before ``python``) by the
literal ``uv run ``. Equivalently, the negative-lookbehind regex
``(?<!uv run )python -m slice_orchestrator`` matches zero times across the
envelope.

Envelope (four operator-facing docs):
  - commands/claude-code/start-slice.md         (line 3, primary)
  - commands/claude-code/start-slice-legacy.md  (line 3, prose mirror)
  - CHANGELOG.md                                (line 14, CLI ref)
  - docs/features/compression.md                (line 57, CLI ref)

Out of scope (intentionally NOT scanned): ``docs/lessons.md`` (historical
narrative), ``docs/plans/**``, ``docs/adr/**``,
``docs/operational-reference.md``, ``.claude/sweep-results/**``,
``.claude/completed-slices/**``, ``.claude/features/**`` (machine state),
``.claude/current-slice/**`` (this slice's own prose),
``scripts/slice_orchestrator/__init__.py`` and ``__main__.py`` (module
docstrings — code, not operator instruction), and the
``test_slice_orchestrator_package_split.py`` self-references.

Expected at Phase 2 (RED): FAILS — bare form present in all four envelope
files at slice open. After Phase 3 GREEN: PASSES.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent

ENVELOPE_DOCS = (
    "commands/claude-code/start-slice.md",
    "commands/claude-code/start-slice-legacy.md",
    "CHANGELOG.md",
    "docs/features/compression.md",
)

# Fixed-width negative lookbehind: ``uv run `` is exactly 7 chars, so
# Python's ``re`` accepts it. A match indicates a bare dispatcher reference
# that an operator copying the line would hit ModuleNotFoundError on.
BARE_DISPATCHER_RE = re.compile(r"(?<!uv run )python -m slice_orchestrator")
CANONICAL_PREFIX = "PYTHONPATH=scripts uv run python -m slice_orchestrator"


@pytest.mark.parametrize("rel_path", ENVELOPE_DOCS)
def test_envelope_doc_has_no_bare_dispatcher_reference(rel_path: str) -> None:
    """intent §Specification — every ``python -m slice_orchestrator`` in the
    four envelope docs must be preceded by ``uv run ``.

    A failure surfaces the line number(s) carrying the bare form so Phase-3
    can replace them in place.
    """
    doc_path = CAIRN_ROOT / rel_path
    assert doc_path.is_file(), (
        f"envelope doc missing on disk: {rel_path} (expected at {doc_path})"
    )
    body = doc_path.read_text()
    offending: list[tuple[int, str]] = []
    for lineno, line in enumerate(body.splitlines(), start=1):
        if BARE_DISPATCHER_RE.search(line):
            offending.append((lineno, line.rstrip()))
    assert not offending, (
        f"intent §Specification — {rel_path} contains bare "
        f"`python -m slice_orchestrator` references that must carry the "
        f"`PYTHONPATH=scripts uv run ` prefix; offending lines: "
        f"{offending!r}"
    )


@pytest.mark.parametrize("rel_path", ENVELOPE_DOCS)
def test_envelope_doc_uses_canonical_prefix_when_dispatcher_named(
    rel_path: str,
) -> None:
    """intent §Specification — when a doc names the dispatcher at all, the
    canonical ``PYTHONPATH=scripts uv run python -m slice_orchestrator``
    prefix MUST appear in the file body.

    Guards against a vacuous Phase-3 fix that deletes every dispatcher
    reference rather than rewriting it. The four envelope docs all
    legitimately need to name the dispatcher (primary command surface,
    legacy fallback note, changelog CLI ref, feature closeout summary), so
    presence of the canonical form is load-bearing.
    """
    doc_path = CAIRN_ROOT / rel_path
    body = doc_path.read_text()
    assert "slice_orchestrator" in body, (
        f"envelope assumption broken — {rel_path} no longer references "
        f"`slice_orchestrator` at all; either the slice envelope is stale "
        f"or Phase-3 over-deleted"
    )
    assert CANONICAL_PREFIX in body, (
        f"intent §Specification — {rel_path} references the dispatcher but "
        f"is missing the canonical prefix `{CANONICAL_PREFIX}`; an operator "
        f"copying the documented line would hit ModuleNotFoundError"
    )
