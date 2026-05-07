"""Phase 2 validation tests for SLICE-002 — context discipline protocol.

Verifies intent.md V1–V7: the rewritten handoff/catchup/start-slice skill
templates, the new templates/handoff.md pointer template, the
.claude/learning.md staging ground, and the docs/operational-reference.md
Context Discipline Protocol section collectively satisfy context-discipline-protocol's
three-layer context discipline commitment (INV-002).

These are contract-conformance tests — static artifacts must match
intent.md's spec. The primitive layer below absorbs repeated parse and
assertion logic so each test_vN_* body reads like the intent bullet it
checks. Pytest + stdlib only (no hypothesis; see slice rescope 2026-04-12).
"""

import re
from pathlib import Path

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


# --- Primitives ------------------------------------------------------------


def slice_frontmatter(text: str) -> str | None:
    """Return the YAML frontmatter block between leading `---` fences, or None."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return text[4:end]


def slice_section(text: str, header: str) -> str | None:
    """Return the section starting at a line matching `header`.

    A line matches if it equals `header` exactly OR begins with `header`
    followed by a non-word boundary. This lets callers pass `## Step 7`
    and match `## Step 7: Complete a Slice` without committing to exact
    header wording.

    The section runs from the matched line to the next line beginning
    with `## ` (same-level header) or EOF. Subheaders (`### …`) stay
    inside. Returns None when no line matches.
    """
    pattern = re.compile(re.escape(header) + r"(?:$|\W)")
    lines = text.splitlines(keepends=True)
    start: int | None = None
    for i, line in enumerate(lines):
        if pattern.match(line.rstrip("\n")):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "".join(lines[start:end])


def contains_all(
    text: str,
    phrases: list[str],
    *,
    case_insensitive: bool = False,
) -> list[str]:
    """Return phrases NOT present in text. Empty list == all present."""
    haystack = text.lower() if case_insensitive else text
    missing: list[str] = []
    for phrase in phrases:
        needle = phrase.lower() if case_insensitive else phrase
        if needle not in haystack:
            missing.append(phrase)
    return missing


def contains_none(
    text: str,
    phrases: list[str],
    *,
    case_insensitive: bool = False,
) -> list[str]:
    """Return phrases that ARE present in text. Empty list == none present."""
    haystack = text.lower() if case_insensitive else text
    found: list[str] = []
    for phrase in phrases:
        needle = phrase.lower() if case_insensitive else phrase
        if needle in haystack:
            found.append(phrase)
    return found


def shared_window(
    text: str,
    a: str,
    b: str,
    anchor: str,
    window: int = 100,
) -> bool:
    """V2 option-B: does SOME occurrence of `anchor` have BOTH `a` and `b`
    within ±window chars of it?

    Approach.md locked this to shared-window semantics (both `150` and
    `400` must cluster around the SAME `token` mention) rather than
    independent proximity, so two unrelated `token` references cannot
    spuriously pass.
    """
    start = 0
    while True:
        idx = text.find(anchor, start)
        if idx == -1:
            return False
        lo = max(0, idx - window)
        hi = idx + len(anchor) + window
        chunk = text[lo:hi]
        if a in chunk and b in chunk:
            return True
        start = idx + 1


def proximity(
    text: str,
    keyword: str,
    anchor: str,
    max_distance: int = 300,
    *,
    case_insensitive: bool = False,
) -> bool:
    """Return True if some occurrence of `anchor` has `keyword` within
    ±max_distance chars of it."""
    hay = text.lower() if case_insensitive else text
    key = keyword.lower() if case_insensitive else keyword
    anc = anchor.lower() if case_insensitive else anchor
    start = 0
    while True:
        idx = hay.find(anc, start)
        if idx == -1:
            return False
        lo = max(0, idx - max_distance)
        hi = idx + len(anc) + max_distance
        if key in hay[lo:hi]:
            return True
        start = idx + 1


def rglob_missing(
    root: Path,
    glob: str,
    banned: list[str],
) -> list[tuple[Path, str]]:
    """Return (path, banned_phrase) for every file under root/glob that
    contains any banned phrase. Empty list == compliance."""
    hits: list[tuple[Path, str]] = []
    for path in sorted(root.rglob(glob)):
        try:
            text = path.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        for phrase in banned:
            if phrase in text:
                hits.append((path, phrase))
    return hits


# --- V1: Handoff template exists and is tight ------------------------------


def test_v1_handoff_template_exists_and_is_tight():
    """V1 — templates/handoff.md exists, body ≤2000 chars, frontmatter carries
    the four required keys, body has the four required section headers."""
    path = CAIRN_ROOT / "templates/handoff.md"
    assert path.is_file(), f"{path} does not exist"

    text = path.read_text()
    assert len(text) <= 2000, (
        f"{path} is {len(text)} chars, exceeds 2000 (~400 token budget)"
    )

    fm = slice_frontmatter(text)
    assert fm is not None, "templates/handoff.md has no `---` frontmatter block"
    missing_keys = contains_all(fm, ["slice:", "phase:", "branch:", "as-of:"])
    assert not missing_keys, f"frontmatter missing keys: {missing_keys}"

    missing_headers = contains_all(
        text,
        ["## State", "## Next", "## Blocked / Pending", "## Pointers"],
    )
    assert not missing_headers, f"body missing section headers: {missing_headers}"


# --- V5: Learning staging ground exists and is minimal -------------------


def test_v5_learning_staging_ground_exists_and_is_minimal():
    """V5 — .claude/learning.md exists, size < 500 bytes, first non-blank
    line is exactly `# Session Learning Staging Ground`."""
    path = CAIRN_ROOT / ".claude/learning.md"
    assert path.is_file(), f"{path} does not exist"

    size = path.stat().st_size
    assert size < 500, f"{path} is {size} bytes, exceeds 500"

    lines = path.read_text().splitlines()
    non_blank = next((line for line in lines if line.strip()), None)
    assert non_blank == "# Session Learning Staging Ground", (
        f"first non-blank line is {non_blank!r}, expected `# Session Learning Staging Ground`"
    )


# --- V6: Operational reference documents the new protocol --------------


def test_v6_operational_reference_documents_protocol():
    """V6 — operational-reference.md has a `## Context Discipline Protocol`
    section with all required keywords; old `## Session Handoff Protocol`
    section either absent or cross-references the new section."""
    path = CAIRN_ROOT / "docs/operational-reference.md"
    assert path.is_file(), f"{path} does not exist"
    text = path.read_text()

    section = slice_section(text, "## Context Discipline Protocol")
    assert section is not None, "missing `## Context Discipline Protocol` section"

    missing = contains_all(
        section,
        [
            "150",
            "400",
            "Tier 1",
            "Tier 2",
            "DISPATCH",
            "learning.md",
            "context-discipline-protocol",
        ],
    )
    assert not missing, f"section missing required keywords: {missing}"
    assert "wipe" in section or "remove" in section, (
        "Context Discipline Protocol section has no wipe/remove keyword"
    )

    old = slice_section(text, "## Session Handoff Protocol")
    assert old is None or "Context Discipline Protocol" in old, (
        "`## Session Handoff Protocol` exists but does not cross-reference the new section"
    )


# --- V7: No stale narrative residue under commands/ or templates/ --------


def test_v7_no_stale_narrative_residue():
    """V7 — literal phrases `Surprises or Discoveries` and
    `What This Session Was About` appear 0 times across commands/ and templates/."""
    banned = ["Surprises or Discoveries", "What This Session Was About"]
    commands_hits = rglob_missing(CAIRN_ROOT / "commands", "*.md", banned)
    templates_hits = rglob_missing(CAIRN_ROOT / "templates", "*.md", banned)
    hits = commands_hits + templates_hits
    assert not hits, f"stale narrative residue found: {hits}"
