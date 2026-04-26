# Intent — compression/lever-X-knowledge-index

> Slice 1 of the knowledge-substrate program. Implementation plan:
> `docs/plans/2026-04-25-knowledge-substrate-slice-1-plan.md`
> Design doc: `docs/plans/2026-04-25-knowledge-substrate-design.md`

## Envelope

```yaml
adrs-referenced: []
adrs-created: []
invariants-touched:
  - INV-001  # no pipeline bypass — this slice runs through Phases 1–4
  - INV-008  # no new commit sites — close_slice remains sole `slice: complete` producer
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

## What / Why / Boundary (≤200 w)

**What.** Ship `scripts/cairn_query/` — a stdlib-plus-deps Python package that extracts typed records from cairn's existing markdown corpus into a kuzudb-backed graph index, exposed via a Python API and a `typer` CLI, gated by a CI round-trip validator. Adds four deps to `pyproject.toml` (pydantic, kuzu, mistune, typer); no agent integration, no MCP server, no ADR.

**Why.** Foundation of the knowledge-substrate program (design doc §6). Today every phase agent re-reads raw markdown to recover invariants/decisions/lessons; cost is O(corpus) per dispatch. A typed query layer over a derived graph index turns that into O(query). Slice 1 ships only the substrate; Slice 2 wires it to FastMCP and co-lands the authorizing ADR `cairn-substrate-and-fastmcp` (design §6, §8.1). Splitting capability from architectural commitment lets us validate the extractor against the live corpus before binding the stack.

**Boundary.** Operator-only consumer this slice — no phase-agent reads, no role_guard lockdown (Slice 2/3), no orchestrator edits, no ADR file. Index is derived and `.gitignore`d under `.claude/cairn_query/`. ADR posture explicitly recorded: `adrs-referenced: []`, `adrs-created: []`.

## Specification detail

Three-layer system per design §4:

**(1) Extraction.** `mistune` AST over canonical sources → pydantic-validated typed entities. Seven entity types: `Invariant`, `Decision`, `Lesson`, `SpecSection`, `OpRule`, `Feature`, `Slice` (`scripts/cairn_query/models.py`). Each extractor (`scripts/cairn_query/extractors/{invariant,decision,lesson,spec_section,op_rule,feature,slice}.py`) implements the `Extractor` protocol: `extract(snapshot_id) -> (nodes, edges)`. Sources: `docs/ARCHITECTURE.md` (invariant-check blocks), `docs/adr/*.md` (frontmatter+body), `docs/lessons.md` (L-NNN entries), `docs/spec-v1.md` (§N), `docs/operational-reference.md`, `.claude/features/*.yaml`, and `git log --grep='^slice: .* — complete$'`.

**(2) Storage.** kuzudb on disk at `.claude/cairn_query/index.kz`. Schema (`scripts/cairn_query/schema.py`) declares one NODE TABLE per entity plus a synthetic `Path` node, with REL TABLES for `SUPERSEDES`, `TOUCHES`, `REFERENCES`, `CREATES`, `PARENT`, `CHILD`, `INSTANCE_OF`, `BINDS` (path-binding inverse view), `ANCHORED_AT`. List-valued fields are edges, not node properties. `KuzuStorage` (`scripts/cairn_query/storage.py`) exposes `upsert_node`, `upsert_edge`, `lookup`, `search`, `path_bindings`, `cypher`, `count`. A `SnapshotLRU(maxsize=8)` keys cached snapshots by git SHA; `sources_changed_since` does mtime-fingerprint comparison for lazy rebuild.

**(3) Public surface.** `scripts/cairn_query/__init__.py` re-exports `rebuild_from_sources`, `lookup`, `search`, `path_bindings`, `cypher`. `scripts/cairn_query/__main__.py` is the `typer` app with commands `show`, `path-bindings`, `graph`, `supersedes`, `slices`, `cypher`, `dump`, `stats`, `rebuild`, `validate` (env override `CAIRN_QUERY_DB`). `scripts/cairn_query/validators.py` runs the CI round-trip validator: re-extract → re-serialise → diff; emits `ValidationFailure` on supersession asymmetry, dangling invariant references, or non-existent BINDS paths.

**Sequencing notes.** Plan is split into 18 tasks; Tasks 7–13 (per-entity extractors) are the Phase-3 fan-out unit. Phase 2 writes one RED test commit per task; Phase 3 ships one GREEN implementation commit per task. Phase-3 fan-out for the seven extractors uses `superpowers:dispatching-parallel-agents`. INV-008 DC-4 preserved: no new commit sites; `close_slice` remains sole `slice: <id> — complete` producer.

## Verification (Phase 4 audit gates)

The slice closes when ALL hold (plan §Slice-close criteria, §6 of design doc):

1. `uv run pytest -q` — full suite GREEN; pre-existing 836-test baseline unchanged plus all new tests passing, 0 failed.
2. `uv run python -m cairn_query rebuild` — succeeds against the live cairn corpus.
3. `uv run python -m cairn_query stats` — populated counts: ≥9 Invariants, ≥16 Decisions, ≥2 Lessons, ≥1 Feature, ≥4 Slices.
4. `uv run python -m cairn_query path-bindings docs/ARCHITECTURE.md` — returns ≥9 entities.
5. `uv run python -m cairn_query path-bindings scripts/slice_orchestrator/lifecycle.py` — returns INV-008.
6. `uv run python -m cairn_query path-bindings docs/lessons.md` — returns L-001 and L-002.
7. `uv run python -m cairn_query validate` — exits 0 (round-trip validator passes on current corpus).
8. `uv run python scripts/validate_architecture.py` — exits 0 (cairn invariant validator unaffected).
9. `sweep-notes.md` documents invariant evidence for INV-001 (no pipeline bypass — slice ran Phases 1–4) and INV-008 (no new commit sites; `close_slice` only).

**Cost note (informational).** Slice 1 is pure-infrastructure cost (~$5–10); cost-delta measurement begins in Slice 2 once the FastMCP adapter lands and Phase-1 lockdown bites.
