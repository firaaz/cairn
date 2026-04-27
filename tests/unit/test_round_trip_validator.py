"""RED tests — CI round-trip validator failure modes.

The validator runs in CI (`cairn_query validate`). It must:

1. Pass cleanly on the current cairn corpus.
2. Fail when a Decision's `superseded_by` is not mirrored in the successor's
   `supersedes` (asymmetric supersession link).
3. Fail when a Slice references an unresolvable INV-NNN.
4. Fail when a BINDS edge points at a non-existent on-disk path.
"""

from __future__ import annotations

from datetime import date

from cairn_query.models import Decision, PathAnchor, Slice
from cairn_query.validators import (
    run_validator,
    validate_binds_paths,
    validate_invariant_references,
    validate_supersession_symmetry,
)


def test_validator_passes_on_current_corpus(tmp_path, monkeypatch):
    """Cairn's existing markdown corpus must pass the round-trip validator."""
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    rc = run_validator()
    assert rc == 0


def test_supersession_symmetry_catches_one_sided_link():
    """If A says superseded_by:B but B doesn't list A in supersedes, FAIL."""
    a = Decision(
        id="adr-a",
        name="A",
        status="superseded",
        firmness="firm",
        topic="x",
        date=date(2026, 1, 1),
        superseded_by="adr-b",
        body_anchor=PathAnchor(path="x"),
    )
    b = Decision(
        id="adr-b",
        name="B",
        status="accepted",
        firmness="firm",
        topic="x",
        date=date(2026, 1, 1),
        supersedes=[],  # MISSING adr-a
        body_anchor=PathAnchor(path="x"),
    )
    failures = validate_supersession_symmetry([a, b])
    assert len(failures) == 1
    assert "adr-a" in failures[0].message
    assert "adr-b" in failures[0].message


def test_supersession_symmetry_passes_when_mirrored():
    a = Decision(
        id="adr-a",
        name="A",
        status="superseded",
        firmness="firm",
        topic="x",
        date=date(2026, 1, 1),
        superseded_by="adr-b",
        body_anchor=PathAnchor(path="x"),
    )
    b = Decision(
        id="adr-b",
        name="B",
        status="accepted",
        firmness="firm",
        topic="x",
        date=date(2026, 1, 1),
        supersedes=["adr-a"],
        body_anchor=PathAnchor(path="x"),
    )
    assert validate_supersession_symmetry([a, b]) == []


def test_invariant_reference_catches_unresolvable_id():
    """A Slice referencing INV-999 (not in the Invariant set) FAILs."""
    s = Slice(
        id="x/y",
        name="x",
        feature_id="x",
        status="complete",
        started=date(2026, 1, 1),
        invariants_touched=["INV-999"],
        close_commit="abc1234",
    )
    failures = validate_invariant_references(slices=[s], invariants=[])
    assert len(failures) == 1
    assert "INV-999" in failures[0].message


def test_binds_path_validation_catches_nonexistent_path():
    """A BINDS edge from a non-existent path FAILs."""
    failures = validate_binds_paths(
        [("docs/does-not-exist.md", "Invariant", "INV-001")]
    )
    assert len(failures) == 1
    assert "does-not-exist" in failures[0].message


def test_binds_path_validation_skips_existing_path():
    """A BINDS edge from an extant path passes (uses repo's own ARCHITECTURE.md)."""
    failures = validate_binds_paths([("docs/ARCHITECTURE.md", "Invariant", "INV-001")])
    assert failures == []
