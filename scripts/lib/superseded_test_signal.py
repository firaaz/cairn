"""Triager helper: detect a RAISE_ISSUE pointing at tests superseded by a firm contract.

Pure function. Re-located from scripts/slice_orchestrator/core.py during the
M4 cairn-shrink (2026-05-07). The triager-tdd agent prose references this
function as the canonical heuristic for biasing toward ESCALATE_TO_USER instead
of RE_DISPATCH-to-Phase-2 when a recently-firm contract supersedes the tests
named in the issue.

Tests pin the semantics at tests/unit/test_triager_superseded_heuristic.py.
"""

from __future__ import annotations

import re

_SUPERSEDE_RE = re.compile(r"\bsuperseded?\b", re.IGNORECASE)
_INV_RE = re.compile(r"\bINV-\d{3}\b", re.IGNORECASE)
_DC_RE = re.compile(r"\bDC-\d+\b", re.IGNORECASE)


def detect_superseded_test_signal(raise_issue_summary, current_slice_intent):
    """Pure-function signal detector for RAISE_ISSUE text that names tests
    superseded by a firm contract the current slice just landed.

    Returns ``{"hint": "likely_superseded", "evidence": [<tokens>]}`` when any
    trigger fires, else ``None``. Triggers:

    - ``\\bsuperseded?\\b`` (the root ``supersede`` or ``superseded``; trailing
      ``s`` as in ``supersedes`` is deliberately excluded by the right word
      boundary).
    - ``\\bINV-\\d{3}\\b`` — fires regardless of intent text.
    - ``\\bDC-\\d+\\b`` — AND-gated on the same token appearing (case
      insensitively) in ``current_slice_intent``, so unrelated DC references
      (e.g. a Phase-3 quoting someone else's ADR) do not fire.

    Evidence is the list of distinct matched tokens in first-match order of
    the summary. No I/O, deterministic; suitable for unit test. Advisory
    only — the orchestrator passes the dict through to the triager and does
    not second-guess the triager's final action.
    """
    if not raise_issue_summary:
        return None
    hits = []
    for m in _SUPERSEDE_RE.finditer(raise_issue_summary):
        hits.append((m.start(), m.group(0)))
    for m in _INV_RE.finditer(raise_issue_summary):
        hits.append((m.start(), m.group(0)))
    for m in _DC_RE.finditer(raise_issue_summary):
        token = m.group(0)
        if current_slice_intent and re.search(
            r"\b" + re.escape(token) + r"\b",
            current_slice_intent,
            re.IGNORECASE,
        ):
            hits.append((m.start(), token))
    if not hits:
        return None
    hits.sort(key=lambda h: h[0])
    evidence = []
    seen = set()
    for _, text in hits:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        evidence.append(text)
    return {"hint": "likely_superseded", "evidence": evidence}
