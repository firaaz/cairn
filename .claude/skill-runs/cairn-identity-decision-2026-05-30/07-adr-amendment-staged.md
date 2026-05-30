# Staged additive body amendment for `docs/adr/cairn-thin-substrate-direction.md`

Append-only / additive (new ⊇ old) → requires `ADR_EDITORIAL_FIX=1` in the hook env.
Apply as: (1) append acceptance note to `## Status`; (2) insert D7 + D8 immediately before `## Consequences`.

---

## Edit 1 — append to `## Status` (anchor: the "Companion trials plan:" line)

> — **Accepted 2026-05-30** via the cairn-identity `/decision` arc (`.claude/skill-runs/cairn-identity-decision-2026-05-30/`). Premise-grounding (D2.5) elevated to keystone (D7); charter-cycle direction reconciled (D8); the premise-grounding assertion is built and tested.

---

## Edit 2 — insert before `## Consequences`

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

---

## Supersession (already landed via frontmatter — recorded here for the body trail)

This ADR supersedes `identity-and-scope-deferral` (via its own D3.4 operator-directive revisit trigger) and `slice-intent-contract` (its contract concept survives in D2.1's grammar). Both carry `status: superseded` + `superseded-by: cairn-thin-substrate-direction`. The three firm phase ADRs are retained (see D8).
