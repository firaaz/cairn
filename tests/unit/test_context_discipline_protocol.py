"""Phase 2 validation tests for SLICE-002 — context discipline protocol.

Verifies intent.md V1–V7: the rewritten handoff/catchup/start-slice skill
templates, the new templates/handoff.md pointer template, the
.claude/learning.md staging ground, and the docs/operational-reference.md
Context Discipline Protocol section collectively satisfy ADR-002's
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


# --- V2: Handoff skill template free of old narrative format ---------------


def test_v2_handoff_skill_template_has_no_narrative_residue():
    """V2 — handoff.md skill template carries NO banned narrative headings,
    references templates/handoff.md as target format, and documents the
    150–400 token budget as a single fact (shared-window around `token`)."""
    path = CAIRN_ROOT / "commands/claude-code/handoff.md"
    assert path.is_file(), f"{path} does not exist"
    text = path.read_text()

    found = contains_none(
        text,
        [
            "What This Session Was About",
            "What Was Accomplished",
            "Surprises or Discoveries",
            "Self-Check",
            "Self Check",
        ],
        case_insensitive=True,
    )
    assert not found, f"forbidden narrative substrings present: {found}"

    assert "templates/handoff.md" in text, (
        "skill template does not reference templates/handoff.md as target format"
    )

    assert shared_window(text, "150", "400", "token", window=100), (
        "handoff.md does not document the 150–400 token budget as a single "
        "fact (both `150` and `400` must appear within 100 chars of the same "
        "`token` occurrence)"
    )


# --- V3: Catchup skill template encodes the tier model --------------------


def test_v3_catchup_skill_template_encodes_tier_model():
    """V3 — catchup.md labels Tier 1/2/3, carries the verbatim DISPATCH
    admission-criteria header, a subagent contract with all required keys,
    and the exact Tier 1 read list."""
    path = CAIRN_ROOT / "commands/claude-code/catchup.md"
    assert path.is_file(), f"{path} does not exist"
    text = path.read_text()

    missing_tiers = contains_all(text, ["Tier 1", "Tier 2", "Tier 3"])
    assert not missing_tiers, f"tier labels missing: {missing_tiers}"

    assert "DISPATCH Tier 2 subagent if and only if:" in text, (
        "missing verbatim admission-criteria header"
    )

    missing_contract_keys = contains_all(
        text,
        [
            "CONTEXT:",
            "QUESTION:",
            "FILES AVAILABLE:",
            "YOUR BEHAVIOR:",
            "YOUR RETURN",
            "DO NOT return:",
        ],
    )
    assert not missing_contract_keys, (
        f"subagent contract block missing keys: {missing_contract_keys}"
    )

    missing_tier1_reads = contains_all(
        text,
        [
            ".claude/handoff.md",
            ".claude/current-slice/slice.yaml",
            ".claude/sweep.yaml",
            "git log --oneline -5",
            "git status --short",
        ],
    )
    assert not missing_tier1_reads, (
        f"Tier 1 read list missing items: {missing_tier1_reads}"
    )


# --- V4: Start-slice closure wipes current-slice --------------------------


def test_v4_start_slice_closure_wipes_current_slice():
    """V4 — start-slice.md Step 7 places a wipe verb within 300 chars of
    `.claude/current-slice`; `.claude/archive/` appears nowhere; Step 8 still
    references `.claude/completed-slices/`."""
    path = CAIRN_ROOT / "commands/claude-code/start-slice.md"
    assert path.is_file(), f"{path} does not exist"
    text = path.read_text()

    assert ".claude/archive/" not in text, (
        "`.claude/archive/` appears in start-slice.md (ADR-002 rejected the archive alternative)"
    )

    step7 = slice_section(text, "## Step 7")
    assert step7 is not None, "no `## Step 7` section in start-slice.md"

    wipe_keywords = ["wipe", "rm -r", "git rm", "remove", "delete"]
    wipe_ok = any(
        proximity(
            step7,
            verb,
            ".claude/current-slice",
            max_distance=300,
            case_insensitive=True,
        )
        for verb in wipe_keywords
    )
    assert wipe_ok, (
        "Step 7 does not place any wipe verb "
        f"({wipe_keywords}) within 300 chars of `.claude/current-slice`"
    )

    step8 = slice_section(text, "## Step 8")
    assert step8 is not None, "no `## Step 8` section in start-slice.md"
    assert ".claude/completed-slices/" in step8, (
        "Step 8 no longer references `.claude/completed-slices/` (failed-slice path)"
    )


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
        ["150", "400", "Tier 1", "Tier 2", "DISPATCH", "learning.md", "SLICE-003"],
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
