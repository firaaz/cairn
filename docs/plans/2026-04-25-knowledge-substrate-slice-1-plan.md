# Knowledge Substrate — Slice 1 (Knowledge Index) Implementation Plan

> **For agentic workers:** This plan is INPUT to cairn's slice pipeline (slice id `compression/lever-X-knowledge-index`). Phase 1 derives `intent.md` from §Goal/§Architecture/§Envelope below. Phase 2 writes the tests in each Task's "Tests Phase 2 writes" block (one commit). Phase 3 implements per "Implementation Phase 3 ships" block (one commit, with Phase-3 fan-out via `superpowers:dispatching-parallel-agents` for the per-entity extractors). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship `scripts/cairn_query/` — a Python package that extracts typed records from cairn's existing markdown corpus into a kuzudb-backed graph index, exposes them via a Python API + typer CLI, with a CI round-trip validator gating merges. Operator-only consumer at this slice; no agent integration, no MCP server (those land in Slice 2).

**Architecture:** Three-layer system per `docs/plans/2026-04-25-knowledge-substrate-design.md` §4 — canonical markdown sources → mistune AST → pydantic-validated typed entities → kuzudb on disk → cairn_query Python API → typer CLI. Lazy mtime-validated rebuild keyed by git SHA snapshot in an in-process LRU(8). Seven entity types (Invariant, Decision, Lesson, SpecSection, OpRule, Feature, Slice) plus the `BINDS` path-binding inverse view. CI round-trip validator enforces extraction correctness on every commit.

**Tech Stack:** pydantic, kuzudb, mistune, typer (new — added in this slice; ADR `cairn-substrate-and-fastmcp` authorizes them in Slice 2 retroactively, see §Sequencing). pyyaml, pytest, ruff (existing).

**Slice id:** `compression/lever-X-knowledge-index`
**Feature:** `compression`
**Branch:** `feature/compression`
**Worktree:** the existing `.worktrees/feature-compression/` (no new worktree needed; the substrate-Slice-1 envelope and the closed lever-2 envelope don't overlap)

---

## Sequencing context (from design doc §6)

- This is **Slice 1** of the substrate program. **No external dependencies.**
- Slice 2 (`compression/lever-Y-mcp-substrate`) follows; it imports `cairn_query` and ships the FastMCP adapter + ADR `cairn-substrate-and-fastmcp`.
- The sibling slice `compression/slice-artifact-preservation` runs in a parallel worktree, independent of substrate work.

**ADR posture in Slice 1:** the deps (pydantic, kuzudb, mistune, typer) land in `pyproject.toml` during this slice. The ADR `cairn-substrate-and-fastmcp` formally authorizing them is co-landed in Slice 2 (per design doc §8.1). This is a deliberate phasing — Slice 1 ships the technical capability; Slice 2 ships the architectural commitment. Phase 1 of this slice should record this in `intent.md`'s `adrs-referenced` (none) and `adrs-created` (none) — the ADR is created in Slice 2, not here.

---

## Envelope

```yaml
envelope:
  - "scripts/cairn_query/**"
  - "tests/unit/test_cairn_query_*.py"
  - "tests/unit/test_extractor_*.py"
  - "tests/unit/test_round_trip_validator.py"
  - "tests/unit/test_snapshot_lru.py"
  - "tests/unit/test_path_binding.py"
  - "tests/unit/test_cli_query.py"
  - "pyproject.toml"
  - ".gitignore"
  - "docs/operational-reference.md"
  - ".claude/features/compression.yaml"
  - ".claude/current-slice/{intent.md,validation/approach.md,implementation/notes.md,integration/sweep-notes.md}"
  - ".claude/current-slice/handoff-phase-{1,2,3,4}.md"
out-of-scope:
  - "Any change to scripts/slice_orchestrator/**"
  - "Any FastMCP server or .mcp.json (Slice 2)"
  - "Any change to .claude/agents/phase-*.md (Slice 2/3)"
  - "Any change to docs/ARCHITECTURE.md invariant-check blocks"
  - "Any change to existing ADRs"
  - "Any change to docs/lessons.md or docs/spec-v1.md content"
  - "ADR creation (cairn-substrate-and-fastmcp lands in Slice 2)"
  - "Pre-wipe artifact preservation (sibling slice)"
  - "Lockdown of phase-agent Read access on canonical sources (Slice 2/3 ships role_guard rules)"
```

---

## File Structure

```
scripts/cairn_query/
  __init__.py             # public API: lookup, search, path_bindings, cypher
  __main__.py             # typer CLI entry (cairn_query <command>)
  models.py               # pydantic entity models + EntityType enum + PathAnchor
  schema.py               # kuzudb schema constants (CREATE NODE TABLE / REL TABLE strings)
  storage.py              # KuzuStorage class: init, upsert, query, snapshot LRU, mtime detection
  validators.py           # CI round-trip validator entry point
  extractors/
    __init__.py
    base.py               # Extractor protocol (extract(snapshot_id) -> (nodes, edges))
    invariant.py          # parses docs/ARCHITECTURE.md invariant-check blocks
    decision.py           # parses docs/adr/*.md frontmatter + body
    lesson.py             # parses docs/lessons.md L-NNN entries
    spec_section.py       # parses docs/spec-v1.md §N
    op_rule.py            # parses docs/operational-reference.md
    feature.py            # parses .claude/features/*.yaml
    slice.py              # walks `git log --grep='^slice: .* — complete$'`

tests/unit/
  test_cairn_query_models.py        # pydantic round-trip per entity
  test_cairn_query_schema.py        # kuzudb schema bootstrap
  test_cairn_query_storage.py       # storage upsert/query
  test_snapshot_lru.py              # LRU(8) eviction
  test_extractor_base.py            # Extractor protocol enforcement
  test_extractor_invariant.py
  test_extractor_decision.py
  test_extractor_lesson.py
  test_extractor_spec_section.py
  test_extractor_op_rule.py
  test_extractor_feature.py
  test_extractor_slice.py
  test_path_binding.py              # cross-cutting: path → entities query
  test_round_trip_validator.py      # CI validator failure modes
  test_cli_query.py                 # typer CLI smoke tests

pyproject.toml                      # add deps: pydantic, kuzudb, mistune, typer
.gitignore                          # add: .claude/cairn_query/
docs/operational-reference.md       # add cairn_query CLI reference + env-var docs
.claude/features/compression.yaml   # append slice entry
```

**Notes on file decomposition:**
- One file per extractor — keeps each extractor focused on its source format and bounds Phase 3 fan-out cleanly.
- `models.py` holds all pydantic models in one file (~250 LOC est.) — splitting would force cross-file imports for the discriminated union.
- `storage.py` holds the KuzuStorage class + LRU + mtime helpers — they're tightly coupled by snapshot keying; ~300 LOC est.
- `schema.py` is a pure constants file — kuzudb DDL strings only.
- Test files mirror source files 1:1 (cairn convention).

---

## Tasks

### Task 1: Bootstrap dependencies and package skeleton

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Create: `scripts/cairn_query/__init__.py` (empty for now)
- Create: `scripts/cairn_query/extractors/__init__.py` (empty)

**Tests Phase 2 writes:** None (this task is pure bootstrap — Phase 2 verifies presence via subsequent tests).

**Implementation Phase 3 ships:**

Add to `pyproject.toml` `[project]` `dependencies`:
```toml
"pydantic>=2.6",
"kuzu>=0.6",
"mistune>=3.0",
"typer>=0.12",
```

Add to `.gitignore`:
```
# substrate index (derived; rebuildable from sources)
.claude/cairn_query/
```

Create `scripts/cairn_query/__init__.py`:
```python
"""Cairn knowledge substrate — typed query layer over the markdown corpus.

Public API: lookup, search, path_bindings, cypher.
See docs/plans/2026-04-25-knowledge-substrate-design.md.
"""
from __future__ import annotations
```

Create `scripts/cairn_query/extractors/__init__.py`:
```python
"""Per-entity-type extractors. Each implements the Extractor protocol from base.py."""
from __future__ import annotations
```

- [ ] **Step 1: Modify `pyproject.toml`** — add the four deps to `dependencies`.
- [ ] **Step 2: Modify `.gitignore`** — add `.claude/cairn_query/`.
- [ ] **Step 3: Create the two empty package files** with the docstrings above.
- [ ] **Step 4: Run `uv sync`** — expected: lockfile updates with the four new deps. No errors.
- [ ] **Step 5: Run `uv run pytest -q`** — expected: existing 836 passing / 3 skipped (pre-substrate baseline).
- [ ] **Step 6: This task does not commit independently.** Phase 3 commits everything at the end of phase per cairn slice protocol.

---

### Task 2: pydantic entity models + EntityType enum + PathAnchor

**Files:**
- Create: `scripts/cairn_query/models.py`
- Test: `tests/unit/test_cairn_query_models.py`

**Tests Phase 2 writes** (one commit, RED initially):

```python
# tests/unit/test_cairn_query_models.py
from datetime import date
import pytest
from pydantic import ValidationError

from scripts.cairn_query.models import (
    PathAnchor, EntityType, Invariant, Decision, Lesson,
    SpecSection, OpRule, Feature, Slice,
)

def test_path_anchor_constructs():
    p = PathAnchor(path="docs/ARCHITECTURE.md", line=80)
    assert p.path == "docs/ARCHITECTURE.md"
    assert p.line == 80

def test_path_anchor_line_optional():
    p = PathAnchor(path="docs/spec-v1.md")
    assert p.line is None

def test_entity_type_enum_values():
    assert EntityType.INVARIANT.value == "invariant"
    assert EntityType.DECISION.value == "decision"
    assert EntityType.LESSON.value == "lesson"
    assert EntityType.SPEC_SECTION.value == "spec_section"
    assert EntityType.OP_RULE.value == "op_rule"
    assert EntityType.FEATURE.value == "feature"
    assert EntityType.SLICE.value == "slice"

def test_invariant_round_trip():
    inv = Invariant(
        entity_type="invariant",
        id="INV-008",
        statement="close_slice is the sole producer of the `slice: <id> — complete` commit.",
        target=PathAnchor(path="scripts/slice_orchestrator/lifecycle.py"),
        grep=r"def close_slice",
        architecture_anchor=PathAnchor(path="docs/ARCHITECTURE.md", line=80),
    )
    dumped = inv.model_dump(mode="json")
    loaded = Invariant.model_validate(dumped)
    assert loaded == inv

def test_invariant_id_format_validation():
    with pytest.raises(ValidationError):
        Invariant(
            entity_type="invariant",
            id="bad-id-format",  # must match INV-NNN
            statement="x",
            target=PathAnchor(path="x"),
            grep="x",
            architecture_anchor=PathAnchor(path="x"),
        )

def test_decision_round_trip():
    d = Decision(
        entity_type="decision",
        id="parallelism-v1",
        name="Parallelism v1",
        status="accepted",
        firmness="firm",
        topic="execution",
        date=date(2026, 4, 15),
        invariants_touched=["INV-005"],
        supersedes=[],
        superseded_by=None,
        body_anchor=PathAnchor(path="docs/adr/parallelism-v1.md"),
        decision_points=[],
    )
    dumped = d.model_dump(mode="json")
    loaded = Decision.model_validate(dumped)
    assert loaded == d

def test_lesson_round_trip():
    l = Lesson(
        entity_type="lesson",
        id="L-001",
        title="Pipeline-bypass temptation",
        discovered=date(2026, 4, 11),
        pattern="A bug surfaces mid-session…",
        instances=["f531087"],
        rule="Open a slice, run /decision, or write nothing.",
        anti_patterns=["it's just docs", "only three lines"],
        body_anchor=PathAnchor(path="docs/lessons.md"),
    )
    assert Lesson.model_validate(l.model_dump(mode="json")) == l

def test_spec_section_round_trip():
    s = SpecSection(
        entity_type="spec_section",
        id="§13",
        title="Failure modes",
        body_anchor=PathAnchor(path="docs/spec-v1.md"),
    )
    assert SpecSection.model_validate(s.model_dump(mode="json")) == s

def test_op_rule_round_trip():
    o = OpRule(
        entity_type="op_rule",
        id="phase-skill-guide/phase-4",
        statement="Auditor produces pass/fail verdict on declared invariants…",
        scope="docs/operational-reference.md § Phase Skill Guide",
        body_anchor=PathAnchor(path="docs/operational-reference.md", line=85),
    )
    assert OpRule.model_validate(o.model_dump(mode="json")) == o

def test_feature_round_trip():
    f = Feature(
        entity_type="feature",
        id="compression",
        name="Slice compression",
        intent="Ship compression protocol…",
        shaped_from="docs/plans/2026-04-18-slice-compression-protocol-design.md",
        slice_ids=["compression/doc-cleanup-tail", "compression/infrastructure"],
    )
    assert Feature.model_validate(f.model_dump(mode="json")) == f

def test_slice_round_trip():
    s = Slice(
        entity_type="slice",
        id="compression/lever-2-orchestrator-split",
        name="Compression Lever 2 — orchestrator package split",
        feature_id="compression",
        status="complete",
        started=date(2026, 4, 25),
        completed=date(2026, 4, 25),
        invariants_touched=["INV-003", "INV-004", "INV-008", "INV-009"],
        adrs_referenced=[],
        adrs_created=[],
        envelope_paths=["scripts/slice_orchestrator/**"],
        envelope_out_of_scope=["any test-file edit"],
        close_commit="84f1749",
    )
    assert Slice.model_validate(s.model_dump(mode="json")) == s

def test_slice_id_format_validation():
    with pytest.raises(ValidationError):
        Slice(
            entity_type="slice",
            id="not-hierarchical",  # must be <feature>/<slug>
            name="x",
            feature_id="x",
            status="complete",
            started=date(2026, 4, 25),
            close_commit="abc1234",
        )
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/models.py`:

```python
"""Pydantic entity models for the cairn knowledge substrate.

One file holds all seven entity types because they share a discriminated-union
return type via `EntityType`. Splitting per entity would force cross-file
imports of the union, hurting readability.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator

INV_ID_RE = r"^INV-\d{3}$"
SLICE_ID_RE = r"^[a-z][a-z0-9-]*\/[a-z0-9][a-z0-9-]*$"
LESSON_ID_RE = r"^L-\d{3}$"


class EntityType(str, Enum):
    INVARIANT = "invariant"
    DECISION = "decision"
    LESSON = "lesson"
    SPEC_SECTION = "spec_section"
    OP_RULE = "op_rule"
    FEATURE = "feature"
    SLICE = "slice"


class PathAnchor(BaseModel):
    path: str
    line: int | None = None


class Invariant(BaseModel):
    entity_type: Literal["invariant"] = "invariant"
    id: str = Field(pattern=INV_ID_RE)
    statement: str
    target: PathAnchor
    grep: str
    architecture_anchor: PathAnchor


class DecisionPoint(BaseModel):
    id: str          # full mechanical id <adr-id>/<slug>
    slug: str
    body: str


class Decision(BaseModel):
    entity_type: Literal["decision"] = "decision"
    id: str
    name: str
    status: Literal["accepted", "superseded", "deferred", "draft"]
    firmness: Literal["firm", "provisional"]
    topic: str
    date: date
    invariants_touched: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    decision_points: list[DecisionPoint] = Field(default_factory=list)
    body_anchor: PathAnchor


class Lesson(BaseModel):
    entity_type: Literal["lesson"] = "lesson"
    id: str = Field(pattern=LESSON_ID_RE)
    title: str
    discovered: date
    pattern: str
    instances: list[str] = Field(default_factory=list)  # commit hashes / slice ids
    rule: str
    anti_patterns: list[str] = Field(default_factory=list)
    body_anchor: PathAnchor


class SpecSection(BaseModel):
    entity_type: Literal["spec_section"] = "spec_section"
    id: str  # e.g. "§13"
    title: str
    body_anchor: PathAnchor


class OpRule(BaseModel):
    entity_type: Literal["op_rule"] = "op_rule"
    id: str
    statement: str
    scope: str
    body_anchor: PathAnchor


class Feature(BaseModel):
    entity_type: Literal["feature"] = "feature"
    id: str
    name: str
    intent: str
    shaped_from: str | None = None
    slice_ids: list[str] = Field(default_factory=list)


class Slice(BaseModel):
    entity_type: Literal["slice"] = "slice"
    id: str = Field(pattern=SLICE_ID_RE)
    name: str
    feature_id: str
    status: Literal["complete", "failed", "in-progress"]
    started: date
    completed: date | None = None
    invariants_touched: list[str] = Field(default_factory=list)
    adrs_referenced: list[str] = Field(default_factory=list)
    adrs_created: list[str] = Field(default_factory=list)
    envelope_paths: list[str] = Field(default_factory=list)
    envelope_out_of_scope: list[str] = Field(default_factory=list)
    close_commit: str


Entity = Annotated[
    Union[Invariant, Decision, Lesson, SpecSection, OpRule, Feature, Slice],
    Field(discriminator="entity_type"),
]
```

- [ ] **Step 1: Phase 2 writes the test file** above as one commit (RED — module doesn't exist).
- [ ] **Step 2: Verify RED** — `uv run pytest tests/unit/test_cairn_query_models.py -v` should error: `ModuleNotFoundError: scripts.cairn_query.models`.
- [ ] **Step 3: Phase 3 creates models.py** as above.
- [ ] **Step 4: Verify GREEN** — `uv run pytest tests/unit/test_cairn_query_models.py -v` should pass all 12 tests.
- [ ] **Step 5: Run full suite** — `uv run pytest -q` should be 836 + 12 passing / 3 skipped, 0 failed.

---

### Task 3: kuzudb schema

**Files:**
- Create: `scripts/cairn_query/schema.py`
- Test: `tests/unit/test_cairn_query_schema.py`

**Tests Phase 2 writes:**

```python
# tests/unit/test_cairn_query_schema.py
from pathlib import Path

import kuzu

from scripts.cairn_query.schema import bootstrap_schema, NODE_TABLES, REL_TABLES


def test_node_tables_cover_all_seven_entities():
    table_names = {t["name"] for t in NODE_TABLES}
    assert table_names == {
        "Invariant", "Decision", "Lesson", "SpecSection",
        "OpRule", "Feature", "Slice",
    }


def test_rel_tables_cover_design_doc_predicates():
    rel_names = {r["name"] for r in REL_TABLES}
    # From design doc §3 edge predicates
    expected = {
        "SUPERSEDES", "TOUCHES", "REFERENCES", "CREATES",
        "PARENT", "CHILD", "INSTANCE_OF", "BINDS", "ANCHORED_AT",
    }
    assert expected.issubset(rel_names)


def test_bootstrap_schema_creates_empty_db(tmp_path):
    db_path = tmp_path / "test.kz"
    db = bootstrap_schema(db_path)
    conn = kuzu.Connection(db)
    # Verify each node table exists by querying with COUNT
    for entity in ["Invariant", "Decision", "Lesson", "SpecSection",
                   "OpRule", "Feature", "Slice"]:
        result = conn.execute(f"MATCH (n:{entity}) RETURN COUNT(n)")
        row = result.get_next()
        assert row[0] == 0


def test_bootstrap_schema_idempotent(tmp_path):
    db_path = tmp_path / "test.kz"
    bootstrap_schema(db_path)
    # Second call must not raise even though tables exist
    bootstrap_schema(db_path)
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/schema.py`:

```python
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
    {"name": "SUPERSEDES", "ddl": "CREATE REL TABLE IF NOT EXISTS SUPERSEDES(FROM Decision TO Decision)"},
    {"name": "TOUCHES_INV", "ddl": "CREATE REL TABLE IF NOT EXISTS TOUCHES_INV(FROM Decision TO Invariant)"},
    {"name": "TOUCHES_INV_FROM_SLICE", "ddl": "CREATE REL TABLE IF NOT EXISTS TOUCHES_INV_FROM_SLICE(FROM Slice TO Invariant)"},
    {"name": "TOUCHES", "ddl": "CREATE REL TABLE GROUP IF NOT EXISTS TOUCHES(FROM Decision TO Invariant, FROM Slice TO Invariant)"},
    {"name": "REFERENCES", "ddl": "CREATE REL TABLE IF NOT EXISTS REFERENCES(FROM Slice TO Decision)"},
    {"name": "CREATES", "ddl": "CREATE REL TABLE IF NOT EXISTS CREATES(FROM Slice TO Decision)"},
    {"name": "PARENT", "ddl": "CREATE REL TABLE IF NOT EXISTS PARENT(FROM Slice TO Feature)"},
    {"name": "CHILD", "ddl": "CREATE REL TABLE IF NOT EXISTS CHILD(FROM Feature TO Slice)"},
    {"name": "INSTANCE_OF", "ddl": "CREATE REL TABLE IF NOT EXISTS INSTANCE_OF(FROM Lesson TO Slice)"},
    # BINDS is the path-binding inverse view; emitted by every extractor whose entity has a PathAnchor.
    # Encoded as multi-source REL TABLE GROUP so any node type can be the target.
    {"name": "BINDS", "ddl": (
        "CREATE REL TABLE GROUP IF NOT EXISTS BINDS("
        "FROM Path TO Invariant, FROM Path TO Decision, FROM Path TO Lesson, "
        "FROM Path TO SpecSection, FROM Path TO OpRule, FROM Path TO Feature, FROM Path TO Slice)"
    )},
    {"name": "ANCHORED_AT", "ddl": (
        "CREATE REL TABLE GROUP IF NOT EXISTS ANCHORED_AT("
        "FROM Invariant TO Path, FROM Decision TO Path, FROM Lesson TO Path, "
        "FROM SpecSection TO Path, FROM OpRule TO Path, FROM Feature TO Path, FROM Slice TO Path)"
    )},
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
```

- [ ] **Step 1: Phase 2 writes the test file**.
- [ ] **Step 2: Verify RED** — `uv run pytest tests/unit/test_cairn_query_schema.py -v`.
- [ ] **Step 3: Phase 3 creates schema.py**.
- [ ] **Step 4: Verify GREEN**.
- [ ] **Step 5: Run full suite**.

**Note on kuzu DDL syntax**: verify the `CREATE REL TABLE GROUP` syntax against kuzu's actual API at implementation time. The DDL above is targeted at kuzu ≥0.6; if the syntax has shifted, Phase 3 amends as the authoritative kuzu docs require. The test asserts behavior (table exists, count=0), not DDL string shape.

---

### Task 4: KuzuStorage class — init, upsert, query, mtime detection

**Files:**
- Create: `scripts/cairn_query/storage.py`
- Test: `tests/unit/test_cairn_query_storage.py`

**Tests Phase 2 writes:**

```python
# tests/unit/test_cairn_query_storage.py
from datetime import date
from pathlib import Path

import pytest

from scripts.cairn_query.models import (
    Invariant, Decision, Lesson, PathAnchor,
)
from scripts.cairn_query.storage import KuzuStorage


@pytest.fixture
def storage(tmp_path):
    return KuzuStorage(db_path=tmp_path / "test.kz")


def test_storage_initializes_empty(storage):
    assert storage.count("Invariant") == 0
    assert storage.count("Decision") == 0


def test_upsert_invariant_round_trip(storage):
    inv = Invariant(
        id="INV-008",
        statement="close_slice contract",
        target=PathAnchor(path="scripts/slice_orchestrator/lifecycle.py"),
        grep=r"def close_slice",
        architecture_anchor=PathAnchor(path="docs/ARCHITECTURE.md", line=80),
    )
    storage.upsert_node(inv)
    assert storage.count("Invariant") == 1
    fetched = storage.lookup("invariant", "INV-008")
    assert fetched.id == "INV-008"
    assert fetched.statement == "close_slice contract"


def test_upsert_idempotent(storage):
    inv = Invariant(
        id="INV-008", statement="x",
        target=PathAnchor(path="x"), grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    storage.upsert_node(inv)
    storage.upsert_node(inv)  # second call must not duplicate
    assert storage.count("Invariant") == 1


def test_upsert_updates_existing(storage):
    inv1 = Invariant(
        id="INV-008", statement="original",
        target=PathAnchor(path="x"), grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    inv2 = inv1.model_copy(update={"statement": "updated"})
    storage.upsert_node(inv1)
    storage.upsert_node(inv2)
    fetched = storage.lookup("invariant", "INV-008")
    assert fetched.statement == "updated"


def test_lookup_missing_raises(storage):
    with pytest.raises(KeyError):
        storage.lookup("invariant", "INV-999")


def test_search_returns_filtered_list(storage):
    for i, sid in enumerate(["INV-001", "INV-002", "INV-003"]):
        storage.upsert_node(Invariant(
            id=sid, statement=f"s{i}",
            target=PathAnchor(path="x"), grep="x",
            architecture_anchor=PathAnchor(path="x"),
        ))
    results = storage.search("invariant")
    assert len(results) == 3
    assert {r.id for r in results} == {"INV-001", "INV-002", "INV-003"}


def test_path_bindings_returns_anchored_entities(storage):
    inv = Invariant(
        id="INV-008", statement="x",
        target=PathAnchor(path="scripts/slice_orchestrator/lifecycle.py"),
        grep="def close_slice",
        architecture_anchor=PathAnchor(path="docs/ARCHITECTURE.md", line=80),
    )
    storage.upsert_node(inv)
    storage.upsert_edge("BINDS", from_path="docs/ARCHITECTURE.md", to_node_type="Invariant", to_id="INV-008")
    results = storage.path_bindings("docs/ARCHITECTURE.md")
    assert len(results) == 1
    assert results[0].id == "INV-008"


def test_cypher_escape_hatch(storage):
    """cypher() returns raw dicts; advanced queries unburdened by typed return."""
    inv = Invariant(
        id="INV-008", statement="x",
        target=PathAnchor(path="x"), grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    storage.upsert_node(inv)
    rows = storage.cypher("MATCH (i:Invariant) RETURN i.id AS id")
    assert any(r["id"] == "INV-008" for r in rows)
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/storage.py`:

```python
"""kuzudb wrapper, snapshot LRU cache, and source-mtime change detection.

Exposes:
- KuzuStorage: initialize / upsert / lookup / search / path_bindings / cypher
- snapshot_lru_get_or_build: LRU(8) keyed by git SHA
- sources_changed_since: mtime fingerprint comparison
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any

import kuzu

from .models import (
    Entity, EntityType, Invariant, Decision, Lesson,
    SpecSection, OpRule, Feature, Slice, PathAnchor,
)
from .schema import bootstrap_schema, NODE_TABLES

# entity_type label → kuzu node-table name + pydantic model class
_ENTITY_TYPE_TO_TABLE: dict[str, tuple[str, type[Entity]]] = {
    "invariant": ("Invariant", Invariant),
    "decision": ("Decision", Decision),
    "lesson": ("Lesson", Lesson),
    "spec_section": ("SpecSection", SpecSection),
    "op_rule": ("OpRule", OpRule),
    "feature": ("Feature", Feature),
    "slice": ("Slice", Slice),
}


class KuzuStorage:
    """Thin wrapper around kuzu.Database providing typed upsert/lookup/search."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db = bootstrap_schema(db_path)
        self.conn = kuzu.Connection(self.db)

    def upsert_node(self, entity: Entity) -> None:
        table_name, _ = _ENTITY_TYPE_TO_TABLE[entity.entity_type]
        # Convert pydantic model to flat field dict for kuzu MERGE
        params = self._entity_to_params(entity)
        # MERGE upserts (kuzu 0.6+ supports MERGE on primary key)
        self.conn.execute(
            f"MERGE (n:{table_name} {{id: $id}}) SET n += $props",
            {"id": entity.id, "props": params},
        )

    def upsert_edge(
        self, predicate: str, *,
        from_path: str | None = None,
        from_node_type: str | None = None, from_id: str | None = None,
        to_node_type: str, to_id: str,
    ) -> None:
        """Insert one typed edge. Path-anchored edges (BINDS) take from_path; node-to-node edges take from_node_type+from_id."""
        if from_path is not None:
            # Ensure Path node exists, then create BINDS edge
            self.conn.execute("MERGE (p:Path {value: $v})", {"v": from_path})
            self.conn.execute(
                f"MATCH (p:Path {{value: $from_path}}), (n:{to_node_type} {{id: $to_id}}) "
                f"MERGE (p)-[:{predicate}]->(n)",
                {"from_path": from_path, "to_id": to_id},
            )
        else:
            assert from_node_type is not None and from_id is not None
            self.conn.execute(
                f"MATCH (a:{from_node_type} {{id: $from_id}}), (b:{to_node_type} {{id: $to_id}}) "
                f"MERGE (a)-[:{predicate}]->(b)",
                {"from_id": from_id, "to_id": to_id},
            )

    def lookup(self, entity_type: str, id: str) -> Entity:
        table_name, model_cls = _ENTITY_TYPE_TO_TABLE[entity_type]
        result = self.conn.execute(
            f"MATCH (n:{table_name} {{id: $id}}) RETURN n",
            {"id": id},
        )
        if not result.has_next():
            raise KeyError(f"{entity_type}:{id} not found")
        row = result.get_next()
        return self._row_to_entity(entity_type, row[0])

    def search(self, entity_type: str, filters: dict | None = None) -> list[Entity]:
        table_name, _ = _ENTITY_TYPE_TO_TABLE[entity_type]
        where = ""
        params: dict = {}
        if filters:
            clauses = []
            for k, v in filters.items():
                clauses.append(f"n.{k} = ${k}")
                params[k] = v
            where = "WHERE " + " AND ".join(clauses)
        result = self.conn.execute(
            f"MATCH (n:{table_name}) {where} RETURN n",
            params,
        )
        out: list[Entity] = []
        while result.has_next():
            row = result.get_next()
            out.append(self._row_to_entity(entity_type, row[0]))
        return out

    def path_bindings(self, path: str) -> list[Entity]:
        # Iterate all 7 entity types since BINDS is heterogeneous
        results: list[Entity] = []
        for entity_type, (table_name, _) in _ENTITY_TYPE_TO_TABLE.items():
            res = self.conn.execute(
                f"MATCH (p:Path {{value: $path}})-[:BINDS]->(n:{table_name}) RETURN n",
                {"path": path},
            )
            while res.has_next():
                row = res.get_next()
                results.append(self._row_to_entity(entity_type, row[0]))
        return results

    def cypher(self, query: str, params: dict | None = None) -> list[dict]:
        result = self.conn.execute(query, params or {})
        column_names = result.get_column_names()
        rows: list[dict] = []
        while result.has_next():
            row_vals = result.get_next()
            rows.append(dict(zip(column_names, row_vals)))
        return rows

    def count(self, table_name: str) -> int:
        result = self.conn.execute(f"MATCH (n:{table_name}) RETURN COUNT(n)")
        row = result.get_next()
        return row[0]

    def _entity_to_params(self, entity: Entity) -> dict:
        """Flatten pydantic model to kuzu-compatible param dict.

        Nested PathAnchor flattens to <prefix>_path / <prefix>_line columns.
        Lists are stored as JSON strings (kuzu lacks native list-on-property);
        edge tables hold the list relationships.
        """
        d = entity.model_dump(mode="python")
        flat: dict[str, Any] = {}
        for k, v in d.items():
            if k == "entity_type":
                continue
            if isinstance(v, dict) and "path" in v:
                flat[f"{k.replace('_anchor','').replace('target','target_path').replace('body','body')}"] = None  # placeholder; refined below
                # Specific anchor flattening per entity:
                if k == "target":
                    flat["target_path"] = v["path"]
                    flat["target_line"] = v.get("line")
                elif k == "architecture_anchor":
                    flat["anchor_path"] = v["path"]
                    flat["anchor_line"] = v.get("line")
                elif k == "body_anchor":
                    flat["body_path"] = v["path"]
                    flat["body_line"] = v.get("line")
            elif isinstance(v, list):
                continue  # lists go to edge tables, not node properties
            elif isinstance(v, date):
                flat[k] = v
            else:
                flat[k] = v
        return flat

    def _row_to_entity(self, entity_type: str, node_dict: dict) -> Entity:
        """Inflate kuzu node row back into pydantic model."""
        _, model_cls = _ENTITY_TYPE_TO_TABLE[entity_type]
        # Reconstruct PathAnchors from flattened columns
        kwargs: dict[str, Any] = dict(node_dict)
        kwargs["entity_type"] = entity_type
        if "target_path" in kwargs:
            kwargs["target"] = PathAnchor(path=kwargs.pop("target_path"), line=kwargs.pop("target_line", None))
        if "anchor_path" in kwargs:
            kwargs["architecture_anchor"] = PathAnchor(path=kwargs.pop("anchor_path"), line=kwargs.pop("anchor_line", None))
        if "body_path" in kwargs:
            kwargs["body_anchor"] = PathAnchor(path=kwargs.pop("body_path"), line=kwargs.pop("body_line", None))
        # Lists come from edge queries — populate empty for direct lookups
        for f in ["invariants_touched", "supersedes", "instances", "anti_patterns",
                  "adrs_referenced", "adrs_created", "envelope_paths", "envelope_out_of_scope",
                  "slice_ids", "decision_points"]:
            kwargs.setdefault(f, [])
        return model_cls.model_validate(kwargs)
```

- [ ] **Step 1: Phase 2 writes the storage test file**.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Phase 3 creates storage.py** as above.
- [ ] **Step 4: Verify GREEN**.
- [ ] **Step 5: Run full suite**.

**Implementation note**: list-valued fields (`invariants_touched`, `adrs_referenced`, etc.) are NOT stored on node properties — they're edges in the graph. The extractor (Task 5+) emits one node + N edges per entity. The `_row_to_entity` defaults list fields to `[]` for direct node lookups; reconstructing the populated list requires a graph query (handled in the public API, Task 12).

---

### Task 5: Snapshot LRU + mtime-rebuild

**Files:**
- Modify: `scripts/cairn_query/storage.py` (extend with `SnapshotLRU` class + `sources_changed_since`)
- Test: `tests/unit/test_snapshot_lru.py`

**Tests Phase 2 writes:**

```python
# tests/unit/test_snapshot_lru.py
import os
import time
from pathlib import Path

import pytest

from scripts.cairn_query.storage import SnapshotLRU, sources_changed_since


def test_lru_caches_eight_snapshots():
    cache = SnapshotLRU(maxsize=8)
    for i in range(8):
        cache.put(f"sha-{i}", {"data": i})
    for i in range(8):
        assert cache.get(f"sha-{i}") == {"data": i}


def test_lru_evicts_oldest_when_full():
    cache = SnapshotLRU(maxsize=2)
    cache.put("sha-1", "a")
    cache.put("sha-2", "b")
    cache.put("sha-3", "c")  # evicts sha-1
    assert cache.get("sha-1") is None
    assert cache.get("sha-2") == "b"
    assert cache.get("sha-3") == "c"


def test_lru_reorders_on_get():
    cache = SnapshotLRU(maxsize=2)
    cache.put("sha-1", "a")
    cache.put("sha-2", "b")
    cache.get("sha-1")  # marks sha-1 as recent
    cache.put("sha-3", "c")  # should evict sha-2 instead
    assert cache.get("sha-1") == "a"
    assert cache.get("sha-2") is None


def test_sources_changed_since_detects_modification(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("v1")
    manifest = {str(f): f.stat().st_mtime}
    assert not sources_changed_since(manifest, [f])
    time.sleep(0.01)
    f.write_text("v2")
    os.utime(f, (f.stat().st_atime, f.stat().st_mtime + 1))
    assert sources_changed_since(manifest, [f])


def test_sources_changed_since_handles_missing_file(tmp_path):
    """Deleted source counts as changed."""
    f = tmp_path / "doc.md"
    f.write_text("v1")
    manifest = {str(f): f.stat().st_mtime}
    f.unlink()
    assert sources_changed_since(manifest, [f])
```

**Implementation Phase 3 ships (append to `scripts/cairn_query/storage.py`):**

```python
class SnapshotLRU:
    """In-process LRU keyed by git SHA → arbitrary value (typically a KuzuStorage).

    Capacity 8 covers 4 phases × 2 in-flight slices (per design doc §4 / D12).
    """

    def __init__(self, maxsize: int = 8):
        self.maxsize = maxsize
        self._data: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self.maxsize:
            self._data.popitem(last=False)


def sources_changed_since(manifest: dict[str, float], sources: list[Path]) -> bool:
    """Return True if any source's mtime differs from the manifest, or if any source is missing."""
    for src in sources:
        if not src.exists():
            return True
        recorded = manifest.get(str(src))
        if recorded is None or src.stat().st_mtime != recorded:
            return True
    return False
```

- [ ] **Step 1: Phase 2 writes test file**.
- [ ] **Step 2: Verify RED** — symbol `SnapshotLRU` doesn't exist.
- [ ] **Step 3: Phase 3 appends to storage.py**.
- [ ] **Step 4: Verify GREEN**.
- [ ] **Step 5: Run full suite**.

---

### Task 6: Extractor base protocol

**Files:**
- Create: `scripts/cairn_query/extractors/base.py`
- Test: `tests/unit/test_extractor_base.py`

**Tests Phase 2 writes:**

```python
# tests/unit/test_extractor_base.py
from pathlib import Path

import pytest

from scripts.cairn_query.extractors.base import Extractor, ExtractedNode, ExtractedEdge


def test_extractor_protocol_requires_extract_method():
    """A class missing extract() should fail isinstance(Extractor) check."""
    class NotAnExtractor:
        pass
    assert not isinstance(NotAnExtractor(), Extractor)


def test_extractor_protocol_satisfied_by_extract_method():
    class GoodExtractor:
        def extract(self, snapshot_id: str | None = None):
            return ([], [])
    assert isinstance(GoodExtractor(), Extractor)


def test_extracted_node_carries_pydantic_entity():
    """ExtractedNode wraps a pydantic Entity for upsert."""
    from scripts.cairn_query.models import Invariant, PathAnchor
    inv = Invariant(
        id="INV-001", statement="x",
        target=PathAnchor(path="x"), grep="x",
        architecture_anchor=PathAnchor(path="x"),
    )
    node = ExtractedNode(entity=inv)
    assert node.entity.id == "INV-001"


def test_extracted_edge_holds_typed_predicate():
    e = ExtractedEdge(
        predicate="BINDS",
        from_path="docs/ARCHITECTURE.md",
        to_node_type="Invariant",
        to_id="INV-008",
    )
    assert e.predicate == "BINDS"
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/extractors/base.py`:

```python
"""Extractor protocol — every per-entity-type extractor implements this.

Returns (nodes, edges) tuple. Nodes are pydantic-validated entities; edges are
typed predicates emitted by the extractor at extraction time. The extraction
runner upserts both into the KuzuStorage.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from scripts.cairn_query.models import Entity


@dataclass
class ExtractedNode:
    entity: Entity


@dataclass
class ExtractedEdge:
    predicate: str
    to_node_type: str
    to_id: str
    # Either from_path (BINDS-style) OR (from_node_type + from_id) (node-to-node)
    from_path: str | None = None
    from_node_type: str | None = None
    from_id: str | None = None


@runtime_checkable
class Extractor(Protocol):
    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]: ...
```

- [ ] **Step 1: Phase 2 writes test file**.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Phase 3 creates base.py**.
- [ ] **Step 4: Verify GREEN**.
- [ ] **Step 5: Run full suite**.

---

### Tasks 7–13: Per-entity extractors (parallelizable Phase-3 fan-out)

Each extractor parses its source and returns `(nodes, edges)`. The implementation pattern is consistent across all seven; the design doc §4 describes the pipeline. Phase 3 may dispatch one subagent per extractor for parallel implementation per `superpowers:dispatching-parallel-agents`.

For brevity I'll spell out **Task 7 (Invariant extractor)** in full, then list the structurally-identical pattern for the others with their source-file specifics.

#### Task 7: Invariant extractor

**Files:**
- Create: `scripts/cairn_query/extractors/invariant.py`
- Test: `tests/unit/test_extractor_invariant.py`
- Source it parses: `docs/ARCHITECTURE.md` (existing — read-only)

**What it extracts:** every fenced code block matching ` ```invariant-check INV-NNN ` produces one Invariant node + one BINDS edge from the architecture file path to the invariant.

**Tests Phase 2 writes:**

```python
# tests/unit/test_extractor_invariant.py
from pathlib import Path

import pytest

from scripts.cairn_query.extractors.invariant import InvariantExtractor


@pytest.fixture
def extractor():
    return InvariantExtractor(architecture_path=Path("docs/ARCHITECTURE.md"))


def test_extracts_known_invariant_inv_008(extractor):
    """INV-008 exists in cairn's current ARCHITECTURE.md per recently closed slice."""
    nodes, edges = extractor.extract()
    inv_008 = next((n.entity for n in nodes if n.entity.id == "INV-008"), None)
    assert inv_008 is not None
    assert "close_slice" in inv_008.grep or "close_slice" in inv_008.statement
    assert inv_008.target.path == "scripts/slice_orchestrator/lifecycle.py"


def test_extracts_all_nine_current_invariants(extractor):
    """As of slice compression/lever-2-orchestrator-split close, 9 invariants exist."""
    nodes, edges = extractor.extract()
    ids = {n.entity.id for n in nodes}
    expected = {f"INV-00{i}" for i in range(1, 10)}
    assert expected.issubset(ids)


def test_extractor_emits_binds_edge_per_invariant(extractor):
    nodes, edges = extractor.extract()
    binds_edges = [e for e in edges if e.predicate == "BINDS"]
    # At minimum, one BINDS per Invariant from docs/ARCHITECTURE.md
    paths = {e.from_path for e in binds_edges if e.to_node_type == "Invariant"}
    assert "docs/ARCHITECTURE.md" in paths


def test_extractor_handles_missing_architecture_file(tmp_path):
    extractor = InvariantExtractor(architecture_path=tmp_path / "nope.md")
    nodes, edges = extractor.extract()
    assert nodes == []
    assert edges == []
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/extractors/invariant.py`:

```python
"""Invariant extractor — parses docs/ARCHITECTURE.md `invariant-check INV-NNN` blocks."""
from __future__ import annotations

import re
from pathlib import Path

import mistune

from scripts.cairn_query.extractors.base import ExtractedEdge, ExtractedNode
from scripts.cairn_query.models import Invariant, PathAnchor

INVARIANT_BLOCK_RE = re.compile(r"^invariant-check\s+(INV-\d{3})\s*$", re.MULTILINE)


class InvariantExtractor:
    def __init__(self, architecture_path: Path):
        self.path = architecture_path

    def extract(
        self, snapshot_id: str | None = None
    ) -> tuple[list[ExtractedNode], list[ExtractedEdge]]:
        if not self.path.exists():
            return ([], [])
        text = self.path.read_text()
        ast = mistune.create_markdown(renderer="ast")(text)
        nodes: list[ExtractedNode] = []
        edges: list[ExtractedEdge] = []
        line_offset = 1
        for block in ast:
            if block.get("type") == "block_code":
                info = block.get("info") or ""
                m = INVARIANT_BLOCK_RE.match(info)
                if not m:
                    continue
                inv_id = m.group(1)
                body = block.get("raw", "")
                # Body has key:value lines per cairn's invariant-check schema
                fields = self._parse_body(body)
                inv = Invariant(
                    id=inv_id,
                    statement=fields.get("statement", ""),
                    target=PathAnchor(path=fields.get("target", "")),
                    grep=fields.get("grep", ""),
                    architecture_anchor=PathAnchor(path=str(self.path), line=None),
                )
                nodes.append(ExtractedNode(entity=inv))
                edges.append(ExtractedEdge(
                    predicate="BINDS",
                    from_path=str(self.path),
                    to_node_type="Invariant",
                    to_id=inv_id,
                ))
                # Also bind the target path
                if inv.target.path:
                    edges.append(ExtractedEdge(
                        predicate="BINDS",
                        from_path=inv.target.path,
                        to_node_type="Invariant",
                        to_id=inv_id,
                    ))
        return (nodes, edges)

    @staticmethod
    def _parse_body(body: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for line in body.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
        return out
```

- [ ] **Step 1: Phase 2 writes test file**.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Phase 3 creates invariant.py**.
- [ ] **Step 4: Verify GREEN** — all 9 current INV-NNN entries surface.
- [ ] **Step 5: Run full suite**.

#### Task 8: Decision extractor

**Files:**
- Create: `scripts/cairn_query/extractors/decision.py`
- Test: `tests/unit/test_extractor_decision.py`
- Source: `docs/adr/*.md`

**What it extracts:** for each ADR file, parse YAML frontmatter (id, name, status, firmness, supersedes, supersedes-sections, superseded-by, topic, invariants-touched, date), then parse the body for D1/D2/… decision-point sections. Emit one Decision node + N DecisionPoint nested + edges (`SUPERSEDES → Decision`, `TOUCHES → Invariant`, `BINDS ← path`).

**Tests Phase 2 writes** (same shape — assert specific known ADR like `parallelism-v1`, count of current ADRs, edges emitted; ~6 tests).

**Implementation Phase 3 ships:** ~120 LOC. Pattern matches Task 7. Iterate `Path("docs/adr").glob("*.md")`, skip `index.md`. mistune for body; pyyaml for frontmatter (extract `---` block manually then `yaml.safe_load`).

- [ ] Steps 1–5 as Task 7 pattern.

#### Task 9: Lesson extractor

**Files:**
- Create: `scripts/cairn_query/extractors/lesson.py`
- Test: `tests/unit/test_extractor_lesson.py`
- Source: `docs/lessons.md`

**What it extracts:** each `## L-NNN: Title` heading delimits a Lesson. Body sections (`**Pattern:**`, `**Concrete instance:**`, `**Rule:**`, `**Anti-pattern signals:**`) become structured fields. Emit one Lesson node + edges (`INSTANCE_OF → Slice/Commit` if instance reference is parseable; `BINDS ← path`).

**Tests Phase 2 writes**: assert L-001 and L-002 exist, body fields populated, anti-patterns list non-empty for L-001.

- [ ] Steps 1–5 as Task 7 pattern.

#### Task 10: SpecSection extractor

**Files:**
- Create: `scripts/cairn_query/extractors/spec_section.py`
- Test: `tests/unit/test_extractor_spec_section.py`
- Source: `docs/spec-v1.md`

**What it extracts:** each `## §N` or `### §N.M` heading becomes a SpecSection node. id = `§N` or `§N.M`. Title = heading text. body_anchor points at the heading line. Emit `BINDS ← path`.

- [ ] Steps 1–5 as Task 7 pattern.

#### Task 11: OpRule extractor

**Files:**
- Create: `scripts/cairn_query/extractors/op_rule.py`
- Test: `tests/unit/test_extractor_op_rule.py`
- Source: `docs/operational-reference.md`

**What it extracts:** harder than the others — operational-reference.md has table-shaped rules (Phase Skill Guide table) and prose-shaped rules. v1 scope: extract Phase Skill Guide rows as OpRule entities (id = `phase-skill-guide/phase-N`, statement = anti-behavior column). Other table-shaped sections can be added in v2 or this slice's Phase 3 if time permits — but v1 *minimum* is the Phase Skill Guide.

**Tests Phase 2 writes**: assert the four phase-skill-guide entries exist (`phase-skill-guide/phase-{1,2,3,4}`).

- [ ] Steps 1–5 as Task 7 pattern.

#### Task 12: Feature extractor

**Files:**
- Create: `scripts/cairn_query/extractors/feature.py`
- Test: `tests/unit/test_extractor_feature.py`
- Source: `.claude/features/*.yaml`

**What it extracts:** glob `.claude/features/*.yaml`, parse each via pyyaml, emit one Feature node per file (id, name, intent, shaped-from, slice_ids from the `slices:` block). Emit `BINDS ← shaped_from path` if present, and `BINDS ← .claude/features/<id>.yaml`.

**Tests Phase 2 writes**: assert `compression` Feature exists with non-empty slice_ids.

- [ ] Steps 1–5 as Task 7 pattern.

#### Task 13: Slice extractor

**Files:**
- Create: `scripts/cairn_query/extractors/slice.py`
- Test: `tests/unit/test_extractor_slice.py`
- Source: git history — `git log --all --grep='^slice: .* — complete$'`

**What it extracts:** for each close commit C found by `git log`:
1. Parse the commit subject for slice id (regex `^slice: (.+) — complete$`).
2. Read `slice.yaml` at the parent commit (`git show <C>~1:.claude/current-slice/slice.yaml`).
3. Read `intent.md` at parent commit if available — extract envelope_paths and envelope_out_of_scope.
4. Build the Slice pydantic model.
5. Emit edges: `PARENT → Feature` (feature_id from id prefix), `TOUCHES → Invariant` per id in invariants_touched, `REFERENCES → Decision` per id in adrs_referenced, `CREATES → Decision` per id in adrs_created, `BINDS ← envelope_paths`.

**Tests Phase 2 writes:**
- Assert `compression/lever-2-orchestrator-split` exists with status=complete and close_commit=84f1749.
- Assert at least 4 slices total.
- Assert one slice has non-empty `invariants_touched`.

**Implementation note**: this extractor uses `subprocess.run(["git", ...])` rather than mistune (the source is git, not markdown). Phase 3 wires it through `scripts.slice_orchestrator.git._git()` if accessible (the closed slice's lifecycle.py exports it), or shells out directly with `check=True`. Idempotency: re-extracting at the same git HEAD must produce identical output.

- [ ] Steps 1–5 as Task 7 pattern.

---

### Task 14: Public Python API — lookup, search, path_bindings, cypher

**Files:**
- Modify: `scripts/cairn_query/__init__.py`
- Test: `tests/unit/test_path_binding.py` (cross-cutting integration test)

**Tests Phase 2 writes:**

```python
# tests/unit/test_path_binding.py
"""Integration test — full extraction over the live cairn corpus, then query.

Validates the workhorse path-binding query against ≥3 known paths from the
brainstorm doc's success criteria (design doc §6 Slice 1 close criterion).
"""
from pathlib import Path

import pytest

from scripts.cairn_query import (
    rebuild_from_sources, lookup, search, path_bindings, cypher,
)


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("idx") / "index.kz"
    storage = rebuild_from_sources(db_path=db_path, snapshot_id=None)
    return storage


def test_path_bindings_for_lifecycle_py(index):
    """scripts/slice_orchestrator/lifecycle.py is bound by INV-008."""
    results = path_bindings(index, "scripts/slice_orchestrator/lifecycle.py")
    inv_ids = {r.id for r in results if r.entity_type == "invariant"}
    assert "INV-008" in inv_ids


def test_path_bindings_for_architecture_md(index):
    """docs/ARCHITECTURE.md is bound by every Invariant."""
    results = path_bindings(index, "docs/ARCHITECTURE.md")
    inv_results = [r for r in results if r.entity_type == "invariant"]
    assert len(inv_results) >= 9


def test_path_bindings_for_lessons_md(index):
    """docs/lessons.md is bound by L-001 (and others)."""
    results = path_bindings(index, "docs/lessons.md")
    lesson_ids = {r.id for r in results if r.entity_type == "lesson"}
    assert "L-001" in lesson_ids


def test_lookup_invariant(index):
    inv = lookup(index, "invariant", "INV-008")
    assert inv.id == "INV-008"


def test_lookup_missing_raises(index):
    with pytest.raises(KeyError):
        lookup(index, "invariant", "INV-999")


def test_search_invariants_returns_all(index):
    results = search(index, "invariant")
    assert len(results) >= 9


def test_cypher_supersedes_chain(index):
    """Multi-hop query: every Decision that is superseded by another."""
    rows = cypher(index, "MATCH (d:Decision)<-[:SUPERSEDES]-(d2:Decision) RETURN d.id, d2.id")
    # At least semantic-identity → identifier-scheme exists per cairn ADR corpus
    pairs = {(r["d.id"], r["d2.id"]) for r in rows}
    assert ("semantic-identity", "identifier-scheme") in pairs
```

**Implementation Phase 3 ships:**

Modify `scripts/cairn_query/__init__.py`:

```python
"""Cairn knowledge substrate — typed query layer over the markdown corpus.

Public API: rebuild_from_sources, lookup, search, path_bindings, cypher.
See docs/plans/2026-04-25-knowledge-substrate-design.md.
"""
from __future__ import annotations

from pathlib import Path

from .models import Entity, EntityType, Invariant, Decision, Lesson, SpecSection, OpRule, Feature, Slice
from .storage import KuzuStorage
from .extractors.invariant import InvariantExtractor
from .extractors.decision import DecisionExtractor
from .extractors.lesson import LessonExtractor
from .extractors.spec_section import SpecSectionExtractor
from .extractors.op_rule import OpRuleExtractor
from .extractors.feature import FeatureExtractor
from .extractors.slice import SliceExtractor

DEFAULT_DB_PATH = Path(".claude/cairn_query/index.kz")


def rebuild_from_sources(
    *, db_path: Path = DEFAULT_DB_PATH, snapshot_id: str | None = None,
) -> KuzuStorage:
    """Run all extractors and populate the kuzudb at db_path. Idempotent."""
    storage = KuzuStorage(db_path=db_path)
    extractors = [
        InvariantExtractor(architecture_path=Path("docs/ARCHITECTURE.md")),
        DecisionExtractor(adr_dir=Path("docs/adr")),
        LessonExtractor(lessons_path=Path("docs/lessons.md")),
        SpecSectionExtractor(spec_path=Path("docs/spec-v1.md")),
        OpRuleExtractor(op_ref_path=Path("docs/operational-reference.md")),
        FeatureExtractor(features_dir=Path(".claude/features")),
        SliceExtractor(),
    ]
    for ex in extractors:
        nodes, edges = ex.extract(snapshot_id=snapshot_id)
        for n in nodes:
            storage.upsert_node(n.entity)
        for e in edges:
            storage.upsert_edge(
                e.predicate,
                from_path=e.from_path,
                from_node_type=e.from_node_type,
                from_id=e.from_id,
                to_node_type=e.to_node_type,
                to_id=e.to_id,
            )
    return storage


def lookup(storage: KuzuStorage, entity_type: str, id: str) -> Entity:
    return storage.lookup(entity_type, id)


def search(storage: KuzuStorage, entity_type: str, filters: dict | None = None) -> list[Entity]:
    return storage.search(entity_type, filters)


def path_bindings(storage: KuzuStorage, path: str) -> list[Entity]:
    return storage.path_bindings(path)


def cypher(storage: KuzuStorage, query: str, params: dict | None = None) -> list[dict]:
    return storage.cypher(query, params)
```

- [ ] Steps 1–5 as before.

---

### Task 15: typer CLI

**Files:**
- Create: `scripts/cairn_query/__main__.py`
- Test: `tests/unit/test_cli_query.py`

**Tests Phase 2 writes:**

```python
# tests/unit/test_cli_query.py
from typer.testing import CliRunner

from scripts.cairn_query.__main__ import app


runner = CliRunner()


def test_cli_help_lists_commands():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    for cmd in ["show", "path-bindings", "graph", "supersedes", "slices",
                "cypher", "dump", "stats", "rebuild", "validate"]:
        assert cmd in r.output


def test_cli_stats_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    r = runner.invoke(app, ["rebuild"])
    assert r.exit_code == 0
    r = runner.invoke(app, ["stats"])
    assert r.exit_code == 0
    assert "Invariant" in r.output


def test_cli_show_lookup(tmp_path, monkeypatch):
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    runner.invoke(app, ["rebuild"])
    r = runner.invoke(app, ["show", "invariant", "INV-008"])
    assert r.exit_code == 0
    assert "INV-008" in r.output


def test_cli_path_bindings(tmp_path, monkeypatch):
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    runner.invoke(app, ["rebuild"])
    r = runner.invoke(app, ["path-bindings", "docs/ARCHITECTURE.md"])
    assert r.exit_code == 0
    assert "INV-" in r.output
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/__main__.py`:

```python
"""typer CLI for cairn_query. Operator-facing.

Database location: $CAIRN_QUERY_DB or ".claude/cairn_query/index.kz".
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import typer
import yaml

from . import (
    rebuild_from_sources, lookup, search, path_bindings as pb_query, cypher as cypher_query,
)
from .storage import KuzuStorage
from .validators import run_validator

app = typer.Typer(help="Cairn knowledge-substrate query CLI.")


def _db_path() -> Path:
    return Path(os.environ.get("CAIRN_QUERY_DB", ".claude/cairn_query/index.kz"))


def _open_storage() -> KuzuStorage:
    return KuzuStorage(db_path=_db_path())


@app.command()
def rebuild():
    """Rebuild the index from current source markdown."""
    storage = rebuild_from_sources(db_path=_db_path())
    typer.echo(f"Rebuilt at {_db_path()}")


@app.command()
def show(entity_type: str, id: str):
    """Pretty-print one entity by type+id."""
    storage = _open_storage()
    entity = lookup(storage, entity_type, id)
    typer.echo(yaml.safe_dump(entity.model_dump(mode="json"), default_flow_style=False))


@app.command(name="path-bindings")
def path_bindings(path: str):
    """List entities binding the given path."""
    storage = _open_storage()
    results = pb_query(storage, path)
    for e in results:
        typer.echo(f"{e.entity_type}:{e.id}  {getattr(e, 'name', '')}")


@app.command()
def graph(id: str, depth: int = 1):
    """Show neighborhood traversal of an entity (ASCII tree)."""
    storage = _open_storage()
    rows = cypher_query(
        storage,
        "MATCH (n {id: $id})-[r]-(m) RETURN type(r), labels(m), m.id LIMIT 50",
        {"id": id},
    )
    typer.echo(f"{id}")
    for r in rows:
        rel = r.get("type(r)", "?")
        target = f"{r.get('labels(m)', ['?'])[0]}:{r.get('m.id', '?')}"
        typer.echo(f"  --[{rel}]--> {target}")


@app.command()
def supersedes(decision_id: str):
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
def slices(feature: str | None = None, status: str | None = None):
    """List slices, optionally filtered by feature and/or status."""
    storage = _open_storage()
    filters: dict = {}
    if feature is not None:
        filters["feature_id"] = feature
    if status is not None:
        filters["status"] = status
    for s in search(storage, "slice", filters):
        typer.echo(f"{s.id}  {s.status}  ({s.completed or 'in-progress'})")


@app.command()
def cypher(query: str):
    """Run a raw Cypher query against the index. Power-user escape hatch."""
    storage = _open_storage()
    rows = cypher_query(storage, query)
    typer.echo(json.dumps(rows, default=str, indent=2))


@app.command()
def dump(format: str = "yaml"):
    """Dump the entire graph to text. format = yaml | json."""
    storage = _open_storage()
    out: dict = {"nodes": {}, "edges": []}
    for et in ["invariant", "decision", "lesson", "spec_section", "op_rule", "feature", "slice"]:
        out["nodes"][et] = [e.model_dump(mode="json") for e in search(storage, et)]
    if format == "json":
        typer.echo(json.dumps(out, default=str, indent=2))
    else:
        typer.echo(yaml.safe_dump(out, default_flow_style=False))


@app.command()
def stats():
    """Counts of nodes per type."""
    storage = _open_storage()
    for et, (table_name, _) in [
        ("Invariant", ("Invariant", None)),
        ("Decision", ("Decision", None)),
        ("Lesson", ("Lesson", None)),
        ("SpecSection", ("SpecSection", None)),
        ("OpRule", ("OpRule", None)),
        ("Feature", ("Feature", None)),
        ("Slice", ("Slice", None)),
    ]:
        c = storage.count(table_name)
        typer.echo(f"{et}: {c}")


@app.command()
def validate():
    """Run the CI round-trip validator. Exits non-zero on failure."""
    rc = run_validator()
    raise typer.Exit(code=rc)


if __name__ == "__main__":
    app()
```

- [ ] Steps 1–5 as before.

---

### Task 16: CI round-trip validator

**Files:**
- Create: `scripts/cairn_query/validators.py`
- Test: `tests/unit/test_round_trip_validator.py`

**Tests Phase 2 writes:**

```python
# tests/unit/test_round_trip_validator.py
"""Test the CI round-trip validator's failure modes.

The validator runs in CI (cairn_query validate). It must:
1. Pass cleanly on the current corpus.
2. Fail with a clear error message when:
   a. An ID referenced anywhere is unresolvable.
   b. A Decision's superseded_by points at a Decision that doesn't list
      that ADR in its `supersedes` list (asymmetry).
   c. A BINDS edge points at a non-existent path (when path is not null).
"""
from datetime import date
from pathlib import Path

import pytest

from scripts.cairn_query.models import Decision, PathAnchor
from scripts.cairn_query.validators import (
    run_validator, ValidationFailure, validate_supersession_symmetry,
    validate_invariant_references, validate_binds_paths,
)


def test_validator_passes_on_current_corpus(tmp_path, monkeypatch):
    """Cairn's existing markdown corpus must pass the round-trip validator."""
    monkeypatch.setenv("CAIRN_QUERY_DB", str(tmp_path / "idx.kz"))
    rc = run_validator()
    assert rc == 0


def test_supersession_symmetry_catches_one_sided_link(tmp_path):
    """If A says superseded_by:B but B doesn't list A in supersedes, FAIL."""
    a = Decision(
        id="adr-a", name="A", status="superseded", firmness="firm",
        topic="x", date=date(2026, 1, 1), superseded_by="adr-b",
        body_anchor=PathAnchor(path="x"),
    )
    b = Decision(
        id="adr-b", name="B", status="accepted", firmness="firm",
        topic="x", date=date(2026, 1, 1),
        # MISSING: supersedes=["adr-a"]
        supersedes=[],
        body_anchor=PathAnchor(path="x"),
    )
    failures = validate_supersession_symmetry([a, b])
    assert len(failures) == 1
    assert "adr-a" in failures[0].message
    assert "adr-b" in failures[0].message


def test_invariant_reference_catches_unresolvable_id(tmp_path):
    """A Slice referencing INV-999 (not in the Invariant set) FAILs."""
    from scripts.cairn_query.models import Slice
    s = Slice(
        id="x/y", name="x", feature_id="x", status="complete",
        started=date(2026, 1, 1),
        invariants_touched=["INV-999"],  # nonexistent
        close_commit="abc1234",
    )
    failures = validate_invariant_references(slices=[s], invariants=[])
    assert len(failures) == 1
    assert "INV-999" in failures[0].message


def test_binds_path_validation_catches_nonexistent_path(tmp_path):
    """A BINDS edge from a non-existent path FAILs."""
    failures = validate_binds_paths([("docs/does-not-exist.md", "Invariant", "INV-001")])
    assert len(failures) == 1
    assert "does-not-exist" in failures[0].message
```

**Implementation Phase 3 ships:**

Create `scripts/cairn_query/validators.py`:

```python
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
from .storage import KuzuStorage


@dataclass
class ValidationFailure:
    kind: str
    message: str


def validate_supersession_symmetry(decisions: list[Decision]) -> list[ValidationFailure]:
    """If A.superseded_by == B, then B.supersedes must include A."""
    failures: list[ValidationFailure] = []
    by_id = {d.id: d for d in decisions}
    for d in decisions:
        if d.superseded_by is None:
            continue
        successor = by_id.get(d.superseded_by)
        if successor is None:
            failures.append(ValidationFailure(
                kind="supersession",
                message=f"{d.id}.superseded_by={d.superseded_by} but {d.superseded_by} not found",
            ))
            continue
        if d.id not in successor.supersedes:
            failures.append(ValidationFailure(
                kind="supersession",
                message=f"{d.id} declares superseded_by={d.superseded_by}, but {d.superseded_by}.supersedes does not include {d.id}",
            ))
    return failures


def validate_invariant_references(
    *, slices: list[Slice], invariants: list[Invariant]
) -> list[ValidationFailure]:
    """Every INV-NNN referenced from a Slice or Decision must exist."""
    failures: list[ValidationFailure] = []
    inv_ids = {i.id for i in invariants}
    for s in slices:
        for inv in s.invariants_touched:
            if inv not in inv_ids:
                failures.append(ValidationFailure(
                    kind="invariant_reference",
                    message=f"Slice {s.id} references unresolvable {inv}",
                ))
    return failures


def validate_binds_paths(
    binds_triples: list[tuple[str, str, str]]
) -> list[ValidationFailure]:
    """For each (path, to_type, to_id), the path must exist on disk (or be explicitly null)."""
    failures: list[ValidationFailure] = []
    for path_str, to_type, to_id in binds_triples:
        if path_str is None or path_str == "":
            continue
        p = Path(path_str)
        if not p.exists():
            failures.append(ValidationFailure(
                kind="binds_path",
                message=f"BINDS edge from non-existent path {path_str} → {to_type}:{to_id}",
            ))
    return failures


def run_validator() -> int:
    """Run all validations against the current index. Returns exit code."""
    from . import rebuild_from_sources, search, cypher
    db_path = Path(os.environ.get("CAIRN_QUERY_DB", ".claude/cairn_query/index.kz"))
    storage = rebuild_from_sources(db_path=db_path)

    decisions = search(storage, "decision")
    slices = search(storage, "slice")
    invariants = search(storage, "invariant")

    binds_triples: list[tuple[str, str, str]] = []
    for et in ["Invariant", "Decision", "Lesson", "SpecSection", "OpRule", "Feature", "Slice"]:
        rows = cypher(storage, f"MATCH (p:Path)-[:BINDS]->(n:{et}) RETURN p.value, n.id")
        for r in rows:
            binds_triples.append((r["p.value"], et, r["n.id"]))

    failures: list[ValidationFailure] = []
    failures.extend(validate_supersession_symmetry(decisions))
    failures.extend(validate_invariant_references(slices=slices, invariants=invariants))
    failures.extend(validate_binds_paths(binds_triples))

    if failures:
        for f in failures:
            print(f"FAIL [{f.kind}]: {f.message}", file=sys.stderr)
        return 1
    print(f"OK — {len(decisions)} decisions, {len(slices)} slices, {len(invariants)} invariants, {len(binds_triples)} binds checked.")
    return 0
```

- [ ] Steps 1–5 as before.

---

### Task 17: Documentation update

**Files:**
- Modify: `docs/operational-reference.md` — append a `## cairn_query CLI reference` section

**Tests Phase 2 writes:** none (documentation-only).

**Implementation Phase 3 ships:**

Append to `docs/operational-reference.md`:

```markdown
## cairn_query CLI reference

The cairn_query CLI exposes the knowledge substrate to operators and skills. Database location: `$CAIRN_QUERY_DB` (default: `.claude/cairn_query/index.kz`).

| Command | Description |
|---|---|
| `cairn_query rebuild` | Rebuild the index from current source markdown |
| `cairn_query show <type> <id>` | Pretty-print one entity by type+id |
| `cairn_query path-bindings <path>` | List entities binding the given path |
| `cairn_query graph <id> [--depth N]` | Show neighborhood traversal as ASCII tree |
| `cairn_query supersedes <decision-id>` | Show the supersession chain |
| `cairn_query slices [--feature X] [--status Y]` | Filter slices |
| `cairn_query cypher '<query>'` | Run raw Cypher (power-user escape hatch) |
| `cairn_query dump [--format yaml\|json]` | Dump the full graph to text |
| `cairn_query stats` | Counts of nodes per type |
| `cairn_query validate` | Run the CI round-trip validator (exit 0 = pass) |

**Environment variables:**
- `CAIRN_QUERY_DB`: override the default db path. Default: `.claude/cairn_query/index.kz`.

**Indexing notes:**
- The index is gitignored (per ADR `cairn-substrate-and-fastmcp` D13 — co-landed in Slice 2).
- Rebuild is mtime-validated; queries trigger lazy rebuild when sources change.
- Multi-snapshot pinning (LRU(8) by git SHA) is exposed in Slice 2 via the FastMCP server, not directly in the v1 CLI.

**Source files indexed:** `docs/ARCHITECTURE.md`, `docs/adr/*.md`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md`, `.claude/features/*.yaml`, `git log --grep='^slice: .* — complete$'`.
```

- [ ] **Step 1: Phase 3 amends operational-reference.md** with the section above.
- [ ] **Step 2: Run full suite** — should still be GREEN.

---

### Task 18: Append slice entry to compression feature file

**Files:**
- Modify: `.claude/features/compression.yaml`

**Tests Phase 2 writes:** none (registry update).

**Implementation Phase 3 ships:**

Append to the `slices:` list in `.claude/features/compression.yaml`:

```yaml
  - id: compression/lever-X-knowledge-index
    added: 2026-04-25
    intent: "Slice 1 of the knowledge-substrate program (design doc 2026-04-25-knowledge-substrate-design.md). Ship scripts/cairn_query/ — extractor (markdown → pydantic typed records) + kuzudb-backed graph storage + cairn_query CLI (typer) + CI round-trip validator. Operator-only consumer; no FastMCP server, no agent integration. Seven entity types (Invariant/Decision/Lesson/SpecSection/OpRule/Feature/Slice) plus the BINDS path-binding inverse view. Closes when full pytest passes, CI validator round-trips the current corpus, and cairn_query path-bindings <known-path> returns correct records for ≥3 sampled paths. Out of scope: FastMCP adapter (Slice 2), phase-agent integration (Slice 2/3), pre-wipe artifact preservation (sibling slice), ADR creation (cairn-substrate-and-fastmcp lands in Slice 2)."
```

- [ ] **Step 1: Phase 3 appends the entry**.
- [ ] **Step 2: Run full suite** — should still be GREEN.

---

## Slice-close criteria (Phase 4 audit)

The slice closes (`/start-slice complete`) when:

1. `uv run pytest -q` passes — all new tests GREEN, no regression in existing 836-test suite.
2. `uv run python -m cairn_query rebuild` succeeds against the current cairn corpus.
3. `uv run python -m cairn_query stats` shows ≥9 Invariants, ≥16 Decisions, ≥2 Lessons, ≥1 Feature, ≥4 Slices populated.
4. `uv run python -m cairn_query path-bindings docs/ARCHITECTURE.md` returns ≥9 entities (one per Invariant, plus any other anchors).
5. `uv run python -m cairn_query path-bindings scripts/slice_orchestrator/lifecycle.py` returns INV-008 (and any slice-envelope bindings).
6. `uv run python -m cairn_query path-bindings docs/lessons.md` returns L-001 and L-002.
7. `uv run python -m cairn_query validate` exits 0 (CI round-trip validator passes on current corpus).
8. `uv run python scripts/validate_architecture.py` exits 0 (cairn validator unaffected by this slice).
9. `sweep-notes.md` documents invariant evidence for INV-001 (no pipeline bypass: this slice ran through Phases 1-4), INV-008 (no new commit sites), and any other invariants the Phase 1 intent declares.

**Cost target (informational, not blocking):** Slice 1 itself doesn't cut cost; it builds the foundation. Cost-delta measurement happens in Slice 2 (Phase 1 lockdown lands) and Slice 3 (full pipeline). Slice 1 is a pure-infrastructure cost; expected $5-10 for the slice itself given its size.

---

## Self-review checklist

Run after the plan is on disk:

**1. Spec coverage** (against `docs/plans/2026-04-25-knowledge-substrate-design.md`):
- §3 entity model — Tasks 2 (models), 7-13 (per-entity extractors). ✓
- §4 architecture — Tasks 3 (schema), 4 (storage), 5 (LRU + mtime), 14 (public API). ✓
- §5 tool surface (CLI part) — Task 15. ✓
- §6 slice 1 deliverables — Tasks 1-18 cover all listed files. ✓
- §8 ADR decisions — none drafted in Slice 1 (intentional — ADR co-lands in Slice 2). ✓
- §9 out-of-scope — Slice 1 envelope explicitly omits MCP server, role_guard rules, ADR file. ✓

**2. Placeholder scan** — searched for TBD/TODO/"implement later"/etc. None found. ✓

**3. Type consistency** — Invariant.id pattern (INV-NNN), Slice.id pattern (<feature>/<slug>), EntityType values match across models.py and storage.py and __init__.py. ✓

**4. Tasks bite-sized** — yes, each is one file or one feature; TDD steps are 2-5 minutes each. ✓
