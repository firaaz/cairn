---
id: cairn-substrate-and-fastmcp
name: "Cairn substrate — v1 dep set, FastMCP adapter, and agent-context structural lockdown"
status: accepted
firmness: firm
supersedes:
  - "cliff-failure-mode-and-v1-defenses D4 (partial: commitment #6 mechanization — Read-tool role-keyed enforcement returns to v1 scope for canonical-knowledge lockdown only, where the MCP exposes a query surface for that source. Windsurf portability, spec-v1 §9 three-track routing, retroactive invariant enforcement, slice pause/resume command, and ARCHITECTURE.md chunking remain time-boxed to v2+. Parallels parallelism-v1's partial supersession of D4's commitment #2.)"
supersedes-sections:
  - "compression-infrastructure-bootstrap §47/§69/§84 mechanism-ceiling — lifts the Read-tool role-keyed prohibition for canonical knowledge sources where the MCP exposes a query surface (D8 below). Bootstrap-ADR §40 mechanism authorization (role_guard.py PreToolUse hook for the compression feature) is preserved verbatim — this ADR extends the policy-table content, not the mechanism class. Other items the bootstrap-ADR did NOT authorize (role-keyed Bash, role-keyed subagent dispatch) remain v2+."
  - "CLAUDE.md:26 prose — replaces 'New code is Python, stdlib-only, function-based' with 'New code is Python, function-based, with the v1 standing dep set as the only allowed dependencies' (D3); retires 'one-for-one Rust-mapping target for end-of-v1' (D4). CLAUDE.md is operational guidance, not an ADR; the amendment is propagation, not formal ADR supersession, but recorded here so the prose change is traceable to this ADR."
superseded-by: null
topic: architecture
adrs-referenced: [phase-lock-and-role-declaration, compression-infrastructure-bootstrap, context-discipline-protocol, slice-close-contract, parallelism-v1, identifier-scheme, feature-slice-model, cliff-failure-mode-and-v1-defenses]
invariants-touched: []
date: 2026-04-26
---

# cairn-substrate-and-fastmcp: v1 dep set, FastMCP adapter, agent-context structural lockdown

## Status
Accepted

## Date
2026-04-26

## Context

Cairn's compression program (`docs/plans/2026-04-25-knowledge-substrate-design.md`) introduces a typed knowledge substrate: a kuzudb-backed graph index of cairn's markdown corpus, exposed to phase agents via a FastMCP server with four tools (`lookup`, `search`, `path_bindings`, `cypher`). The substrate's value-prop is cost reduction — eliminate the ~30 KB / 30k-token re-reads that phase agents currently perform to answer questions whose answers are structurally extractable from the corpus.

Three commitments are load-bearing for this value-prop and must be made together, not piecemeal:

1. **A standing dependency set.** Pydantic, kuzudb, mistune, typer, and fastmcp are not optional. CLAUDE.md's current "Python, stdlib-only" guidance (`CLAUDE.md:26`, written when cairn had no agent-facing typed query layer) is incompatible with FastMCP and with the typed-entity model the substrate ships. The substrate's correctness, reviewability, and ergonomics all depend on these libraries.

2. **A FastMCP server as the agent-facing surface.** Direct Python imports from `scripts/cairn_query` would technically work, but they would defeat the cost-reduction goal: phase agents would still load the substrate's source code into context (~50 KB for the package), substituting one re-read for another. MCP's process boundary lets the substrate live outside agent context entirely; agents see only the four tool definitions (~2 KB total).

3. **Structural agent-context lockdown.** When the MCP exposes a query surface for a knowledge source, phase agents lose direct read access to that source. Without lockdown, agents have a "just Read the file" escape hatch that defeats the substrate. The lockdown ships at the role_guard / allowed-tools layer (per `compression-infrastructure-bootstrap`'s authorized mechanism), not just the prompt layer, because prompt-layer enforcement is provably bypassable under context pressure (L-005 skill-coordination tax pattern).

Each of these commitments alone is non-controversial; the combined posture is controversial enough to warrant a firm ADR. Once committed, the dep set and lockdown stance are architectural properties that supersession (not amendment) is the only way to change. This is appropriate firmness: the dep set is the foundation for entity validation, the storage layer, the MCP framework, and the CLI — retraction would unwind the substrate program. The lockdown stance is appropriate firmness because partial lockdown (cultural/prompt-only) is empirically inadequate; only structural enforcement preserves the cost-reduction value-prop under future agent-prompt drift.

This ADR formally supersedes two prior time-boxed positions to authorize what's needed:

- **cliff-failure-mode-and-v1-defenses D4 commitment #6 mechanization** — partial supersession (Read-tool role-keyed enforcement returns to v1 scope for canonical-knowledge lockdown only). Parallels how `parallelism-v1` returned D4 commitment #2 to v1 scope. All other commitment-#6 v2+ items remain time-boxed.
- **compression-infrastructure-bootstrap §47/§69/§84 mechanism-ceiling** — lifts the Read-tool prohibition. The bootstrap-ADR positioned itself as a "narrow exception" with the explicit expectation that "Slice B's Part 0 ADR" would absorb it (§70). This ADR is the Read-mechanization successor that fulfills that absorption for canonical-knowledge lockdown.

A second-order commitment: the substrate is a **derived view, not authoritative state**. Source markdown remains canonical. Substrate disagreement with markdown is a substrate bug, never a markdown bug. The CI round-trip validator gates this asymmetry: any extraction failure breaks CI. Operator memory under `~/.claude/projects/.../memory/` is permanently excluded from the agent surface — operator memory is unreviewed and has different trust class than reviewed canonical knowledge (per `feedback_substrate_context_separation.md`).

The decision was stress-tested against five alternative shapes (direct imports, on-disk JSON cache, RAG-over-markdown, status quo, prompt-only-lockdown) in Phase 2 forced enumeration; the chosen MCP-server shape wins on three independent axes — cost reduction, structural lockdown enforceability, and Cypher escape-hatch capacity for ad-hoc queries that didn't earn typed surfaces. Phase 5 fresh-context independent verification confirmed the conclusion and surfaced six amendments — incorporated below: time-box supersession formality, MCP transport commitment, D9 abuse tripwire mechanical check, D12 worktree/detached-HEAD/shallow-clone sub-clause, D8 interaction with `/refresh-architecture` and pipeline-substrate sessions, and D2 pyyaml grandfather acknowledgment.

## Decision

### D1 — v1 standing dependency set

The v1 standing dependencies are exactly:

| Package | Capability | First use | Pre-existing? |
|---|---|---|---|
| `pydantic` (>=2.6) | typed entity models + runtime validation | Slice 1 (`scripts/cairn_query/models.py`) | new |
| `kuzudb` (>=0.6) | embedded graph storage + Cypher query | Slice 1 (`scripts/cairn_query/storage.py`) | new |
| `mistune` (>=3.0) | markdown AST parsing | Slice 1 (`scripts/cairn_query/extractors/`) | new |
| `typer` (>=0.12) | CLI framework | Slice 1 (`scripts/cairn_query/__main__.py`) | new |
| `fastmcp` | MCP server framework | Slice 2 (FastMCP adapter) | new |
| `pyyaml` | yaml parsing — orchestrator state, slice/feature files | existing (pre-policy) | yes |

*Rationale:* each library buys a specific capability that hand-rolled stdlib code would re-implement worse. Pydantic eliminates ~100 LOC boilerplate per entity type. Kuzudb is the right shape for the data (knowledge graph, not table or document). Mistune replaces brittle regex over prose. Typer pairs with pydantic for type-driven CLI args. FastMCP is Python-native; no realistic stdlib-only equivalent. Pyyaml predates this ADR (introduced in `compression/slice-1-foundation`); D2's "deliberate-ADR" rule applies to additions made *after* this ADR — pre-existing deps are grandfathered into the standing set rather than being retroactively justified, since their use was authorized by the slices that introduced them.

### D2 — New third-party deps require a deliberate ADR

No implicit-add policy *going forward*. New dependencies (post-this-ADR) land via supersession of D1 or via a new ADR that amends D1's standing set. Casual `uv add foo` without an ADR is out of policy.

Pre-existing project deps (pyyaml, plus anything currently in `pyproject.toml`'s `[project] dependencies` at the time this ADR commits) are grandfathered. Any future audit that surfaces a non-grandfathered, non-ADR'd dep treats it as a defect to either ratify (new ADR) or remove.

*Rationale:* prevents dep-creep that would dilute the new policy line. Forces deliberate review of each addition. Grandfathering avoids retroactive paperwork on deps that were authorized by their introducing slice but predate this ADR's policy framing.

### D3 — Retire stdlib-only constraint

Amend `CLAUDE.md:26` from:

> "**New code is Python, stdlib-only, function-based** — one-for-one Rust-mapping target for end-of-v1. Existing bash hooks stay until their own migration slices. No third-party deps, decorators, or metaprogramming."

to:

> "**New code is Python, function-based, with the v1 standing dep set as the only allowed dependencies** (pydantic, kuzudb, mistune, typer, fastmcp, pyyaml — see ADR `cairn-substrate-and-fastmcp`). Existing bash hooks stay until their own migration slices. No decorators or metaprogramming."

The "no third-party deps" phrase is replaced by the standing-set whitelist. "Decorators or metaprogramming" prohibition stays — pydantic-the-library uses metaclasses internally but `scripts/cairn_query/**` does not write decorators or metaclasses.

*Rationale:* stdlib-only was load-bearing for D4's Rust-mapping target. With D4 retired, stdlib-only over-constrains. The standing-set whitelist replaces the binary "stdlib vs anything" with a small, named, justified policy.

### D4 — Retire Rust-mapping target

Remove from `CLAUDE.md:26`: the phrase "one-for-one Rust-mapping target for end-of-v1." No Rust port has been started; the FastMCP framework has no Rust equivalent; the ecosystem has not produced one in the year since the target was set.

*Rationale:* the target was hypothetical and non-binding. Retiring it removes a constraint that no current code respects, and brings CLAUDE.md into alignment with reality.

### D5 — Substrate is a derived view, never authoritative

Markdown corpus (ADRs, lessons.md, ARCHITECTURE.md, spec-v1.md, operational-reference.md, feature/slice yamls) remains canonical. Any disagreement between substrate and source markdown resolves in favor of markdown. The CI round-trip validator (D14) gates this asymmetry by hard-failing on extraction errors.

*Rationale:* the markdown corpus is human-authored and human-reviewed; the substrate is mechanically derived. Source-of-truth in markdown preserves authoring ergonomics, version-control narrative, and review process. Substrate-as-authoritative would invert all three.

### D6 — Read-only v1 tool surface, stdio transport

The v1 MCP server exposes exactly four tools: `lookup`, `search`, `path_bindings`, `cypher`. No write tools. No mutation tools. No tools that escape the substrate's typed model.

**Transport: stdio.** The FastMCP server runs as a child process of the Claude Code session that loads it; communication is over stdio (JSON-RPC over stdin/stdout per MCP spec). SSE and websocket transports are not in scope for v1 — they introduce network state, daemon lifecycle, and authentication concerns that a local typed-query substrate does not need.

*Rationale:* mutation surface is its own design problem (race semantics, conflict resolution, round-trip-to-markdown invertibility). v1's value-prop is cost reduction (cut re-reads), not capability addition. Stdio is the natural transport for an orchestrator-spawned local subprocess — it composes with the existing `claude` CLI subprocess model and inherits process-lifecycle from the parent session. SSE/websocket would add daemon-management complexity that v1's per-session-spawn use case does not require.

### D7 — Mutation surface explicitly deferred

When typed-claim writes earn their need (observed workflow asks for them, demonstrated cost-or-correctness benefit), a future ADR (`cairn-substrate-mutation-surface` or similar) drafts the design. v1 commits to NOT having mutation; v2+ may add it via supersession of D6 + D7.

*Rationale:* explicit deferral prevents implicit drift. The ADR records the boundary so future sessions can't quietly add write tools that bypass the design problem mutation creates.

### D8 — Agent-context structural lockdown

When the MCP server exposes a query surface for a knowledge source, phase agents lose direct read access to that source AT THE ROLE_GUARD / ALLOWED-TOOLS LAYER. Lockdown ships with the prompt update per phase, in two stages:

**Slice 2 (with this ADR's co-landing):** phase-1-writer's allowed-tools is tightened; `checks/role_guard.py`'s `ROLE_POLICIES` gains a deny rule for phase-1-writer covering: `scripts/cairn_query/**`, `docs/ARCHITECTURE.md`, `docs/adr/**`, `docs/lessons.md`, `docs/spec-v1.md`, `docs/operational-reference.md`. The deny applies to Read and Bash (cat/head/grep equivalents); writes to these paths are already governed by the existing per-phase write rules.

**Slice 3:** lockdown extends to phase-2-skeptic, phase-3-implementer, phase-4-integrator. Deny scope per phase is determined by Slice 3's brainstorm (each phase has different read needs).

Lockdown is layered: agent frontmatter `tools:` removes tool *availability* (outer gate); role_guard.py PreToolUse hook denies *use* (inner gate). Both gates must pass for a tool call to proceed. PreToolUse is the load-bearing gate; frontmatter is defense-in-depth.

**Scope of D8:** the lockdown applies only when `AGENT_ROLE` is set (i.e., the call is dispatched as a phase agent by the orchestrator). Pipeline-substrate sessions that run *without* `AGENT_ROLE` — `/refresh-architecture` (per `cliff-failure-mode-and-v1-defenses` D1's dedicated-refresh-session model), `/integration-sweep` close-time pipeline-substrate commits, the operator's own interactive `claude` sessions for slice authoring — are unaffected by D8. role_guard.py's existing pattern is to default-allow when `AGENT_ROLE` is unset; this ADR preserves that default-allow.

*Rationale:* without structural lockdown, the cost-reduction value-prop is at risk — agents have an escape hatch to "just Read the file" that defeats the substrate. Prompt-layer enforcement is empirically inadequate (L-005 skill-coordination-tax pattern). Lockdown enforces the bias toward typed query at the structural level. Per `compression-infrastructure-bootstrap` §40, role_guard.py is the authorized PreToolUse mechanism for the compression feature; the §47/§69/§84 mechanism-ceiling that previously forbade Read-tool role-keyed scope is partially superseded by this ADR (frontmatter `supersedes-sections`). cliff-ADR D4 commitment #6 mechanization is partially superseded for read-mechanization (frontmatter `supersedes`), parallel to how `parallelism-v1` returned commitment #2 to v1 scope.

### D9 — Envelope-grant escape hatch for D8

A slice whose `slice.yaml` envelope explicitly declares one of the locked-down paths gets read access for that path only, during that slice. Default-deny + envelope-grant.

**Implementation:** each phase agent (not just phase-3-implementer as today) reads `AGENT_ENVELOPE` env var (JSON array of regex patterns); `role_guard.py` extends `_envelope_patterns(envelope)` matching to all phase agents. Pre-existing phase-3-implementer behavior is preserved verbatim.

**Abuse tripwire (mechanical):** every envelope-grant of a locked-down path appends one line to `.claude/envelope-grants.log`: `<slice-id> <YYYY-MM-DD> <granted-path> <granting-phase>`. The log is append-only and does not exist until the first grant. After logging, role_guard counts entries in the log whose slice-id numeric/date suffix falls within the last 10 slices. If 3 or more grants of the SAME path exist in that window, role_guard prints a warning to stderr: "envelope-grant abuse — path X granted in 3 of last 10 slices; consider adding an MCP tool for this query pattern (D6 amendment) instead of repeated bypass."

The 3-in-10 threshold mirrors `cliff-failure-mode-and-v1-defenses` D1's `.claude/d1-bypasses.log` rolling-window pattern; the warning is advisory, not a hard block. Three repeated grants are a signal that the lockdown is the wrong shape (D6 missed a tool) rather than that grants should be denied.

Envelope grants are per-slice and per-path; they expire when the slice closes. No global allow-list, no persistent overrides.

*Rationale:* slices that legitimately edit ADRs / lessons / cairn_query source must read them. Routing through envelope-declaration matches cairn's existing role_guard discipline (no new exception list to maintain) and aligns with `feature-slice-model`'s "envelope is the source of truth for what's in scope this slice." The abuse tripwire prevents D9 from hollowing out D8 over time.

### D10 — Tool-count discipline

MCP tools group by query intent (`lookup`, `search`, `path_bindings`, `cypher`), not by entity type. Adding a new tool requires demonstrating Cypher escape-hatch insufficiency for an actually-used query — a written use case, not a hypothetical.

*Rationale:* tool count is a context-cost line item (each tool's schema + description + example consumes agent-context tokens). Per-entity-type proliferation would multiply context cost without adding capability. Polymorphic tools + discriminated union return types cover the surface tightly.

### D11 — Cross-workflow-primitive principle gates entity inclusion

Substrate types are cross-workflow primitives — referenced by **at least two** of: validator, phase agents, ADRs, lessons, slice metadata, ARCHITECTURE.md, spec-v1.md. Single-program artifacts, ephemeral artifacts, and operator-side analysis outputs do NOT earn types.

Promotion checklist for proposed v2 entities (`Lever`, `Phase-event`, `SliceClass`):
1. Show ≥2 cross-workflow consumers.
2. Show that at least one consumer cannot be served by a Cypher escape over existing types.
3. Show that the entity has a stable identity (id) and a canonical extraction source.

Failure on any item parks the entity until criteria are met.

*Rationale:* prevents v2+ scope-creep. Forces every proposed new entity to demonstrate cross-workflow value before being added. Mirrors the "prove the type" discipline that pydantic and kuzudb both encourage.

### D12 — Snapshot pinning via git SHA + AGENT_ENVELOPE

Snapshot identity = git commit SHA. Orchestrator captures `git rev-parse HEAD` at each phase open; passes as `cairn_query_snapshot` in `AGENT_ENVELOPE`; FastMCP session pins to that SHA; tools propagate it implicitly to kuzudb queries. In-process LRU(8) caches kuzudb result by SHA.

Cache size of 8 covers: 4 phases × 2 in-flight slices = 8 distinct SHAs at any moment, with cushion. Eviction is LRU on the (SHA → query-result) cache; warm-cache rebuilds are mtime-validated (a SHA whose source files haven't changed reuses the cached graph).

**Worktree, detached-HEAD, and shallow-clone semantics:**

- **Worktrees (parallelism-v1 case):** each worktree has its own `HEAD`. `git rev-parse HEAD` invoked from a slice worktree returns that worktree's slice-branch HEAD, not the main checkout's HEAD. This is the correct behavior — concurrent slices on separate branches naturally have distinct snapshot SHAs, and the LRU(8) sizing accommodates this.
- **Detached HEAD (mid-phase rebase or `git checkout <sha>`):** `git rev-parse HEAD` returns the SHA of the detached checkout. The substrate pins to that SHA correctly. If the operator does this mid-phase, the snapshot reflects the checkout state, which matches the agent's working-tree view.
- **Shallow clone (CI):** `git rev-parse HEAD` works in shallow clones. The substrate's extractors read source markdown from the working tree (mtime-validated), not from git history, so shallow-clone history truncation does not affect extraction. The CI round-trip validator runs against the working tree's HEAD.
- **`git rev-parse HEAD` failure (corrupted .git, partial fetch):** orchestrator falls back to a sentinel snapshot ID `unknown-sha-<iso8601>` and emits a stderr warning. Phase still runs but cache is bypassed (no LRU hit on a sentinel); the substrate is queried fresh on every call. This is degraded but correct — the substrate's correctness depends on extraction, not on cache hits.

*Rationale:* git is already cairn's source-of-truth for "where are we." Mtime hashes or other fingerprints buy nothing. LRU(8) is small enough to fit in memory at all reasonable concurrency levels and big enough to avoid thrash within a slice. The sub-clauses cover the git operations cairn already commits to (parallelism-v1 worktrees, CI-shallow-clones); they do NOT introduce new failure modes, only document existing ones.

### D13 — kuzudb storage gitignored

`.claude/cairn_query/index.kz/` is added to `.gitignore` in Slice 1. The substrate is derived (D5); committing the binary catalog files would produce noisy diffs that add nothing the source markdown doesn't show, and would break round-trip determinism testing across machines.

*Rationale:* matches the "derived, not authoritative" stance. CI round-trip validator (D14) is what asserts correctness in CI; committing the index isn't required for that and is actively harmful for diff hygiene.

### D14 — CI round-trip validator gates merges

The validator runs in CI on every commit. Extraction failure (unresolvable INV-NNN reference, Decision supersession asymmetry, unmatched BINDS path, malformed frontmatter) breaks the build, never silently degrades. The validator is the load-bearing trust mechanism for D5 (substrate-as-derived-view).

The validator's failure semantics:
- Hard-fail (exit non-zero, fail CI) on extraction error.
- No degraded mode, no partial-extraction success path.
- Per-source error messages name the file and line that broke extraction.

*Rationale:* the substrate's value depends on extraction correctness. Silent-degrade mode would let drift accumulate undetected. Hard-fail forces the operator to fix the extractor or fix the source markdown — both desirable outcomes. Provides the structural integrity guarantee D5 promises.

### D15 — Operator memory permanently excluded from agent surface

Operator memory under `~/.claude/projects/.../memory/` is **NOT** queryable through any MCP tool, even as opt-in. It is not mentioned in the substrate schema. The exclusion is permanent.

Promotion path for an operator-memory entry that the operator wants agents to see: migrate to `docs/lessons.md` via `/decision` or a slice. The migration is a content-review event, not a configuration toggle.

*Rationale:* trust-class boundary (per `feedback_substrate_context_separation.md`). Operator memory is unreviewed personal-context state; making it agent-queryable invites phase agents to lean on it instead of canonical knowledge — defeating the canonical-knowledge integrity model. Even an opt-in flag would create an attractive nuisance.

### D16 — Substrate's MCP tool surface is structural enforcement of context-isolation

The MCP exposes only canonical, cross-workflow primitives (per D11). Mid-slice ephemerals (`intent.md`, `validation/approach.md`, `implementation/notes.md`, `integration/sweep-notes.md`, `handoff-phase-N.md`) are unreachable through tools by design — even after the `slice-artifact-preservation` archive exists, the substrate v1 does not extract them. Phase agents querying the substrate cannot reach into another phase's reasoning.

This is the structural-enforcement counterpart to `context-discipline-protocol`'s prose-level isolation between phases. Where context-discipline-protocol defines the *property*, this ADR defines the *mechanism*: the tool surface itself is the enforcement (you cannot query what is not exposed). No new invariant is introduced; INV-002 (envelope discipline) and the existing `context-discipline-protocol` Layer 2 (phase isolation) cover the property surface; this ADR extends the structural mechanism set.

*Rationale:* the phased pipeline (P1→P2→P3→P4) is cairn's safety architecture; information barriers between phases are deliberate. The substrate strengthens these barriers structurally rather than relying on prompt-level discipline alone. Decision D11's cross-workflow-primitive principle is what makes this enforceable: a substrate that included ephemerals would lose the enforcement property for free.

## Consequences

### Easier

- **Cost reduction is reachable.** With the FastMCP server adapter (Slice 2) and substrate (Slice 1), phase agents can query for invariants, decisions, lessons, and op-rules without loading the source files. Cost-delta target: ≥40% Phase-1 reduction (Slice 2 closes-when), ≥50% total stacked reduction (Slice 3 closes-when).
- **Structural lockdown is testable.** `checks/role_guard.py` is a single Python file with a deterministic policy table. Tests assert that phase-1-writer cannot Read `docs/ARCHITECTURE.md` (without envelope grant) and CAN read it (with envelope grant). Lockdown correctness is a property tested in CI, not a hope.
- **Cypher escape hatch covers ad-hoc queries.** Polymorphic tools (D10) plus a `cypher` query tool mean agents can answer questions the typed surface didn't anticipate without forcing a schema change. Adding a new question is no-code; adding a new ENTITY TYPE is an ADR (D11).
- **Operator memory is structurally separated from canonical knowledge.** D15 closes a class of trust-leak failures by making operator memory unreachable through any agent path.
- **CLAUDE.md becomes accurate.** Today's "stdlib-only" prose is contradicted by the substrate's deps the moment Slice 1 ships. D3 + D4 align prose with reality.
- **Time-box supersessions formalize what was implicit.** cliff-ADR D4 commitment #6 read-mechanization and bootstrap-ADR mechanism-ceiling are now explicit successors, so future ADRs see clean precedent for similar narrow expansions instead of implicit drift.

### Harder

- **Five new dependencies enter the graph.** Pydantic, kuzudb, mistune, typer, fastmcp each have their own CVE surfaces, version trains, and breakage modes. D2's "deliberate-ADR" gate slows down future additions but doesn't address the existing five — ongoing maintenance cost.
- **FastMCP API stability.** FastMCP is a relatively young library; breaking changes in its API will require Slice-2-and-after rework. Mitigation: pin to specific minor version in `pyproject.toml`; update via deliberate ADR when the substrate program needs a newer feature.
- **Role_guard policy table grows substantially.** Today's table has 4 phase-policy entries; D8 adds knowledge-source deny rules for each phase × locked-down sources. Slice 3 extends to all four phases. Maintenance cost of the policy table grows with corpus size.
- **`AGENT_ENVELOPE` extension touches more orchestrator code.** Today only phase-3-implementer reads `AGENT_ENVELOPE`. D9 extends this to all phases, requiring orchestrator changes (Slice 2 ships these for phase-1-writer; Slice 3 for the rest). Risk of regression in existing phase-3-implementer behavior.
- **Snapshot SHA capture adds one git call per phase.** Negligible (~5 ms), but introduces a new per-phase orchestrator-side I/O point. New failure mode handled in D12 (sentinel + warning).
- **No migration path for existing phase agents that read canonical sources.** Slice 2's lockdown for phase-1-writer means EVERY existing phase-1-writer call that read `docs/ARCHITECTURE.md` directly must either (a) move to MCP query, or (b) get an envelope grant. Slice 2's plan explicitly handles this transition for phase-1-writer; Slice 3 handles phases 2-4. Plans must be reviewed for backwards-compatibility on a per-phase basis.
- **D9 abuse log is one more append-only file under `.claude/`.** Joins `d1-bypasses.log`, `d3-bypasses.log`, `adr-editorial-fixes.log`. Operator-side maintenance burden if logs grow large.

## Alternatives Considered

### Alternative A: Substrate via direct Python imports (no MCP)

Phase agents `import scripts.cairn_query` and call its functions directly.

**Rejected because:**
- Defeats cost-reduction: the agent's context still includes the cairn_query source code (~50 KB) to know what's available. MCP's process boundary keeps that out of context.
- Defeats structural lockdown: an agent that can `import` cairn_query can equally `import` anything else; role_guard's deny list would have to grow to forbid each import path, which doesn't scale.
- Doesn't enable cross-process snapshot pinning (D12) cleanly — each agent process has its own LRU(8), no shared cache, no shared SHA.
- Doesn't compose with future remote-substrate cases (e.g., a CI process querying the substrate without spinning up Python).

### Alternative B: Substrate as on-disk JSON cache (no kuzudb, no MCP)

Extract the corpus to a JSON file at every commit; phase agents read JSON.

**Rejected because:**
- No graph queries: path_bindings (e.g., "what entities reference `scripts/slice_orchestrator/lifecycle.py:480`?") becomes either an O(n) scan or a custom indexer — re-implementing kuzudb badly.
- No ad-hoc query: the Cypher escape hatch (D10) requires a query engine. JSON+jq covers some cases but not relational ones.
- No structural lockdown: JSON is a file like any other; role_guard would need to deny the JSON path, and agents could re-derive the JSON from source markdown trivially.
- Cost reduction is partial: JSON is smaller than markdown, but agents still must learn the JSON schema (context cost) and execute their own filters (correctness risk).

### Alternative C: RAG over markdown (vector embeddings, no graph)

Embed markdown chunks; phase agents query by similarity.

**Rejected because:**
- Wrong tool for the problem: cairn's queries are precise (lookup-by-id, path_bindings, structured Cypher), not similarity-based. "What's INV-008's invariant-check block?" has a deterministic answer; embedding similarity is fuzzy.
- No structural integrity: vector search hides the corpus's internal references; an agent cannot tell if its retrieved context has stale data or has missed a related entity.
- No round-trip validator equivalent: vector embeddings don't have a "this fails extraction" failure mode that a CI gate can rely on.
- Higher infra cost: embedding model + vector DB for a corpus of <100 ADRs and <50 lessons is over-engineering.

### Alternative D: Status quo — no substrate

Ship no substrate; phase agents continue reading source markdown.

**Rejected because:**
- Cost-reduction goal is unmet. Lever-2 baseline ($18.71/slice) is the price floor without intervention; the substrate program targets ≥50% reduction.
- The structural-lockdown property (D8/D16) cannot be achieved without an alternative knowledge surface for agents to use — without the MCP, locking down direct reads would simply prevent agents from accessing the knowledge they need.

### Alternative E: Hybrid — substrate as MCP, but with prompt-only lockdown

Ship the MCP and phase-agent prompts that say "use the MCP, don't read source files," but no role_guard enforcement.

**Rejected because:**
- Empirically inadequate (L-005 skill-coordination-tax pattern). Prompt-level "discipline" reliably degrades under context pressure; phase-3-implementer's existing prompt-level constraints have failed in field cases.
- The structural lockdown's cost-reduction guarantee (D8/D16) becomes aspirational rather than enforced.
- Disagrees with `compression-infrastructure-bootstrap`'s rationale: that ADR specifically introduced role_guard.py because prompt-level enforcement was insufficient.

### Alternative F: Split into three ADRs (deps, MCP, lockdown)

Ship `python-dep-policy`, `cairn-substrate-mcp-adapter`, and `agent-context-lockdown` as three independent ADRs.

**Rejected because:**
- The three commitments are load-bearing for one another (per Context above): the dep set authorizes FastMCP and pydantic; the MCP gates the lockdown's enforceability; the lockdown gates the cost-reduction value-prop. Splitting forces three sequential ADRs with cross-reference dependencies, where the second waits on the first and the third waits on the second.
- Supersession granularity argument cuts both ways: dep policy and lockdown stance are likely to evolve at different cadences, but the cost of bundled supersession (rewriting one ADR vs three) is lower than the cost of three sequenced ADRs that each must justify the bundle they're part of.
- D3/D4 (CLAUDE.md amendment + Rust-target retirement) are technically independent of the substrate program, but they are the natural prose effect of D1 + D6 — splitting them out would create a `python-dep-policy` ADR whose only Decision is "amend CLAUDE.md to match this co-landing ADR's dep set," which is empty paperwork.

### Alternative G: MCP via SSE or websocket transport instead of stdio

Run the substrate as a long-lived HTTP daemon (SSE) or websocket server; phase agents connect over network.

**Rejected because:**
- Adds daemon-lifecycle management (start/stop, port allocation, crash detection) that v1's per-slice spawn use case does not need.
- Adds authentication concerns (any-client-on-port can query); stdio's parent-process authority is sufficient for a local-only substrate.
- Worktree story is harder: each worktree's phase agent would need to know which port the substrate listens on; stdio's parent-process inheritance solves this for free.
- Cost-reduction claim depends on negligible per-call overhead; stdio JSON-RPC is cheaper than HTTP + framing.

## Risk Register

- **Risk: FastMCP releases a breaking API change mid-Slice-3.** Slice 2 ships the FastMCP adapter; Slice 3 extends prompt+lockdown across phases. A FastMCP breaking change between those slices would force adapter rework. **Mitigation:** D1 specifies version constraints; Slice 2 pins FastMCP to a minor version. Breaking changes in pinned versions are operator-visible at `uv sync` time. New ADR per D2 if version bump is needed.

- **Risk: kuzudb's Cypher dialect drift across versions.** Kuzudb is young; its Cypher coverage may shift between versions. **Mitigation:** D14's CI validator catches extraction failures; query failures in agent tools surface as MCP errors, not silent wrong answers. Operator can roll back the version pin via `pyproject.toml`.

- **Risk: D8 lockdown breaks an existing phase-agent workflow that legitimately needed canonical-source reads.** **Mitigation:** D9's envelope-grant mechanism. Slice 2's plan explicitly enumerates phase-1-writer's known canonical-source reads and either routes them through MCP or grants envelope. Slice 3 does the same per-phase. CI tests assert the lockdown works AND that envelope-grants succeed when declared.

- **Risk: D8 lockdown affects pipeline-substrate sessions (`/refresh-architecture`, `/integration-sweep` close-time commits).** D8's scope clause defaults role_guard to allow when `AGENT_ROLE` is unset, which is the case for these sessions. **Mitigation:** sessions that DO inherit `AGENT_ROLE` (e.g., a future skill that runs as a phase agent) are explicitly responsible for declaring envelope grants if they need to read locked-down paths. The `/refresh-architecture` D1 dedicated-session contract is preserved verbatim — no `AGENT_ROLE` is set, no policy applies. CI tests cover this seam.

- **Risk: D9 envelope-grant abuse hollows out D8.** Operators may declare paths in envelope as a habit, never adopting MCP query. **Mitigation:** D9's mechanical 3-in-10 rolling-window log + stderr warning. The warning is advisory, not blocking; intentional repeated grants (e.g., a slice that legitimately edits ADRs three times in 10 slices) are not blocked, but the operator sees the signal and can either ignore (if intentional) or amend D6 to add a tool (if a missing-tool pattern).

- **Risk: D12 git-SHA capture under unusual git states.** Sub-clauses cover worktrees, detached HEAD, shallow clones, and `git rev-parse` failure. **Mitigation:** sentinel snapshot fallback + cache bypass. Substrate correctness depends on extraction (which reads from working tree, not git history), so sentinel-mode degrades performance, not correctness.

- **Risk: D15 creates a class of unreviewable operator-memory leaks via copy-paste.** D15 prevents MCP-level access; it cannot prevent an operator from manually copy-pasting memory content into a slice's `intent.md`. **Mitigation:** the boundary is structural at the agent-tool layer, advisory at the human layer. The operator-memory file format itself flags entries with `type: feedback|user|project|reference` so an operator considering copy-paste sees the trust class.

- **Risk: D11's promotion checklist is too strict and parks legitimate entity proposals indefinitely.** **Mitigation:** the checklist is a default, not an absolute. A future ADR can amend D11 to lower the bar (e.g., 1 cross-workflow consumer + 1 future-planned consumer) if the v1 standing-set entities prove the model.

- **Risk: Provisional → firm transition cost.** This ADR is firm. If field experience reveals an unanticipated failure mode in any of D1/D6/D8/D11, retraction requires a superseding ADR — higher cost than retracting a provisional ADR. **Mitigation:** the firmness is appropriate per the design-doc's framing — these decisions are architectural commitments where the supersession path is the *correct* mechanism for change, not an obstacle. Provisional firmness on architectural commitments would create false ambiguity ("is this real or are we just trying it out?") that operationally degrades the cost-reduction value-prop's enforceability.

- **Risk: Time-box supersession cascade.** This ADR partially supersedes cliff-ADR D4 commitment #6 and bootstrap-ADR §47/§69/§84. A future ADR that re-tightens canonical-knowledge access (e.g., to lock down Bash too) would itself need to traverse these supersessions. **Mitigation:** supersession is the documented change path; the precedent set by `parallelism-v1` (commitment #2) and this ADR (commitment #6 read-mechanization) means future expansions of role_guard's policy table follow a known protocol. The ADR chain remains coherent.
