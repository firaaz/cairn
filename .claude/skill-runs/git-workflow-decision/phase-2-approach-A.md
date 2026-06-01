# Phase 2 — Approach A (branch-per-feature + `merge --no-ff`)

Steelman of the operator's chosen direction: each `cairn-tdd-feature` run on `feat/<feature-id>` off `dev`; skill stays branch-agnostic (4 phase commits to HEAD); operator merges `--no-ff` into `dev`. SNAPSHOT_SHA = branch point.

## Constraint fit
**Satisfies cleanly:**
- **C1/C6 force-push + INV-001.** `--no-ff` is purely additive — never rewrites `dev`, so the force-push block (`reversibility-guard.sh:24-26`) never fires. INV-001's walk is `--no-merges` (`validate_architecture.py:362,367`), so the merge bubble is excluded and the 4 registered phase prefixes are all the walk sees (C6).
- **C3 ADR append-only.** Branch model touches no ADR hook path; supersession is the normal frontmatter-Edit + new-file Write, identical to any `/decision`.
- **C8/C9 SNAPSHOT_SHA.** `--no-ff` preserves the 4 phase SHAs, so intent.md/sweep-notes pointers and the Phase-4 baseline diff stay resolvable. This is A's *load-bearing* fit: D2's rebase rejection exists precisely to protect it (C9, F6).
- **C14/C17 naming.** `feat/<feature-id>` reuses the flat-slug `id:`; commit scope already `<type>(<feature-id>)`. Consistent with INV-005.
- **C8 branch-agnostic skill.** The skill creating no branch/no merge is *exactly* what A's D6-interim wants — zero skill change required.

**Strains:**
- **C10 (operator-session envelope).** The `--no-ff` merge runs in an operator session (`AGENT_ROLE` unset), so `active-envelope.yaml` must permit `docs/adr/` + hooks if `mode: operator`. Bash `git merge` itself is ungated — neither hook touches merge direction (the F5 hole).
- **C11/INV-002 handoff-on-dev.** Phase 4 appends the pointer on `feat/`, not `dev`. `--no-ff` carries it back, so solo it lands on dev *by accident* — but the placement contract (`feature-slice-model.md:48-52`) is technically unmet at write time.
- **C20 derived status.** "Complete = branch merged" re-anchors onto `feat/<id>` merge; the derivation table still cites slice branches and must be amended.

## Pre-mortem exposure
- **F1 (handoff collide):** *Mitigated solo* — single `--no-ff` lands the append cleanly. *Residual:* deferred-D4 concurrent merge is a textual conflict in the Pointers block → `test_handoff_contract.py:74` reds. Honest: A does not fix this; it defers it to the D4 line.
- **F2 (unregistered merge subject):** *Avoided by `--no-merges`* — but the avoidance is undocumented and one-flag-fragile. The ADR must pin `--no-merges` as the contract that *makes `--no-ff` legal*, else a future flag drop reds every historical merge.
- **F3 (`/tmp` baseline clobber):** *Avoided solo single-run.* Residual at D4 (concurrent / re-run clobber); not introduced by A's committed scope.
- **F4 (log noise):** **Not avoided — A causes it.** Every feature = 5 commits (4 phase + 1 merge), 25% merge bubbles on `dev`. INV-001 is fine (`--no-merges`), but `/catchup` and cut-point selection walk a bubbled log. Honest: this is A's standing cost, immediate and scaling with volume, not concurrency.
- **F5 (no merge guard):** **A's worst exposure.** `reversibility-guard.sh:21-31` guards `rm -rf`/force-push/`reset`/`clean` only — no merge-direction, no merge-omission, no `-ff`/squash block. D2 rejects squash *in prose*; the hook layer is silent. The entire committed audit-trail guarantee rests on operator discipline with zero mechanical backstop. A cannot close this without new tooling (out of committed scope).
- **F6 (stale-dev rebase):** *Mitigated* — `--no-ff` preserves SHAs. Residual: nothing *forbids* a tidy-rebase before merge, which would dangle every phase SHA. Must forbid mid-feature rebase in prose.

## Downstream impact
- **`/catchup`:** must skip merge commits when reconstructing phase history (or read first-parent), else the 5th commit pollutes the per-feature view (F4).
- **`release`/`dist/` cut (m5, INV-012 sha-pin):** `feat/` merges into `dev`, never `release` — sits upstream of the cut cadence, no boundary change. Cut-point SHA selection walks a bubbled log but pins a real SHA; legibility tax only.
- **Dispatch skill:** unchanged — branch-agnostic-to-HEAD is already true; D6-interim is consistent (C8).
- **3 superseded ADRs:** `feature-slice-model` D1/D4/D5 + D0 amend; `identifier-scheme` D4 supersede + D2 "Slice" row amend; `parallelism-v1` Consequences-punt re-homed as deferred D4/D5.

## What the ADR must pin to make A safe
1. **`--no-merges` walk contract** — record that INV-001's walk excludes merge commits; this is the invariant that legalizes the `--no-ff` bubble (F2). Forbid dropping the flag without re-handling merge subjects.
2. **Forbid mid-feature rebase** — phase SHAs are pinned vs SNAPSHOT_SHA; no rebase/squash between branch and merge (F6, D2).
3. **Merge ceremony** — operator-owned `git merge --no-ff` only; explicitly reject `-ff` and squash in the committed text, since no hook enforces it (F5).
4. **Handoff-placement supersession** — supersede `feature-slice-model` D1 "handoff on dev"; record that Phase-4 appends on `feat/` and `--no-ff` carries it back, flagging the concurrent-append conflict as a deferred-D4 open question.

---
**Summary (5 lines)**
1. Strongest advantage: `--no-ff` preserves the 4 phase SHAs, so the entire SNAPSHOT_SHA-anchored audit chain (intent.md, sweep-notes, Phase-4 baseline, handoff pointers) stays resolvable with zero skill change.
2. Worst exposure: F5 — operator-owned merge has no hook guard; one `-ff`/squash slip irreversibly destroys the 4-commit trail D2 exists to protect (pure-instruction enforcement, gh#17 class).
3. Must-pin: `--no-merges` walk contract (legalizes the bubble).
4. Must-pin: forbid mid-feature rebase/squash (protects phase SHAs vs SNAPSHOT_SHA).
5. Must-pin: merge ceremony — `--no-ff`-only, reject `-ff`/squash in prose + supersede handoff-on-dev placement, flagging concurrent-append as deferred D4.
