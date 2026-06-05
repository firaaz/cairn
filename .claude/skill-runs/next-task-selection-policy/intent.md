---
id: next-task-selection-policy
name: "Codify the next-task selection policy in operational-reference.md"
snapshot-sha: fd6576f3db2bc50016602946fa007963e8514677
invariants-touched: []
---

## Operator Prompt
> the question is simple -- we need to have a way to figure out the next task, what systematic way do we have for it -- is there a plugin or anything to help with thay
>
> [follow-ups] "I would actually prefer a research before we get into this -- AI has a build everything at home -- but this adds maintenance and only one person instead of people who are actively working on that" / "quick scan + methods and research -- use subagents and ultracode to help"

## What
Add a `## Next-task selection` section to `docs/operational-reference.md` that codifies the selection policy as a written ranking ladder anchored to signal cairn already carries (handoff `open|blocked|deferred` states, GitHub `severity:S1/S2` labels, `docs/roadmap.md` `Depends on` ordering). The policy turns an unwritten heuristic into a repeatable, auditable procedure. No new tool, no code, no command, no new file.

## Why
Research (workflow `wf_3f3b1c0d-7a7`) + repo verification established that the gap is a **policy gap, not a tooling gap**: no off-the-shelf tool ranks "next" for cairn's constraints; the planning-substrate adopt-decision is already made (`board-as-roadmap-substrate`, GitHub Projects v2) but is capture-only and largely unbuilt, and **nothing anywhere ranks which open item to work next**. A bespoke ranker is rejected (operator's build-at-home/drift allergy; mirrors the ADR's own F5 hard-coupling-drift risk). Codifying the policy is the lowest-maintenance, zero-drift fix.

## Boundary
Does NOT build a ranking script, command, or `/next` aid; does NOT adopt external SaaS; does NOT advance or relitigate the board ADR; does NOT add new GitHub fields or any new data the operator must maintain; does NOT create a new standalone doc file.

## Specification
- Target file: `docs/operational-reference.md` (in the write envelope; a standalone `docs/next-task-selection-policy.md` is NOT in the envelope and would be denied).
- New section heading: `## Next-task selection` (placed adjacent to the routing / context-discipline material).
- Content is a 6-rung ladder: (1) `blocked` rots → unblock or surface; (2) `deferred` is parked behind its trigger → skip until it fires; (3) finish-started beats start-new (staged → unpushed → paused-mid-trial → fresh); (4) tiebreak severity `S1 > S2`; (5) tiebreak roadmap `Depends on` order (lowest unblocked Must-land first); (6) route by weight (outward-facing / decision-weight → surface to operator).
- Each rung names the existing signal source it reads. ≤ ~1 page (≤ ~60 lines added).

## Verification
- `grep -n "Next-task selection" docs/operational-reference.md` resolves to the new heading.
- The section references only existing signal sources (handoff state, `severity:` labels, roadmap `Depends on`) — no new field/command/file named as a maintenance surface.
- Dogfood: applying the written ladder to the current `.claude/handoff.md` reproduces a defensible next pick (recorded in the close / field note).
- `git diff --stat` shows only `docs/operational-reference.md` changed by the construct step.

## Risk Surface
The policy could codify a heuristic that *reads* systematic but yields a wrong/contested pick on real backlog state — domain wrongness that no grep catches. The close-review must smell-test the ladder against an actual handoff state, not just confirm the section exists.

## Feature-Local Invariants
- The section introduces no new maintained data: every signal it reads (handoff state, severity labels, roadmap deps) already exists and is populated independent of this policy.

## Explicit Scope-Out
- The optional read-only `/next` aid and the board D2/D4/D7 implementation slice are deferred (separate tracks; default-no until the written policy proves insufficient).

## Premise Grounding

```yaml
premises:
  - source: docs/adr/board-as-roadmap-substrate.md
    quote: |
      The board is **never** a mirror of cairn-side state.
    label: "the board is a capture surface, not a ranked view of the backlog — it does not answer 'which task next'"
  - source: docs/adr/board-as-roadmap-substrate.md
    quote: |
      None of the four are required by this ADR.
    label: "the board-driven PM commands are decided-but-unbuilt, so no built path ranks the next task"
```

## Contract

```yaml
scope-statement: add a written next-task selection ladder to operational-reference.md, anchored to existing handoff/severity/roadmap signal, introducing no tool or new maintained data
must-satisfy:
  - the operational-reference.md section shall present the six-rung selection ladder in order
  - clause: every rung shall name the existing signal source it reads
    except: "universal-set: the rungs are the 6 enumerated in this intent's Specification"
  - if a rung would require a new field, command, or file the operator must maintain, then the section shall not introduce it
must-not-violate:
  - no new standalone doc file is created; the policy lives in docs/operational-reference.md
  - no executable ranking logic (script/command/weights) is added
wrong-if:
  - applying the ladder to the current handoff state yields an indefensible or contradictory next pick
  - the section names a signal source that does not already exist in the repo
escalate-when:
  - the ladder cannot resolve a defensible pick from existing signal without inventing a new maintained input
evidence:
  - grep of docs/operational-reference.md shows the new heading and the six rungs
  - git diff --stat shows only docs/operational-reference.md changed
  - a dogfood note recording the ladder applied to the current handoff
execution-scope:
  - docs/operational-reference.md
  - .claude/skill-runs/next-task-selection-policy/
  - .claude/handoff.md
  - docs/operator-field-notes-2026-06-05.md
```
