"""CI round-trip validator for the cairn knowledge substrate.

Runs in CI (cairn_query validate). Asserts that the substrate's graph state
is internally consistent and matches the source markdown's structural assertions.

Failure breaks the build per ADR cairn-substrate-and-fastmcp D14.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .models import Decision, Invariant, Slice


@dataclass
class ValidationFailure:
    kind: str
    message: str


def validate_supersession_symmetry(
    decisions: list[Decision],
) -> list[ValidationFailure]:
    """If A.superseded_by == B, then B.supersedes must include A."""
    failures: list[ValidationFailure] = []
    by_id = {d.id: d for d in decisions}
    for d in decisions:
        if d.superseded_by is None:
            continue
        successor = by_id.get(d.superseded_by)
        if successor is None:
            failures.append(
                ValidationFailure(
                    kind="supersession",
                    message=(
                        f"{d.id}.superseded_by={d.superseded_by} but "
                        f"{d.superseded_by} not found in decision set"
                    ),
                )
            )
            continue
        if d.id not in successor.supersedes:
            failures.append(
                ValidationFailure(
                    kind="supersession",
                    message=(
                        f"{d.id} declares superseded_by={d.superseded_by}, but "
                        f"{d.superseded_by}.supersedes does not include {d.id}"
                    ),
                )
            )
    return failures


def validate_invariant_references(
    *,
    slices: list[Slice],
    invariants: list[Invariant],
) -> list[ValidationFailure]:
    """Every INV-NNN referenced from a Slice must exist in the Invariant set."""
    failures: list[ValidationFailure] = []
    inv_ids = {i.id for i in invariants}
    for s in slices:
        for inv_ref in s.invariants_touched:
            if inv_ref not in inv_ids:
                failures.append(
                    ValidationFailure(
                        kind="invariant_reference",
                        message=f"Slice {s.id} references unresolvable {inv_ref}",
                    )
                )
    return failures


def validate_binds_paths(
    binds_triples: list[tuple[str, str, str]],
) -> list[ValidationFailure]:
    """For each (path, to_type, to_id) triple, path must exist on disk."""
    failures: list[ValidationFailure] = []
    for path_str, to_type, to_id in binds_triples:
        if not path_str:
            continue
        p = Path(path_str)
        if not p.exists():
            failures.append(
                ValidationFailure(
                    kind="binds_path",
                    message=(
                        f"BINDS edge from non-existent path {path_str} "
                        f"→ {to_type}:{to_id}"
                    ),
                )
            )
    return failures


def run_validator() -> int:
    """Run all validations against a freshly rebuilt index.

    Returns 0 on success, 1 on any validation failure.
    """
    from . import cypher, rebuild_from_sources, search

    db_path = Path(os.environ.get("CAIRN_QUERY_DB", ".claude/cairn_query/index.kz"))
    storage = rebuild_from_sources(db_path=db_path)

    decisions: list[Decision] = search(storage, "decision")  # type: ignore[assignment]
    slices: list[Slice] = search(storage, "slice")  # type: ignore[assignment]
    invariants: list[Invariant] = search(storage, "invariant")  # type: ignore[assignment]

    # Rehydrate supersedes lists from graph SUPERSEDES edges.
    # Node properties don't store list fields; the relationships are in graph edges.
    supersedes_rows = cypher(
        storage,
        "MATCH (a:Decision)-[:SUPERSEDES]->(b:Decision) RETURN a.id, b.id",
    )
    supersedes_map: dict[str, list[str]] = {}
    for row in supersedes_rows:
        from_id = row.get("a.id", "")
        to_id = row.get("b.id", "")
        supersedes_map.setdefault(from_id, []).append(to_id)

    rehydrated_decisions: list[Decision] = []
    for d in decisions:
        if supersedes_map.get(d.id):
            d = d.model_copy(update={"supersedes": supersedes_map[d.id]})
        rehydrated_decisions.append(d)

    binds_triples: list[tuple[str, str, str]] = []
    for et in [
        "Invariant",
        "Decision",
        "Lesson",
        "SpecSection",
        "OpRule",
        "Feature",
        "Slice",
    ]:
        rows = cypher(
            storage,
            f"MATCH (p:Path)-[:BINDS]->(n:{et}) RETURN p.value, n.id",
        )
        for r in rows:
            binds_triples.append((r["p.value"], et, r["n.id"]))

    # Filter out glob patterns — these are not real filesystem paths and
    # cannot be expected to exist as single files (e.g. ".claude/features/*.yaml").
    real_binds_triples = [
        (p, t, i) for p, t, i in binds_triples if "*" not in p and "?" not in p
    ]

    failures: list[ValidationFailure] = []
    failures.extend(validate_supersession_symmetry(rehydrated_decisions))
    failures.extend(validate_invariant_references(slices=slices, invariants=invariants))
    failures.extend(validate_binds_paths(real_binds_triples))

    if failures:
        for f in failures:
            print(f"FAIL [{f.kind}]: {f.message}", file=sys.stderr)
        return 1

    print(
        f"OK — {len(decisions)} decisions, {len(slices)} slices, "
        f"{len(invariants)} invariants, {len(real_binds_triples)} binds checked."
    )
    return 0
