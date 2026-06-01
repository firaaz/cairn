# Phase 5 — Independent verification: cairn's working-branch + merge + naming model

Derived from scratch (SKILL.md, the 3 ADRs, ARCHITECTURE.md, both guards, the validator, phase-4-tdd.md, live git state). Did not read the other analyst's run.

## Recommendation

**Branch-per-feature + `--no-ff` merge into `dev`, branch named `feature/<feature-id>`.**

One short-lived branch per `cairn-tdd-feature` run. The skill's 4 commits (intent / RED / impl / sweep) land on the branch off `dev` at SNAPSHOT_SHA; finish with `git merge --no-ff`. Default to native branches, not worktrees — worktrees are an *option* for concurrent features (parallelism-v1 D1), not the baseline.

### Why `--no-ff`, decisively

`scripts/validate_architecture.py:367` runs the INV-001 walk with `--no-merges`:
```python
["git", "log", range_arg, "--no-merges", "--format=%H%x09%s", "--name-only"],
```
So merge commits are *never* classified — a `Merge branch...` subject (no CC prefix → would fail the classifier) is skipped. `--no-ff` is therefore the only mechanism that (a) preserves all 4 phase commits verbatim for INV-001's per-prefix verifiers and the phase-4 audit trail, and (b) keeps the merge node invisible to the walk. Verified: repo history is currently 100% linear on `dev` (no merge commits exist yet), so this introduces the first merge nodes — safe under the walk.

- **Squash → reject.** Collapses 4 commits into 1, destroying the intent/RED/impl/sweep prefixes the registry verifies and the audit trail phase-4 cites. Also orphans SNAPSHOT_SHA (the squash commit's parent is `dev`, not the snapshot the skill captured).
- **Rebase/ff → reject.** Linear, but the merge node carries no record of feature boundary, and rebasing rewrites the 4 commit SHAs that phase-4 sweep-notes and `git show <commit_hash>` (SKILL.md step 5/11) already reference.

## Pre-mortem (≥3 failure modes)

1. **Phase-4 commits the sweep on the feature branch; `--no-ff` merge subject is auto-generated and unverified.** Mitigated: walk skips merges. But a *consumer* with a stricter walk would break — must pin "merge subject is exempt by `--no-merges`" in the ADR.
2. **Operator forgets to branch; 4 commits land on `dev` directly.** This is today's behavior and is *not* wrong under INV-001 (envelope-gated direct work is registered). Risk is loss of feature isolation, not a guard failure. The ADR must state direct-to-dev remains legal (fallback), not forbidden — else honest current history violates a new firm rule retroactively.
3. **Concurrent features touch the same file; no `after` graph exists post-orchestrator.** parallelism-v1's `after` field lived in feature files the orchestrator wrote; the skill writes none. Merge-time conflict is the only backstop. ADR must say: serialize by default, worktrees opt-in, conflicts resolve on the branch before merge.
4. **role_guard envelope is worktree-scoped + `AGENT_ROLE` often unset on dispatch** (per the live envelope's own M7 note) → a feature branch in a new worktree has no `active-envelope.yaml`, so operator-session writes are unguarded there. ADR must require envelope-copy on worktree creation.

## Must-pin list (for safety)

1. **Merge mechanism = `--no-ff`**, and an explicit statement that the merge commit is exempt from INV-001 *because* the walk uses `--no-merges` (cite `validate_architecture.py:367`). If that flag ever changes, the merge subject must adopt a registered prefix.
2. **Branch naming.** Supersede identifier-scheme D4 (`slice/<feature>/<slice>`) — there is no slice unit post-M4. Pin `feature/<feature-id>`, `feature-id` = the skill's frontmatter `id:`/filename stem. Flat, not hierarchical (no slice child).
3. **Base = SNAPSHOT_SHA.** Branch is cut at the SHA the skill captures (step 2) so the 4 commits' parent chain matches what phase-4 audits against the baseline.
4. **Direct-to-dev stays legal** as the single-feature fast path (envelope-gated); branch-per-feature is the default, not a hard gate. Avoids retroactively invalidating linear `dev` history.
5. **"Complete" redefinition.** feature-slice-model D4 says Complete = *branch merged*; that survives, but retire the slice.yaml/feature-file machinery it depended on. Pin: Complete = feature branch merged `--no-ff` into `dev` with phase-4 sweep PASS.
6. **Worktree lifecycle** (parallelism-v1 punted this): if a feature uses a worktree, copy `.claude/active-envelope.yaml` into it (role_guard is worktree-scoped, fail-open when absent on the unset-`AGENT_ROLE` path).
7. **Supersede the three stale ADRs** — feature-slice-model (branch-per-*slice*), identifier-scheme D4 (slice branch naming), parallelism-v1's punted worktree lifecycle — in the governing ADR's frontmatter `supersedes`/`supersedes-sections`, or the validator's Check B/C flags drift.
