---
id: cairn-thin-substrate-direction
name: "Cairn thin substrate — six load-bearing primitives at three time scales"
status: accepted
firmness: provisional
supersedes: []
supersedes-sections: []
superseded-by: null
topic: architecture
invariants-touched: []
date: 2026-05-20
---

# Cairn thin substrate — six load-bearing primitives at three time scales

## Status

Proposed. Provisional firmness. Body subject to amendment until flipped to `accepted`. Companion trials plan: `docs/plans/2026-05-20-cairn-thin-substrate-trials.md`.

**Accepted 2026-05-30** via the cairn-identity `/decision` arc (`.claude/skill-runs/cairn-identity-decision-2026-05-30/`) — premise-grounding (D2.5) elevated to keystone (D7), charter-cycle direction reconciled (D8), the premise-grounding assertion built and tested.

## Date

2026-05-20

## Context

Three forces converge here.

**M4 retired the substrate** (cairn-substrate-and-fastmcp-superseded, 2026-05-07). The typed-knowledge graph, the FastMCP wrapper, and kuzu/fastmcp deps are gone. Cairn at HEAD is the dispatch skill, hooks, slash commands, validator, ADR corpus, and templates — much smaller than pre-M4.

**The 2026-05-13 reframe** (docs/plans/2026-05-13-cairn-as-interaction-protocol.md) recast cairn as an interaction protocol: contracts at every artifact boundary; property-based testing as the falsification surface; micro-contract delegation. Trial selection was deferred.

**A May 2026 plan** (`govllm-trial/CAIRN_PLAN.md`, authored downstream) proposed making cairn a "thin contract-and-decision substrate" composing with whichever AI coding tool the operator runs. Five load-bearing primitives. One aspirational claim (PBT-on-clauses). A three-trial sequence ending in dropping the four-phase pipeline.

Before accepting that direction, three load-bearing claims were empirically probed (parallel agent dispatch, 2026-05-20):

1. **EARS notation is LLM-authorable without prose leakage.** *Partially supported.* +25-33% ceremony surcharge; sharper on heavy/medium intents, ritualistic on light ones; ~50-60% of real `must-satisfy` clauses pass atomicity as-written. Failure mode found: EARS catches trigger/response clarity but does not catch universal-quantification-over-implicit-domain — authors can write grammatically-correct EARS that should fail atomicity, with no syntactic hook to catch it.

2. **PBT-on-clauses is the falsification surface that replaces Phase 2 Skeptic.** *Overclaim by ~2x.* Falsification mechanically works for ~30-40% of real clauses (mechanical predicates over synthesizable inputs). The remaining 60-70% are qualitative, process, cross-artifact, or SUT-is-oracle clauses that need judge agents, static analyzers, or single-shot integration assertions instead.

3. **Contract grammar alone defeats wrong-model propagation (Trial 3 of the proposal).** *Falsified.* The slice #25 counterfactual (a wrong-premise xfail at `tests/unit/test_root_resolver_migration.py:421-440` would have driven a wrong implementation past every cairn-simplified layer) shows no mechanical layer catches semantic-grounding failures. EARS, scope-split, role_guard, reversibility-guard, ADR corpus, and PBT-on-clauses all check internal consistency — none read source to challenge premises.

The trials plan carries the probes verbatim and the gating they imply.

This ADR records the direction in its amended form.

## Decision

### D1 — Cairn at layers 1–3; layer 4 is the host tool

Cairn governs three time scales:

| Scale | Solves | Mechanism |
|-------|--------|-----------|
| Per-action | Destructive ops, secret leaks, ADR mutation | Hooks (provider-agnostic shell/Python, JSON in/out) |
| Per-session | Intent drift, scope creep, wrong-model propagation | Contract grammar + envelope + scope-split + premise-grounding |
| Per-project (years) | Decisions forgotten, re-litigated, retconned | ADR corpus + identifier-scheme + mechanical supersession |

Layer 4 — elicitation, planning, execution, subagent dispatch — belongs to the host tool (Claude Code, Codex, Cursor, others with hook primitives). Cairn does not own layer 4. Composition, not competition.

Hook-portability is provider-dependent: enforcement-portable on hook-complete providers (Claude Code, Codex 0.117+); convention-portable elsewhere (Cursor's narrower hook surface; pre-hook providers).

### D2 — Six load-bearing primitives

Cairn's substrate is exactly these six things:

1. **Contract grammar.** `must-satisfy` / `must-not-violate` / `wrong-if` / `escalate-when` / `evidence`. EARS notation internal to `must-satisfy`. One clause per testable claim.
2. **Envelope.** Path-regex array declared in the intent file's frontmatter. Mechanically enforced per write by `role_guard.py`.
3. **Scope-split rule.** Atomic-primitive check on `must-satisfy`. Authoring-time hook. Atomicity exceptions named in D3.
4. **ADR corpus + identifier-scheme.** Append-only via `reversibility-guard.sh`; supersession via new ADR with `supersedes:`; `id:` immutable, `name:` mutable (identifier-scheme); `firmness:` field; AgDR-compatible optional `agent` / `model` / `trigger` frontmatter for AI-authored ADRs.
5. **Premise-grounding.** For any `must-satisfy` / `must-not-violate` clause that names a file path, regex, or specific source location, the contract includes an `evidence.premise:` field quoting the cited source text verbatim plus a one-line current-behavior label. A hook (call it `premise_guard.py`) mechanically diffs quoted text against actual source at intent-approval time; mismatch denies the session start. This primitive is *new* relative to the original plan; the slice #25 counterfactual showed the other five primitives do not catch semantic-grounding failures.
6. **Two enforcement hooks.** `reversibility-guard.sh` (destructive ops + secrets + ADR append-only) and `role_guard.py` (envelope enforcement). Plus the new `premise_guard.py` from D2.5. All provider-agnostic by construction; configured into the host's PreToolUse / pre-session hook surface.

PBT-on-clauses is *not* listed as a load-bearing primitive. It is one of several falsification mechanisms (D4).

### D3 — EARS for `must-satisfy`, with named exception classes

`must-satisfy` clauses are written in EARS notation (Ubiquitous / Event-driven / State-driven / Unwanted / Optional). The scope-split rule checks atomicity: a clause is atomic iff verifiable by a single tool call or single file check.

Four named exception classes do not have to be atomic but must be tagged:

- **`universal-set:`** — universal quantification over an implicit domain ("every consumer-facing surface", "all ADRs"). Must declare the set's enumeration source.
- **`regression-meta:`** — "existing behaviour unchanged" / regression-class meta-claims. Must declare the regression-detection mechanism (test suite, validator, hook).
- **`operator-bound:`** — clauses requiring operator judgment ("pointer-only, no narrative"). Must declare the rubric the operator applies.
- **`trivial-existence:`** — file-exists / file-contains-string clauses on small intents. May skip EARS structuring.

Clauses without a tag must pass atomicity. The exception system makes EARS adoption non-blocking on the ~40-50% of real clauses that don't fit the atomic-primitive rule cleanly. Without the exceptions, the rule fires on ~half of real intents on first authorship and operators learn to game it.

### D4 — PBT-on-clauses as one of several falsification surfaces

PBT-on-clauses is the falsification mechanism for mechanical-predicate clauses (envelope path matching, regex-allowlist invariants, ADR frontmatter shape, identifier-scheme parsing, supersession-graph acyclicity, force-push-flag detection, similar). Estimated coverage: ~30-40% of real `must-satisfy` clauses.

The remaining 60-70% require complementary mechanisms:

- **Judge agent (operator-bound or qualitative clauses):** the role previously called Phase 2 Skeptic. *Retained, not deleted.* A judge can be a fresh subagent or a checklist the operator applies; the role is preserved by the substrate even if its name changes.
- **Static analyzer (cross-artifact clauses):** validator scripts that walk the ADR corpus, supersession graph, identifier-scheme references. `scripts/validate_architecture.py` is the existing example.
- **Single-shot integration assertion (process clauses):** one-time runtime check at session close.

The substrate names *all four* mechanisms; intents declare which mechanism their clauses use via `evidence:`. PBT is not the universal falsification surface. The original plan's framing of PBT as "the falsification surface that replaces Phase 2 Skeptic" was an overclaim; this ADR scopes PBT correctly and preserves the judge role.

### D5 — ADR corpus is the load-bearing per-project artifact

The ADR corpus is the bet for long-term project memory. The other five primitives exist in service of feeding and protecting it.

Mechanical guarantees:

- **Append-only bodies** via `reversibility-guard.sh`. Frontmatter edits to `status:`, `superseded-by:`, `firmness:` lines are permitted; body mutations are denied. `ADR_EDITORIAL_FIX=1` is the typo escape hatch.
- **Supersession trail** via new ADR with `supersedes: <id>`. Real projects change their minds; the trail preserves history. Spec Kit's immutable-constitution shape is rejected — it does not match how real engineering projects evolve.
- **Identifier-scheme** (id immutable, name mutable). Renames don't break cross-references.

AGENTS.md / CLAUDE.md is a thin view of the corpus, not a parallel source of truth. Generation policy (manual vs. auto) is deferred.

### D6 — Migration is gradient and trial-gated

No big-bang refactor. The current four-phase TDD dispatch skill (`cairn-tdd-feature`) is *not* deprecated by this ADR. The migration sequence and trial gating live in the companion trials plan, which carries the empirical probes' findings and the gating they imply. Specifically:

- Trial 1 (contract block on handoff) is unblocked.
- Trial 2 (EARS in intent.md) is unblocked, gated on Trial 1 success.
- **Trial 3 (drop phase 1 derivation) is gated on `premise_guard.py` shipping first.** The slice #25 counterfactual showed Trial 3 is unsafe without premise-grounding; this ADR makes that gating durable.

The four-phase pipeline is retained until at minimum Trials 1, 2, and the premise-grounding implementation succeed under operator confirmation.

### D7 — Premise-grounding is the keystone; evidence-grounding is the identity

The six primitives (D2) are one move at different scopes: **force a load-bearing claim to bind to checkable evidence.** Hooks bind irreversible actions; the envelope binds writes; the append-only ADR corpus binds decisions; the validator binds cross-references. The one scope with no rent-collector was the **claim** — a premise about what the code or an ADR actually says — which is exactly the gap the slice-#25 counterfactual exposed: no layer reads source to challenge a premise.

**Premise-grounding (D2.5) is therefore not the sixth item in a list — it is the keystone.** Cairn's identity is *the layer that keeps AI-authored intent bound to verifiable evidence.* The cliff (the correlated-error / drift failure cairn targets, `cliff-failure-mode-and-v1-defenses`, `why-cairn.md`) is what happens when claims outrun their grounding — plausible-but-unchecked claims compounding until they surface at scale. Grounding is the mechanical defense, and it is what survives native runtimes (arc A: the per-dispatch isolation primitives are now native; the cross-slice evidence contract is not).

This **resolves, rather than defers,** the intent↔ADR alignment mechanism that `docs/plans/2026-05-22-cairn-identity-direction.md` §3 filed as unmechanizable-so-wait-for-N≥3-failures. You do not mechanize *semantics* (impossible under the closed validator-type whitelist, `invariant-binding-strategy`); you mechanize the *verbatim quote*. A clause that cites a source quotes it; the validator diffs the quote against live source; a stale, superseded, or fabricated reference breaks the build at authoring time.

**Built, not narrated.** The premise-grounding check ships as a `premise-grounding` validator assertion type (`scripts/validate_architecture.py`, a sibling of the existing `grep` assertion), bound by `tests/unit/test_premise_grounding.py` (grounded premise passes; stale, fabricated, or missing premise fails). It runs as a Check-D assertion on the existing hook+validator substrate — no new hook event. This is the load-bearing deliverable of the identity decision and the buildable core of D6's `premise_guard.py` gate.

**Honest limits.** Premise-grounding catches stale, fabricated, or missing grounding; it does *not* catch a correct quote the author misreads. It raises the floor mechanically; it does not eliminate semantic error. Authoring friction (≈+25–33% per the EARS probe, §1.1) is scoped to clauses that cite a specific source location — exactly where wrong-premise is both possible and catchable.

### D8 — Relationship to the charter-cycle direction (brainstorm-1)

The 2026-05-22 cairn-identity brainstorm (`docs/plans/2026-05-22-cairn-identity-direction.md`; `.claude/skill-runs/cairn-identity-brainstorm-2026-05-22/`) proposed replacing the four-phase pipeline with a "charter cycle." The 2026-05-30 identity `/decision` arc (`.claude/skill-runs/cairn-identity-decision-2026-05-30/`) adjudicated it against this ADR and split it:

- **The charter *primitive* is adopted** as an instance of D2.1's contract grammar (`goal` / `done` / `constraints` / `amendments` ≈ `must-satisfy` / `evidence` / envelope / append-only) — a layers-1–3 artifact cairn owns, and the natural carrier of D2.5 premise-grounding.
- **The charter *cycle* (formation dialogue, blind-worker dispatch, build≠check) is layer 4** — host-tool territory per D1. Cairn may *document* it as a preset; it is not substrate and is not shipped as identity.
- **"Goal-commitment vs input-reactivity" is recorded as a falsifiable sub-claim, not a co-equal identity value** — operator-self-reported, with no in-repo evidence (unlike the cliff/drift failures: `docs/lessons.md` L-012 / L-016 / L-022). Promotion trigger: N≥3 logged instances of a committed `goal:` whipsawing on a single message without an amendment (per `schema-amendment-threshold`). Until then, no per-turn re-injection hook is built.
- **Dropping the four-phase pipeline stays gated** per D6 (Trial E + `premise_guard.py`); the arc's pre-mortem (S1 unmeasurable-headline / S2 within-vs-cross-cycle axis mismatch / S3 build≠check-is-role-purity-not-decorrelation) is the recorded rationale. The firm phase ADRs (`phase-lock-and-role-declaration`, `phase-pipeline-evaluation`, `feature-slice-model`) and INV-003 are **retained** — methodology is orthogonal to the grounding identity, not superseded by it.

## Consequences

- **Six primitives is the new shape**, up from the original plan's five-plus-aspirational. Premise-grounding (D2.5) becomes a load-bearing mechanism, not a future amendment. ~30-60 LOC hook to build; same provider-agnostic shape as the existing two.
- **PBT-on-clauses ships as a *narrow* tool**, not a universal falsification surface. Operators authoring `must-satisfy` clauses pick the falsification mechanism (PBT / judge / static-analyzer / integration-assertion) via the `evidence:` field. Phase 2 Skeptic's role survives as the judge mechanism.
- **EARS adoption is gated on the exception-class system (D3).** Without exceptions, the atomicity rule fires on ~half of intents and produces ceremony without payoff.
- **The four-phase TDD dispatch skill stays.** Trial 3 (drop phase 1) is explicitly *not* approved by this ADR; the trials plan gates it on premise-grounding.
- **CLAUDE.md / AGENTS.md remain thin pointer indices.** The ADR corpus is source of truth.
- **The `govllm-trial/CAIRN_PLAN.md` document is superseded by this ADR** as the canonical record of cairn's direction. The downstream file may remain as historical context or be removed at the operator's discretion; this ADR does not require its deletion.
- **Provider-agnostic-by-construction is qualified, not absolute.** Enforcement-portable on hook-complete providers; convention-portable elsewhere. Documentation must surface this.

## Out of scope (anti-temptations recorded)

This ADR does NOT do the following. Each is a real direction that was considered and deliberately rejected.

- **No bidirectional spec↔code sync** (Tessl pattern). MDD-failure risk; track but do not adopt.
- **No SMT-solver requirements-consistency** (Kiro pattern). Heavy; revisit only if the contract corpus grows large enough that internal inconsistencies become a real problem.
- **No LLM auto-generation of TLA+ specs.** State of the art is 8.6% semantic correctness; not ready.
- **No mandatory multi-artifact pipeline** (Spec Kit pattern). One intent.md per session is the default; resist artifact multiplication.
- **No immutable-constitution articles** (Spec Kit pattern). The ADR corpus *with supersession* is the right shape; principles evolve.
- **No new orchestrator, MCP, daemon, or state layer.** M4 retired the substrate; this ADR does not re-add it.
- **No `/catchup`-equivalent built into cairn.** That is host-tool territory.

## References

- docs/plans/2026-05-20-cairn-thin-substrate-trials.md — companion trials plan with empirical probes verbatim
- docs/plans/2026-05-13-cairn-as-interaction-protocol.md — the reframe this direction extends
- docs/adr/cairn-substrate-and-fastmcp-superseded.md — M4 retirement of the FastMCP substrate
- docs/adr/identifier-scheme.md — id/name two-field model invoked here
- docs/adr/phase-pipeline-evaluation.md — the four-phase pipeline this ADR explicitly retains pending trials
- `.claude/scratch/ears-authorability-spike.md`, `.claude/scratch/pbt-spike/`, `.claude/scratch/slice-25-counterfactual.md` — empirical probe artifacts (untracked)
- govllm-trial/CAIRN_PLAN.md — the downstream proposal this ADR amends and supersedes
