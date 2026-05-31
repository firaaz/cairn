---
id: thin-cairn-intent-management
name: "Thin cairn — intent-management loop (brainstorm design → /decision input)"
firmness: provisional
status: draft
date: 2026-05-31
scope: >
  Design the intent-management workflow that replaces the predefined four-phase
  dispatch (cairn-tdd-feature) as cairn's default for new work. Brainstorm output;
  the terminal step is a /decision arc, NOT direct implementation. Captures the
  agreed shape, the adversarial pre-mortem that reshaped it, and the residual
  questions /decision must adjudicate before any build.
inputs:
  - docs/adr/cairn-thin-substrate-direction.md   # the accepted direction (D1-D8)
  - docs/plans/2026-05-20-cairn-thin-substrate-trials.md  # Trials A-E + probes
  - docs/spec-v2.md                              # the feature-loop / daily-usability proposal
  - docs/adr/delivery-mechanism-friction.md      # the using-cairn SessionStart carrier (D1)
  - templates/intent.md                          # the Contract block
  - checks/{atomicity_guard,premise_guard,role_guard}.py  # the three shipped gates
---

# Thin cairn — intent-management loop

## Context / why

The operator stopped using cairn's four-phase pipeline for daily work: the per-feature
ceremony (author intent → RED → GREEN → audit across fresh sessions) cost more attention
and tokens than it returned (`spec-v2.md` §2). The accepted `cairn-thin-substrate-direction`
ADR resolves this at the substrate level — six primitives, five-and-a-half already shipped,
including the premise-grounding **keystone** and the scope-split rule. What remains is the
**migration**: Trial D (scope-split measurement) → Trial E (drop phase-1 derivation).

"New cairn" = **intent management**. The intent (a contract:
`must-satisfy`/`must-not-violate`/`wrong-if`/`escalate-when`/`evidence`/`execution-scope`)
becomes the durable anchor of a work-session; the predefined four-phase sequence is retired
in favour of managing intents directly, test-first, so cairn can dogfood its own next
increment on the new footing. **Structure lives in the anchor, not in a fixed process.**

This document is the brainstorm output. Per operator choice the next step is a **`/decision`
arc** (this is a decision-weight, cross-cutting methodology migration), not direct build.

## The agreed shape

Resolved with the operator during brainstorming, then hardened by an adversarial pre-mortem
(6 independent refuters; see "How this answers the pre-mortem"):

- **Unit:** single-intent execution loop + lightweight on-disk tracking (intent files +
  handoff pointers; no portfolio/DB).
- **Anchor ≠ approval.** The intent always *exists* and is edited live (always-on floor).
  But operator confirmation — and the front-loaded challenge below — fire **only on a new
  intent or a material change**, never on plain resume. Session-start *loads* (cheap, no
  gate); approval is delta-triggered. (Reshaped from the original "approve every session.")
- **Construction is fluid.** One continuous conversation, tests written test-first; no phase
  resets, no context re-bootstrapping. Cairn does not sequence the work.
- **Two decorrelation checkpoints bracket construction** (the reshaped core):
  1. **Front-loaded intent-challenge** — on a new/materially-changed intent, a fresh-context
     agent attacks the intent's premises against live code (*does the code actually mean what
     the intent claims?*) **before** construction. Mandatory; this is the Skeptic's value,
     front-loaded — the ADR's required "equivalent mechanism."
  2. **Fresh close-review** — at close, a clean-context subagent gets contract + diff + test
     output and verifies the work against the intent.
- **Contract mandatory, graduated by size, with a completeness floor.** Trivial work → a
  one-liner `must-satisfy`; heavy work → full grammar + premise-grounding. D3 exception tags
  (`universal-set`/`regression-meta`/`operator-bound`/`trivial-existence`) are the depth dial.
  A **completeness floor** prevents trivializing a heavy change into a bundle of existence
  checks (mechanism is a /decision open question).
- **Enforcement is ambient — all already shipped, unchanged.** `premise_guard` (verbatim
  grounding at intent-approval), `role_guard` (envelope on every write), `atomicity_guard`
  (scope-split as the contract is authored).
- **Realization (Approach A):** a new dispatch skill that **coexists** with `cairn-tdd-feature`
  (kept as fallback). Running cairn's own next change this way **is Trial E**.

## Components (Approach A)

- **New loop skill** (working name `cairn-intent`) — orchestrates: load-or-form intent →
  (on delta) challenge + approve → fluid construct → close-review → close (commit + handoff).
- **SessionStart carrier** — the accepted-but-unbuilt `using-cairn` SessionStart skill
  (`delivery-mechanism-friction` D1) is the "always-on" mechanism: on session open it *loads*
  the current intent (resume) or signals that a new one is needed. **Built as part of this
  work**, with a testable "carrier fired" definition + a fallback when it doesn't fire.
- **Front-challenge subagent** (`.claude/agents/intent-challenge.md`, new) — fresh context;
  input = the new/changed intent + the cited source; output = a verdict attacking each premise
  semantically. Blocks approval on a sustained challenge.
- **Close-review subagent** (`.claude/agents/intent-review.md`, new) — fresh context; input =
  contract + diff + test output; output = pass / findings.
- **Graduated-contract + completeness rules** — guidance in `templates/intent.md` + the dial,
  plus the completeness floor.
- **Reused unchanged:** `atomicity_guard.py`, `premise_guard.py`, `role_guard.py`,
  `scripts/validate_architecture.py` assertions, `.claude/handoff.md` (thin tracking).

## How this answers the pre-mortem

Six independent refuters attacked the agreed design (2 fatal, 4 serious). The reshaping above
resolves them:

- **FATAL — always-on recreates v1 ceremony** (approving every session → rubber-stamping):
  resolved by *anchor ≠ approval* — confirmation is delta-triggered, not per-session.
- **FATAL — session-start load = stale artifact / context poisoning + ceremony on trivial
  sessions:** resolved by load-≠-gate (load is cheap/contextual; the live intent is edited in
  place) and the trivial-session exemption (no write → nothing to govern).
- **SERIOUS ×2 — semantic misread of the intent is caught by nothing** (premise_guard is
  verbatim-only; a same-family close-review is too late + inherits the frame): resolved by the
  **front-loaded intent-challenge** (decorrelated, pre-construction). This is the operator's
  chosen fix.
- **SERIOUS — graduated dial is gameable:** resolved (mechanism TBD) by the **completeness
  floor**.
- **SERIOUS — SessionStart carrier doesn't exist:** folded into build scope with a
  "carrier-fired" test + fallback.

## Open questions for /decision

The brainstorm intentionally leaves these for the `/decision` arc to adjudicate adversarially:

1. **"Material change" threshold** — what delta to an intent re-triggers approval + the
   front-challenge (diff-size? clause edit? premise change?). Too loose → ceremony returns;
   too tight → drift slips through.
2. **Completeness-floor mechanism** — cardinality heuristic (N clauses per LOC band),
   operator attestation that shallow is deliberate, or an agent-proposed completeness check.
3. **Decorrelation strength** — is same-family sufficient for the front-challenge and
   close-review, or does either need cross-family dispatch (Kim et al. 60% same-family
   agreement)?
4. **Carrier contract** — the testable definition of "SessionStart carrier fired," its
   ≤2k-token budget (delivery-friction D1/D6), and the fallback path.
5. **Fate of the four-phase substrate** — coexistence is the migration posture, but what is
   the retirement trigger for `cairn-tdd-feature`, and what happens to the firm phase ADRs
   (`phase-lock-and-role-declaration`, `phase-pipeline-evaluation`, `feature-slice-model`) +
   INV-003? (ADR D8 retains them; Trial E pass is the candidate trigger.)
6. **Multi-session / multi-operator intent divergence** — how the live intent stays the single
   source across resumes and (for consumers) branches.
7. **Trivial-session boundary** — the precise rule for "this session touches the repo, so it
   needs at least a thin intent" vs. exempt read-only/Q&A.

## Testing

- **Unit-tested (TDD, mandatory):** the graduated-contract + completeness-floor rules; the
  front-challenge and close-review subagent input/verdict contracts; the SessionStart
  carrier's "fired" detection + fallback. The three gates are already tested and unchanged.
- **Dogfooded:** the loop itself — cairn's next real increment runs through `cairn-intent`
  (this is Trial E); the operator authors a Contract block live (this is also the Trial-D
  3-intent measurement data point).
- **Decorrelation is the load-bearing property to verify:** re-run the slice-#25 counterfactual
  through the front-challenge and confirm it blocks at approval (Trial E pass criterion).

## Coexistence & Trial-E framing

`cairn-tdd-feature` stays as the fallback during transition (ADR D6 retains the pipeline
pending trials). The first production session run through `cairn-intent` *is* Trial E: "drop
phase-1 derivation; intent.md + premise-grounding + envelope replaces it, operator confirms no
semantic-grounding failure leaked." A Trial-E failure is a real finding (retain the pipeline /
escalate the front-challenge), not a bug to paper over.

## Next-session sequencing (the build is NOT a single session)

Two open threads exist; order matters:

1. **Trial-D 3-intent measurement FIRST** (`docs/plans/2026-05-30-cairn-trial-d-scope-split.md`
   §Next-session). It is cheap, operator-authored (non-headless), *gates* Trial E per the trials
   plan, AND validates `atomicity_guard` — a component this loop's contract gate reuses. If its
   false-positive rate is still >10%, the graduated-contract gate (D3) needs work *before* the
   build relies on it.
2. **THEN the Trial-E build.** First action is `writing-plans` to decompose the 4 components
   (skill + `intent-challenge` + `intent-review` + carrier) into TDD slices — this is multiple
   sessions, not one. Build the **`intent-challenge` subagent first**: it is the load-bearing
   decorrelation piece and carries the slice-#25 counterfactual acceptance gate (ADR D7/D9).
   Bootstrap: build it via the existing 4-phase / a focused TDD pass, since the new loop does
   not exist yet. Re-scope `.claude/active-envelope.yaml` to the build paths at session start;
   single-operator-per-branch (ADR D8).

## References

- `docs/adr/cairn-thin-substrate-direction.md` — D1–D8 (accepted direction)
- `docs/plans/2026-05-20-cairn-thin-substrate-trials.md` — Trials A–E, probes A/B/C, open Qs
- `docs/spec-v2.md` — feature-loop + daily-usability proposal (unpromoted; v1 canonical)
- `docs/adr/delivery-mechanism-friction.md` — D1 `using-cairn` SessionStart carrier
- Pre-mortem run: workflow `intent-management-design-premortem` (6 refuters), 2026-05-31
