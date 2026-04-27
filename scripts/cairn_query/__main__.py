"""typer CLI for cairn_query. Operator-facing.

Database location: $CAIRN_QUERY_DB or ".claude/cairn_query/index.kz".

Commands: rebuild, show, path-bindings, graph, supersedes,
          slices, cypher, dump, stats, validate.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import yaml

from . import (
    cypher as cypher_query,
    lookup,
    path_bindings as pb_query,
    rebuild_from_sources,
    search,
)
from .storage import KuzuStorage
from .validators import run_validator

app = typer.Typer(help="Cairn knowledge-substrate query CLI.")


def _db_path() -> Path:
    return Path(os.environ.get("CAIRN_QUERY_DB", ".claude/cairn_query/index.kz"))


def _open_storage() -> KuzuStorage:
    return KuzuStorage(db_path=_db_path())


@app.command()
def rebuild() -> None:
    """Rebuild the index from current source markdown."""
    storage = rebuild_from_sources(db_path=_db_path())  # noqa: F841
    typer.echo(f"Rebuilt at {_db_path()}")


@app.command()
def show(entity_type: str, id: str) -> None:
    """Pretty-print one entity by type+id."""
    storage = _open_storage()
    entity = lookup(storage, entity_type, id)
    typer.echo(yaml.safe_dump(entity.model_dump(mode="json"), default_flow_style=False))


@app.command(name="path-bindings")
def path_bindings(path: str) -> None:
    """List entities binding the given path."""
    storage = _open_storage()
    results = pb_query(storage, path)
    for e in results:
        name = getattr(e, "name", "") or getattr(e, "title", "") or ""
        typer.echo(f"{e.entity_type}:{e.id}  {name}")


@app.command()
def graph(id: str, depth: int = 1) -> None:
    """Show neighbourhood traversal of an entity (ASCII tree)."""
    storage = _open_storage()
    rows = cypher_query(
        storage,
        "MATCH (n {id: $id})-[r]-(m) RETURN type(r), labels(m), m.id LIMIT 50",
        {"id": id},
    )
    typer.echo(id)
    for r in rows:
        rel = r.get("type(r)", "?")
        labels = r.get("labels(m)", ["?"])
        label = labels[0] if labels else "?"
        target = f"{label}:{r.get('m.id', '?')}"
        typer.echo(f"  --[{rel}]--> {target}")


@app.command()
def supersedes(decision_id: str) -> None:
    """Show the supersession chain rooted at decision_id."""
    storage = _open_storage()
    rows = cypher_query(
        storage,
        "MATCH (d:Decision {id: $id})-[:SUPERSEDES*1..]->(d2) RETURN d2.id",
        {"id": decision_id},
    )
    for r in rows:
        typer.echo(r.get("d2.id"))


@app.command()
def slices(
    feature: str | None = None,
    status: str | None = None,
) -> None:
    """List slices, optionally filtered by feature and/or status."""
    storage = _open_storage()
    filters: dict = {}
    if feature is not None:
        filters["feature_id"] = feature
    if status is not None:
        filters["status"] = status
    for s in search(storage, "slice", filters):
        typer.echo(
            f"{s.id}  {s.status}  ({getattr(s, 'completed', None) or 'in-progress'})"
        )


@app.command()
def cypher(query: str) -> None:
    """Run a raw Cypher query against the index. Power-user escape hatch."""
    storage = _open_storage()
    rows = cypher_query(storage, query)
    typer.echo(json.dumps(rows, default=str, indent=2))


@app.command()
def dump(format: str = "yaml") -> None:
    """Dump the entire graph to text. format = yaml | json."""
    storage = _open_storage()
    out: dict = {"nodes": {}}
    for et in [
        "invariant",
        "decision",
        "lesson",
        "spec_section",
        "op_rule",
        "feature",
        "slice",
    ]:
        out["nodes"][et] = [e.model_dump(mode="json") for e in search(storage, et)]
    if format == "json":
        typer.echo(json.dumps(out, default=str, indent=2))
    else:
        typer.echo(yaml.safe_dump(out, default_flow_style=False))


@app.command()
def stats() -> None:
    """Counts of nodes per type."""
    storage = _open_storage()
    for table_name in [
        "Invariant",
        "Decision",
        "Lesson",
        "SpecSection",
        "OpRule",
        "Feature",
        "Slice",
    ]:
        c = storage.count(table_name)
        typer.echo(f"{table_name}: {c}")


@app.command()
def validate() -> None:
    """Run the CI round-trip validator. Exits non-zero on failure."""
    rc = run_validator()
    raise typer.Exit(code=rc)


if __name__ == "__main__":
    app()
