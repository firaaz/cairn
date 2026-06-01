# Decision context — git-workflow-v1

**Question:** Canonicalize cairn's git working-branch + merge + naming model post-orchestrator-retirement, and formally supersede the firm ADRs that describe a retired branch-per-slice model.

This file is the shared brief. Agents: read it, then read only the specific files your task names. Keep outputs to the artifact your task specifies; cite `file:line`.

---

## The problem (bifurcation)

The merge model isn't just undocumented — the firm ADRs describing it reference machinery retired at M4 (2026-05-07).

- **Post-M4 reality (authoritative).** `.claude/skills/cairn-tdd-feature/SKILL.md` is the dispatch primitive. It emits **4 phase commits** to whatever branch HEAD is on, creates **no branch**, has **no merge step**:
  - Phase 1 `feat(<id>): phase 1 — intent`; Phase 2 `test(<id>): phase 2 — RED tests`; Phase 3 `feat(<id>): phase 3 — implementation`; Phase 4 `chore(<id>): phase 4 — sweep + handoff`.
  - SKILL.md:91 "the git log is the durable record; no slice.yaml." SKILL.md:93-95 "Coexistence with the orchestrator" note is **stale** (orchestrator retired).
  - Feature id derives from plan-doc frontmatter `id:` or filename stem; per-feature plan at `docs/plans/<feature>.md`.
  - SKILL.md:56 captures `SNAPSHOT_SHA = git rev-parse HEAD` at start; Phase 4 baseline diff anchors on `/tmp/<feature-id>-baseline-failures.txt` (SKILL.md:30,36).
- **Recent `dev` history confirms** work lands directly on `dev` (native phase commits, no merges).

### Firm ADRs that contradict reality (the supersession targets)

- `docs/adr/feature-slice-model.md` (**accepted, firm**) — D1: feature files on feature branches, `slice.yaml` on slice branches; D4: "Complete = branch merged"; D5: trigger events `/start-slice` + `/handoff` (both **retired** with the orchestrator). D0: slice = unit of execution (slice unit retired).
- `docs/adr/identifier-scheme.md` (**accepted, firm**) — D4: slice branch naming `slice/<feature>/<slice>`. The id+name two-field model (D1/D2/D3/D9) stays firm; only D4 + the D2 "Slice" entity row are affected.
- `docs/adr/parallelism-v1.md` (**accepted, provisional**) — concurrent slices on separate worktrees/branches via `after` deps; **explicitly punts** branching strategy, worktree creation, merge ordering to "the slice that operationalizes parallelism" (Consequences) — which **never shipped** (orchestrator retired first).

### Already-settled (out of scope — cross-reference, do not reopen)

- `docs/adr/m5-plugin-distribution-and-symlink-retire.md` (**firm**) — dev → `release` branch → curated `dist/` → `v0.x.y` tags. The dev→release→tag cadence is NOT part of this decision.
- `docs/adr/slice-close-contract-superseded.md` — records the M4 retirement of `close_slice`/`slice_orchestrator`. Useful background on why the slice unit is gone.

---

## Operator decisions (already made — do not re-litigate; pressure-test, don't re-select)

1. **Vehicle:** full `/decision` → ADR `docs/adr/git-workflow-v1.md`.
2. **Branch model = Approach A:** `feat/<feature-id>` branch off `dev` per `cairn-tdd-feature` run; integrate via `git merge --no-ff` to preserve the 4 phase commits.
3. **Narrow committed output:** the ADR commits only D1/D2/D3 + supersession. D4/D5/D6 are **recorded as deferred open questions** (operator is solo today; concurrent-merge/worktree machinery is unmeasured — `commit-only-evidence-supports`).
4. **Interim D6:** branch create/merge is **operator-owned**; the skill stays branch-agnostic (commits to HEAD). Skill automation is the deferred part.

### Committed decision points
- **D1** Working-branch model: `feat/<feature-id>` off `dev`.
- **D2** Merge mechanism: `git merge --no-ff` into `dev`. Reject squash (destroys phase-commit audit trail). Reject rebase-onto-dev as the integration step (rewrites phase SHAs that intent.md/sweep-notes pin vs SNAPSHOT_SHA).
- **D3** Naming: unit is now **feature**; branch taxonomy `feat/<feature-id>` (active), `plan/<…>`, `archive/<…>`, `abort/<…>`. Supersede identifier-scheme D4.

### Deferred (record as open questions, gated on first real concurrent feature)
- **D4** Concurrent / out-of-order completion (rebase-or-re-merge rule for trailing feature).
- **D5** Worktree lifecycle (optional worktree create + cleanup). Live precedent: `.worktrees/feature-compression` on `archive/compression`.
- **D6** Skill automation of branch lifecycle (vs operator-owned interim).

---

## Known constraints (from CLAUDE.md + hooks — cite these, don't re-derive)

- **Force-push blocked**; `--force-with-lease` allowed (`checks/reversibility-guard.sh:24-26`). `git reset --hard`, `git clean -fd`, `rm -rf` blocked.
- **ADRs append-only** (`reversibility-guard.sh:59-106`): `Write` allowed on new ADR file; overwriting existing blocked; `Edit` allowed only for frontmatter (first line matches `status:`/`superseded-by:`/`superseded_by:`/`firmness:`). Escape hatch `ADR_EDITORIAL_FIX=1`. The glob is `docs/adr/*.md` — matches flat-slug names, so `git-workflow-v1.md` is protected and the new-file Write is permitted.
- **Edit canonical paths only**, never via `.slice-system/` (role_guard denies the prefix).
- **Commit convention:** conventional commits with scope `<type>(<feature-id>): …`.
- **No hardcoded timeouts/sizes** in consumer-facing scripts; env-var override with cairn default.
- **supersedes-sections:** frontmatter field exists for partial supersession (identifier-scheme uses it) — supersede *sections*, not whole ADRs, since these ADRs carry still-valid decisions.

## Supersession scope (precise)
- `feature-slice-model`: supersede D1, D4, D5; amend D0.
- `identifier-scheme`: supersede/amend D4; amend D2 "Slice" row. Rest stays firm.
- `parallelism-v1` (provisional): amend its open "implementation concern" by recording D4/D5 as deferred here. Phase 3 decides whether substantive enough to warrant `parallelism-v2` (per identifier-scheme D3 versioning).
