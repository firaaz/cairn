# Operator field notes — 2026-05-10

Status: field memo from extended operator-side use of cairn. Not an ADR; not a spec amendment. Observations and proposed mechanisms for roadmap consideration.

## What this is

Notes from operator-side use against AI-driven-dev pain points that cairn touches but does not fully address. The frame is not "cairn is wrong" — most observations sit downstream of cairn being directionally right — but "cairn's substrate is agent-shaped, and the operator's re-entry, judgment, and comprehension are first-class problems that need their own surface."

## Core finding

Cairn's mechanisms — `handoff.md`, `/catchup`, `active-envelope.yaml`, git-as-source-of-truth — are designed for **fresh AI sessions** loading committed state. The operator is implicitly treated as a degraded fresh-agent and asked to use the same tools. They are not the same consumer:

- **Fresh agent:** stateless, loads everything, needs full state.
- **Operator:** partially stale, holds model in head, needs *triage* and *what's pending on them*, not state.

The git-heavy substrate doesn't fail — it just doesn't answer the operator's actual question, which is *"what needs my action right now"* rather than *"what is the current state."*

## Specific gaps observed

### 1. Operator re-entry has no dedicated surface

Returning to a project after hours or days, the operator needs:

- What's blocking on them (decision queue)
- What changed since *their last engagement*, not since the last commit
- Active slices, phases, last activity, blocking-on-what
- What's red (failed tests, validator, missing Phase 5)
- Concrete next action, not state

`/catchup` is for fresh agents. The existing `commands/claude-code/.local/dev-mode` morning briefing is a one-off solving exactly the operator-brief problem for cairn-dev — the pattern is recognized, just not generalized into the methodology.

### 2. No decision-queue primitive

Decisions arrive interleaved with execution. Interrupt-driven decisions are systematically lower-quality than batched ones, and parallel agent contexts make this worse — by the time a decision surfaces, the operator has lost framing.

Missing: a structured-ask format, a single decisions log per slice, scheduled processing passes, reversibility split, agents that block on `pending` and resume on `decided`. Without it, parallelism produces rubber-stamping at scale.

### 3. The operator gets no role reset

Cairn solves role contamination *for the AI* via session boundaries. The operator is permanently in author-mode for their own project — same brain wrote the plan and "reviews" it, no narrative interruption. Rubber-stamping is the rational outcome, not a discipline failure.

The substrate doesn't address this. Candidate mechanisms: deliberate cool-off between author and review, adversarial AI reviewer (a `/critique-intent`-shape command with no investment in shipping), forced falsification questions before approval, occasional external review.

### 4. Intent artifacts have three concrete failures

- **Context broken at review.** Operator initiated session hours earlier; cold-reads the intent without remembering original framing.
- **Agents write too much.** Intents balloon into multi-page documents that get vibes-graded, not read.
- **No mid-flight interactivity.** Cairn's role-reset bet forbids course-correction inside Phase 1 — for good reason — but the cost is high when initial framing was wrong.

All three are upstream symptoms of one thing: **session-start prompts are too thin**. *"Write an intent for X"* leaves the agent to fill the vacuum verbosely; you've forgotten the framing by review time; mid-flight redirect is needed only because the start was loose.

Mitigations, in order of leverage:

1. **Tighter session-start prompts** — explicit constraints, out-of-scope, length cap.
2. **Pin the operator prompt verbatim at the top of `intent.md`** so cold-reading restores framing immediately.
3. **Hard length caps with per-section caps** in the intent template.
4. **Cheap re-runs over interactivity.** Phase 1 is the cheapest phase; reject and re-run with a tighter prompt rather than add checkpoints.
5. **Adversarial review pass** (`/critique-intent`) on the artifact before approval.

### 5. Parallelism unit is misaligned

The default reading of cairn-as-parallel suggests fanning out **intents**. This produces speculative inventory: 10 intents, bandwidth for 2, 8 dead artifacts polluting the substrate. Fan-out belongs at **Phase 3** — long agent runs, no operator attention needed if Phases 1–2 were good, role-guard + envelope keep slices from colliding.

Realistic shape:

- Cap Phase 1 in flight at small N (3–5).
- **Pull, don't push:** a new Phase 1 starts only when Phase 3 capacity opens.
- Phase 3 runs concurrent, unattended.
- Phases 1, 2, 4 batched into operator brief / decision queue.

Corollary: tying intent inventory to Phase 3 throughput keeps the substrate honest about what's actually shippable.

## The operator surface — proposed shape

Minimal addition, no methodology rewrite:

- **`/operator-brief`** (operator-facing, not agent-facing). Pulls from decision queue + active-envelope + slice plan files + diff-since-last-operator-engagement + red status. Output is *what needs you*, ordered: blocking-irreversible → blocking-reversible → non-blocking. Generalizes the existing `dev-mode` pattern into the methodology.
- **`active-slices.yaml`** at project root. Which slices, what phase, what branch, last activity, blocking-on-what. Materialized for ergonomics; derivable from substrate. Tiebreak: substrate wins.
- **`decisions.md`** per slice. Structured asks with six fields: *question, options, recommendation, reversibility, blocking, why-now*. Append-only. Agent contract: fill all six or go back to research. Operator processes at scheduled passes. Reversible non-blocking decisions may be agent-decided with logging; irreversible always escalates.
- **Per-operator-session marker** so `/operator-brief` computes diffs from "last time you engaged" rather than arbitrary git points.

**Discipline that keeps this from sprawling:** every operator-facing artifact must be derivable from the underlying substrate. If a materialized view ever disagrees with ADRs/plans/git, the substrate wins. Materialization is ergonomic, not authoritative.

## Rivalrous practices — route per artifact

The "AI as typist" middle-ground (operator authors signature/contract, AI fills body, operator reads every body) is **not a softer cairn** — it's a different bet about where comprehension lives. They don't compose for the same artifact:

- Cairn: spec is load-bearing, comprehension lives upstream of code, don't read implementation.
- Middle-ground: comprehension partly lives at the code layer, read every body, stay in loop at function granularity.

Granularity, role, and comprehension stance all conflict. The honest model is to route work by lifespan and load-bearing-ness, committing to one practice per artifact:

- **Cliff-shaped, long-lived, accumulating** → pure cairn.
- **Daily mechanical (refactor, scaffold, format)** → AI-as-typist.
- **Exploratory / prototype / throwaway** → middle-ground or handwriting.
- **Debugging, forensics, load-bearing tools** → handwriting + AI review.

Naming which mode is in effect per task is the discipline. Blending them on the same code is what produces incoherent practice. Cairn's spec already restricts scope (§1) — making the *complement* explicit (what cairn is *not for*, and what practice covers it) would harden the boundary.

## The cairn-on-cairn paradox

Cairn's load-bearing components — `role_guard.py`, validators, hooks, dispatch protocol — are exactly the code where mechanical comprehension is most load-bearing for the maintainer. Pure cairn says don't comprehend the code. The methodology therefore asks the maintainer to give up comprehension precisely where it's most needed for cairn-the-codebase to stay debuggable.

Honest resolution: **maintainer carve-out**. Cairn-on-cairn runs differently from cairn-on-everything-else. Hand-author or middle-ground for load-bearing components; cairn-pipeline for tests, scaffolding, docs, ADR drafts. Consistent with existing carve-outs (`.slice-system` self-symlink, `commands/claude-code/.local/`). Worth making explicit as an ADR rather than dogfooding-uniformly-while-paying-the-tax.

## Calibration disclosures

- **Velocity vs. durable progress.** AI-driven dev produces fast first drafts; durable progress over the lifecycle is closer than line-count suggests and may favor handwriting for load-bearing code. Cairn implicitly assumes the durability gap is closeable through substrate; it is not yet fully closed.
- **Comprehension gap is real, bounded, not eliminated.** Cairn preserves *strategic* comprehension via ADRs/invariants/architecture. Structural and mechanical comprehension still degrade. No tooling fixes this; only scheduled reading, debugging-without-AI, and operational use of the system close the residual gap.
- **Tests are false-confidence.** Shared-blind-spot problem (AI-author + AI-test miss the same things). Property-based testing and cross-family verification on the roadmap are exactly the right direction. Until they ship, "all tests pass" should not be read as "system is correct" — only as "no imagined failure occurred."
- **Spec-as-load-bearing is partially realized.** Works for greenfield well-typed slices. Doesn't yet work for the messy middle (perf, error subtleties, integration interactions). Gap closes via formality: typed contracts, properties, runtime invariants, routine regeneration, cross-family verification. All on the roadmap.

## Open tensions

- The decision queue and operator brief introduce materialized state. Cairn's instinct is against ambient state — derive from substrate, don't materialize. Whether the operator surface earns its carve-out is itself a `/decision`-shaped question.
- Hard length caps on intents may surface a different problem (slices too big to fit a 1-page intent). That is the right signal, but it shifts where the discipline shows up.
- The "AI as typist" middle-ground is a competing local optimum. Declaring it explicitly out of cairn's scope (cairn is for cliff-shaped work; middle-ground covers the rest) is cleaner than trying to support both.

## Action shortlist

If only one item lands: build `/operator-brief` and the decision-queue primitive together. They compose — the brief reads the queue — and they fix the largest current pain (operator re-entry under parallelism with rubber-stamping risk). Everything else here is downstream of having a real operator surface.

Order, if more than one:

1. `decisions.md` format + agent contract (no tooling, manual protocol first).
2. `/operator-brief` command pulling from queue + diff-since-last-engagement + slice register.
3. `active-slices.yaml` materialization.
4. Pinned operator-prompt at top of `intent.md` template; per-section length caps.
5. `/critique-intent` adversarial pass.
6. Maintainer carve-out for cairn-on-cairn, documented as ADR.

Each is small. The leverage compounds.
