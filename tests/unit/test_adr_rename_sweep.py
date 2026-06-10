"""Rename-sweep outcome AND ongoing flat-slug shape guard for docs/adr/.

Originally Phase-2 tests for identifier-scheme/adr-rename-sweep (§D7 Phase 2
Part 1: rename 9 numeric-prefix ADRs → flat slugs, migrate `id:` frontmatter,
sweep live-tree cross-references, add CHANGELOG entry). Widened under slice
identifier-scheme/rename-sweep-test-robust: the module now additionally guards
the ongoing flat-slug shape of every live docs/adr/ ADR (filename regex +
frontmatter id/stem match) so `/new-adr` additions pass without test-source
edits. The corpus is NOT size-latched — no assertion compares docs/adr/ to a
fixed cardinality or a hardcoded whole-corpus allowlist.

RED pre-Phase-3 (rename-sweep-test-robust), GREEN post-Phase-3:
  V1 — rename outcome: flat-slug targets exist, numeric-prefix files removed
  V2 — each renamed ADR's `id:` frontmatter matches the flat slug
  V3 — `git log --follow` on a renamed ADR preserves pre-rename history
  V4 — zero `ADR-NNN` / `docs/adr/NNN-*` references in the live tree
       (excluding test_hook_tolerance.py and test_hook_relpath_bypass.py,
        whose legacy-format fixtures are load-bearing for dual-format coverage)
  V5 — `docs/adr/index.md` entries use flat-slug id and filename only
  V6 — `CHANGELOG.md` contains the migration entry (header, 9-row table,
       consumer-impact paragraph naming complex-rag-analysis, link to D7)
  V-shape — flat-slug shape over live docs/adr/*.md (identifier-scheme D2):
       filename matches ^[a-z][a-z0-9-]*\\.md$ AND frontmatter `id:` equals
       stem. Not a size-latch; scales with /new-adr additions.

GREEN pre/post (regression guards):
  V7  — scripts/validate_architecture.py exits 0
  V10 — tolerance test files still present (Phase 4 full-suite pass covers
        the behavioral re-greening via Phase-3 fixture restructuring)

Not asserted here:
  V8 — full pytest suite (Phase 4 integration check)
  V9 — ADR_EDITORIAL_FIX audit trail in implementation/notes.md (Phase 3 artifact)

Pytest + stdlib only.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

CAIRN_ROOT = Path(__file__).resolve().parent.parent.parent


# --- Rename table (canonical per intent §Specification Detail) ---------------
# (old filename, new filename, new flat-slug id)
RENAME_TABLE: list[tuple[str, str, str]] = [
    ("001-bootstrap-exception.md", "bootstrap-exception.md", "bootstrap-exception"),
    (
        "002-context-discipline-protocol.md",
        "context-discipline-protocol.md",
        "context-discipline-protocol",
    ),
    (
        "003-cliff-failure-mode-and-v1-defenses.md",
        "cliff-failure-mode-and-v1-defenses.md",
        "cliff-failure-mode-and-v1-defenses",
    ),
    (
        "004-phase-lock-and-role-declaration.md",
        "phase-lock-and-role-declaration.md",
        "phase-lock-and-role-declaration",
    ),
    ("005-semantic-identity.md", "semantic-identity.md", "semantic-identity"),
    ("006-feature-slice-model.md", "feature-slice-model.md", "feature-slice-model"),
    ("007-parallelism-v1.md", "parallelism-v1.md", "parallelism-v1"),
    (
        "008-context-tiers-integration.md",
        "context-tiers-integration.md",
        "context-tiers-integration",
    ),
    (
        "009-phase-pipeline-evaluation.md",
        "phase-pipeline-evaluation.md",
        "phase-pipeline-evaluation",
    ),
]

# Historical record only: the two pre-existing flat-slug ADRs that did not pass
# through the rename sweep. NOT used as an exhaustive allowlist for live-corpus
# shape checks — per rename-sweep-test-robust intent §2, post-sweep ADRs must
# not be enumerated in test source.
UNRENAMED_ADR_FILES = {"d3-bypass-classification.md", "identifier-scheme.md"}
INDEX_FILE = "index.md"

CHANGELOG_HEADER_TEXT = "ADR identifier migration (Phase 2 Part 1)"

# identifier-scheme D2: flat semantic slug — lowercase start, kebab-case body.
ADR_FLAT_SLUG_FILENAME_RE = re.compile(r"^[a-z][a-z0-9-]*\.md$")


# --- Live-tree scanner -------------------------------------------------------
#
# In-scope per intent envelope + verification #4:
#   docs/ (excluding docs/plans/, docs/reviews/)
#   commands/
#   scripts/
#   tests/unit/ (excluding test_hook_tolerance.py, test_hook_relpath_bypass.py)
#   .claude/features/
#   CLAUDE.md
#   CHANGELOG.md
#
# Out-of-scope per intent: .claude/completed-slices/, .claude/sweep-results/,
# .claude/plans/, docs/plans/, docs/reviews/.

_SCAN_ROOTS: list[tuple[str, set[str]]] = [
    ("docs", {"docs/plans", "docs/reviews"}),
    ("commands", set()),
    ("scripts", set()),
    ("tests/unit", set()),
    (".claude/features", set()),
]
_SCAN_TOP_FILES: list[str] = ["CLAUDE.md", "CHANGELOG.md"]
_FILE_EXCLUDES: set[str] = {
    "tests/unit/test_hook_tolerance.py",
    "tests/unit/test_hook_relpath_bypass.py",
    # Phase 2 test file itself contains the rename table as source-of-truth
    # constants; excluding it prevents self-reference false positives.
    "tests/unit/test_adr_rename_sweep.py",
}


def _scan_live_tree(pattern: re.Pattern) -> list[tuple[Path, int, str]]:
    """Return (relative-path, 1-based-line-no, line) for every pattern hit."""
    hits: list[tuple[Path, int, str]] = []

    for root_rel, dir_excludes in _SCAN_ROOTS:
        root = CAIRN_ROOT / root_rel
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(CAIRN_ROOT)
            rel_str = rel.as_posix()
            if any(rel_str.startswith(ex + "/") for ex in dir_excludes):
                continue
            if rel_str in _FILE_EXCLUDES:
                continue
            if "__pycache__" in p.parts or p.suffix in (".pyc",):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append((rel, i, line))

    for file_rel in _SCAN_TOP_FILES:
        p = CAIRN_ROOT / file_rel
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append((Path(file_rel), i, line))

    return hits


def _format_hits_summary(hits: list[tuple[Path, int, str]], limit: int = 20) -> str:
    sample = "\n".join(f"  {p}:{n}: {line.rstrip()}" for p, n, line in hits[:limit])
    tail = f"\n  ...and {len(hits) - limit} more" if len(hits) > limit else ""
    return sample + tail


# ---------------------------------------------------------------------------
# V1 — Rename outcome
# ---------------------------------------------------------------------------


class TestV1RenameOutcome:
    """Intent §Verification 1: rename table applied, numeric prefixes gone."""

    def test_all_flat_slug_targets_exist(self):
        adr_dir = CAIRN_ROOT / "docs/adr"
        missing = [
            new_name
            for _, new_name, _ in RENAME_TABLE
            if not (adr_dir / new_name).is_file()
        ]
        assert not missing, (
            f"Expected flat-slug ADR files not present under docs/adr/: {missing}. "
            f"Phase 3 must `git mv` each entry from the rename table."
        )

    def test_zero_numeric_prefix_files(self):
        adr_dir = CAIRN_ROOT / "docs/adr"
        numeric = sorted(p.name for p in adr_dir.glob("[0-9]*.md"))
        assert not numeric, (
            f"Numeric-prefix ADR files still present in docs/adr/: {numeric}. "
            f"Phase 3 must complete all renames."
        )


# ---------------------------------------------------------------------------
# V2 — Frontmatter id migration
# ---------------------------------------------------------------------------


ID_LINE_RE = re.compile(r"^id:\s*(.+?)\s*$", re.MULTILINE)


class TestV2FrontmatterIds:
    """Intent §Verification 2: each renamed ADR's `id:` is the flat slug."""

    @pytest.mark.parametrize(
        "new_name,expected_id",
        [(new, slug) for _, new, slug in RENAME_TABLE],
        ids=[slug for _, _, slug in RENAME_TABLE],
    )
    def test_id_matches_rename_table(self, new_name, expected_id):
        path = CAIRN_ROOT / "docs/adr" / new_name
        if not path.exists():
            pytest.fail(
                f"V2 prerequisite unmet: {new_name} does not exist yet "
                f"(V1 rename must apply first)"
            )
        content = path.read_text(encoding="utf-8")
        m = ID_LINE_RE.search(content)
        assert m, f"{new_name}: no `id:` frontmatter line found"
        actual = m.group(1).strip().strip("\"'")
        assert actual == expected_id, (
            f"{new_name}: id is '{actual}', expected '{expected_id}'"
        )


# ---------------------------------------------------------------------------
# V3 — git log --follow preserves rename history
# ---------------------------------------------------------------------------


class TestV3GitLogFollow:
    """Intent §Verification 3: sample check that `git mv` was used for renames."""

    def test_bootstrap_exception_history_preserved(self):
        target_path = "docs/adr/bootstrap-exception.md"
        if not (CAIRN_ROOT / target_path).exists():
            pytest.fail(
                f"V3 prerequisite unmet: {target_path} does not exist yet "
                f"(V1 rename must apply first)"
            )
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%H", "--", target_path],
            cwd=str(CAIRN_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert result.returncode == 0, (
            f"`git log --follow` failed: rc={result.returncode}\n"
            f"stderr: {result.stderr}"
        )
        commits = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
        assert len(commits) >= 2, (
            f"git log --follow {target_path} returned {len(commits)} commit(s); "
            f"expected >= 2 (one rename commit + pre-rename history). "
            f"Phase 3 must use `git mv`, not delete+create."
        )


# ---------------------------------------------------------------------------
# V4 — Live-tree grep cleanliness
# ---------------------------------------------------------------------------


class TestV4GrepCleanliness:
    """Intent §Verification 4: zero ADR-NNN / docs/adr/NNN- references live."""

    def test_no_adr_nnn_token_in_live_tree(self):
        pattern = re.compile(r"ADR-00[0-9]")
        hits = _scan_live_tree(pattern)
        assert not hits, (
            f"Found {len(hits)} `ADR-NNN` references in live-tree (excluding "
            f"legacy-tolerance tests):\n{_format_hits_summary(hits)}"
        )

    def test_no_numeric_adr_path_in_live_tree(self):
        pattern = re.compile(r"docs/adr/00[0-9]")
        hits = _scan_live_tree(pattern)
        assert not hits, (
            f"Found {len(hits)} `docs/adr/NNN-*` path references in live-tree "
            f"(excluding legacy-tolerance tests):\n{_format_hits_summary(hits)}"
        )


# ---------------------------------------------------------------------------
# V5 — index.md shape
# ---------------------------------------------------------------------------


class TestV5IndexShape:
    """Intent §Verification 5: index.md rebuilt with flat-slug ids + filenames."""

    def _read_index(self) -> str:
        return (CAIRN_ROOT / "docs/adr/index.md").read_text(encoding="utf-8")

    def test_no_numeric_adr_token_in_index(self):
        content = self._read_index()
        offenders = [ln for ln in content.splitlines() if re.search(r"ADR-00[0-9]", ln)]
        assert not offenders, (
            "docs/adr/index.md still contains `ADR-NNN` tokens:\n"
            + "\n".join(f"  {ln}" for ln in offenders)
        )

    def test_no_numeric_prefix_path_in_index(self):
        content = self._read_index()
        offenders = [
            ln for ln in content.splitlines() if re.search(r"docs/adr/00[0-9]", ln)
        ]
        assert not offenders, (
            "docs/adr/index.md still contains `docs/adr/NNN-*` path references:\n"
            + "\n".join(f"  {ln}" for ln in offenders)
        )

    def test_every_id_column_is_known_flat_slug(self):
        content = self._read_index()
        # Expected ids derive from the live docs/adr/ corpus (stems minus the
        # index itself), NOT a hardcoded allowlist — /new-adr additions flow
        # through without test-source edits (rename-sweep-test-robust §2).
        adr_dir = CAIRN_ROOT / "docs/adr"
        expected_ids = {p.stem for p in adr_dir.glob("*.md") if p.name != INDEX_FILE}
        # Parse markdown table rows: | id | title | ... |
        row_ids: list[str] = []
        for ln in content.splitlines():
            if not ln.strip().startswith("|"):
                continue
            if re.match(r"^\s*\|[-:\s|]+\|\s*$", ln):  # separator row
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not cells:
                continue
            first = cells[0]
            if first.lower() == "id":  # header row
                continue
            row_ids.append(first)
        assert row_ids, "docs/adr/index.md has no parseable table rows"
        unknown = [rid for rid in row_ids if rid not in expected_ids]
        assert not unknown, (
            f"docs/adr/index.md contains id entries outside the expected "
            f"flat-slug set: {unknown}\n"
            f"Expected one of: {sorted(expected_ids)}"
        )


# ---------------------------------------------------------------------------
# V6 — CHANGELOG migration entry
# ---------------------------------------------------------------------------


class TestV6ChangelogEntry:
    """Intent §Verification 6: migration entry in CHANGELOG.md [Unreleased]."""

    def _load_unreleased(self) -> str:
        content = (CAIRN_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        m = re.search(
            r"##\s*\[Unreleased\]\s*\n(?P<body>.*?)(?=\n##\s|\Z)",
            content,
            re.DOTALL,
        )
        assert m, "CHANGELOG.md does not contain a `## [Unreleased]` section"
        return m.group("body")

    def _load_migration_subsection(self) -> str:
        unreleased = self._load_unreleased()
        idx = unreleased.find(CHANGELOG_HEADER_TEXT)
        assert idx >= 0, (
            f"CHANGELOG.md [Unreleased] missing header '{CHANGELOG_HEADER_TEXT}'"
        )
        sub = unreleased[idx:]
        # Cut off at the next H3 heading (### ...) that isn't the header line itself
        lines = sub.splitlines()
        out: list[str] = [lines[0]]
        for ln in lines[1:]:
            if ln.startswith("### "):
                break
            out.append(ln)
        return "\n".join(out)

    def test_header_present(self):
        unreleased = self._load_unreleased()
        assert CHANGELOG_HEADER_TEXT in unreleased, (
            f"CHANGELOG [Unreleased] section missing '{CHANGELOG_HEADER_TEXT}'"
        )

    def test_rename_table_has_nine_data_rows(self):
        sub = self._load_migration_subsection()
        table_lines = [ln for ln in sub.splitlines() if ln.strip().startswith("|")]
        assert len(table_lines) >= 3, (
            f"migration subsection has no markdown table "
            f"(got {len(table_lines)} table lines, need at least header + "
            f"separator + 1 data row)"
        )
        # Classify lines: header, separator, data rows
        header = table_lines[0]
        separator = table_lines[1]
        assert re.match(r"^\s*\|[-:\s|]+\|\s*$", separator), (
            f"second table line should be markdown separator, got: {separator!r}"
        )
        data_rows = table_lines[2:]
        # Some data rows may be followed by prose; the table is the contiguous
        # prefix of pipe-prefixed lines — split there.
        contiguous_data: list[str] = []
        for ln in data_rows:
            contiguous_data.append(ln)
        assert len(contiguous_data) == 9, (
            f"migration rename table should have 9 data rows (one per "
            f"renamed ADR), found {len(contiguous_data)}.\nTable:\n"
            + "\n".join([header, separator] + contiguous_data)
        )

    def test_consumer_paragraph_names_complex_rag_analysis(self):
        sub = self._load_migration_subsection()
        assert "complex-rag-analysis" in sub, (
            "migration subsection must name `complex-rag-analysis` in the "
            "consumer-impact paragraph"
        )

    def test_cross_link_to_identifier_scheme_d7(self):
        sub = self._load_migration_subsection()
        has_adr = "identifier-scheme" in sub
        has_d7 = bool(re.search(r"\bD7\b", sub))
        assert has_adr and has_d7, (
            f"migration subsection must cross-link ADR identifier-scheme D7 "
            f"(identifier-scheme present: {has_adr}, D7 present: {has_d7})"
        )


# ---------------------------------------------------------------------------
# V-shape — Flat-slug shape guard over the live docs/adr/ corpus
# ---------------------------------------------------------------------------


def _live_adr_filenames() -> list[str]:
    """Enumerate docs/adr/*.md at collection time, excluding the index.

    Pure live-corpus enumeration — no hardcoded allowlist, no cardinality
    latch. /new-adr additions appear automatically on next collection.
    """
    adr_dir = CAIRN_ROOT / "docs/adr"
    if not adr_dir.exists():
        return []
    return sorted(p.name for p in adr_dir.glob("*.md") if p.name != INDEX_FILE)


class TestLiveCorpusFlatSlugShape:
    """Shape guard over every present docs/adr/ ADR (identifier-scheme D2).

    Widened contract (rename-sweep-test-robust §Specification Detail 3):
    every file in the live corpus (a) has a flat-slug filename and (b) carries
    `id: <stem>` frontmatter. Assertion messages always name the offending
    filename so Phase-4 log triage is single-hop. NOT size-latched: this test
    neither counts the corpus nor cross-checks it against any static allowlist.
    """

    @pytest.mark.parametrize("filename", _live_adr_filenames())
    def test_filename_is_flat_slug(self, filename):
        assert ADR_FLAT_SLUG_FILENAME_RE.match(filename), (
            f"docs/adr/{filename}: filename violates identifier-scheme D2 "
            f"flat-slug pattern `^[a-z][a-z0-9-]*\\.md$` — lowercase start, "
            f"kebab-case body, `.md` suffix required."
        )

    @pytest.mark.parametrize("filename", _live_adr_filenames())
    def test_frontmatter_id_matches_stem(self, filename):
        path = CAIRN_ROOT / "docs/adr" / filename
        content = path.read_text(encoding="utf-8")
        m = ID_LINE_RE.search(content)
        assert m, (
            f"docs/adr/{filename}: no `id:` frontmatter line found "
            f"(identifier-scheme D2 requires `id: <stem>`)."
        )
        actual = m.group(1).strip().strip("\"'")
        stem = filename[: -len(".md")]
        assert actual == stem, (
            f"docs/adr/{filename}: frontmatter id is '{actual}', "
            f"expected '{stem}' (D2: id must equal filename stem)."
        )


# ---------------------------------------------------------------------------
# V7 — Validator regression guard
# ---------------------------------------------------------------------------


class TestV7Validator:
    """Intent §Verification 7: validator exits 0. Regression guard pre+post."""

    def test_validate_architecture_exits_0(self):
        result = subprocess.run(
            [sys.executable, str(CAIRN_ROOT / "scripts" / "validate_architecture.py")],
            cwd=str(CAIRN_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"scripts/validate_architecture.py exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# V10 — Legacy-tolerance test files still present
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 2 skeptic contract (slice: identifier-scheme/rename-sweep-test-robust)
#
# The classes below assert the WIDENED contract required by the robustness
# slice: the module must guard rename-sweep outcome AND ongoing flat-slug
# shape of every docs/adr/*.md file WITHOUT a fixed-cardinality latch and
# WITHOUT a hardcoded allowlist that enumerates post-sweep ADRs. Phase 3
# must refactor the rest of this file until these classes pass; they must
# NOT be deleted.
#
# RED pre-Phase-3 (current file contains a size-latch method against a
# 12-file corpus; a 13th ADR has since landed). GREEN post-Phase-3.
#
# This section avoids hardcoding any post-sweep ADR slug literally (V3):
# the C2 probe reconstructs the forbidden slug from fragments so the grep-
# count assertion can inspect the file without naming the slug inline.
# ---------------------------------------------------------------------------


_SELF_PATH = Path(__file__).resolve()


def _self_source() -> str:
    return _SELF_PATH.read_text(encoding="utf-8")


_FLAT_SLUG_FILENAME_RE = re.compile(r"^[a-z][a-z0-9-]*\.md$")


def _run_self_in_subprocess() -> subprocess.CompletedProcess:
    """Invoke pytest against this file only, isolated from the caller.

    Uses `-k` to exclude the subprocess-driver classes (C3, C4). Without
    this, the inner pytest would re-enter those classes and spawn its own
    subprocesses, causing unbounded recursion / fixture-stage collisions.
    A nested-suppression env var is also set as a belt-and-braces guard.
    """
    env = dict(os.environ)
    env["CAIRN_SWEEP_SUPPRESS_SUBPROCESS_PROBES"] = "1"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(_SELF_PATH),
            "-q",
            "--no-header",
            "-rN",
            "-p",
            "no:cacheprovider",
            "-k",
            "not TestContractC3 and not TestContractC4",
        ],
        cwd=str(CAIRN_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )


class TestContractC1NoSizeLatch:
    """Intent §1 / §V2: retire the fixed-cardinality corpus-size assertion.

    The forbidden method name is fragment-joined so this probe itself does
    not contribute to the source-count it measures (same technique used by
    C2 for the post-sweep ADR slug). A literal occurrence anywhere in this
    file — including inside assertion bodies or error messages — would make
    the probe unsatisfiable by construction.
    """

    def test_exact_count_method_removed(self):
        forbidden = "_".join(["test", "exact", "twelve", "adr", "files", "total"])
        count = _self_source().count(forbidden)
        assert count == 0, (
            f"Method name `{forbidden}` appears in source {count} time(s); "
            f"intent §Specification Detail 1 requires it to be removed or "
            f"rewritten (no `len(docs/adr/*.md) == <int>` latch)."
        )

    def test_no_int_equality_against_adr_corpus(self):
        offenders: list[tuple[int, str]] = []
        for i, ln in enumerate(_self_source().splitlines(), 1):
            if re.search(r"==\s*\d+\b", ln) and re.search(
                r"docs/adr|adr_dir|ADR_DIR", ln
            ):
                offenders.append((i, ln.rstrip()))
        assert not offenders, (
            "Fixed-integer comparison against ADR corpus detected (intent §V2):\n"
            + "\n".join(f"  L{i}: {ln}" for i, ln in offenders)
        )

    def test_no_whole_corpus_set_equality_against_allowlist(self):
        bad = re.search(
            r'adr_dir\.glob\(\s*["\']\*\.md["\']\s*\)[\s\S]{0,600}?'
            r"UNRENAMED_ADR_FILES[\s\S]{0,300}?==",
            _self_source(),
        )
        assert bad is None, (
            "Whole-corpus set equality still constructed from "
            "UNRENAMED_ADR_FILES — intent §2 forbids its use as an "
            "exhaustive allowlist."
        )


class TestContractC2NoHardcodedPostSweepADR:
    """Intent §V3: the post-sweep ADR slug must not appear in source.

    The full slug is reconstructed from fragments below so this probe
    itself does not contribute to the grep count it measures.
    """

    def test_post_sweep_adr_slug_absent_from_source(self):
        forbidden = "-".join(["compression", "infrastructure", "bootstrap"])
        count = _self_source().count(forbidden)
        assert count == 0, (
            f"Source mentions the post-sweep ADR slug {count} time(s); "
            f"intent §V3 requires grep-count 0 for any post-sweep ADR slug."
        )


_SUPPRESS_SUBPROCESS_PROBES = (
    os.environ.get("CAIRN_SWEEP_SUPPRESS_SUBPROCESS_PROBES") == "1"
)


@pytest.mark.skipif(
    _SUPPRESS_SUBPROCESS_PROBES,
    reason="nested subprocess run: C3 driver suppressed to prevent recursion",
)
class TestContractC3CurrentCorpusPasses:
    """Intent §V1: sweep suite exits 0 against the present docs/adr/ contents."""

    def test_sweep_tests_pass_on_live_corpus(self):
        result = _run_self_in_subprocess()
        assert result.returncode == 0, (
            f"pytest exited {result.returncode} on the live corpus.\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )


@pytest.fixture
def _synthetic_valid_adr():
    slug = "z-synthetic-valid-adr-probe"
    path = CAIRN_ROOT / "docs/adr" / f"{slug}.md"
    # Idempotent setup: purge any leftover from an interrupted prior run.
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    path.write_text(
        "---\n"
        f"id: {slug}\n"
        'name: "synthetic probe ADR — phase-2 skeptic fixture"\n'
        "status: accepted\n"
        "carrier: rationale-only\n"
        "---\n"
        "\n"
        "Synthetic body. No residue tokens.\n",
        encoding="utf-8",
    )
    try:
        yield slug, path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def _synthetic_malformed_filename_adr():
    # Underscore violates ^[a-z][a-z0-9-]*\.md$ (kebab-case only).
    name = "bad_underscore_name_probe.md"
    path = CAIRN_ROOT / "docs/adr" / name
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    path.write_text(
        "---\nid: bad_underscore_name_probe\nstatus: accepted\n---\n\nbody\n",
        encoding="utf-8",
    )
    try:
        yield name, path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def _synthetic_mismatched_id_adr():
    slug = "z-synthetic-id-mismatch-probe"
    path = CAIRN_ROOT / "docs/adr" / f"{slug}.md"
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    path.write_text(
        "---\nid: totally-wrong-id-value\nstatus: accepted\n---\n\nbody\n",
        encoding="utf-8",
    )
    try:
        yield slug, path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


@pytest.mark.skipif(
    _SUPPRESS_SUBPROCESS_PROBES,
    reason="nested subprocess run: C4 driver suppressed to prevent recursion",
)
class TestContractC4RobustnessUnderGrowth:
    """Intent §V4: suite is robust to corpus growth, specific to offender naming."""

    def test_valid_new_adr_keeps_suite_green(self, _synthetic_valid_adr):
        slug, _ = _synthetic_valid_adr
        result = _run_self_in_subprocess()
        assert result.returncode == 0, (
            f"Adding a valid flat-slug synthetic ADR `{slug}.md` broke the "
            f"suite — the guard is size-latched or allowlist-scoped.\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_malformed_filename_fails_with_name_in_output(
        self, _synthetic_malformed_filename_adr
    ):
        name, _ = _synthetic_malformed_filename_adr
        result = _run_self_in_subprocess()
        assert result.returncode != 0, (
            f"Suite stayed green despite malformed filename `{name}` — the "
            f"flat-slug shape assertion is missing.\n"
            f"--- stdout ---\n{result.stdout}\n"
        )
        combined = result.stdout + result.stderr
        assert name in combined, (
            f"Failure output does not name offending file `{name}` "
            f"(intent §V4 requires assertion messages to name the offender).\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )

    def test_mismatched_id_fails_with_name_in_output(
        self, _synthetic_mismatched_id_adr
    ):
        slug, _ = _synthetic_mismatched_id_adr
        expected = f"{slug}.md"
        result = _run_self_in_subprocess()
        assert result.returncode != 0, (
            f"Suite stayed green despite id/stem mismatch in `{expected}` — "
            f"the frontmatter shape assertion is missing or permissive.\n"
            f"--- stdout ---\n{result.stdout}\n"
        )
        combined = result.stdout + result.stderr
        assert expected in combined, (
            f"Failure output does not name offending file `{expected}`.\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )


class TestContractC5RegressionGuardsRetained:
    """Intent §4 / §V5: rename-outcome regression coverage is preserved."""

    def test_rename_table_constant_retained(self):
        assert "RENAME_TABLE" in _self_source(), (
            "RENAME_TABLE constant removed — V1/V2 coverage lost."
        )

    def test_flat_slug_targets_exist_check_retained(self):
        assert "test_all_flat_slug_targets_exist" in _self_source(), (
            "`test_all_flat_slug_targets_exist` removed — V1 coverage lost."
        )

    def test_zero_numeric_prefix_check_retained(self):
        assert "test_zero_numeric_prefix_files" in _self_source(), (
            "`test_zero_numeric_prefix_files` removed — numeric-prefix "
            "glob regression guard lost."
        )

    def test_v2_id_matches_rename_table_retained(self):
        assert "test_id_matches_rename_table" in _self_source(), (
            "`test_id_matches_rename_table` removed — V2 frontmatter-id "
            "regression for rename-table rows lost."
        )

    def test_v4_residue_scanner_retained(self):
        src = _self_source()
        assert "test_no_adr_nnn_token_in_live_tree" in src, "V4 method missing."
        assert "test_no_numeric_adr_path_in_live_tree" in src, "V4 method missing."
        assert "_SCAN_ROOTS" in src, "V4 _SCAN_ROOTS removed."
        assert "_FILE_EXCLUDES" in src, "V4 _FILE_EXCLUDES removed."

    def test_v4_tolerance_excludes_retained(self):
        src = _self_source()
        assert "tests/unit/test_hook_tolerance.py" in src, (
            "V4 _FILE_EXCLUDES no longer exempts test_hook_tolerance.py."
        )
        assert "tests/unit/test_hook_relpath_bypass.py" in src, (
            "V4 _FILE_EXCLUDES no longer exempts test_hook_relpath_bypass.py."
        )

    def test_v5_index_shape_retained(self):
        src = _self_source()
        assert "TestV5IndexShape" in src or (
            "test_every_id_column_is_known_flat_slug" in src
        ), "V5 index-shape assertions removed."

    def test_v6_changelog_header_retained(self):
        assert "ADR identifier migration" in _self_source(), (
            "V6 changelog header constant / assertion removed."
        )


class TestContractC6DocstringWidened:
    """Intent §7: module docstring names the widened (non-size-latched) guard."""

    def _docstring(self) -> str:
        m = re.match(r'\s*"""(.*?)"""', _self_source(), re.DOTALL)
        return (m.group(1) if m else "").lower()

    def test_docstring_acknowledges_non_size_latch(self):
        doc = self._docstring()
        markers = ("size-latch", "size latch", "not size-latched", "cardinality")
        assert any(m in doc for m in markers), (
            f"Module docstring does not acknowledge the non-cardinality "
            f"contract. Expected one of {markers!r} (intent §7)."
        )

    def test_docstring_mentions_shape_guard(self):
        doc = self._docstring()
        assert "shape" in doc, (
            "Module docstring does not mention `shape` — the widened guard "
            "(flat-slug filename + id/stem match) should be called out (§7)."
        )
