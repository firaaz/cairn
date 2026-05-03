---
id: pipeline-substrate-naming
status: accepted
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: []
date: 2026-05-02
---

# pipeline-substrate-naming: Pipeline-Substrate Commit Class — Definition and Registry

## Status
Accepted

## Date
2026-05-02

## Context

INV-001 (`bootstrap-exception`) commits cairn to a pipeline-first rule: every commit after the bootstrap commit `25ff49f` flows through `/decision` or `/start-slice`. The invariant prose lists no other exception.

Operational reality has produced a third class of commit that is neither slice-phase (`slice:`, `handoff:`) nor decision-driven (an ADR landing inside a slice), and that is also not a violation: commits emitted by pipeline-substrate tools — `/integration-sweep` (`sweep:`), `/refresh-architecture`, post-merge cleanup, and a small handful of others. `docs/lessons.md` L-001 names these as **pipeline-substrate operations** and explicitly identifies the unresolved debt: *"context-discipline-protocol does not name sweep commits as pipeline-substrate operations"* (L-001:17).

This unresolved debt is load-bearing for `invariant-binding-strategy`: a true machine-check on INV-001 must classify every commit subject between `25ff49f` and HEAD, and pipeline-substrate commits must be a recognized legitimate class or the binding self-violates on its own substrate. The binding ADR cannot land until the class is named.

This ADR closes the L-001 debt. It defines the pipeline-substrate class, enumerates its current member tools and commit-subject prefixes, and establishes the registry mechanism that future tools join through.

## Decision

### D1 — The pipeline-substrate commit class is named

A **pipeline-substrate commit** is a commit emitted by a named cairn substrate tool (not directly by an operator) whose purpose is to maintain the pipeline itself rather than to produce slice or decision output. Pipeline-substrate commits are a legitimate exception to INV-001 alongside slice-phase and decision-recording commits.

**Authorization is by name, not by subject prefix alone.** A commit is pipeline-substrate iff (a) its subject prefix appears in the registry (D2) AND (b) it was emitted by the registered tool. The registry pairs each prefix with its owning tool so that an operator-typed `sweep: …` does not bypass INV-001.

### D2 — Registry shape and location

The pipeline-substrate registry lives at **`.claude/pipeline-substrate-registry.yaml`** with the schema:

```yaml
entries:
  - prefix: "sweep:"
    tool: "/integration-sweep"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
  - prefix: "handoff:"
    tool: "/integration-sweep | /start-slice (boundary handoffs)"
    owner-adr: pipeline-substrate-naming
    since: 2026-05-02
  # ... full list per D3
```

Each entry MUST include `prefix`, `tool`, `owner-adr`, `since`. Optional `notes` field permitted.

### D3 — Initial registry contents (effective 2026-05-02)

| Prefix | Owning tool | Notes |
|---|---|---|
| `slice:` | `/start-slice` | Slice-phase boundary and close commits. Slice-phase, not strictly substrate, but registered for completeness. |
| `handoff:` | `/start-slice` (phase boundary), `/integration-sweep` (sweep handoff) | Phase boundary handoff or sweep handoff. |
| `sweep:` | `/integration-sweep` | Integration sweep close commit. |
| `bootstrap:` | one-shot at `25ff49f` per `bootstrap-exception` ADR | Single historical commit; no future entries. |
| `feat:` | `git merge --squash` per merge protocol | Feature-to-dev squash-merge subject. Tool is git itself; per L-015 the merge protocol is the operator. |
| `docs:` | `/refresh-architecture`, ADR landings inside slices | Refresh-architecture emits `docs:`; ADR landings during a slice are inside slice-phase commits and inherit slice-class authorization. Operator-typed `docs:` outside these contexts is a violation. |
| `fix:` | post-sweep substrate fix-ups initiated by `/integration-sweep` Step 6.5 | Constrained: must reference a sweep, must touch only files named in sweep-results. Operator-typed `fix:` outside this context is a violation. |
| `chore:` | post-merge cleanup hooks | Rare. Documented per emission. |
| `test:` | Phase 2 RED commits (slice-phase) | Slice-phase via `/start-slice` Phase 2; not substrate proper but registered to prevent walker confusion. |

### D4 — Registry update mechanism

Adding a new entry requires either:
- **An ADR amendment to this ADR** (sibling registry-amendment ADR; this ADR is append-only per repo policy), OR
- **A row added by `/refresh-architecture`** under operator authorization (recorded in the refresh's commit message), restricted to entries whose `tool:` is itself a registered cairn substrate tool. Net-new tools must go through the ADR path.

Removing an entry always requires an ADR — entries cannot be silently dropped.

### D5 — Authorization-by-name verification

INV-001's binding (specified in `invariant-binding-strategy`) MUST verify both halves of the authorization-by-name pair. A commit subject `sweep: backfill` produced by an operator (not by `/integration-sweep`) is a violation. The verification mechanism is conservative:
- For prefixes with a deterministic emitter (`/integration-sweep`, `/refresh-architecture`, `git merge --squash`), the binding verifies the commit's authorship/file-shape is consistent with the registered tool's contract (e.g., `sweep:` commits MUST modify files under `.claude/sweep-results/` AND `.claude/sweep.yaml`).
- For prefixes where verification is structurally infeasible (e.g., `feat:` from human-initiated squash-merge), the registry entry is treated as best-effort and the binding accepts the prefix; the trade-off is recorded as a residual risk in `invariant-binding-strategy`'s F2 mitigation.

## Consequences

### Easier
- INV-001 binding becomes implementable.
- Future substrate tools (e.g., a `/cleanup` or `/migrate` command) have a defined path to legitimacy: register in the YAML via ADR amendment, document the emitter contract.
- Forensic audits of "is this commit legitimate" become mechanical: walk registry → check prefix → check emitter contract.
- L-001:17 debt closed.

### Harder
- Adding new substrate tools is now ADR-gated. Casual `chore:` commits emitted ad-hoc by future scripts will fail INV-001 unless registered.
- The registry is a new piece of process state to keep current. Drift (registry stale relative to actual emitter behavior) is the primary failure mode and is named in `invariant-binding-strategy`'s F1 risk.
- Squash-merge `feat:` commits are accepted on prefix alone (D5 trade-off). A direct `feat:` commit by a confused operator passes the binding.

## Alternatives Considered

**Tag commits with a trailer at emit time** (`Pipeline-Substrate: /integration-sweep`). Rejected: substrate tools today are bash + Python that don't reliably append trailers, and retrofitting every emitter is heavier than the registry. The registry is the canonical source; tools merely emit subjects matching their registered prefix.

**Author-based classification** (`GIT_AUTHOR_NAME=cairn-pipeline`). Rejected: cairn does not own author identity (operators commit under their own names); coupling INV-001 to author identity would conflate pipeline-substrate-ness with bot identity, which cairn explicitly does not have.

**No naming — INV-001 stays advisory forever.** Rejected: contradicts D2's v1-defense-D2 commitment in `cliff-failure-mode-and-v1-defenses` and leaves `cairn-substrate-and-fastmcp`'s validator commitment unfulfilled.

## Risk Register

- **Registry rot.** Mitigation: D4 requires ADR or `/refresh-architecture` for additions; pipeline-substrate-registry edits surface in ARCHITECTURE.md so drift is visible.
- **Operator-typed substrate prefix.** A confused operator committing `sweep: x` directly bypasses the binding for prefixes that lack structural verification (D5). Mitigation: documented in `invariant-binding-strategy` F2 and accepted as residual risk.
