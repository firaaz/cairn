# Part 5: Meta-Evolution Layer

**Date:** 2026-04-18
**Gates:** Part 0 ADR; some sub-slices gate on F6
**Estimated:** ~5 slices
**Deployment:** Mixed — S2 (invariant registry) and S4 (doc tiers) pre-F6; S1 (telemetry), S3 (validator), S5 (multi-repo) benefit from or require F6.

## Intent

Elevate cairn from "methodology described in prose" to "methodology mechanically verifiable + evidence-fed." Make future structural decisions (phase compression, policy tuning, role granularity) data-driven, not guessed.

## Sub-slices

### S1 — Continuous slice telemetry + auto-dogfood-log

**Problem:** Cairn's spec evolves on incidents (dogfood run, sweep finding), not on continuous data. Every future structural decision is currently guessed.

**Change:** Each slice auto-records timing, gate-count, context-cost, human-touch events into `docs/plans/measurements/<slice-id>.yaml`. Hook (PostToolUse or SessionEnd-equivalent) writes data points; a compaction job rolls them into aggregates.

**Telemetry schema (v0):**
```yaml
slice_id: identifier-scheme/slice-and-feature-rename
branch: feature/identifier-scheme
started_at: 2026-04-17T12:00:00Z
phases:
  - phase: 1
    duration_seconds: 847
    tool_calls_total: 42
    tool_calls_by_type: { Read: 20, Write: 3, Edit: 8, Bash: 11 }
    gate_prompts_total: 5
    gate_prompts_auto_approved: 3
    gate_prompts_manual: 2
    subagent_invocations: 1
    context_tokens_peak: 30600
    phase_boundary_commit: af660a5
  - phase: 2
    ...
human_touch_events:
  - t: "..."
    type: approval
    worker: main
  - ...
handoff_verifier_fires: []
```

**Auto-dogfood-log:** A second hook on slice-complete reads the slice's telemetry + artifacts, writes one entry to `docs/dogfood-log.md` using a structured format. Uses `lesson-extractor` (Part 4) for the "pain points" section.

**Slice:** `part-5-s1-telemetry`.

**Dependency:** F6 makes this robust (daemon owns event log); pre-F6 a lightweight hook-based emitter works but with gaps.

---

### S2 — Invariant registry

**Problem:** Invariants are currently prose embedded in `docs/ARCHITECTURE.md` + referenced ADRs. No machine-readable registry. `invariant-preflight` (Part 1 A4) parses prose as a fallback; it's fragile.

**Change:** Extract to `docs/invariants/<id>.yaml`, one file per invariant:
```yaml
id: INV-004
name: slice-envelope-locked
statement: "No tool-call with Edit or Write may target a path outside the current slice's envelope."
referenced_by: [adr-001-pipeline-framework, adr-005-context-discipline]
enforced_by:
  - hook: scope-guard.sh
  - test: tests/unit/test_feature_scope_guard.py
  - doc: docs/operational-reference.md §Envelope
firmness: firm
history:
  - date: 2026-04-11
    action: established
    adr: bootstrap-exception
```

`docs/ARCHITECTURE.md` regenerates its invariants section from the registry via `scripts/refresh_architecture.py` (already exists; extend it).

**Slice:** `part-5-s2-invariant-registry`.

**Migration:** One-shot script reads current ARCHITECTURE.md + ADRs, extracts each invariant, writes a file. Human reviews. No semantic change.

---

### S3 — Methodology validator

**Problem:** No end-to-end consistency check across skills + ADRs + features + invariants + hooks. `validate_architecture.py` exists but only checks ARCHITECTURE.md coherence.

**Change:** `scripts/validate_methodology.py` extends `validate_architecture.py` with:
- Every skill's frontmatter declares Tier 1 reads — each file exists.
- Every ADR's `referenced_by` + `supersedes` pointers resolve.
- Every feature's slices have unique IDs.
- Every hook in `.claude/settings.json` matches a script that exists.
- Every invariant in the registry is referenced by ≥1 ADR and has a stated enforcement mechanism.
- Every agent in the roster has a system prompt file.
- Schema drift: `slice.yaml`, `sweep.yaml`, feature files conform to their schemas.

**Invocation:** Runs in CI-equivalent (pre-commit hook at slice close; integration-sweep pre-flight). Also manual `/validate`.

**Slice:** `part-5-s3-methodology-validator`.

---

### S4 — Doc-tier declaration

**Problem:** Tier discipline (when to load a doc) lives in skill prose ("DO NOT auto-load spec-v1"). Drift is invisible.

**Change:** Every `.md` doc carries a `tier:` frontmatter field:
- `tier: 0-always` — auto-loaded by all Claude sessions in the project (CLAUDE.md).
- `tier: 1-session-entry` — loaded at session start (operational-reference.md).
- `tier: 2-phase-input` — loaded per phase declared inputs (ADRs referenced in intent.md).
- `tier: 3-decision-only` — loaded during `/decision` phases (spec-v1.md).
- `tier: 4-reference` — load on demand, no automatic loading.

Session-start hooks + `/catchup` obey these tiers mechanically. Methodology validator (S3) asserts every doc carries the field.

**Slice:** `part-5-s4-doc-tiers`.

**Migration:** One-shot pass over all .md files. Map current loading behavior to tier. Reviewed.

---

### S5 — Multi-repo slice protocol + decision-note tier

**Problem 1:** When cairn + downstream consumer both need coordinated changes (API breaking), no protocol. Manual juggling of two worktrees.

**Problem 2:** Not every decision earns a full ADR (Phase 0-6, 5 subagents, stress test, propagation). Middle ground missing.

**Change 1 — Multi-repo slice:**
```yaml
slice_id: cairn/api-hardening + complex-rag-analysis/api-migration
paired: true
repos:
  - path: ~/Developer/lab/cairn
    envelope: [scripts/validate_architecture.py, docs/adr/api-hardening.md]
  - path: ~/Developer/lab/complex-rag-analysis
    envelope: [src/integration/cairn_client.py]
merge_gate: both  # both must merge atomically or neither
```

Two worktrees share one `slice.yaml` (stored in the "primary" repo, by convention cairn). Phase boundaries sync across both — you can't finish Phase 3 in cairn if complex-rag-analysis's Phase 3 tests haven't gone green.

**Change 2 — Decision-note tier:**
- `docs/decisions/<slug>.md` for one-paragraph decisions, carrying `firmness: light`.
- Schema: id, name, date, decision (one paragraph), rationale (one paragraph), supersedable (bool).
- No Phase 5 required. Promotable to ADR if later pressured.
- Used for: "we'll use dataclasses for config rather than pydantic," "slice status labels will be bare names not numbered," — decisions that need a record but don't warrant adversarial review.

**Slice:** `part-5-s5-multi-repo-decision-notes`.

**Split option:** These can be separate slices if the multi-repo work pulls ahead (e.g., if a breaking change is imminent).

## Slice breakdown

- **S1** — Telemetry hook + auto-dogfood-log agent integration.
- **S2** — Invariant registry schema + migration.
- **S3** — Methodology validator script + CI integration.
- **S4** — Doc-tier frontmatter + loader updates.
- **S5** — Multi-repo slice protocol + decision-note tier. May split.

## Cross-cutting

1. **Schema discipline.** Every new YAML file (telemetry, registry, coupling-clusters, permission-policy, transitions) has a versioned schema. Validator (S3) enforces schema-match.
2. **Backward compat.** Existing ADRs + ARCHITECTURE.md remain authoritative during migration. New files derive-from / reference-back to existing docs. No break.
3. **Migrations are one-shot scripts.** Extract + review + commit. Not embedded in skill code.

## Success criteria

1. Any future structural decision about cairn has telemetry evidence: "we have N slices of Phase 2 timing showing a bimodal distribution; compression is justified for cluster A, not cluster B."
2. Invariant drift is mechanically detectable. Validator fires on any invariant whose enforcement mechanism disappears.
3. Doc loading is predictable: from tier field, you know when this doc enters context. No surprise loads.
4. Breaking cairn changes are impossible without conscious multi-repo slice planning — because without the paired `slice.yaml`, the sweep catches the consumer drift.
5. Low-stakes decisions stop being either (a) un-recorded or (b) over-ceremonialized as ADRs. Decision-notes cover the middle.

## Out of scope

- A `/revise-spec` protocol for modifying spec-v1.md itself. Raised as Program-level open question #5.
- Cross-organization coordination (if cairn ever has downstream consumers across teams). Single-user-multi-repo only, for now.
- Integration with external systems (GitHub PRs, CI status, issue trackers). Seams can be left but no implementation.

## Open questions

1. Telemetry PII: `docs/plans/measurements/` is committed to git. Do we want every tool-call count public, or does the telemetry go to `.claude/measurements/` (local/gitignored) with opt-in sync?
2. Invariant registry vs ADR duplication: if an invariant's statement differs between the registry YAML and the ADR body, which is authoritative? Propose: registry is derived; ADR body is canonical; validator asserts coherence.
3. Doc-tier field: should `CLAUDE.md` carry a tier? It's auto-loaded by Claude Code natively — tier metadata is descriptive, not enforcing. Either is fine.
4. Multi-repo slice: atomic merge gate ("both or neither") is hard across independent git repos without a coordinator. Does this need F6 daemon extension to handle pair-merges? Probably yes.
5. Decision-note frontmatter: should decision-notes have id: as mechanical like ADRs? Proposed yes, for consistency with identifier-scheme.
