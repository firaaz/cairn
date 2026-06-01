# Phase 0.5 — User-journey trace (enabled `feat/<id>` model)

Journey: plan → branch off `dev` → `cairn-tdd-feature` (4 phase commits) → `merge --no-ff`.

## B1 — Operator has plan `docs/plans/<feature>.md`
Mechanism: skill Step 1 reads frontmatter `id:`/filename stem + `envelope:`. No gap; pre-dates branch.

## B2 — Create `feat/<feature-id>` off `dev`
Mechanism (D1/D6): operator runs `git switch -c feat/<id> dev`. Branch-agnostic skill commits to HEAD (context.md:38). **GAP G1 (naming-drift):** nothing asserts `<feature-id>` in branch name = plan `id:`. D3 names the taxonomy but no hook validates it; a typo'd branch still gets 4 commits. Cosmetic-only — skill keys off plan, not branch.

## B3 — `SNAPSHOT_SHA = git rev-parse HEAD` (Step 2)
Mechanism: captured at branch tip = branch point off `dev`. Baseline file `/tmp/<feature-id>-baseline-failures.txt` (Step 30/36) pins pre-existing failures. **No gap on a single branch:** SNAPSHOT_SHA is a SHA, branch-independent; Phase-4 diff stays correct. **GAP G2 (`/tmp` collision):** baseline path has no branch/run qualifier — two concurrent features (or a re-run) share `/tmp/<feature-id>-baseline-failures.txt`; same id ⇒ clobber. Single-feature interim hides it; surfaces at D4.

## B4 — Phases 1–4 commit on `feat/`
Mechanism: 4 conventional commits to HEAD; envelope/role_guard write-gates unchanged (paths are repo-root-relative, branch-agnostic — role_guard.py:156). No gap.

## B5 — Phase-4 appends `.claude/handoff.md` (phase-4-tdd.md:18)
Mechanism: append one Pointers line; State/Next operator-owned. **GAP G3 (the sharp one):** `feature-slice-model` D1 says handoff lives *on `dev`*, but Phase 4 writes it on `feat/`. Pointers is a flat append-only list (handoff.md:13–49); every feature appends at the same EOF hunk. `--no-ff` does a 3-way merge — the first feature merges clean, but a *second* concurrent `feat/` whose Phase-4 append touches the same trailing region conflicts on merge. The conflict surfaces as `<<<<<<<`/`=======`/`>>>>>>>` markers, which `test_handoff_contract.py` treats as non-resolvable pointer lines ⇒ red suite post-merge, contract violated silently until tests run. D1 placement-on-`dev` is unreachable by an automated Phase-4 that only sees `feat/` HEAD.

## B6 — `git merge --no-ff feat/<id>` into `dev`
Mechanism (D2): operator-run; preserves 4 phase SHAs (no squash/rebase). **GAP G4:** skill Step 11 verifies `git log --oneline | head -4` == 4 phase commits — true at *Phase-4 tip on the branch*, but the skill **ends before the merge** (D6 interim: merge is operator-owned, post-skill). So nothing in-tool verifies the merge commit landed or that `head -4` still reads cleanly on `dev` after `--no-ff` (the merge commit is now HEAD, pushing phase-4 to position 2). No post-merge assertion exists; the 5th commit (merge) is unverified.

## B7 — `.claude/active-envelope.yaml` across branch vs worktree
Mechanism: worktree-scoped (CLAUDE.md). A plain `feat/` branch in the *same* worktree shares the existing envelope — `mode: operator` with the current `paths` (envelope:11–83 already covers `docs/adr/.*`, `tests/.*`, `.claude/**`). No behavior change. **GAP G5 (D5 only):** a *separate* worktree (precedent `.worktrees/feature-compression`) gets no envelope by default ⇒ fail-open (role_guard.py:151 `env is None` → allow) unless copied. Branch model = no change; worktree model = silent enforcement gap.

## Sharpest
G3 (concurrent handoff-append merge conflict + D1-placement contradiction), G4 (no post-merge verification of the merge commit), G2 (`/tmp` baseline collision). All three are masked by the solo/single-feature interim and bite at the D4/D5 concurrency line.
