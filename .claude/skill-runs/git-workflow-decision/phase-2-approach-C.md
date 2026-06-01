# Phase 2 — Approach C (status quo): direct-to-dev / rebase-stacked

Two sub-variants of "no merge model." **C1 direct-to-dev**: 4 phase commits straight onto `dev`, no branch, no merge (today's reality — context.md:13-18). **C2 rebase-stacked**: `feat/` branches that rebase onto `dev` and fast-forward (linear, no bubbles).

## Constraint fit

**C1 — the cleanest INV-001 story of any approach.** No merge commit ever exists, so the `Merge branch …` unregistered-prefix question (constraint-6 `[V]`, F2) cannot arise. `git log` on `dev` is already exactly the 4 registered phase prefixes; the `--no-merges` walk and the human walk see *identical* history. SNAPSHOT_SHA (constraint-9) is captured on `dev` HEAD and never rewritten — phase SHAs that intent.md/sweep-notes/handoff pin stay valid forever. Force-push block (constraint-1) is a non-event: C1 only ever appends. Zero new machinery, zero supersession-execution risk, lowest cost. This is the pillar: **C1 is the only approach with no merge-commit prefix gap and no SHA-rewrite surface at all.**

**C2 — force-push block makes it fragile.** Rebase+ff needs the feat branch rebased (rewrites *its* SHAs) then `dev` fast-forwarded. The ff update to `dev` is additive (allowed), but any re-rebase after a failed push, or pushing the rebased feat branch to a remote, trips `reversibility-guard.sh:24-26` unless `--force-with-lease` is used deliberately. Linear history is preserved, but at the cost of the very property D2 protects.

## Pre-mortem exposure (F1–F6)

**C1 dodges F1/F4/F5/F6 outright.** No branch ⇒ no handoff-append-on-wrong-branch (F1) and no merge conflict surface. No merge commit ⇒ no 5th-commit log noise (F4 — `dev` stays 4 commits/feature, not 5). No operator-owned merge ⇒ no `-ff`/squash/forgotten-merge slip (F5). No rebase-before-merge temptation (F6). C1 is genuinely the lowest-exposure variant on the solo path. F3 (`/tmp` baseline clobber) still bites under concurrency, but that is approach-independent.

**C2 hits F6 HARD — this is disqualifying.** Rebase-stacked makes SHA rewrite the *integration mechanism*, not an avoidable operator slip. Every rebase onto an advanced `dev` rewrites all 4 phase SHAs (constraint-9 `[V]`, F6). intent.md/sweep-notes pin phase SHAs against SNAPSHOT_SHA; the Phase-4 baseline diff and the handoff commit-pointer (`test_handoff_contract.py:122`) dangle the instant the rebase lands. D2 rejects rebase-onto-dev *by name* (context.md:42) for exactly this reason — C2 is the rejected mechanism elevated to policy.

## The fatal gap

The operator's explicit ask is three things: **define how MERGE works**, **branch-per-feature isolation**, and **parallelism-v1 enablement** (context.md:3, D4/D5). C cannot deliver any of them.

- **C1 has no merge to define and no isolation.** The question is unanswerable inside C1 — there is no branch, so there is nothing to merge and nothing to isolate. parallelism-v1's punt (constraint-24, `parallelism-v1.md:85-87`) stays an open hole forever; concurrent features would interleave phase commits on a single `dev` line, which the 4-ordered-phase invariant (INV-003, constraint-7) cannot disentangle.
- **C2 produces a merge-shaped answer but destroys the audit anchor.** Linear history reads well, but rebase rewrites the phase SHAs that are the *durable record* (SKILL.md:91, "the git log is the durable record"). C2 buys legibility by demolishing the thing D2 exists to preserve.

C is cheapest precisely because it does the least — and the operator's goal is to add structure C definitionally lacks.

## What survives into A

- **C1's clean INV-001 story** is the bar A must clear: A's `--no-ff` must keep the walk's `--no-merges` filter (F2) so `dev`'s *non-merge* history stays as clean as C1's. Pin `--no-merges` in the ADR as the contract that makes `--no-ff` legal.
- **The `--first-parent` view** recovers C1-grade linear readability *on top of* A's bubbles: `git log --first-parent dev` collapses each feature to one line, neutralizing F4's legibility tax. `/catchup` and the m5 cut-point walk should adopt it. This is the single most valuable carry-over — it gives A C1's readability without C's missing isolation.

---

**Summary (5 lines):**
1. C1's strongest pillar: the only approach with zero merge-commit prefix gap and zero SHA-rewrite surface — `dev` is already exactly 4 registered phase commits/feature, SNAPSHOT_SHA never dangles.
2. C1 dodges F1/F4/F5/F6 on the solo path; it is genuinely the lowest-cost, lowest-exposure variant.
3. Fatal gap: C1 has no merge to define and no branch isolation, so it cannot answer the operator's ask or enable parallelism-v1 — it does the least by construction.
4. C2 is worse than the status quo: rebase-stacked makes SHA rewrite the integration mechanism (F6 HARD), demolishing the phase-commit audit anchor D2 explicitly rejects rebase to protect.
5. Salvage into A: pin `--no-merges` so A's non-merge history stays C1-clean, and adopt `git log --first-parent dev` to recover C1's linear readability without losing isolation.
