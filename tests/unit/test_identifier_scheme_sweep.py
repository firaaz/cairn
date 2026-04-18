"""Phase 2 validation tests for identifier-scheme/doc-sweep.

Covers ADR identifier-scheme §D7 Phase 2 cross-reference-sweep bullet
(`docs/adr/identifier-scheme.md:120`; intent's "§D7 Phase 2 Part 3"
shorthand). Sweeps residual `SLICE-NNN` and `ADR-NNN` references out of
the active long-form prose corpus enumerated in intent.md's envelope.

RED pre-Phase-3 (fails until the sweep lands), GREEN post-Phase-3:
  - test_envelope_zero_residual_modulo_allowlist
      → intent verification item 1 (zero-residual grep on in-scope files,
        modulo the discussion-of-legacy-format allowlist below).
  - test_dogfood_docstring_identifier_migrated
      → intent verification item 2 (tests/unit/test_dogfood_evaluate.py
        module docstring contains no SLICE-NNN/ADR-NNN).

GREEN pre/post (canary):
  - test_preserve_allowlist_entries_still_present
      → Phase 3 scope guard. Every PRESERVE snippet must still appear in
        its source file after sweep; Phase 3 must not accidentally delete
        discussion-of-legacy-format sites while sweeping nearby residuals.

Phase 4 Auditor checklist (NOT asserted here; see validation/approach.md):
  - intent items 3 (diff scope), 4 (tolerance suites), 5 (full suite),
    6 (validate_architecture), 7 (no frontmatter crossref diffs),
    8 (ADR_EDITORIAL_FIX audit trail).

Stdlib + pytest.
"""

import ast
import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent

IDENTIFIER_PATTERN = re.compile(r"(SLICE-[0-9]+|ADR-[0-9]+)")


def _envelope_paths() -> list[Path]:
    paths = [
        CAIRN_ROOT / "commands/claude-code/handoff.full.md",
        CAIRN_ROOT / "docs/spec-v1.md",
        CAIRN_ROOT / "docs/lessons.md",
        CAIRN_ROOT / "docs/operational-reference.md",
        CAIRN_ROOT / "docs/ARCHITECTURE.md",
    ]
    paths.extend(sorted((CAIRN_ROOT / "docs/adr").glob("*.md")))
    return paths


# Discussion-of-legacy-format allowlist (intent §Specification Detail).
# Each snippet is a substring of the preserved line; a matching line in
# the envelope is exempted iff it contains at least one snippet for its
# relative path. Phase 3 MUST retain these sites unchanged.
PRESERVE: dict[str, tuple[str, ...]] = {
    "docs/adr/semantic-identity.md": (
        "sequential numeric prefixes for both slices (SLICE-001, SLICE-002)",
        "`SLICE-003` communicates nothing",
        "`after: [SLICE-007]`",
    ),
    "docs/adr/bootstrap-exception.md": (
        "a degenerate SLICE-000",
        "Treat the bootstrap as SLICE-000",
    ),
    "docs/adr/feature-slice-model.md": (
        "Completed slices (SLICE-001 through current) retain their identities",
    ),
}


def _residuals(path: Path) -> list[tuple[int, str]]:
    text = path.read_text()
    rel = path.relative_to(CAIRN_ROOT).as_posix()
    snippets = PRESERVE.get(rel, ())
    out: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not IDENTIFIER_PATTERN.search(line):
            continue
        if any(s in line for s in snippets):
            continue
        out.append((lineno, line.rstrip()))
    return out


def test_envelope_zero_residual_modulo_allowlist() -> None:
    offenders: list[str] = []
    for path in _envelope_paths():
        rel = path.relative_to(CAIRN_ROOT).as_posix()
        for lineno, line in _residuals(path):
            offenders.append(f"{rel}:{lineno}: {line}")
    assert not offenders, (
        "Residual legacy identifiers in envelope after sweep:\n" + "\n".join(offenders)
    )


def test_dogfood_docstring_identifier_migrated() -> None:
    path = CAIRN_ROOT / "tests/unit/test_dogfood_evaluate.py"
    tree = ast.parse(path.read_text())
    docstring = ast.get_docstring(tree) or ""
    match = IDENTIFIER_PATTERN.search(docstring)
    assert match is None, (
        f"test_dogfood_evaluate.py module docstring still contains "
        f"legacy identifier {match.group(0)!r}"
    )


def test_preserve_allowlist_entries_still_present() -> None:
    missing: list[str] = []
    for rel, snippets in PRESERVE.items():
        path = CAIRN_ROOT / rel
        text = path.read_text() if path.exists() else ""
        for s in snippets:
            if s not in text:
                missing.append(f"{rel}: {s!r}")
    assert not missing, (
        "Preserved discussion-of-legacy-format sites missing after sweep:\n"
        + "\n".join(missing)
    )
