# Knowledge Substrate — Design

**Status:** Draft. Inputs ready for (a) two `/decision` sessions to draft the co-landing ADRs `cairn-substrate-and-fastmcp` and `slice-artifact-preservation`; (b) `/brainstorm` + `/write-plan` for Slice 1 (`compression/lever-X-knowledge-index`); (c) lightweight GitHub Project board (agent-managed via GitHub MCP, Path C). Does NOT itself draft the ADRs — every commitment that requires supersession is enumerated below as input for the `/decision` flow, not as a finished ADR.

**Date:** 2026-04-25

**Brainstorm source:** `~/.claude/plans/with-humans-the-hard-zany-otter.md` (2026-04-25, thin design from plan-mode session that exited without writing the canonical design doc)

**Audit context (what this supersedes):** `docs/plans/2026-04-25-efficiency-program-part-8-compression-audit.md` §10 / §13 — the substrate program absorbs M0 (per-slice orientation) + M0.5 (API digests) + S1 (constraint-harvest subagent) + structural H1 (doc-port layer) into a single architectural commitment.

**Related operator memory:**
- `project_knowledge_substrate_proposal.md` — original proposal pointer
- `feedback_substrate_context_separation.md` — agent-facing query MUST NOT expose operator memory
- `project_github_project_management_initiative.md` — agent-managed via GitHub MCP, parallel to substrate

---

## 1. Context and motivation

The Part-8 compression audit measured a single slice at $18.71 cost-per-slice, dominated by `cache_creation` (phase agents re-reading the same large markdown corpus each phase). Levers H2/M0/M0.5/M3/S1/S3/H1 were enumerated as separate slices; cumulative stacked savings estimate was 65-95% off the baseline, but the leverage was uncertain because the levers compose in ways the audit could not measure.

Operator framing during brainstorm 2026-04-25: *"with humans the hard part is to distill knowledge into the core steps and give clear directions, while predicting the needs and handling it"* — and a prompt to look at "the system as a whole being more right" rather than at additional tree-level levers.

**Conclusion:** there is a system-level move that collapses M0 + M0.5 + S1 + structural H1 into a single architectural commitment — a **knowledge substrate**: a typed, queryable index over cairn's existing markdown corpus, exposed to phase agents as a FastMCP server. The phased pipeline (P1→P2→P3→P4 with bounded role authority) is preserved as the safety architecture; the substrate is the *optimization and reliability layer* below it.

**Intended outcome:** phase agents query typed records instead of re-reading markdown; `cache_creation` drops sharply; canonical-knowledge drift between agent paraphrase and source-of-truth becomes mechanically impossible because typed records can't be paraphrased.

---

## 2. Load-bearing decisions

Decisions carried over from the brainstorm (lines 23-41 of the source brainstorm doc) plus extensions made during the 2026-04-25 design session.

### Carried over from brainstorm

1. **Substrate is a derived view, never authoritative.** ADRs / `lessons.md` / `ARCHITECTURE.md` / `spec-v1.md` / `operational-reference.md` / `.claude/features/*.yaml` / `slice.yaml` stay as authoring sources. Index is parallel-derived; on disagreement, source markdown wins. CI round-trip validator gates merges.

2. **Entity model.** Originally ten entities; tightened in this design session (see §3 — five knowledge entities, two scope/pipeline entities, plus the derived path-binding inverse view).

3. **MCP-as-adapter, not MCP-as-implementation.** Core is the Python module `scripts/cairn_query/`; FastMCP server wraps it for phase-agent tool surface; typer CLI wraps it for operator and skill use. Same logic, three callers.

4. **Lives in cairn repo.** Substrate ships with cairn via the existing `.slice-system → .` symlink. Downstream consumers get it transparently.

5. **Read-side first; mutation surface deferred.** v1 is read-only — every index change comes from a markdown edit. Mutation (typed claims by agents) is its own ADR-shaped decision when observed need accretes.

6. **Lazy mtime-validated rebuild.** Substrate checks source mtimes vs stored manifest on every query; rebuilds if anything changed. No hooks, no daemons, no race conditions.

7. **Index snapshot per phase boundary.** Orchestrator captures `snapshot_id` at each phase open; passes via `AGENT_ENVELOPE`; phase queries pin to it for determinism. Snapshots are immutable; eligible for GC after slice close.

8. **Phased pipeline preserved.** Phase 1/2/3/4 with bounded role authority is the safety architecture — not optimized away. Substrate makes phase handoffs *richer* (prose for humans + typed-claim diff for next phase, both committed atomically), not absent.

9. **Rust migration target retired; stdlib-only constraint replaced.** New constraint: *new code is Python, function-based, with v1 standing dependencies as the only allowed deps; new third-party deps require a deliberate ADR.* Co-landed in ADR `cairn-substrate-and-fastmcp`.

### Extensions made during the 2026-04-25 design session

10. **Cross-workflow-primitive principle (entity inclusion test).** Substrate types are cross-workflow primitives — referenced by multiple flows (validator, phase agents, ADRs, lessons, slice metadata). Single-program artifacts (e.g. lever rankings from one audit), ephemeral artifacts (intent.md, approach.md, notes.md mid-slice), and operator-side analysis outputs (slice classifications, retrospective metrics) do NOT earn a substrate type, even when they have IDs. This gates v2+ expansion.

11. **Tool-count discipline.** MCP tool count is a context-cost line item — every tool's pydantic schema loads into the phase agent's context on FastMCP init. Tools group by query intent (lookup / search / traverse), not by entity type. Adding a new tool requires demonstrating Cypher escape-hatch insufficiency for an actually-used query.

12. **Substrate's MCP surface is structural enforcement of context-isolation.** The MCP tool surface exposes only canonical, cross-workflow primitives. Ephemeral artifacts, mid-slice reasoning from other phases, and operator memory are unreachable through the tool surface by design — and are revoked at the role_guard / allowed-tools layer once MCP coverage exists. Slices that legitimately edit those sources unlock them via envelope declaration.

13. **Path-3 archival discipline.** Cairn's "no archive directory for successful slices" stance (`commands/claude-code/start-slice.full.md:210`) is amended: orchestrator's `close_slice` gains a copy-before-wipe step that snapshots ephemeral phase artifacts to `.claude/sweep-results/<slice-id>/artifacts/`. Substrate v1 does NOT extract these artifacts — preservation is operator-side optionality for future analysis. Co-landed in ADR `slice-artifact-preservation`.

14. **Operator memory permanently excluded from agent surface.** Operator memory under `~/.claude/projects/.../memory/` is in a different trust class (unreviewed, private) and MUST NOT be queryable by phase agents — even as an opt-in tagged surface. Promotion path for memory that should become agent-queryable: migrate to `docs/lessons.md` via `/decision` or a slice. (Per `feedback_substrate_context_separation.md`.)

---

## 3. Entity model

Seven typed nodes + path-binding inverse view. Each entity passes the cross-workflow-primitive test.

### Knowledge entities (canonical, persistent, referenced by multiple flows)

| Entity | Source | Notes |
|---|---|---|
| `Invariant` | `docs/ARCHITECTURE.md` `invariant-check INV-NNN` blocks | 9 today (INV-001..INV-009). Properties: id, statement, target PathAnchor, grep regex, architecture_anchor. |
| `Decision` | `docs/adr/*.md` | ~16 today. Frontmatter (id, name, status, firmness, supersedes, supersedes-sections, superseded-by, topic, invariants-touched, date) + nested `DecisionPoint` children identified by `<adr-id>/<decision-slug>`. |
| `Lesson` | `docs/lessons.md` | Currently L-001, L-002. Properties: id, title, discovered date, pattern, instances (commit/slice references), rule, anti-patterns, body_anchor. |
| `SpecSection` | `docs/spec-v1.md` | Sections cited as `§N`. Properties: id, title, body. |
| `OpRule` | `docs/operational-reference.md` | Operational rules (e.g. Phase Skill Guide entries). Properties: id, statement, scope. |

### Scope/pipeline entities

| Entity | Source | Notes |
|---|---|---|
| `Feature` | `.claude/features/<id>.yaml` | Properties: id, name, intent, shaped-from path, slices (id refs). |
| `Slice` | Reconstructed from `slice: <id> — complete` git commits | Stub-only post-close (cairn wipes intent.md etc. at close): id, name, feature_id, status, started, completed, invariants_touched, adrs_referenced, adrs_created, envelope_paths, envelope_out_of_scope, close_commit SHA. Past-slice extraction reads `slice.yaml` from the parent of the close commit. |

### Derived view: `BINDS` (path-binding inverse)

For any path → list of entities binding it. Computed during extraction. Workhorse query.

```cypher
MATCH (p:Path {value: $path})-[:BINDS]->(e)
RETURN labels(e), e.id, e.name
```

Powers both the operator CLI (`cairn_query path-bindings <path>`) and the phase-agent MCP tool (`path_bindings(path)`).

### Edge predicates

```
SUPERSEDES        Decision  → Decision
TOUCHES           Decision  → Invariant
TOUCHES           Slice     → Invariant
REFERENCES        Slice     → Decision
CREATES           Slice     → Decision   (ADRs born in this slice)
PARENT            Slice     → Feature
CHILD             Feature   → Slice
INSTANCE_OF       Lesson    → Slice|Commit
BINDS             Path      → ANY        (the inverse view)
ANCHORED_AT       ANY       → Path       (where the source lives)
```

### Excluded entities (with rationale per the cross-workflow-primitive principle, §2 D10)

| Excluded | Reason | Promotion path |
|---|---|---|
| `Lever` | Single-analysis artifact (compression-program audit table); not cross-workflow | If lever queries become a regular workflow, ship `docs/levers/<id>.md` as first-class files. v2+. |
| `Phase-event` | Single-flow consumer (cost-discipline runtime check); already structured in `result.json` | v2 ingest from `.claude/sweep-results/` once cost-discipline analysis becomes a regular operator query. |
| `Envelope` (separate entity) | Subsumed by Slice fields; no v1 query needs it as a separate node | If multi-hop Envelope-specific queries emerge, promote in v2. |
| `SliceClass` | No v1 phase-agent consumer; classification fuzzy | If phase prompts later differentiate by class, ship as a manual `intent.md` field (operator-assigned), not heuristic. v2+. |
| `OperatorMemory` | Trust-class boundary | **Permanent exclusion**, not deferral (per §2 D14). Migration path: lessons.md via /decision. |
| Mid-slice ephemerals as queryable entities | Information-isolation invariant (per §2 D12) | **Permanent exclusion** for run-time agent surface. Path-3 archive is operator-side post-close analysis only. |

---

## 4. Architecture

Three-layer system: canonical sources → derived substrate (kuzudb) → adapters (FastMCP server + typer CLI).

### Data flow

```
                 CANONICAL SOURCES (markdown, never overridden by substrate)
                 ┌────────────────────────────────────────────────┐
                 │  docs/ARCHITECTURE.md  → Invariant             │
                 │  docs/adr/*.md         → Decision              │
                 │  docs/lessons.md       → Lesson                │
                 │  docs/spec-v1.md       → SpecSection           │
                 │  docs/operational-reference.md → OpRule        │
                 │  .claude/features/*.yaml → Feature             │
                 │  git log → `slice: <id> — complete` → Slice    │
                 └────────────────┬───────────────────────────────┘
                                  │
                          mtime check + (snapshot ? git show <SHA> : HEAD)
                                  │
                                  ▼
                 ┌────────────────────────────────────────────────┐
                 │  EXTRACTORS  (mistune AST → pydantic)         │
                 │  scripts/cairn_query/extractors/<entity>.py   │
                 │  - one extractor per entity type              │
                 │  - emit pydantic-validated nodes              │
                 │  - emit BINDS / TOUCHES / REFERENCES edges    │
                 └────────────────┬───────────────────────────────┘
                                  │ idempotent upsert
                                  ▼
                 ┌────────────────────────────────────────────────┐
                 │  kuzudb  (.claude/cairn_query/index.kz/)       │
                 │  - schema = nodes(7) + edges(typed predicates) │
                 │  - LRU(8) keyed by snapshot_id (git SHA)       │
                 │  - gitignored; rebuildable from sources        │
                 └────────────────┬───────────────────────────────┘
                                  │ Cypher
                                  ▼
                 ┌────────────────────────────────────────────────┐
                 │  cairn_query  (Python module API)              │
                 │  - typed query functions returning pydantic    │
                 │  - snapshot pinning per session                │
                 └────────────┬─────────────────────────┬─────────┘
                              │                         │
                              ▼                         ▼
                     ┌──────────────────┐    ┌──────────────────┐
                     │  FastMCP server  │    │  typer CLI       │
                     │  AGENT-facing    │    │  OPERATOR-facing │
                     │  (Slice 2+)      │    │  (Slice 1)       │
                     └──────────────────┘    └──────────────────┘
```

### Extractor pipeline (per entity type)

Each extractor implements `extract(snapshot_id: str | None) -> tuple[list[Node], list[Edge]]`:

1. **Read source** — at HEAD by default; at `git show <SHA>:<path>` if snapshot pinned.
2. **Parse** — mistune produces AST; entity-specific traversal extracts structural blocks.
3. **Validate** — pydantic model construction. Malformed source raises `ValidationError` with field-level pointer.
4. **Emit edges** — extractor knows its outbound predicates. The `BINDS` inverse edge is emitted by every extractor that anchors at a `PathAnchor`.
5. **Upsert** — idempotent write to kuzudb.

### Lazy mtime-validated rebuild

On every query through `cairn_query`:
- If `snapshot_id is None` → check current-HEAD source mtimes against stored manifest; rebuild only the entity types whose sources changed.
- If `snapshot_id` pinned → check LRU cache; on miss, rebuild against `git show <SHA>` for each source, cache, return.

**Build cost at our scale**: ~30 markdown files, ~400 nodes, ~2000 edges. Sub-second on cached SHA, single-digit seconds on full rebuild from cold.

### CI round-trip validator

Runs in CI on every commit:
1. Extract everything against current HEAD.
2. Re-serialize each entity to canonical form via `model.model_dump(mode='json')`.
3. Assert structural shape:
   - Every `INV-NNN` referenced anywhere resolves to an extracted Invariant.
   - Every `adrs-referenced:` ID in slice.yaml resolves to a Decision.
   - Every `BINDS` edge's source path exists in the working tree (or is explicitly null for prose-only references).
   - Every Decision with `superseded-by:` set has a matching Decision whose `supersedes:` includes it (bi-directional consistency).
4. Fail build on any unresolvable reference. Extraction failure breaks the build, never silently degrades.

### Snapshot determinism mechanism

```
phase open → orchestrator: snapshot_id = git rev-parse HEAD
           → AGENT_ENVELOPE['cairn_query_snapshot'] = <sha>
           → FastMCP session state pins to <sha>
           → every query call uses it implicitly
post-close → snapshots eligible for GC (LRU eviction handles)
```

LRU bound: N=8 snapshots in-process (covers 4 phases × 2 in-flight slices, with cushion for triager re-dispatch).

### Concrete file layout

```
scripts/cairn_query/                # Slice 1 deliverable
  __init__.py              # public API: query functions
  __main__.py              # typer CLI entry
  models.py                # pydantic entity models
  storage.py               # kuzudb wrapper, snapshot LRU, mtime detection
  schema.py                # kuzudb schema (CREATE NODE TABLE, edges)
  extractors/
    __init__.py
    base.py                # Extractor protocol
    invariant.py           # parses invariant-check blocks
    decision.py            # parses ADR frontmatter + sections
    lesson.py              # parses L-NNN entries
    spec_section.py        # parses §N
    op_rule.py             # parses operational-reference rules
    feature.py             # parses .claude/features/*.yaml
    slice.py               # walks git log for `slice: <id> — complete`
  validators.py            # CI round-trip validator entry

tests/unit/                # Slice 1 deliverable
  test_extractor_invariant.py     (one per entity type)
  test_round_trip_validator.py
  test_snapshot_lru.py
  test_path_binding.py
  test_cli_query.py

mcp_servers/cairn_knowledge/        # Slice 2 deliverable
  server.py                # FastMCP server, wraps cairn_query
  tools.py                 # 4-tool surface (lookup/search/path_bindings/cypher)

.mcp.json                  # Slice 2 deliverable

.gitignore                 # Slice 1 amendment: .claude/cairn_query/index.kz/
```

---

## 5. Tool surface

### MCP tools (Slice 2 — agent-facing, 4 tools total)

```python
lookup(entity_type: EntityType, id: str) -> Entity
# Single-entity lookup. Polymorphic typed return via pydantic discriminated union.

search(entity_type: EntityType, filters: dict | None = None) -> list[Entity]
# List + filter for an entity type.

path_bindings(path: str) -> list[Entity]
# Workhorse: every entity that binds this path. Inverse view.

cypher(query: str) -> list[dict]
# Escape hatch for multi-hop / cross-entity queries.
```

`snapshot_id` is **session-level**, not per-call. Set once via `AGENT_ENVELOPE`; FastMCP session context propagates it to every tool. Tool signatures stay clean.

```python
class EntityType(str, Enum):
    INVARIANT = "invariant"
    DECISION = "decision"
    LESSON = "lesson"
    SPEC_SECTION = "spec_section"
    OP_RULE = "op_rule"
    FEATURE = "feature"
    SLICE = "slice"

Entity = Annotated[
    Invariant | Decision | Lesson | SpecSection | OpRule | Feature | Slice,
    Field(discriminator="entity_type")
]
```

Each pydantic model carries an `entity_type: Literal[...]` discriminator field. FastMCP exposes the union as the typed return.

### CLI commands (Slice 1 — operator-facing, granular)

```bash
cairn_query show <id>                              # pretty-print one entity + outbound edges
cairn_query path-bindings <path>                   # workhorse: what binds this path
cairn_query graph <id> [--depth 2]                 # neighborhood traversal as ASCII tree
cairn_query supersedes <decision-id>               # supersession chain
cairn_query slices --feature <id> [--status complete]   # filter slices
cairn_query cypher '<query>'                       # raw Cypher escape hatch
cairn_query dump [--format yaml|json]              # full graph → text for snapshot or grep
cairn_query stats                                  # node/edge counts per type, sanity check
cairn_query rebuild [--snapshot <sha>]             # force rebuild (default: HEAD)
cairn_query validate                               # CI round-trip validator entry
```

### Asymmetry rationale

MCP is tight (4 tools) because **context-cost**: every tool's pydantic schema loads into agent context on FastMCP init. CLI is broad (~10 commands) because **human UX**: typer makes commands cheap, and operators benefit from short discoverable verbs.

### What is NOT in the v1 tool surface

- No write/mutation tools (deferred per §2 D5 + ADR `cairn-substrate-and-fastmcp` decision)
- No per-entity-type get/list tools (consolidated into 4 polymorphic tools per §2 D11)
- No subscription / change-notification tools (orthogonal to snapshot pinning)
- No operator-memory tools (per §2 D14 — permanent exclusion)
- No mid-slice ephemeral tools (per §2 D12 — context-isolation invariant)
- No SliceClass / Lever / PhaseEvent tools (per §3 cross-workflow-primitive principle)

---

## 6. Slice sequencing

Three substrate slices form a hard chain. One sibling slice runs in parallel.

### Substrate slices (sequential — 1 → 2 → 3)

**Slice 1 — `compression/lever-X-knowledge-index`**
- **Ships:** extractor (markdown → pydantic), `scripts/cairn_query/` package, kuzudb-backed graph storage, `cairn_query` CLI (typer), CI round-trip validator.
- **Out-of-scope:** any agent integration; any MCP server; any orchestrator change.
- **Consumer at this slice:** operator-only.
- **Closes when:** full pytest passes; CI validator round-trips every entity for the current corpus; `cairn_query path-bindings <known-path>` returns correct typed records for ≥3 sampled paths.
- **Parallelism:** Phase 3 implementation is a natural fan-out — one subagent per entity-type extractor (7 extractors → 7 parallel subagents per `superpowers:dispatching-parallel-agents`). Within-slice parallel dispatch is v1-legal per `parallelism-v1` D4.

**Slice 2 — `compression/lever-Y-mcp-substrate`**
- **Ships:** FastMCP server adapter wrapping `cairn_query`; `.mcp.json` registration; orchestrator captures `git rev-parse HEAD` as `snapshot_id` per phase, passes via `AGENT_ENVELOPE`; phase-1-writer agent prompt updated to query-first (single phase as proof-of-concept); role_guard / allowed-tools lockdown for phase-1-writer (revokes Read on `scripts/cairn_query/**` + canonical knowledge sources unless slice envelope grants).
- **Co-lands ADR `cairn-substrate-and-fastmcp`** (decisions enumerated in §8.1 below).
- **Closes when:** ADR lands; FastMCP server starts under `.mcp.json`; phase-1-writer queries cairn_query through MCP successfully on a real slice; cost-delta measured against Lever-1 baseline ($2.96 / 105k cache_creation for Phase 1) — target ≥40% Phase-1 reduction.
- **Depends on:** Slice 1 (`cairn_query` module must exist for the MCP server to import).

**Slice 3 — `compression/lever-Z-substrate-full-pipeline`**
- **Ships:** phase-2-skeptic / phase-3-implementer / phase-4-integrator agent prompt updates (query-first); role_guard / allowed-tools lockdown extended to phases 2/3/4; `invariant_check_results` integration (phase-4-integrator reads typed evidence instead of running each invariant check by hand); sweep-notes template generation from typed records.
- **Closes when:** full-slice cost re-measured against $18.71 baseline; target ≥50% total stacked reduction; sweep-notes template correctly fills invariant-evidence rows from substrate query.
- **Depends on:** Slice 2 (MCP server must be live for phase 2/3/4 prompts to call tools that don't exist until Slice 2).

### Sibling slice (parallel with substrate chain)

**`compression/slice-artifact-preservation`**
- **Ships:** orchestrator's `close_slice` gains a copy-before-wipe step that snapshots `intent.md` / `validation/approach.md` / `implementation/notes.md` / `integration/sweep-notes.md` / `handoff-phase-{1,2,3,4}.md` / `envelope-expansions.log` / pre-close `slice.yaml` to `.claude/sweep-results/<slice-id>/artifacts/`.
- **Co-lands ADR `slice-artifact-preservation`** (decisions enumerated in §8.2 below).
- **Envelope:** `scripts/slice_orchestrator/lifecycle.py`; new test file `tests/unit/test_slice_orchestrator_artifact_preservation.py`; `commands/claude-code/start-slice.full.md:210` line amendment; `.gitignore` (add `.claude/sweep-results/*/artifacts/`); `docs/ARCHITECTURE.md` (INV-008 amendment to include the copy step); new ADR file; standard slice metadata.
- **Out-of-scope:** any extractor or substrate-side change (substrate slices own that); compaction policy (deferred per ADR D4); commit-vs-gitignore reconsideration (deferred to extraction time).
- **Closes when:** pytest passes; ADR lands; close_slice copies are byte-identical to pre-wipe artifacts; idempotency test passes; manual run on a throwaway slice confirms `.claude/sweep-results/<id>/artifacts/` populates correctly.
- **Parallelism with substrate Slice 1:** green-lit per `parallelism-v1`. Recommended sequencing: open the sibling worktree at substrate Slice 1's start; both close before substrate Slice 2 begins (so Slice 2's first close has the new archival in place).

### Slice ordering summary

```
        Time →

main worktree:    [Slice 1] ──→ [Slice 2 + ADR1] ──→ [Slice 3]

parallel worktree: [Sibling + ADR2] (during Slice 1 — recommended)
```

### Card structure for the GitHub Project board (Path C, agent-managed)

| Card | Slice | ADR co-landed | Parallelizable with |
|---|---|---|---|
| 1 | `compression/lever-X-knowledge-index` | — | sibling |
| 2 | `compression/lever-Y-mcp-substrate` | `cairn-substrate-and-fastmcp` | nothing (depends on 1) |
| 3 | `compression/lever-Z-substrate-full-pipeline` | — | nothing (depends on 2) |
| 4 (sibling) | `compression/slice-artifact-preservation` | `slice-artifact-preservation` | 1 |

Six total cards (4 slices + 2 ADRs). Initial board setup: agent-driven via GitHub MCP server (per `project_github_project_management_initiative.md` — operator does not manage manually).

---

## 7. Mutation surface — explicit deferral

The substrate's v1 MCP tool surface is **read-only**. No tools allow phase agents to write typed claims back to the index.

**Why deferred:**
- Mutation introduces a write path that competes with the canonical-markdown source-of-truth model (§2 D1). Resolving the resulting race / authority semantics requires more design than v1 wants.
- v1's value-prop is *cost reduction* (cut markdown re-reads). Mutation is a *capability addition*, not a cost-reduction lever.
- Without observed need, designing the mutation API risks committing to the wrong shape.

**Promotion path:** when an actually-used workflow needs typed-claim writes, draft a new ADR (likely `cairn-substrate-mutation-surface` or similar), specifying: which entities can be written, by whom, with what conflict semantics, and how mutations roundtrip back to canonical markdown. This is its own design pass, not bundled with substrate v1.

---

## 8. ADR decisions inventory

This section is the **input for the two `/decision` sessions** that draft the co-landing ADRs. Each decision below is a commitment statement with rationale. The `/decision` flow's Phase 0 (Constraint Harvest) and Phase 2 (Decision Enumeration) operate against this list directly.

**Convention:** prose shorthand `<adr-id> D<N>` per identifier-scheme; mechanical identifier per decision is `<adr-id>/<decision-slug>` (slugs assigned during ADR drafting). D-numbers below are this design's working numbering — final ADR may reorder.

### 8.1 ADR `cairn-substrate-and-fastmcp` (co-lands with Slice 2)

**Topic:** dependency policy, agent-context discipline, substrate's architectural posture.

**Firmness:** firm. The dep set, context-isolation extension, and substrate-as-derived-view stance are architectural commitments; supersession is the only path to change.

**Likely invariants touched:** verified during ADR drafting — substrate's MCP-as-structural-enforcement (D16) likely amends or extends an existing context-isolation invariant (INV-005 region per `docs/ARCHITECTURE.md`), or warrants a new INV codifying §2 D12. ADR draft Phase 0 (Constraint Harvest) resolves this.

#### Decisions

**D1 — Standing dependency set.** The v1 standing dependencies are:
- `pydantic` (typed entity models + validation)
- `kuzudb` (graph storage + Cypher query)
- `mistune` (markdown AST parsing)
- `typer` (CLI framework)
- `fastmcp` (MCP server framework — already committed via brainstorm §3)
- `pyyaml` (already a project dep)

*Rationale:* each library buys a specific capability that hand-rolled stdlib code would re-implement worse. Pydantic is brought transitively by FastMCP; using it directly removes ~100 LOC boilerplate per entity type. Kuzudb is the right shape for the data (knowledge graph, not table or document). Mistune replaces brittle regex over prose. Typer pairs with pydantic for type-driven CLI args.

**D2 — New third-party deps require a deliberate ADR.** No implicit-add policy. New deps land via supersession or a new ADR that amends D1's standing set.

*Rationale:* prevents dep-creep that would dilute the new policy line. Forces deliberate review of each addition.

**D3 — Retire stdlib-only constraint.** Amend `CLAUDE.md` "New code is Python, stdlib-only, function-based" to "New code is Python, function-based, with v1 standing deps as the only allowed dependencies." Supersedes the prior CLAUDE.md guidance.

*Rationale:* FastMCP is Python-native; no realistic stdlib-only-FastMCP port. The constraint was load-bearing for a Rust-mapping target now retired (D4). Without that target, "stdlib-only" was over-restrictive.

**D4 — Retire Rust-mapping target.** Remove from `CLAUDE.md`: "one-for-one Rust-mapping target for end-of-v1." Mapping target was load-bearing only under stdlib-only (D3); FastMCP has no realistic Rust port.

*Rationale:* the target was hypothetical; no Rust port has ever been started; ecosystem evolution has not produced a FastMCP-equivalent in Rust. Retiring removes a constraint that was already non-binding.

**D5 — Substrate is derived view, never authoritative.** Markdown corpus (ADRs, lessons.md, ARCHITECTURE.md, spec-v1.md, operational-reference.md, feature/slice yamls) remains canonical. Any disagreement between substrate and source markdown resolves in favor of markdown. CI round-trip validator gates this.

*Rationale:* the markdown corpus is human-authored and reviewed; the substrate is mechanically derived. Keeping the source-of-truth in markdown preserves authoring ergonomics, version control narrative, and review process. Substrate-as-authoritative would invert these.

**D6 — Read-only v1 tool surface.** The v1 MCP server exposes `lookup`, `search`, `path_bindings`, `cypher` only. No write tools.

*Rationale:* mutation surface is its own design problem (race semantics, conflict resolution, roundtrip-to-markdown). v1's value-prop is cost reduction (cut re-reads), not capability addition. See §7 for the deferral.

**D7 — Mutation surface deferred to a future ADR.** When typed-claim writes earn their need (observed workflow asks for them), a new ADR (`cairn-substrate-mutation-surface` or similar) drafts the design. v1 commits to NOT having mutation; v2+ may add it via supersession.

*Rationale:* explicit deferral prevents implicit drift. The ADR records the boundary so future sessions can't quietly add write tools.

**D8 — Agent context-discipline lockdown.** Once the MCP exposes a query surface for a knowledge source, phase agents lose direct read access to that source AT THE ROLE_GUARD / ALLOWED-TOOLS LAYER. Lockdown ships with the prompt update per phase:
- Slice 2: phase-1-writer's allowed-tools tightened; role_guard rule denies Read/Bash on `scripts/cairn_query/**` and on `docs/ARCHITECTURE.md`, `docs/adr/**`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md` for phase-1-writer.
- Slice 3: extends to phase-2-skeptic, phase-3-implementer, phase-4-integrator.

*Rationale:* without structural lockdown, the cost-reduction value-prop is at risk — agents have an escape hatch to "just Read the file" that defeats the substrate. Lockdown enforces the bias toward typed query at the structural level, not just the prompt level.

**D9 — Envelope-grant escape hatch for D8.** A slice whose envelope (in `slice.yaml`) explicitly declares one of the locked-down paths gets read access for that path only, during that slice. Default-deny + envelope-grant.

*Rationale:* slices that legitimately edit ADRs / lessons / cairn_query source must read them. Routing through envelope-declaration matches cairn's existing role_guard discipline (no new exception list to maintain).

**D10 — Tool-count discipline.** MCP tools group by query intent (`lookup`, `search`, `path_bindings`, `cypher`), not by entity type. Adding a new tool requires demonstrating Cypher escape-hatch insufficiency for an actually-used query.

*Rationale:* tool count is a context-cost line item. Per-entity-type proliferation would multiply context cost without adding capability. Polymorphic tools + discriminated unions cover the surface tightly.

**D11 — Cross-workflow-primitive principle gates entity inclusion.** Substrate types are cross-workflow primitives — referenced by ≥2 of: validator, phase agents, ADRs, lessons, slice metadata. Single-program artifacts, ephemeral artifacts, and operator-side analysis outputs do NOT earn types.

*Rationale:* prevents v2+ scope-creep. Forces every proposed new entity to demonstrate cross-workflow value before being added.

**D12 — Snapshot pinning via git SHA + AGENT_ENVELOPE.** Snapshot identity = git commit SHA. Orchestrator captures `git rev-parse HEAD` at each phase open; passes as `cairn_query_snapshot` in `AGENT_ENVELOPE`; FastMCP session pins to it; tools propagate implicitly. In-process LRU(8) caches kuzudb result by SHA.

*Rationale:* git is already cairn's source-of-truth for "where are we." Mtime hashes or other fingerprints buy nothing for this use case. LRU(8) covers 4 phases × 2 in-flight slices with cushion.

**D13 — kuzudb storage gitignored.** `.claude/cairn_query/index.kz/` is gitignored. The substrate is derived (D5); committing the binary catalog files would produce noisy diffs that add nothing the source markdown doesn't show.

*Rationale:* matches the "derived, not authoritative" stance. CI round-trip validator is what asserts correctness in CI; committing the index isn't required for that.

**D14 — CI round-trip validator gates merges.** The validator runs in CI on every commit. Extraction failure (unresolvable INV-NNN reference, Decision supersession asymmetry, unmatched BINDS path) breaks the build, never silently degrades.

*Rationale:* the substrate's value depends on extraction correctness. A silent-degrade mode would let drift accumulate undetected. Hard-fail forces the operator to fix the extractor or fix the source markdown — both desirable outcomes.

**D15 — Operator memory permanently excluded from agent surface.** Operator memory under `~/.claude/projects/.../memory/` is not queryable through any MCP tool, even as opt-in. Promotion path: migrate to `docs/lessons.md` via /decision or a slice.

*Rationale:* trust-class boundary (per `feedback_substrate_context_separation.md`). Operator memory is unreviewed; making it agent-queryable invites phase agents to lean on it instead of canonical knowledge — defeating the canonical-knowledge integrity model.

**D16 — Substrate's MCP tool surface is structural enforcement of the context-isolation invariant.** The MCP exposes only canonical, cross-workflow primitives. Mid-slice ephemerals (intent.md, approach.md, notes.md, sweep-notes.md, handoff-phase-N.md) are unreachable through tools by design — even after the Path-3 archive exists, the substrate v1 does not extract them. Phase agents querying the substrate cannot reach into another phase's reasoning.

*Rationale:* the phased pipeline (P1→P2→P3→P4) is the safety architecture; information barriers between phases are deliberate. The substrate strengthens these barriers structurally, not just at the prompt level.

#### Open questions parked in this ADR (resolved during /decision drafting)

- **D8 detailed shape**: exact role_guard rule syntax, exact allowed-tools list per phase agent. Enumerated above; concrete syntax during drafting.
- **D11 application to v2 candidates**: Lever, Phase-event, SliceClass each get a "promotion checklist" entry in this ADR's appendix.

### 8.2 ADR `slice-artifact-preservation` (co-lands with sibling slice)

**Topic:** cairn's archival discipline — pre-wipe preservation of slice ephemerals.

**Firmness:** firm.

**Likely invariants touched:** INV-008 (slice-close-contract). The ADR amends INV-008's step ordering to include the copy step.

#### Decisions

**D1 — Pre-wipe copy step in close_slice.** `scripts/slice_orchestrator/lifecycle.py:close_slice` gains a copy step that snapshots ephemeral phase artifacts to `.claude/sweep-results/<slice-id>/artifacts/` *before* `_wipe_current_slice` runs.

New step ordering:
1. Sweep-notes presence check (existing — D2 from INV-008)
2. slice.yaml → status=complete (existing)
3. Bundle handoff.md (existing)
4. **NEW: Copy artifacts to `.claude/sweep-results/<slice-id>/artifacts/`**
5. Wipe current-slice (existing — DC-5)
6. Sole `slice: <id> — complete` commit (existing — DC-4)
7. Persist terminal observability state (existing)

*Rationale:* preserves data that would otherwise be destroyed by the wipe, enabling future operator analysis of patterns across slices. Does not alter cairn's INV-008 sole-commit-source contract.

**D2 — Snapshot scope.** The copy includes:
- `intent.md`
- `validation/approach.md`
- `implementation/notes.md`
- `integration/sweep-notes.md`
- `handoff-phase-{1,2,3,4}.md` (each, where present)
- `envelope-expansions.log`
- The pre-close `slice.yaml` (with envelope intact, before status=complete update)

All artifacts the wipe would otherwise destroy except git-tracked sources outside `.claude/current-slice/`.

*Rationale:* completeness — operator analysis of "envelope expansion frequency" / "Phase-2 ambiguity rates" needs the full set. Selective preservation forces future re-design.

**D3 — Gitignored by default.** `.claude/sweep-results/*/artifacts/**` is added to `.gitignore`. Data is on-disk only; not committed.

*Rationale:* preserves the data without polluting git history with mechanical churn. Operator can still grep / analyze locally. Re-considerable when an actual extraction use case lands and demands cross-machine consistency.

**D4 — Retention / compaction policy parked.** v1 ships with no automatic GC, no compaction. Operator runs `du`-based diagnostics if disk-growth becomes a concern. Compaction policy (e.g. gzip after N days, prune after N slices) decided in a future slice once growth observed.

*Rationale:* premature optimization. Ship the preservation; learn what disk-growth looks like in practice; design compaction with data.

**D5 — Supersedes "no archive directory for successful slices" stance.** Amends `commands/claude-code/start-slice.full.md:210` from "no archive directory for successful slices — the `status: complete` commit IS the git-history record" to "no archive directory **for committed history** — ephemeral artifacts preserved on-disk for future analytical use."

*Rationale:* the prior stance was correct that the git-history record is canonical. The amendment narrows it to "no archive in *committed* form" — preserving the commit-narrative purity while enabling on-disk analytical preservation.

**D6 — Idempotency.** The copy step is idempotent — re-closing an already-closed slice (DC-3 re-entry path) does NOT double-write the artifacts. F5-tolerant: missing source files (operator-rebase corner) do NOT break the close; the copy step skips and proceeds.

*Rationale:* matches existing close_slice discipline (DC-3 idempotent, F5 operator-rebase tolerant). The new copy step inherits the same robustness.

**D7 — INV-008 amendment.** `docs/ARCHITECTURE.md` INV-008 (slice-close-contract) is amended to include the new copy step (D1 above) in the ordered sequence. Validator's grep target for INV-008 (`def close_slice` in `scripts/slice_orchestrator/lifecycle.py`) is unchanged.

*Rationale:* the architecture doc is the authoritative declaration of INV-008's contract; the new step must be reflected there, not just in the ADR.

#### Open questions parked in this ADR

- **D3 commit-vs-gitignore reconsideration**: re-examine when extraction work begins. Default gitignore may be wrong if cross-machine analysis is needed.
- **D4 compaction policy specifics**: gzip thresholds, prune horizons, scope (all artifacts vs. selected). Decided in a future slice.

---

## 9. Out of scope / future work

### Explicitly deferred (with promotion path)

| Deferred | Reason | Promotion path |
|---|---|---|
| Lever entity | Single-analysis artifact (per §3 / §2 D10) | If lever queries become regular, ship `docs/levers/<id>.md` first-class files. v2+. |
| Phase-event entity | Single-flow consumer; data already in `result.json` | v2 ingest from `.claude/sweep-results/` once cost-discipline analysis becomes a regular query. |
| Envelope as separate entity | Subsumed by Slice fields | If multi-hop Envelope-specific queries emerge, promote in v2. |
| SliceClass auto-classifier | No v1 phase-agent consumer | If phase prompts later differentiate, ship as manual `intent.md` field (operator-assigned). v2+. |
| Mutation surface | Capability-addition, not cost-reduction (per §7) | New ADR `cairn-substrate-mutation-surface` when observed need accretes. |
| Per-entity-type MCP tools | Polymorphism + Cypher escape hatch covers the surface | New tool requires Cypher-insufficiency demonstration (per ADR D10). |
| Subscription / change-notification tools | Orthogonal to snapshot pinning | Earned only when a use case for live-updating queries appears. |
| Compaction / retention for `.claude/sweep-results/*/artifacts/` | Premature optimization | Resolved when disk-growth observed (per ADR `slice-artifact-preservation` D4). |

### Permanent exclusions (not deferred — never agent-queryable)

| Excluded | Reason |
|---|---|
| Operator memory | Trust-class boundary (per §2 D14) |
| Mid-slice ephemerals as run-time queryable entities | Information-isolation invariant (per §2 D12) |

### Separate initiatives (sequenced after substrate)

- **GitHub Project management — full integration.** Lightweight 6-card board (agent-managed via GitHub MCP) ships in parallel with substrate Slice 1 per Path C. Full integration design (automation rules, slice-close → card status sync, Feature entity gaining `github-project-url`, GitHub issues as v2 substrate entities) is its own brainstorm, sequenced after substrate Slices 1-2 ship.
- **Per-phase model + thinking-level configuration.** Separate orchestrator design direction (per `project_per_phase_model_and_thinking.md`). Not bundled with substrate.

---

## 10. Implementation hand-off

What must happen to start substrate Slice 1:

1. **Two `/decision` sessions** (independent — can be parallel):
   - Session A: drafts ADR `cairn-substrate-and-fastmcp` from §8.1 above. Sixteen decisions ready as input.
   - Session B: drafts ADR `slice-artifact-preservation` from §8.2 above. Seven decisions ready as input.

   Each ADR is **drafted but not committed** until its co-landing slice runs (`cairn-substrate-and-fastmcp` lands at Slice 2; `slice-artifact-preservation` lands at the sibling slice).

2. **`/brainstorm` + `/write-plan` for substrate Slice 1** (`compression/lever-X-knowledge-index`). Concrete extractor architecture per entity type, pydantic schema details, kuzudb schema syntax (`CREATE NODE TABLE` for each entity, edge tables for each predicate), CI round-trip validator test cases, integration with `.claude/features/compression.yaml`. The design doc (this file) is Slice 1's brainstorm input — most architectural decisions are settled, so the slice's own brainstorm focuses on implementation details.

3. **`/start-slice` for sibling slice** (`compression/slice-artifact-preservation`) in a parallel worktree. Independent of substrate work; can land before, during, or after Slice 1.

> **Removed step (2026-04-26):** "GitHub Project board setup (Path C, agent-managed via GitHub MCP)" was originally listed here as a prerequisite. Path C was never enumerated against alternatives in this doc, and per §8.1 D2 a credentialed external dependency requires deliberate ADR — not a 30-minute setup task. Deferred behind substrate Slices 1+2; tracked in `docs/roadmap.md` under "Gated — sequenced after specific milestones." See `agent-managed-planning-substrate` entry there for the full work item.

### Cross-references

- Brainstorm source: `~/.claude/plans/with-humans-the-hard-zany-otter.md`
- Audit context: `docs/plans/2026-04-25-efficiency-program-part-8-compression-audit.md`
- Operator memory:
  - `project_knowledge_substrate_proposal.md` (proposal pointer)
  - `feedback_substrate_context_separation.md` (operator-memory exclusion principle)
  - `project_github_project_management_initiative.md` (GitHub MCP, Path C)
  - `project_per_phase_model_and_thinking.md` (separate initiative — not substrate)
- Recently closed slice (substrate's predecessor lever): `compression/lever-2-orchestrator-split` (close commit `84f1749`)
- Feature file: `.claude/features/compression.yaml` (substrate slices to be appended)
