# Why Cairn

Cairn is a development methodology for complex, AI-assisted software work. This document explains the problem it targets, the bet it makes about why that problem exists, the mechanism it uses today (both within a slice and across many slices), the mechanism it is building toward, and the limits it acknowledges.

For scope — when the methodology is worth its overhead and when it is not — see [`spec-v1.md` §1](spec-v1.md). For the v1 commitments driving cairn's own development, see [`vision.md`](vision.md). For day-to-day operation, see [`operational-reference.md`](operational-reference.md).

## The problem: the medium-scale AI-managed cliff

Simple AI-assisted work — CRUD apps, prototypes, wrappers — runs fine in a single long-running session with planning modes and auto-compaction. Frontier models handle it.

The cliff appears where the codebase crosses a threshold of interwoven components, accumulated architectural decisions, and long-horizon maintenance. Past that point, a single continuous session systematically fails in correlated ways:

- **Role contamination.** The session that authored a design also grades it. Narrative momentum prevents a clean switch from author to critic — neither the human nor the AI can reliably stop defending the work it just produced.
- **Drift.** ADRs and code diverge over months. Two ADRs that pass all mechanical reference checks can still quietly contradict each other in meaning.
- **Integration failures.** Each component passes its own tests, but together they break the system because no session ever held the cross-component invariant explicitly.
- **Ambient authority in context.** The trace of how a decision was reached — earlier turns, rejected alternatives, partial implementations — leaks into the next phase's reasoning and biases evaluation.

Cairn names this target the *medium-scale AI-managed cliff* (see [`docs/adr/cliff-failure-mode-and-v1-defenses.md`](adr/cliff-failure-mode-and-v1-defenses.md)). It is the failure mode the system is designed to prevent, and the only one the system claims to address.

## The bet: two inseparable mechanisms

Cairn's load-bearing claim, quoted from [`spec-v1.md` §2](spec-v1.md):

> Complex AI-assisted development requires phase boundaries with clean context resets between them. The mechanism is **dual and inseparable**.
>
> **Context engineering.** A fresh session loads only the committed artifact of the previous phase, not the accumulated trace of how it was produced.
>
> **Role reset.** The session boundary forces a deliberate switch in cognitive role. Within a continuous session, narrative momentum prevents clean role transitions — neither human nor AI can reliably stop being the author and start being the critic without an external interruption.

Neither half works alone. Context engineering without role reset still has the original author grading their own output. Role reset inside a running session still loads the polluted trace. The bet is that **the session boundary — a committed artifact plus a handoff document plus a new session** — is the unique mechanism that satisfies both at once.

Everything else in cairn is downstream of that bet. And "everything else" has two layers: discipline *within* a single slice, and a substrate that accumulates *across* slices. The short-term layer alone solves nothing — a clean slice that lands into an incoherent codebase is still a bug factory. The long-term layer is where coherence compounds.

## The mechanism today, part 1: within a slice

Cairn operationalises the bet as a four-phase **slice** pipeline. A slice is a vertical feature cut that runs through all four phases; each phase starts in its own fresh session with a declared cognitive role, reading only the previous phase's committed artifact.

| Phase | Role | Reads | Produces |
|---|---|---|---|
| 1. Intent | Reader | ARCHITECTURE.md + ADRs (no source for greenfield; public interfaces only for modification) | `intent.md` + envelope |
| 2. Validation | Skeptic | `intent.md` | Test suite + `approach.md` |
| 3. Implementation | Builder | Tests as black-box + `intent.md` | Code passing tests |
| 4. Integration | Auditor | Implementation + invariants | Pass/fail verdict with `file:line` evidence |

Supporting structure:

- **Envelope.** Each feature's plan doc declares which files the work may touch (a regex array under the plan-doc frontmatter `envelope:` key). The operator envelope at `.claude/active-envelope.yaml` is the operator-session surface — `checks/role_guard.py` reads it when `AGENT_ROLE` is unset and denies writes outside the declared `paths:`; `mode: operator` enforces, `mode: off` disables, malformed YAML or unrecognised mode fails closed. Within a `cairn-tdd-feature` dispatch run, `role_guard.py` instead enforces per-phase write allowlists keyed on `AGENT_ROLE` (Phase 3 specifically takes its envelope from `AGENT_ENVELOPE` at dispatch time). Either way, expansion is explicit — there is no per-edit escape hatch.
- **Handoffs as pointers, not narratives.** `.claude/handoff.md` is a 150–400 token pointer artifact with forbidden sections (spec §10, [`context-discipline-protocol.md`](adr/context-discipline-protocol.md)), so `/catchup` reloads committed state — `.claude/handoff.md`, `git log`, `git status`, and `.claude/active-envelope.yaml` — rather than a previous session's internal reasoning.
- **Phase transitions enforced by git commits,** not by session state. Closing one session and opening another is the external interruption the bet depends on.

This is the *short-term* discipline: one slice stays coherent with itself.

## The mechanism today, part 2: across slices

The long-term story is the substrate — the stones that the cairn is named after. Each slice adds a stone; the pile is what makes the path.

**1. The `/decision` adversarial protocol** ([`spec-v1.md` §6](spec-v1.md), [`commands/claude-code/decision.md`](../commands/claude-code/decision.md)).

The same bet applies one level up: architectural decisions are where correlated errors compound hardest and last longest. So cairn runs a nine-sub-phase protocol for any work that touches invariants, boundaries, data ownership, or module structure:

1. **Constraint Harvest** — read ARCHITECTURE.md, ADRs, lessons; surface conflicts with the proposed change.
2. **User-Journey Trace** — identify the mechanism at every session/artifact/state boundary the change would touch.
3. **Pre-Mortem** — at least three failure scenarios (technical, scale, integration) *before* proposing an approach.
4. **Forced Enumeration** — at least three viable approaches, rated against the pre-mortem. Enumeration combats the correlated-error trap of memory-driven "obvious" choices.
5. **Adversarial Stress Test** — disconfirming search, steel-manned opposition, assumption audit.
6. **Decision Record** — draft ADR, defaulting to `firmness: provisional`.
7. **Independent Verification (Phase 5)** — fresh same-family session re-runs Phases 1–3 blind; conclusions are compared. Firm-only; provisional ADRs skip it.
8. **Propagation** — manual `docs/ARCHITECTURE.md` update synchronised with the new ADR (gated by `reversibility-guard.sh`'s ADR append-only enforcement on the underlying corpus), check in-progress feature plan docs, update superseded ADRs, record patterns.

The `/decision` protocol exists specifically because a single session proposing a decision is indistinguishable from a single session defending one. Forced enumeration and adversarial stress testing before the decision record, plus a fresh-session verification after, are the `/decision` equivalents of a slice's phase boundaries.

**2. ADRs as append-only memory** ([`spec-v1.md` §10](spec-v1.md)).

Every architectural decision becomes an immutable record in `docs/adr/`. Decisions are never rewritten; they are **superseded**. `checks/reversibility-guard.sh` enforces this at the hook layer: `Write` on an existing ADR is blocked; `Edit` is allowed only for frontmatter fields (`status:`, `superseded-by:`, `firmness:`). Full rewrites require a new ADR that cites the one it replaces. The substrate therefore carries not just the current position but the trajectory — the record of why the current shape is current.

**3. `ARCHITECTURE.md` as a derived view, not a source of truth** ([`spec-v1.md` §10](spec-v1.md)).

`docs/ARCHITECTURE.md` is a derived view of the active (non-superseded) ADR corpus. Updates land as part of the same commit as the ADR that justifies them, gated by `reversibility-guard.sh`'s ADR append-only enforcement on the underlying ADR. Pre-shrink, an automated `/refresh-architecture` mechanism regenerated the document at slice close; post-M4 cairn-shrink (2026-05-07) the refresh is manual and operator-driven. Trust flows from ADR → ARCHITECTURE.md, never the other way. There is no scenario in which ARCHITECTURE.md leads and the ADRs follow.

**4. Invariants as the coupling layer.**

`ARCHITECTURE.md` carries a section of **invariants** — specific, testable statements the system must maintain. Each firm ADR contributes at least one invariant. Each invariant references at least one active ADR. `scripts/validate_architecture.py` enforces the reference graph:

- **Check A (forward).** Every invariant must reference a valid, non-superseded ADR.
- **Check B (backward).** Every `firmness: firm` accepted ADR must have at least one invariant in ARCHITECTURE.md.
- **Check C (staleness).** No invariant may reference a superseded or deprecated ADR.
- **Check D (executable assertion).** If an invariant declares an `invariant-check` block (`type: grep | file-exists | test-ref`), the validator runs it and fails if the assertion doesn't hold.

The claims in this document are themselves backed by a 661-test passing suite (`uv run pytest tests/unit/`) that exercises the hooks, the validator, and the phase protocols.

**5. The stone-accumulation mechanism.**

Slice N reads `ARCHITECTURE.md`, which carries invariants distilled from every prior firm ADR. Slice N produces its own ADR (if it touches the decision layer) or lands within existing constraints. When the new ADR lands, `ARCHITECTURE.md` is hand-updated in the same commit — now carrying slice N's new invariant. Slice N+1 reads that new version. Constraints compound. The validator ensures the compounding stays coherent.

This is the answer to "medium-large codebases": the substrate is the thing that scales, not any individual slice. A project that has run 40 slices does not have 40 session traces swimming in context; it has an ADR corpus, a derived architecture document, and an invariant set. Newcomers — human or AI — load the latter, not the former.

**6. Per-feature integration as the horizontal check** ([`spec-v1.md` §12](spec-v1.md)).

The `cairn-tdd-feature` dispatch skill's Phase 4 (Auditor) runs the per-feature integration check: load invariants the feature touches, **enumerate failure modes before checking them** (enumeration-before-verification is a cairn pattern), verify each invariant with `file:line` evidence, run the full test suite + validator + smoketest, and produce a pass/fail verdict. Failures never retroactively edit completed features — they produce new features that fix the problem through the same four-phase pipeline.

Pre-shrink, a separate `/integration-sweep` command ran cross-feature checks every N slices via `.claude/sweep.yaml` cadence; that command and its substrate retired in M4 cairn-shrink (2026-05-07). The cross-feature / structural-snapshot-diff backstop returns to v2+ scope (cliff-failure-mode-and-v1-defenses D3, retired and amendment queued).

## The mechanism being built

The bet is larger than what currently ships. [`roadmap.md`](roadmap.md) and [`spec-v1.md`](spec-v1.md) §§7–9, 15, 16 describe what cairn is building toward:

- **Agent-portable substrate.** Protocols live as plain markdown; checks are shell scripts. Claude Code and Windsurf will each run the full pipeline independently, validated by one slice end-to-end on each and one slice handed off mid-flight between them ([`vision.md`](vision.md) commitments 1, 3; roadmap items 7, 8).
- **Parallelism-native.** Slice state is branch-local, never global. N concurrent slices on separate worktrees run without interference. Two-concurrent-slice validation is a v1 gate ([`vision.md`](vision.md) commitment 2; roadmap items 5, 6, 9; [`parallelism-v1.md`](adr/parallelism-v1.md)).
- **Explicit cognitive roles, mechanically declared.** The phase-rethink decision locks phase count, boundaries, names, and role per phase, with named anti-behaviours ("the architect does not write code, the skeptic does not propose fixes"). `checks/role_guard.py` enforces role-scoped file access for the four canonical TDD roles (`phase-1-tdd`, `phase-2-tdd`, `phase-3-tdd`, `phase-4-tdd`) via hook-layer allow-lists, plus an operator-envelope path read from `.claude/active-envelope.yaml` for non-dispatch sessions. Mechanical role-gating across every cognitive boundary remains a v2+ target ([`vision.md`](vision.md) commitment 6; [`phase-lock-and-role-declaration.md`](adr/phase-lock-and-role-declaration.md)).
- **Retroactive Phase 5 audit of initial-commit firm ADRs.** The firm ADRs committed in cairn's initial commit (`e68840e`) have no Phase 5 evidence. A substrate audit is scheduled to walk each one through Phase 5 retroactively or demote it to provisional with recorded rationale ([`spec-v1.md` §14](spec-v1.md) incident 1).
- **Property-based testing at the Phase 1 → Phase 2 boundary** ([`spec-v1.md` §15](spec-v1.md)). Human-authored properties — idempotence, round-trip consistency, authorization invariants — cross the phase boundary alongside the intent. Phase 2 translates them into Hypothesis/proptest tests whose cases are framework-generated, not AI-generated. This closes the correlated-blind-spot gap between AI-written tests and AI-written implementations.
- **Cross-family adversarial verification** ([`spec-v1.md` §8](spec-v1.md)). Today's Phase 5 uses a fresh *same-family* session, which shares ~60% of structural errors with the original (Kim et al.). Cross-family verification — raw inputs preserved verbatim, independent analysis produced before any view of the original — is designed but not built.
- **Semantic ADR drift detection** ([`spec-v1.md` §16](spec-v1.md)). The current validator catches reference drift; semantic contradiction between ADRs that are technically consistent but mean different things is not mechanically detectable yet. Candidate directions: treat ADRs as a dependency graph so contradictions become a mechanical query; differential invariants that become jointly unsatisfiable on drift; periodic semantic re-review by a separate agent.
- **Validator auto-enforcement on ADR writes** ([`spec-v1.md` §14](spec-v1.md) incident 2). The validator today runs on manual invocation (`uv run python scripts/validate_architecture.py`). A pre-commit hook on ADR file changes is roadmapped.

These are direction, not decoration. Cairn's v1 is the smallest system that puts every one of them on a credible path.

## What isn't proven

Cairn is honest about operating under a *calibration gap*: its discipline is more rigorous than the empirical evidence justifies, deliberately, for safety-critical work ([`spec-v1.md` §17](spec-v1.md)).

The anchors that do exist:

- **Song et al. (2026)**, arXiv:2603.12123 — +4.0 F1 points from cross-context review over same-session self-review across 30 artifacts and 150 injected errors. The control condition (reviewing twice in the same session) did not beat reviewing once, ruling out repetition as the mechanism. Strongest single anchor for "the session boundary itself is load-bearing."
- **Tsui et al. (2025)**, arXiv:2507.02778 — 64.5% average self-correction blind-spot rate across 14 open-source non-reasoning models; a minimal trigger ("Wait") reduced blind spots by 89.3%. Supports role-switching as structurally meaningful.
- **Kim et al. (ICML 2025)**, arXiv:2506.07962 — ~60% error agreement across 350+ LLMs. Bounds how much same-family verification can catch; motivates the cross-family direction above.

What these anchors do not do is prove the role-reset half of the dual mechanism. There is no current experiment that distinguishes "role contamination was a real problem the fresh session prevented" from "the fresh session coincided with higher-quality output for unrelated reasons." Adopting cairn means betting that the role-reset thesis is load-bearing.

Known unenforced disciplines, disclosed rather than hidden ([`spec-v1.md` §14](spec-v1.md)):

- **Phase 5 independent verification is not hook-gated.** The firm ADRs in cairn's initial commit have no Phase 5 evidence; a retroactive substrate audit is scheduled.
- **Modification-slice "read public interfaces only" has no enforcing hook.** The defence is discipline-only.
- **Full role enforcement is instructed, not locked.** `role_guard.py` covers the four canonical TDD roles plus an operator-envelope path; system-wide mechanical role-gating across every cognitive boundary is a v2+ target.
- **Semantic ADR drift is not caught by the validator.** Mechanical reference-graph coherence does not imply semantic coherence.

## When cairn is worth the overhead

In scope ([`spec-v1.md` §1](spec-v1.md)): safety-critical systems, long-horizon projects with interwoven components, integration-heavy domains, projects that actively accumulate and maintain architectural decisions.

Out of scope: CRUD apps, prototypes, AI wrappers, short-lived internal scripts, one-off analyses. There the overhead is pure waste.

The bet only pays off where correlated errors compound. If they do, cairn is an attempt to put a mechanical floor under the damage — both within a slice (four phases, fresh sessions, envelope-scoped edits) and across slices (append-only ADRs, derived architecture, invariant-backed substrate, integration sweeps). If they don't, the same discipline is friction with nothing to catch.
