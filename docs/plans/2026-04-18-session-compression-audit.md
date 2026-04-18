# Session-Compression Audit — `efficiency-program-afternoon-wins/all-seven`

**Date:** 2026-04-18
**Status:** Input to future brainstorm — nail down context isolation before running Part 0 or any ADR-class slice.
**Slice commits:** `5e2194f` (intent) → `b6850bd` (validation) → `b7c3e5e` (implementation) → `92a7b15` (complete) → `7798561` (handoff).

## Context

The slice shipped seven afternoon-wins items in ~1 hour of wall time. A faithful cairn run would have required 4 sessions (one per phase), roughly 4–5 hours including /catchup/handoff overhead. The compression mechanism: one orchestrator session dispatching subagents as fresh-session proxies — Skeptic (Phase 2), five parallel Builders (Phase 3), Auditor (Phase 4). Each subagent received a bounded contract; the orchestrator held every phase's output simultaneously.

The delivered items are mechanically correct (77/77 slice tests green, validator clean, INV-002/003/004 preserved). The question is whether the compression pattern is safe methodology or a fast-but-contaminated approximation.

## Self-assessment vs independent audit

The orchestrator wrote a first-order analysis identifying 4 incidents. A fresh independent auditor (no access to orchestrator reasoning, artifacts-only from git) identified 6 findings. The diff is the contamination signal.

### Findings

| # | Boundary | Leak | Shape | Severity |
|---|---|---|---|---|
| F1 | Phase 3 → Phase 1 (retroactive) | Envelope amended mid-Phase-3 to legalize `scripts/render_status.sh` after Phase 2 tests hard-coded the path | intent-drift-to-match-test (three-way causality collapse) | HIGH |
| F2 | Phase 1 → Phase 2 | Skeptic's `CANDIDATE_HOOK_NAMES` / `CANDIDATE_RENDERER_PATHS` tuples enumerate Phase 3's affordance space; Builder A chose `role-cheatsheet.sh` **because** it was in the candidate set | validation-shapes-implementation-affordance-space (novel) | MEDIUM |
| F3 | Phase 4 → complete | `integration/sweep-notes.md` never committed; Auditor file:line evidence lives only in commit-message body at `92a7b15` | post-hoc-narrative-framing (evidence outside declared artifact) | HIGH |
| F4 | Phase 3 (self-contradictory) | `scripts/verify_handoff.sh` check (b) requires `handoff-phase-<N>.md`; this slice produced none (single-session compression skipped phase-commit handoffs) — verifier would fail its own slice | self-contradictory-contract (novel) | MEDIUM |
| F5 | complete → handoff | Handoff cites specific `1-intent` vs `intent` label drift from `implementation/notes.md`; notes.md deleted at `92a7b15`, so handoff content traces to ephemeral orchestrator memory | post-hoc-narrative-framing via trans-phase memory | MEDIUM |
| F6 | Phase 4 → complete | D3 rolling-window: 8 bypass entries in last 10 slices (far past the 3+ warning threshold). Neither commit body nor handoff surfaces the count; selective framing as "2 new this slice" | protocol-faithful-process failure (selective counting) | HIGH |

### What the orchestrator got RIGHT
F1 (envelope), F5 (handoff distillation), parts of F6 (bypass framing).

### What the orchestrator MISSED
F2 (candidate-set leak), F3 (missing Phase 4 artifact), F4 (self-contradictory verifier), and the rolling-window count in F6 was buried not surfaced.

### What the orchestrator OVERSTATED
- Orchestrator-authored renderer: LEGAL per within-slice-parallelism carve-out (parallelism-v1 memory). Only the envelope amendment was the violation.
- "Single-session compression" framing: phase-lock D2 requires artifact isolation, not session death. If subagents are truly isolated, compression is orthogonal to the correlated-error defense.

## Actionable outputs

### Three follow-up slices (gate next `/integration-sweep`)
1. **envelope-immutability-guard** — scope-guard tightening; Phase-3 edits to `intent.md` require `AMEND_INTENT=1` and log to `envelope-amendments.log`. Mechanical analog of `envelope-expansions.log`.
2. **phase-4-sweepnotes-required** — `scripts/verify_handoff.sh` check (d): when slice is closing, `integration/sweep-notes.md` MUST exist at the close commit. Auditor evidence survives in-tree.
3. **d3-rolling-window-surfacing** — rolling-window count in `/status` dashboard (Item 7 already ships; add one line) and `/integration-sweep` preflight. Commit-message prose does NOT count as surfacing.

### One ADR for Part 0
**`phase-artifact-immutability-and-evidence-persistence`** — three decisions:
- **D1:** Phase 1 envelope is append-only within a slice; appends require machine-readable marker + rationale commit; overwrite/reorder prohibited.
- **D2:** Phase 4 evidence is committed-artifact-first — `sweep-notes.md` must exist at close; commit message is a pointer, not a source.
- **D3:** Phase 2 candidate-sets must cite the `intent.md` line that authorized the ambiguity. No candidate set without a paper trail.

## Brainstorm seeds for next session

1. **Compression as sanctioned mode.** Is single-session subagent compression legal for zero-ADR / additive-reversible slices? What is the mechanical gate that prevents drift into ADR-class work? (Example: a precondition check that refuses compression if `adrs-referenced:` is non-empty or if any touched invariant has `firmness: firm`.)

2. **Orchestrator constraints.** If compression is sanctioned, what is the orchestrator forbidden to read? Concrete candidates: must not read subagent `approach.md`, must not read subagent implementation notes beyond ≤50-word summary, must receive subagent returns as `{commit-hash, pass/fail, ≤N-word summary}` only. This is analog of Tier 2 subagent contract but applied to phase subagents.

3. **Fleet-coordinator implication.** The coordinator architecture (`docs/plans/2026-04-15-fleet-coordinator-design.md`) has a central orchestrator dispatching workers. The orchestrator-holds-all pattern we just executed **is the coordinator pattern**. Every critique of the orchestrator here applies to the fleet coordinator once it ships. The coordinator MUST NOT read worker approach/notes; the coordinator IS the enforcer of artifact-only isolation. This audit is a dry run for F6 coordinator contract.

4. **Evidence persistence as a general principle.** F3 generalizes: any phase output declared in the protocol MUST exist as a committed artifact at close. The commit message is not a substitute. What other phases today rely on ephemeral agent reports instead of committed files? (Candidates: phase-3 `implementation/notes.md` is committed but deleted at close — is that correct? Should it survive as `docs/lessons.md` distillation?)

5. **Candidate-set discipline.** F2 is subtle. Phase 2 tests often need to accept multiple valid implementations (the point of intent-not-impl). But enumerating the set IN THE TEST leaks the set into Phase 3 as an affordance constraint. Alternative shapes: (a) Phase 2 writes contract-only tests (pattern-based, behavioral); (b) Phase 1 intent explicitly enumerates authorized candidate paths in a `candidate-sets:` YAML field. Option (b) pushes the set into the protocol-visible artifact.

6. **Middle-management framing.** The emergent shape — orchestrator, specialist subagents, audit chain, handoff budgets, invariant registry — is organizational design for AI teams. Cairn is becoming the methodology for running an AI team of one operator + N LLMs. The "company" shape is not a bug; it is the intended outcome of solving correlated-error defense at scale. But organizational pathologies (information hoarding at middle management, selective reporting up, rubber-stamp auditors) have LLM analogs. This audit caught four of them.

## Process takeaway

A contaminated self-reviewer catches some but not all of its own leaks. Independent audit earned its keep (found F2/F3/F4 that the orchestrator missed) AND calibrated the orchestrator's overstatements (legal parallelism framed as violation). Both moves — surface AND ground-truth check — are required. Neither alone is sufficient.

## Pointers

- Slice commits: `5e2194f` (intent), `b6850bd` (validation), `b7c3e5e` (implementation), `92a7b15` (complete), `7798561` (handoff).
- Efficiency program: `docs/plans/2026-04-18-efficiency-program/` — Parts -1 through 6. Part -1 is this shipment; Part 0 is the ADR principles slice that will consume this audit.
- Fleet coordinator design: `docs/plans/2026-04-15-fleet-coordinator-design.md` — orchestrator contract will compose with D2/D3 outputs from this audit.
- parallelism-v1 ADR: carve-out for within-slice subagents; v2+ time-box applies to cross-slice only.
