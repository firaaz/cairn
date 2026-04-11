# Methodology Review — Findings from a Consuming Project Session

Source: session 15 of `complex-rag-analysis` (2026-04-11)
Permission: spec-v1.md was read under the CLAUDE.md "adversarial review" carve-out, not auto-loaded
Audience: cairn maintainers / future cairn Claude sessions

> **Triage note (2026-04-11, post-review)**
>
> - **Finding 1 — superseded by SLICE-001** ("Correct validator project root resolution across symlinks"). The slice chose a stricter fix than this review recommended: `scripts/validate_architecture.py` now resolves the project root via `CLAUDE_PROJECT_DIR` → `git rev-parse --show-toplevel`, with **no** `__file__`-based fallback. The rejection of the "drop `.resolve()`" option is documented inline at `scripts/validate_architecture.py:25-38` — loud failure was preferred over any silent canonicalization path.
> - **Findings 2, 3, 4 and open questions** — still open. Deferred to a future slice. File kept in `docs/reviews/` (establishing that convention, answering one of the review's own open questions).

## How this review was produced

A `/decision` session in the consuming project (`complex-rag-analysis`)
was running the full 8-phase protocol for ADR-009 (CSKB vision pilot
vendor selection). During Phase 6 (Propagation) the architecture
validator was invoked and mis-reported — the first finding. During the
closing discussion the user asked an elegance question about the
decision/slice relationship, which opened spec-v1.md for adversarial
review. That review surfaced three more findings.

None of these findings are about ADR-009 itself. They are about cairn's
methodology documents and tooling, which is why they are relayed here
rather than being absorbed into the consuming project's history.

## Finding 1 — Validator symlink bug blocks Phase 6 propagation in consuming projects

**File**: `scripts/validate_architecture.py`, line 22:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
```

**Symptom**: When cairn is consumed via the `.slice-system` symlink
pattern documented in the extraction plan, `Path.resolve()` follows
the symlink chain back to `~/Developer/lab/cairn/` instead of
resolving to the host project's root. The validator then reads
cairn's own `docs/ARCHITECTURE.md` and `docs/adr/` rather than the
host project's, and reports wrong counts.

**Concrete evidence from session 15**: Running the validator against
a host project with 8 invariants and 8 ADRs returned

```
ALL CHECKS PASSED
  Invariants verified: 1
  ADR files checked: 1
```

— it was validating cairn's own minimal docs, not the consuming
project's.

**Fix options**:

1. **Drop `.resolve()`** — use `Path(__file__).parent.parent`. When
   invoked via the symlink, the non-resolved path stays inside
   `.slice-system/scripts/...`, whose `.parent.parent` is the host
   project's `.slice-system/` directory's parent, which is the host
   project root. This is the smallest change and requires no caller
   updates. Needs verification that it works in both symlinked and
   in-place (cairn's own repo) modes.
2. Accept a `--project-root` CLI arg.
3. Read from `PROJECT_ROOT` or `CAIRN_PROJECT_ROOT` env var.

Option 1 is the minimal fix. Verify with manual runs in both modes
before shipping.

**Impact if unfixed**: Every host project's Phase 6 propagation
(`/refresh-architecture`, post-ADR validation sweeps) silently reports
success while not actually validating anything meaningful. This is the
exact "mechanical validator that passes for the wrong reason" failure
mode that spec-v1 §14 warns against in the substrate incidents list.
It is currently a live regression in every cairn-consuming project.

**Priority**: High. A validator that lies is worse than one that
doesn't exist, because it produces false confidence.

## Finding 2 — `operational-reference.md` and `spec-v1.md` disagree on mid-slice decision handling

**operational-reference.md §ADR Rules During a Slice** (line 177-188
in the version at time of review) describes a **pause-and-resume**
pattern:

> If implementation requires violating an invariant:
> 1. STOP implementation.
> 2. Write a new ADR in `docs/adr/` with proper YAML frontmatter...
> ...
> 6. Record the new ADR in `slice.yaml` under `adrs-created`.
>
> (implicit: the slice resumes after the ADR lands)

**spec-v1.md §4 Routing Recovery Rules** (line 78) describes a
**fail-and-restart** pattern:

> Slice started, architectural invariant discovered → fail the slice,
> restart with a `/decision` that produces the ADR, then re-enter the
> slice with the new constraint as input.

These are not the same rule. operational-reference lets a slice keep
going after recording the ADR; spec-v1 says the slice must be failed
entirely and a fresh one started after the ADR lands.

**Why spec-v1's rule is more defensible**: §6 "Decision → Intent
Immutability" (line 124-126) explicitly states:

> The Intent phase that follows a Decision is not free to revisit the
> decision. [...] Intent cannot patch around a flawed decision because
> that would route around the verification.

If a mid-slice decision is handled by pause-and-resume, the slice's
Phase 1 intent was drafted *before* the decision existed, and the
resumed Phase 3 implements against an intent written under an
assumption set that has since changed. That is precisely the "routing
around verification" the immutability rule forbids. Pause-and-resume
preserves the appearance of slice continuity at the cost of the
property the slice system exists to provide.

**Recommended action**: Reconcile by making operational-reference.md
match spec-v1.md. Replace §ADR Rules During a Slice with language
matching Routing Recovery Rules: fail the slice, open a decision,
re-enter a *new* slice whose intent references the new ADR via
`adrs-referenced`. Record the old slice under
`.claude/completed-slices/<ID>-failed/`.

**Caveat worth considering**: fail-and-restart is operationally more
expensive. A lightweight middle ground could be "if the discovered
decision is editorial-grade (frontmatter clarification, typo fix in an
ADR's consequences section), allow in-slice editorial fix via the
`ADR_EDITORIAL_FIX=1` escape hatch (spec-v1 §10). If it is
substantive, fail the slice." Spec-v1 does not explicitly carve this
out, but the existing editorial-fix hook is the nearest precedent for
"some changes are small enough not to require the full mechanism."
Decide whether to document this carve-out or leave it implicit.

**Priority**: Medium. The contradiction is latent — users who read
operational-reference will follow the looser rule; users who read
spec-v1 will follow the stricter rule; same-user-different-sessions
can contradict themselves. This risks exactly the kind of silent
drift the slice system is designed to prevent.

## Finding 3 — The §9 rejected 5-phase track framing is the cleanest unification and may warrant revisiting

spec-v1 §9 "Three-Track Routing" (marked `[DESIGN-ONLY]`) describes a
rejected alternative to the current binary Decision/Slice routing:

> - 3-phase track for low-consequence work: Intent → Implementation → Integration
> - 4-phase track for normal work: Intent → Validation → Implementation → Integration
> - **5-phase track for high-consequence work: adds a Pre-Decision gate before Intent.**
>
> Status: not implemented. The running system uses simpler binary
> routing (Decision vs. Slice). Three-track routing is kept here as a
> design roadmap because the binary routing is a rough fit for actual
> project consequence — small bug fixes should not pay full pipeline
> cost — but the friction of self-classifying into three tracks is
> unproven and may not justify the complexity.

The rejection reason is operational (self-classification friction),
not conceptual. The 5-phase track is strictly more expressive than
current binary routing, and it resolves Finding 2 automatically: if
Pre-Decision is always the first phase of any track that has one,
there is no "decision inside a slice" case to disambiguate — tracks
with a Pre-Decision phase handle decisions before Intent, and tracks
without one are low-consequence enough that the fail-and-restart rule
is cheap when it triggers.

There is also a subtler gain: the 5-phase framing makes the spec's
strongest rule (Decision → Intent Immutability) structural rather
than prescriptive. In the current binary framing, "a decision
upstream of a slice cannot be revisited by the slice" is a rule you
must remember to apply. In the 5-phase framing, Pre-Decision's phase
gate commits the ADR before Phase 1 Intent begins, and the rule
follows automatically from the standard phase-gate discipline.

**Recommended action**: Revisit §9 when cairn's phase rethink slice
runs (roadmap item 1). The rejection was deliberate and evidence-based
at the time ("unproven friction"), but with more slices under the
belt the friction question becomes answerable. Either outcome is
actionable: if friction materialized, the current binary routing is
validated; if friction did not materialize, the unification is
cheap to adopt and cleans up Finding 2 as a side effect.

**Priority**: Low, but worth surfacing as an input to the phase
rethink slice.

## Finding 4 — spec-v1 does not explicitly name the asymmetry that makes the whole design work

The core insight surfaced during the session 15 adversarial review:

> Slice phases are method-agnostic. Decisions are method-prescribed.
> The asymmetry is the whole trick.

A slice's Phase 3 can be written via TDD, via brainstorming then
implementation, via subagent parallelism, via pair programming with
a model, via any approach that produces code passing Phase 2's tests.
spec-v1 prescribes the *boundary discipline* at Phase 3 (fresh
session, declared inputs, committed artifact) but does NOT prescribe
the *method inside* Phase 3. The gate artifact is the contract; the
work inside is free.

A decision's 8 sub-phases are, by contrast, fully method-prescribed.
Constraint harvest → user-journey trace → pre-mortem → forced
enumeration → adversarial stress test → decision record → independent
verification → propagation. There is no "I will run this decision via
brainstorming instead" — the protocol *is* the method.

**Why the asymmetry is correct**: correlated-error cost scales with
upstream-ness. A bad Phase 3 implementation choice is caught by the
tests it must pass. A bad decision poisons every slice that references
it and has no downstream gate that catches it, except later decisions,
which inherit the error. Concentrating the discipline at the most
upstream layer is the right resource allocation.

**Current spec coverage**: §2 Core Thesis describes the dual mechanism
(context engineering + role reset) that makes phase boundaries work.
§6 Decision Protocol opens with "architectural decisions are the most
upstream task" and explains why the decision phase needs high rigor.
Both sections are present but they describe HOW the boundaries work
and WHY decisions need rigor — they do not name the asymmetry between
the slice layer's method-agnosticism and the decision layer's
method-prescription as a single principle.

**Recommended action**: Add a paragraph to spec-v1 §6 (or a new short
section between §5 and §6) that names the asymmetry explicitly. One
candidate phrasing:

> The slice layer is method-agnostic within each phase's gate: any
> approach that produces a committed artifact passing the next phase's
> inputs is legal. The decision layer, by contrast, is
> method-prescribed: the 8 sub-phases are the method, not a suggestion.
> This asymmetry is deliberate. Correlated-error cost scales with
> upstream-ness, and the decision layer is the most upstream task in
> the system. A bad Phase 3 is caught by Phase 4's tests. A bad
> decision has no downstream gate that catches it. Concentrating the
> discipline at the decision layer matches the resource allocation to
> the error-cost distribution.

This would answer the exact elegance question the session 15 review
surfaced, make the design intent legible to future readers, and
justify the two-protocol shape (rather than leaving it to feel like a
ship-vs-polish compromise).

**Priority**: Low-medium. The asymmetry is implicit today and the
system works. Making it explicit is a clarity improvement, not a
bug fix.

## Open questions for cairn

- **Which of the two doc sources is canonical when they disagree?**
  CLAUDE.md in consuming projects typically loads operational-reference
  at Layer 1 and leaves spec-v1 at Layer 2. spec-v1 claims canonical
  status in its own opening ("This document is the spec"). Making this
  explicit in operational-reference.md's opening paragraph would prevent
  the kind of silent disagreement Finding 2 documents.

- **Should `/decision` skill surface the §7 "synthesis paradox"
  warning at invocation time?** The current skill file describes
  Phase 5 Independent Verification but does not cite the spec-v1 §7
  caveat that same-family verification catches role contamination but
  not model-inherent blind spots. Users running `/decision` for firm
  decisions would benefit from seeing this known hole before they
  commit the ADR, not only if they later read spec-v1.

- **Should cairn carry a `docs/reviews/` directory** for
  consuming-project findings like this one, or are flat dated files
  in `docs/` the right shape? This review is the first of its kind,
  so there is no established convention yet.

## What was NOT changed in this review

None of these findings led to file edits in cairn during session 15.
The RAG session's user explicitly scoped session 15 to "ADR-009 and
handoff only, no cairn drift." This document is the full extent of
the cairn-relevant work that session 15 produced. Acting on any of
the findings is a decision for a future cairn session.
