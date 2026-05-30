"""Shared atomicity evaluator for the scope-split rule (cairn-trial-d).

Single source of truth shared by the ``atomicity_guard`` CLI gate and the
validator's ``scope-split`` assertion, so they cannot diverge on the tag set or
the pass/fail logic. The ``is_atomic`` heuristic is deliberately SHY (biased to
return True): the four-tag declaration check is the primary, zero-false-positive
enforcement and the tag is always a one-line escape.
"""

from __future__ import annotations

import re

EXCEPTION_TAGS = frozenset(
    {"universal-set", "regression-meta", "operator-bound", "trivial-existence"}
)
TAGS_REQUIRING_DECLARATION = EXCEPTION_TAGS - {"trivial-existence"}

_UNIVERSAL = re.compile(
    r"\b(every|all|each|any)\b|\bnone of\b|\bexactly the following\b|\bno\s",
    re.IGNORECASE,
)
_REGRESSION = re.compile(
    r"\bunchanged\b|\bbehaves identically\b|\bno regression\b",
    re.IGNORECASE,
)

# A side of a conjunction is a transitive action when an action verb is
# immediately followed by a noun-phrase object (article/pronoun/quantifier or a
# bare noun). Adjectival/intransitive sides ("exists", "is present",
# "well-formed", "parses as valid yaml") lack a direct object and stay atomic.
_ACTION_VERB = (
    r"(?:parses?|writes?|reads?|extracts?|extract|validates?|validate|"
    r"appends?|prints?|resolves?|reports?|normalizes?|raises?|returns?|"
    r"creates?|deletes?|updates?|builds?|generates?|emits?|loads?|stores?|"
    r"records?|checks?|removes?|adds?|sets?|gets?|maps?|sends?|fetches?|"
    r"computes?|produces?|renders?|installs?|registers?|invokes?)"
)
_TRANSITIVE = re.compile(
    rf"\b{_ACTION_VERB}\s+(?:the|a|an|them|it|its|each|all|every|"
    rf"this|that|these|those)\b",
    re.IGNORECASE,
)


def _is_transitive_action(side: str) -> bool:
    return bool(_TRANSITIVE.search(side))


def is_atomic(clause: str) -> bool:
    """Shy heuristic: True unless a universal/regression/verb-conjunction signal fires."""
    text = clause.strip()
    if not text:
        return True
    if _UNIVERSAL.search(text):
        return False
    if _REGRESSION.search(text):
        return False
    sides = re.split(r"\s+and\s+|\s+&\s+|;", text)
    if len(sides) >= 2:
        actions = [s for s in sides if _is_transitive_action(s)]
        if len(actions) >= 2:
            return False
    return True


def parse_exception(item) -> tuple[str | None, str]:
    """From a ``{clause, except: "<tag>: <declaration>"}`` mapping return
    ``(tag, declaration)``; a bare string returns ``(None, "")``."""
    if not isinstance(item, dict):
        return None, ""
    raw = item.get("except")
    if raw is None:
        return None, ""
    spec = str(raw).strip()
    tag, sep, decl = spec.partition(":")
    return tag.strip(), decl.strip()


def check_clauses(must_satisfy: list) -> list[str]:
    """Return offence strings ([] == pass) for a ``must-satisfy`` clause list."""
    offences: list[str] = []
    for item in must_satisfy:
        if isinstance(item, dict):
            tag, decl = parse_exception(item)
            clause = str(item.get("clause", ""))
            if tag is None:
                if not is_atomic(clause):
                    offences.append(f"non-atomic clause (untagged): {clause}")
                continue
            if tag not in EXCEPTION_TAGS:
                offences.append(f"unknown exception tag {tag!r}: {clause}")
                continue
            if tag in TAGS_REQUIRING_DECLARATION and not decl:
                offences.append(
                    f"exception tag {tag!r} requires a non-empty declaration: {clause}"
                )
            continue
        clause = str(item)
        if not is_atomic(clause):
            offences.append(f"non-atomic clause (untagged): {clause}")
    return offences
