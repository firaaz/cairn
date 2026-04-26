"""RED tests — kuzudb schema bootstrap.

Asserts: NODE_TABLES covers all 7 entity types; REL_TABLES covers the 9
design-doc edge predicates; bootstrap_schema is idempotent and produces an
empty queryable database.

Fails at collection until Phase 3 ships scripts/cairn_query/schema.py and
the `kuzu` dep is present.
"""

from __future__ import annotations

import kuzu

from cairn_query.schema import NODE_TABLES, REL_TABLES, bootstrap_schema


def test_node_tables_cover_all_seven_entities():
    table_names = {t["name"] for t in NODE_TABLES}
    assert table_names == {
        "Invariant",
        "Decision",
        "Lesson",
        "SpecSection",
        "OpRule",
        "Feature",
        "Slice",
    }


def test_rel_tables_cover_design_doc_predicates():
    rel_names = {r["name"] for r in REL_TABLES}
    expected = {
        "SUPERSEDES",
        "TOUCHES",
        "REFERENCES",
        "CREATES",
        "PARENT",
        "CHILD",
        "INSTANCE_OF",
        "BINDS",
        "ANCHORED_AT",
    }
    assert expected.issubset(rel_names)


def test_bootstrap_schema_creates_empty_db(tmp_path):
    db_path = tmp_path / "test.kz"
    db = bootstrap_schema(db_path)
    conn = kuzu.Connection(db)
    for entity in [
        "Invariant",
        "Decision",
        "Lesson",
        "SpecSection",
        "OpRule",
        "Feature",
        "Slice",
    ]:
        result = conn.execute(f"MATCH (n:{entity}) RETURN COUNT(n)")
        row = result.get_next()
        assert row[0] == 0


def test_bootstrap_schema_idempotent(tmp_path):
    db_path = tmp_path / "test.kz"
    bootstrap_schema(db_path)
    bootstrap_schema(db_path)
