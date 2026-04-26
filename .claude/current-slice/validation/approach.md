# Phase 2 — Skeptic approach

## What intent these tests assert

Slice 1 of the knowledge-substrate program: ship `scripts/cairn_query/` —
extractor (markdown → pydantic) → kuzudb graph → Python API + `typer` CLI
+ CI round-trip validator. Operator-only consumer; no MCP, no agent
integration, no ADR (Slice 2).

## Test-to-intent mapping

- **Models** (`test_cairn_query_models.py`): seven typed entities + PathAnchor + EntityType enum round-trip via pydantic; INV/L/Slice id patterns reject malformed values. Asserts §3 of design doc / Task 2.
- **Schema** (`test_cairn_query_schema.py`): seven NODE TABLEs + nine REL predicates from design §3; idempotent bootstrap. Task 3.
- **Storage** (`test_cairn_query_storage.py`): typed upsert/lookup/search/path_bindings/cypher; idempotent and update-in-place. Task 4.
- **LRU + mtime** (`test_snapshot_lru.py`): LRU(8) eviction + recency reorder; mtime-fingerprint detects modification *and* deletion. Task 5.
- **Extractor protocol** (`test_extractor_base.py`): `Extractor` Protocol enforces `extract()` shape; ExtractedNode/Edge dataclasses. Task 6.
- **Per-entity extractors** (`test_extractor_{invariant,decision,lesson,spec_section,op_rule,feature,slice}.py`): each parses its canonical source against live cairn corpus, surfaces concrete known entities (INV-008, parallelism-v1, L-001/L-002, phase-skill-guide/phase-{1..4}, compression feature, lever-2 close-commit 84f1749), emits BINDS edges, degrades gracefully on missing source. Tasks 7–13.
- **Public API integration** (`test_path_binding.py`): rebuilds against live corpus; verifies the three slice-close path-binding probes (ARCHITECTURE.md→≥9 invariants, lifecycle.py→INV-008, lessons.md→L-001/L-002) plus cypher escape hatch with the identifier-scheme→semantic-identity supersession. Task 14.
- **CLI** (`test_cli_query.py`): all 10 commands listed; `rebuild`/`stats`/`show`/`path-bindings` round-trip via `CAIRN_QUERY_DB`. Task 15.
- **CI validator** (`test_round_trip_validator.py`): passes on current corpus; catches asymmetric supersession, unresolved INV references, non-existent BINDS paths. Task 16.

## Ambiguities resolved

- Import path: cairn pyproject pins pythonpath=["scripts"], so tests use `from cairn_query....` — `scripts/` is on `pythonpath` and namespace-package import works (verified).
- Tasks 8–13 only sketched in plan; concrete RED probes synthesised from live corpus (parallelism-v1, identifier-scheme→semantic-identity, L-001 instance `f531087`, phase-skill-guide/phase-{1..4}, `compression` feature, slice id `compression/lever-2-orchestrator-split` close `84f1749`).
- No production code written; no ADR; envelope mirrored verbatim.
