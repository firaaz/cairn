---
id: ADR-002
status: accepted
firmness: firm
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
invariants-touched: [INV-002]
date: 2026-04-11
---

# ADR-002: Context Discipline Protocol

## Status
Accepted

## Date
2026-04-11

## Context

Between 2026-03-01 and 2026-04-10, ten cairn and consumer-project sessions were measured for startup context load. Every session began at ~30,300 tokens on turn 1 — near the ~30–40k sweet-spot ceiling — and reached ~47,000 tokens immediately after `/catchup`. Typical sessions peaked between 100k and 170k before `/clear`, where model quality measurably degrades.

The design document at `docs/plans/2026-04-11-context-discipline-design.md` diagnosed the cause as a design-philosophy mismatch, not size bloat. Three concrete patterns emerged:

1. **`/handoff` writes narrative payloads.** Sections like "What This Session Was About", "Surprises or Discoveries", and "Self-Check" — ~3,200 tokens of reflective prose per session — smuggle the previous session's mental state across the `docs/vision.md` v1-commitment-#3 soft-agent-split boundary, collapsing the role-reset property that is supposed to make phase isolation an external check.

2. **`/catchup` reads into main context.** Catchup instructions list every potentially relevant file, and the implementing agent loads each one into the main conversation even when the user has not given a concrete imperative. Subagent dispatch through the `Agent` tool would cost ~100× less per file read but is not the default.

3. **`.claude/current-slice/` accumulates across slices.** Completed slices leave `handoff-phase-N.md`, `intent.md`, and the `validation/implementation/integration/` subtrees in place. The next slice inherits the full residue even though `slice.yaml` declares the predecessor `complete`. This undermines the premise that each phase starts from a clean declared-input set.

The design document proposed and validated a three-layer protocol fix: a pointer-format handoff, a tiered catchup with explicit admission criteria for main-context reads, and a wipe-on-close rule for `.claude/current-slice/`. Measured target: post-catchup context drops from ~47k → ~28–30k per session (~40% reduction).

This ADR formalizes that protocol as an architectural commitment so that future slices (SLICE-003 first, every session-persisting slice thereafter) cannot silently regress it.

## Decision

Cairn commits to a three-layer context discipline protocol governing all session-to-session context transfer.

### Layer 1 — Handoff as pointer, not payload

`.claude/handoff.md` is a pointer artifact with strict structural commitments:

- Target token budget: **150–400 tokens**. Hard upper bound.
- Imperative/declarative voice only. No reflective prose.
- Required sections: `State` (current state, not history), `Next` (one imperative, one line), `Blocked / Pending` (max 5 one-liners with pointers), `Pointers` (annotated file references).
- Forbidden sections: "What This Session Was About", "What Was Accomplished", "Surprises or Discoveries", "Self-Check", narrative paragraphs of reasoning, test-run output with pass/fail tallies. These belong in commit messages, `git log`, ADRs, or `docs/lessons.md` — not the handoff.

A canonical template lives at `templates/handoff.md`. The `/handoff` skill template enforces the format contract.

### Layer 2 — Tiered catchup with admission-gated main-context reads

`/catchup` runs in three tiers:

**Tier 1 — always runs, strictly bounded.** Reads only: `.claude/handoff.md`, `.claude/current-slice/slice.yaml` (if present), `.claude/sweep.yaml` (if present), `git log --oneline -5`, `git status --short`. Produces the orientation summary and stops. No other main-context file reads without Tier 2 admission.

**Tier 2 — dispatched via subagent.** The catchup skill template must contain the following admission-criteria block verbatim, which the main agent applies deterministically:

```
DISPATCH Tier 2 subagent if and only if:
  1. User asked a specific factual question that Tier 1 data did not answer, OR
  2. User directed entry into a specific pipeline phase and the handoff pointers
     explicitly list files for that phase, OR
  3. You are about to take an action that requires verifying the current state
     of a specific file, AND that file is named in the handoff pointers.

DO NOT DISPATCH Tier 2 if:
  - You are orienting "just in case"
  - Tier 1 data sufficed to answer the user
  - The user has not given you a concrete direction
  - You want to "be thorough"
```

The subagent is given a bounded contract (`CONTEXT`, `QUESTION`, `FILES AVAILABLE`, `YOUR BEHAVIOR`, `YOUR RETURN`, `DO NOT return`) and returns ≤200 words to main context regardless of underlying file size.

**Tier 3 — end of catchup.** When the user issues a direct work imperative, catchup is over. Normal file reading into main context is appropriate because the files are about to be modified. Tier 3 is the absence of catchup, not a third protocol step.

### Layer 3 — Slice closure wipes `.claude/current-slice/`

On transition to `status: complete`, `/start-slice` removes every file under `.claude/current-slice/`. The commit carrying the status transition IS the sole git-history record of the slice's artifacts — nothing else is preserved in the working tree. No archive directory is introduced; `git log` plus `.claude/learning.md` (append-only staging, wired by SLICE-003) together cover the post-mortem use case.

Failed slices remain an exception: the existing `.claude/completed-slices/<ID>-failed/` path preserves debugging context that successful closure does not need.

## Consequences

- **INV-002 becomes the enforcement hook.** ARCHITECTURE.md gains a new invariant pairing this ADR. Structural grep-based checks can assert handoff ≤400 tokens, catchup.md contains the literal admission block, and `.claude/current-slice/` is empty between slices.

- **The four-phase pipeline's role-reset property is restored.** Each phase's fresh session receives only the declared artifact — intent.md, test files, source files — with no narrative residue from the prior phase's reasoning.

- **SLICE-003 gains a stable interface to build against.** Self-learn automation depends on the handoff format existing as pointer-format and on `.claude/learning.md` existing as a staging ground. Because these are now an INV-002 commitment, SLICE-003's work cannot be silently broken by a future drive-by rewrite.

- **Cairn consumers inherit the protocol automatically.** Consumer projects mount cairn via `.slice-system → .` and invoke `/handoff` and `/catchup` through the symlinked skill templates. The protocol lands in consumers the moment they pull the updated cairn. No per-consumer migration is required.

- **The ~16.6k stable CLI baseline remains untouched.** This ADR addresses only the addressable ~14k of turn-1 dynamic context plus the ~16k of catchup inflation.

- **Measurement gate.** The design document commits to measuring post-catchup context after SLICE-002 lands and before SLICE-003 begins. If measurement misses the target by >30%, the decision is to stop and re-investigate. A measurement failure that exposes a structural flaw in the protocol is grounds for a superseding ADR, not silent drift.

## Alternatives Considered

**Keep the old narrative-handoff format and compress via `/compact`.** Rejected because `/compact` is symptom-level: it reclaims context mid-session after the damage is done, and its lossy summarization undermines the role-reset property further. The diagnosis is that narrative handoffs leak mental state across roles; compression does not fix leaking, it fixes volume.

**Eager main-context reads with a budget cap instead of a tier model.** Rejected because budget caps do not enforce the discriminating question of whether a read is justified. Any finite budget gets consumed by "just in case" reads until it binds, at which point the agent has already committed to low-value loads. The tier model's admission criteria change behavior; the ceiling does not.

**Archive `.claude/current-slice/` to `.claude/archive/<slice-id>/` on close rather than wipe.** The design document originally proposed this. Rejected after review: the archive's stated use case — post-mortem lookup of "how did SLICE-N handle X" — is already covered by `git log` plus the `learning.md` staging ground. An archive directory is additional state to maintain, index, and retention-police, whereas git history is free and authoritative. This ADR supersedes the archive proposal with wipe-on-close.

**Treat the protocol as operational-reference-only convention, no ADR.** Rejected because SLICE-003 is an immediate downstream dependency and the protocol will be referenced across every future slice that persists context between sessions. A convention in `operational-reference.md` can be rewritten by any future slice that touches that file; an ADR requires supersession. The firmness difference matches the load-bearing nature of the commitment.

**Write the ADR as `firmness: provisional`.** Rejected because SLICE-003 plans to build on this protocol within weeks and cannot take a dependency on a commitment formally marked "we may revisit this". The design document's measurement checkpoint is about whether the *implementation* achieved its savings target, not whether the *protocol direction* was correct — the protocol direction is settled.

## Risk Register

- **Risk:** The 150–400 token handoff budget is too tight for complex session endings and forces users to omit load-bearing state. **Mitigation:** the `Pointers` section can reference any number of external files; the budget constrains prose, not the link set. If unworkable in practice, the measurement checkpoint after SLICE-002 surfaces it and a superseding ADR relaxes the bound with data.

- **Risk:** The Tier 2 admission criteria are too restrictive and block legitimate main-context reads the user actually wanted. **Mitigation:** the user can always directly name a file in chat to force a read — Tier 2 governs the agent's self-initiated reads, not user-directed ones.

- **Risk:** Wipe-on-close loses debugging context from cleanly-closed slices whose artifacts would have been useful later. **Mitigation:** `git log --all -- .claude/current-slice/` recovers the pre-wipe state; `git show <commit>:path` retrieves any historical file. The wipe is working-tree cleanup, not deletion from git history.

- **Risk:** SLICE-003 turns out not to need the `learning.md` staging ground and the file becomes dead state. **Mitigation:** the file is four lines of header and costs nothing; if SLICE-003's design shifts, the file is removed as part of that slice's envelope.
