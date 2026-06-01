# Phase 2 — Approach B: worktree-per-feature + `git merge --no-ff`

Every feature gets its OWN worktree (`.worktrees/<feature-id>`) + `feat/<feature-id>` branch off `dev`; merged `--no-ff` into `dev` on close. Live precedent: `.worktrees/feature-compression` on `archive/compression` (context.md:47, phase-0.5 G5). B is A plus physical-directory isolation.

## Constraint fit

B inherits all of A's fit — `--no-ff` is additive (no force-push, C-1/C-6), preserves the 4 phase SHAs vs SNAPSHOT_SHA (C-9/C-16, D2 rebase-rejection still load-bearing), merge subject excluded by `--no-merges` walk (C-6/INV-001, F2), `feat/<feature-id>` flat slug matches INV-005 (C-14). Worktree-specific:
- **Envelope worktree-scope (G5, role_guard.py:151).** `.claude/active-envelope.yaml` is per-worktree (CLAUDE.md). A fresh worktree has *no* envelope ⇒ `env is None` ⇒ **fail-open**, silently disabling write-gating. B must copy the envelope into every worktree at create time, or it ships with the operator-session guard off — a regression A never has (A reuses the existing worktree's envelope, phase-0.5 B7).
- **Symlink recursion (C-19/INV-011).** `.slice-system → .` is an infinite-depth loop. A new worktree re-materializes the self-symlink; any `feat/`-branch globbing (catchup, baseline scans) inside the worktree must exclude `.slice-system`. Same hazard as A, but B multiplies the entry points by worktree count.
- **`/tmp` sharing (G2/F3).** `/tmp/<feature-id>-baseline-failures.txt` (SKILL.md:30,36) is **not** worktree-scoped — it is global. Two worktrees with re-used ids clobber the same file. **B does not fix this**; physical dir isolation stops at the worktree boundary, and `/tmp` is outside it.

## Pre-mortem exposure (F1–F6)

- **F1 (handoff collision) — B does NOT fix it.** This is the decisive finding. Both worktrees still merge to the *same* `dev`; each Phase 4 appends a Pointers line to its own `.claude/handoff.md` copy, and the second `--no-ff` merge conflicts on the shared trailing region exactly as in A (phase-0.5 G3). Isolation prevents *concurrent-edit-of-one-file* races, but the conflict is at the **shared merge target**, not the working tree — worktrees give every feature its own tree and still funnel into one `dev`/one `handoff.md`. B buys nothing here.
- **F3 (`/tmp` baseline clobber) — B does NOT fix it.** Global `/tmp`, above.
- **F2 (unregistered merge subject) — same as A.** D2 solo, first merge.
- **F4 (5-commits/feature log noise) — same as A.** B adds no commits; identical legibility tax.
- **F5 (operator-owned merge, zero guard) — B *worsens* it.** Now the operator must also create, populate, and tear down a worktree (D5 lifecycle parallelism-v1 left open). More un-guarded manual steps = more slip surface (forgotten teardown, stranded `.worktrees/<id>`, merge from wrong dir).
- **F6 (stale-dev rebase) — same as A,** with one *genuine win*: a long-lived worktree on its own branch is the natural home for a feature that must outlive `dev` churn without polluting the main tree.

**What B actually solves that A does not:** concurrent features never share a *working directory* — no dirty-tree-across-boundary (L-011/C-10) leakage between features, no stash dance to switch features mid-flight, no half-applied edits from feature A visible to feature B's hooks. That is real, and only matters when two features are genuinely in-flight at once.

## Cost

- **Lifecycle D5 (parallelism-v1 punt, never shipped — context.md:47,64).** B *requires* operationalizing the create+cleanup machinery the deferred D5 explicitly leaves open. Create: `git worktree add .worktrees/<id> -b feat/<id> dev` + copy envelope + verify symlink. Cleanup: merge, `git worktree remove`, `git branch -d` — and `rm -rf`/`clean -fd` are blocked (C-2), so a dirty worktree can't be force-removed; teardown is fiddly.
- **Envelope-copy burden** every create (else fail-open, above).
- **Disk** — N working trees of the full repo.
- **Symlink hazard** re-materialized per worktree.

## When B beats A

B pays for its overhead only when **two+ features are genuinely concurrent and one is long-running** — e.g. a multi-day feature whose dirty tree would otherwise block all other work, or a spike you want to keep buildable while shipping fixes on `dev`. Then physical isolation > stash-juggling, and the worktree create/teardown amortizes over days. For one feature at a time, B is pure overhead: A's single-tree branch gives identical merge semantics with none of the lifecycle, envelope-copy, or disk cost.

---

**Summary (5 lines):**
1. B's strongest advantage over A: true physical working-tree isolation — concurrent features never share a dirty tree, no stash-juggling, no cross-feature hook bleed (L-011 boundary).
2. B does NOT fix F1 — both worktrees merge to the same `dev`/`handoff.md`, so the Phase-4 append still collides at the shared merge target; isolation helps working-tree races, not shared-target conflicts.
3. B also does NOT fix F3 — `/tmp/<id>-baseline` is global, outside the worktree boundary — and it *worsens* F5 by adding un-guarded create/teardown steps.
4. B forces operationalizing the D5 worktree lifecycle parallelism-v1 deliberately deferred, plus per-worktree envelope-copy (else fail-open) and the per-worktree symlink hazard.
5. For a solo operator today (one feature at a time), B is not worth its overhead: it solves a concurrency problem the operator doesn't yet have while leaving F1/F3 exactly where A does — defer B to the first real concurrent feature (the D5 line), exactly as the committed scope already gates it.
