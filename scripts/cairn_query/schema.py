"""kuzudb schema definitions for the cairn knowledge substrate.

Plain DDL strings — kuzu requires DDL be issued as SQL-like statements.
Each NODE TABLE / REL TABLE is keyed by its primary `id` field and matches
the pydantic models in scripts.cairn_query.models.
"""

from __future__ import annotations

from pathlib import Path

import kuzu

NODE_TABLES = [
    {
        "name": "Invariant",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS Invariant("
            "id STRING, statement STRING, target_path STRING, target_line INT64, "
            "grep STRING, anchor_path STRING, anchor_line INT64, "
            "PRIMARY KEY(id))"
        ),
    },
    {
        "name": "Decision",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS Decision("
            "id STRING, name STRING, status STRING, firmness STRING, "
            "topic STRING, date DATE, body_path STRING, "
            "PRIMARY KEY(id))"
        ),
    },
    {
        "name": "Lesson",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS Lesson("
            "id STRING, title STRING, discovered DATE, pattern STRING, "
            "rule STRING, body_path STRING, "
            "PRIMARY KEY(id))"
        ),
    },
    {
        "name": "SpecSection",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS SpecSection("
            "id STRING, title STRING, body_path STRING, "
            "PRIMARY KEY(id))"
        ),
    },
    {
        "name": "OpRule",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS OpRule("
            "id STRING, statement STRING, scope STRING, body_path STRING, body_line INT64, "
            "PRIMARY KEY(id))"
        ),
    },
    {
        "name": "Feature",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS Feature("
            "id STRING, name STRING, intent STRING, shaped_from STRING, "
            "PRIMARY KEY(id))"
        ),
    },
    {
        "name": "Slice",
        "ddl": (
            "CREATE NODE TABLE IF NOT EXISTS Slice("
            "id STRING, name STRING, feature_id STRING, status STRING, "
            "started DATE, completed DATE, close_commit STRING, "
            "PRIMARY KEY(id))"
        ),
    },
]

REL_TABLES = [
    {
        "name": "SUPERSEDES",
        "ddl": "CREATE REL TABLE IF NOT EXISTS SUPERSEDES(FROM Decision TO Decision)",
    },
    {
        "name": "TOUCHES",
        "ddl": (
            "CREATE REL TABLE GROUP IF NOT EXISTS TOUCHES("
            "FROM Decision TO Invariant, FROM Slice TO Invariant)"
        ),
    },
    {
        "name": "REFERENCES",
        "ddl": "CREATE REL TABLE IF NOT EXISTS REFERENCES(FROM Slice TO Decision)",
    },
    {
        "name": "CREATES",
        "ddl": "CREATE REL TABLE IF NOT EXISTS CREATES(FROM Slice TO Decision)",
    },
    {
        "name": "PARENT",
        "ddl": "CREATE REL TABLE IF NOT EXISTS PARENT(FROM Slice TO Feature)",
    },
    {
        "name": "CHILD",
        "ddl": "CREATE REL TABLE IF NOT EXISTS CHILD(FROM Feature TO Slice)",
    },
    {
        "name": "INSTANCE_OF",
        "ddl": "CREATE REL TABLE IF NOT EXISTS INSTANCE_OF(FROM Lesson TO Slice)",
    },
    {
        "name": "BINDS",
        "ddl": (
            "CREATE REL TABLE GROUP IF NOT EXISTS BINDS("
            "FROM Path TO Invariant, FROM Path TO Decision, FROM Path TO Lesson, "
            "FROM Path TO SpecSection, FROM Path TO OpRule, FROM Path TO Feature, FROM Path TO Slice)"
        ),
    },
    {
        "name": "ANCHORED_AT",
        "ddl": (
            "CREATE REL TABLE GROUP IF NOT EXISTS ANCHORED_AT("
            "FROM Invariant TO Path, FROM Decision TO Path, FROM Lesson TO Path, "
            "FROM SpecSection TO Path, FROM OpRule TO Path, FROM Feature TO Path, FROM Slice TO Path)"
        ),
    },
]

# Path is a synthetic node table for the path-binding inverse view.
PATH_NODE_TABLE = {
    "name": "Path",
    "ddl": "CREATE NODE TABLE IF NOT EXISTS Path(value STRING, PRIMARY KEY(value))",
}


def bootstrap_schema(db_path: Path) -> kuzu.Database:
    """Create or open a kuzu database with the substrate schema.

    Idempotent — safe to call repeatedly; uses IF NOT EXISTS clauses.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    # Path node first (every BINDS edge needs Path as origin)
    conn.execute(PATH_NODE_TABLE["ddl"])
    for table in NODE_TABLES:
        conn.execute(table["ddl"])
    for rel in REL_TABLES:
        conn.execute(rel["ddl"])
    return db
