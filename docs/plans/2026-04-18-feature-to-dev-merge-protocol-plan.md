# Feature → dev merge protocol: first-instance execution plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Execute the first feature→dev merge in cairn (`feature/identifier-scheme` → `dev`) per the protocol defined in `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md`, producing the precedent for all future merges.

**Architecture:** Fix carry-over failures on feature branch (narrow patch). `git merge --squash` into dev. Apply tree cleanup in staged squash. Two commits on dev: one `feat:` (merged feature), one `docs:` (closeout + lessons + CLAUDE.md). Rename `feature/identifier-scheme` → `archive/identifier-scheme`. Push.

**Tech stack:** git, Python (pytest, ruff, `scripts/validate_architecture.py` — all via `uv run`).

**Working directory:** `/Users/mohammed.farook/Developer/lab/cairn/.worktrees/identifier-scheme` (the feature worktree). The `dev` branch is checked out in a *separate* worktree on disk — do not `git checkout dev` inside this worktree. Use `git worktree list` to locate the dev worktree before attempting step 3.

**Reference doc:** `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` (committed `9a951da`). All *why*-questions are answered there; this plan is *how*.

---

## Worktree topology preflight

Before Task 1, verify the worktree setup:

```bash
git worktree list
```

Expected: at least two entries — the primary clone (likely on `dev` or `master`) and this feature worktree on `feature/identifier-scheme`. The dev-branch worktree is where steps 3–13 run.

If no dev worktree exists, create one before starting:

```bash
cd /Users/mohammed.farook/Developer/lab/cairn
git worktree add .worktrees/dev dev
```

All `git checkout dev` commands in this plan should be interpreted as "switch to the dev worktree" (`cd .worktrees/dev`), not as an in-place checkout. This matches cairn's project-local worktree convention (`.gitignore` already excludes `.worktrees/`).

---

## Task 1: Identify the two carry-over pytest failures

**Files:**
- Read: `tests/unit/test_d3_bypass_log_format.py`
- Read: `.claude/sweep-results/2026-04-18-sweep-17.md` (failure context)
- Read: `.claude/d3-bypasses.log` (the log being validated)

**Step 1: Reproduce the failures locally**

```bash
cd /Users/mohammed.farook/Developer/lab/cairn/.worktrees/identifier-scheme
uv run pytest tests/unit/test_d3_bypass_log_format.py -v
```

Expected: 2 failures. Capture exact failure messages and test names.

**Step 2: Read the test file**

Read `tests/unit/test_d3_bypass_log_format.py` end-to-end. Identify:
- Which regex/validator the tests exercise.
- Which log line shape the failing tests expect vs. what the log actually contains.

**Step 3: Read the failing evidence**

Read `.claude/sweep-results/2026-04-18-sweep-17.md` §Finding 1 (the hierarchical-slug / bypass-log carry-over discussion).

Read `.claude/d3-bypasses.log` — look specifically at line 8 and any line with the non-conforming shape flagged in sweep #17.

**Step 4: Record diagnosis**

In a scratchpad (or in TaskCreate comments), record:
- Which regex needs widening (`CLASSIFIED_LINE_RE` per handoff)
- What the narrow patch looks like (what character class / alternation to add)
- Whether any log line needs its format patched, or only the regex widens to accept it
- Whether the "non-schema class token" failure needs a separate fix or is covered by the same widen

**No commit yet.** This is diagnostic.

---

## Task 2: Apply narrow patch and verify green

**Files:**
- Modify: whichever source file defines `CLASSIFIED_LINE_RE` (most likely `checks/*.sh` or `scripts/*.py` — find via `Grep`)
- Possibly modify: `.claude/d3-bypasses.log` (only if a log entry itself needs reshaping per Task 1 diagnosis)
- Possibly modify: `tests/unit/test_d3_bypass_log_format.py` (only if the test itself was wrong and the schema is correct — rare)

**Step 1: Locate the regex definition**

```bash
```
Use `Grep` tool with pattern `CLASSIFIED_LINE_RE` across the repo. Record file:line.

**Step 2: Design the narrowest patch**

Given the Task 1 diagnosis, write the minimum change that makes both failing tests pass without altering behavior on any passing test. Do NOT:
- Introduce the hierarchical-slug schema migration (that's the queued slice's job).
- Refactor the regex structure.
- Add new fields to the bypass log schema.

**Step 3: Apply the patch**

Use `Edit` tool. Single targeted change.

**Step 4: Run the targeted test**

```bash
uv run pytest tests/unit/test_d3_bypass_log_format.py -v
```

Expected: 0 failures.

**Step 5: Run full pytest suite**

```bash
uv run pytest
```

Expected: 0 failures. If anything else broke, revert the patch and reconsider — this is the signal that narrow-patch is insufficient and the bypass-log-hierarchical-slug slice must run first.

**Step 6: Run ruff and validator**

```bash
uv run ruff check
uv run python scripts/validate_architecture.py
```

Expected: clean / pass.

**Step 7: Stage and commit**

```bash
git add <changed-files-by-name>
git commit -m "chore: resolve test_d3_bypass_log_format carry-over ahead of dev merge

Narrow-patch <what>: <one-line>. Deferred full hierarchical-slug
migration to the queued v1-defense-d3/bypass-log-hierarchical-slug slice."
```

**Checkpoint 1 — feature green.** If pytest/ruff/validator all pass and the commit landed, Task 2 is complete. If any step red, stop the plan and route to the full bypass-log-hierarchical-slug slice instead.

---

## Task 3: Switch to dev worktree and prepare for merge

**Files:** none (git operations only)

**Step 1: Record the feature-branch tip SHA for archaeology**

```bash
cd /Users/mohammed.farook/Developer/lab/cairn/.worktrees/identifier-scheme
git rev-parse HEAD
```

Record the SHA (prefix `FEATURE_TIP_SHA` in notes).

**Step 2: Navigate to the dev worktree**

```bash
cd /Users/mohammed.farook/Developer/lab/cairn/.worktrees/dev
git status
```

Expected: on branch `dev`, working tree clean.

**Step 3: Verify dev is up to date (no surprise commits)**

```bash
git log --oneline -3
```

Expected: tip is `e71ddb5 chore: gitignore .worktrees/ for project-local worktree convention` (per earlier exploration). If anything newer, pause and reconcile — someone else (or an earlier session) pushed to dev.

**Step 4: Check for uncommitted changes or untracked files**

```bash
git status --short
```

Expected: empty. If not empty, deal with the outliers before proceeding.

---

## Task 4: Execute the squash merge

**Files:** staging only; no direct file edits yet.

**Step 1: Run the squash merge**

```bash
git merge --squash feature/identifier-scheme
```

Expected output: `Squash commit -- not updating HEAD` + `Automatic merge went well; stopped before committing as requested`.

If any merge conflict reports: stop. Dev has somehow diverged; reconsider before continuing.

**Step 2: Verify the staged changes**

```bash
git status --short | head -40
```

Expected: many files staged (A/M/D/R status). Cross-check against the earlier `git diff --stat dev..feature/identifier-scheme` count: ~112 files.

**Step 3: Do NOT commit yet**

The commit happens after Task 5 (tree cleanup). Confirm the stage is ready.

---

## Task 5: Apply tree cleanup in the staged squash

Operates on the staged index on `dev`. Each sub-step is independently verifiable.

### Step 5.1: Remove grandfathered gitignored files

```bash
git rm --cached .claude/handoff.md
git rm --cached .claude/adr-editorial-fixes.log
```

Expected: both succeed. These are `.gitignore`'d but tracked; removal is index-only.

If either errors with "not tracked": check whether the feature branch had already removed them. If so, fine — skip.

### Step 5.2: Reset current-slice state

**Inspect what's staged:**

```bash
git diff --cached .claude/current-slice/
```

**Decision:** the staged version of `.claude/current-slice/slice.yaml` contains the completed `identifier-scheme/doc-sweep` state. Reset it to an empty / "no active slice" stub.

**Check what dev had before:**

```bash
git show dev:.claude/current-slice/slice.yaml | head
git show dev:.claude/current-slice/.gitkeep 2>/dev/null
```

**Produce the reset state.** The simplest honest reset is "no active slice" content. If dev previously had a `.gitkeep` or stub, restore it. Example target:

```yaml
# .claude/current-slice/slice.yaml (stub — no active slice)
id: none
name: "No active slice"
status: none
```

**Apply:**

```bash
cat > .claude/current-slice/slice.yaml <<'EOF'
id: none
name: "No active slice"
status: none
EOF
git add .claude/current-slice/slice.yaml
```

### Step 5.3: Inspect slice-018-d3-oob.md

**Read the file:**

```bash
cat .claude/slice-018-d3-oob.md
```

**Decision tree:**
- If content is already captured in an ADR or in `docs/lessons.md` → `git rm --cached .claude/slice-018-d3-oob.md` (delete from the merge).
- If content is durable research → `git mv .claude/slice-018-d3-oob.md docs/plans/2026-04-16-slice-018-d3-oob.md` (migrate with date prefix).
- If content is unclear → leave staged as-is (default to preservation), and log the question in the post-merge open-questions list.

Document the decision in the scratchpad.

### Step 5.4: Migrate dogfood research to docs/plans/

Check whether the staged index already has these at their destination or still at source:

```bash
git diff --cached --stat | grep -E 'dogfood|manual-parallel'
```

If they're staged at `.claude/plans/`, move them:

```bash
git mv .claude/plans/2026-04-16-dogfood-observations.md docs/plans/2026-04-16-dogfood-observations.md
git mv .claude/plans/2026-04-16-manual-parallel-dogfood.md docs/plans/2026-04-16-manual-parallel-dogfood.md
```

Expected: moves staged cleanly; git detects them as renames.

### Step 5.5: Patch dogfood-log frontmatter

**Read current state:**

```bash
head -5 docs/dogfood-log.md
```

**Identify the retired identifier:** the frontmatter key `adr-003-landed-at-slice: 2` uses the retired numeric ID. Determine the current slug by inspecting `docs/adr/index.md` (or `git log --diff-filter=R` on the rename commit).

**Quick lookup:**

```bash
# check which ADR was adr-003 before the rename
git log --diff-filter=R --summary -- docs/adr/ | grep -i 'rename.*adr-003'
```

Most likely: `adr-003` → `cliff-failure-mode-and-v1-defenses` or similar. Verify.

**Patch the file.** Use `Edit` with exact old/new strings. Example (adjust slug):

```
old: adr-003-landed-at-slice: 2
new: cliff-failure-mode-and-v1-defenses-landed-at-slice: 2
```

Stage:

```bash
git add docs/dogfood-log.md
```

### Step 5.6: ADR-level cross-reference audit

```bash
```
Use `Grep` with pattern `adr-00[0-9]|SLICE-0[0-9]` scoped to `docs/adr/`. For each hit:

- **Prose context** (historical "previously known as …" mention) — leave alone.
- **Live cross-reference** (a `see: adr-00X` pointer or similar navigation aid) — patch to current slug using `Edit`.

Most ADR hits from earlier exploration are prose context. If unsure, leave and note in post-merge open questions.

### Step 5.7: Final staged-tree review

```bash
git status --short
git diff --cached --stat | tail -5
```

Expected:
- No `.claude/handoff.md` or `.claude/adr-editorial-fixes.log` in the staged index.
- `.claude/current-slice/slice.yaml` reset.
- Dogfood files at new paths under `docs/plans/`.
- `docs/dogfood-log.md` frontmatter patched.
- Total changed-file count consistent (smaller than the raw `dev..feature/identifier-scheme` diff by a few).

---

## Task 6: Commit the squash on dev

**Files:** creates the `feat:` commit on dev.

**Step 1: Assemble the commit message**

Use the template from the design doc (Section **Merge shape**):

```
feat: identifier-scheme — id/name split, ADR renames, slice renames, doc-sweep

Every ADR, slice, feature, and decision point now carries both `id:`
(immutable mechanical) and `name:` (mutable human-facing). Prose uses
name; cross-references, filenames, and hook inputs use id.

Slices: identifier-scheme/adr-rename-sweep,
identifier-scheme/slice-and-feature-rename,
identifier-scheme/doc-sweep.

ADRs: identifier-scheme (new); rename propagation across the full
corpus.

Carry-over absorbed into compression Slice A/B and the queued
v1-defense-d3/bypass-log-hierarchical-slug slice.

Archive: archive/identifier-scheme (post-merge rename preserves the
170-commit pre-squash history).
Closeout: docs/features/identifier-scheme.md (forthcoming in the
paired docs: commit).
```

**Step 2: Commit via heredoc**

```bash
git commit -m "$(cat <<'EOF'
feat: identifier-scheme — id/name split, ADR renames, slice renames, doc-sweep

Every ADR, slice, feature, and decision point now carries both `id:`
(immutable mechanical) and `name:` (mutable human-facing). Prose uses
name; cross-references, filenames, and hook inputs use id.

Slices: identifier-scheme/adr-rename-sweep,
identifier-scheme/slice-and-feature-rename,
identifier-scheme/doc-sweep.

ADRs: identifier-scheme (new); rename propagation across the full
corpus.

Carry-over absorbed into compression Slice A/B and the queued
v1-defense-d3/bypass-log-hierarchical-slug slice.

Archive: archive/identifier-scheme (post-merge rename preserves the
170-commit pre-squash history).
Closeout: docs/features/identifier-scheme.md (forthcoming in the
paired docs: commit).
EOF
)"
```

**Step 3: Verify the commit**

```bash
git log --oneline -1
git show --stat HEAD | head -30
```

Expected: single `feat:` commit on dev. File count consistent with tree cleanup.

---

## Task 7: Verify dev post-squash green

**Step 1: Run pytest**

```bash
uv run pytest
```

Expected: 0 failures.

**Step 2: Run ruff**

```bash
uv run ruff check
```

Expected: clean.

**Step 3: Run architecture validator**

```bash
uv run python scripts/validate_architecture.py
```

Expected: pass.

**Step 4 (red):** if anything fails, `git reset --hard HEAD~1` and return to Task 5 to reconsider tree cleanup. Do NOT force through.

**Checkpoint 2 — dev post-squash green.**

---

## Task 8: Write feature closeout doc

**Files:**
- Create: `docs/features/identifier-scheme.md`

**Step 1: Create the `docs/features/` directory**

```bash
mkdir -p docs/features
```

**Step 2: Author the closeout**

Use the `Write` tool. Template from design doc Section **Summary documentation artifacts**:

```markdown
---
id: identifier-scheme
name: "Identifier scheme"
status: merged
opened: 2026-04-15
merged: 2026-04-18
archive-branch: archive/identifier-scheme
---

# Identifier scheme

## What shipped

Every ADR, slice, feature, and decision point now carries both `id:` (immutable mechanical identifier) and `name:` (mutable human/LLM-facing label). Prose uses `name:`; cross-references, filenames, and hook inputs use `id:`. Full protocol in `docs/adr/identifier-scheme.md` and `docs/operational-reference.md`.

## Slices

- **identifier-scheme/adr-rename-sweep** — 2026-04-15 → 2026-04-16 — complete. ADRs renamed from numeric IDs (`adr-NNN`) to semantic slugs.
- **identifier-scheme/slice-and-feature-rename** — 2026-04-17 — complete. Slice and feature namespace migrated to feature-scoped slugs.
- **identifier-scheme/doc-sweep** — 2026-04-18 — complete. Residual prose references cleaned up.

## ADRs

- Created: [`docs/adr/identifier-scheme.md`](../adr/identifier-scheme.md)
- Touched via rename propagation: the full ADR corpus (see archive branch for exact touch list per slice)

## User-visible changes

- ADR files moved from `adr-NNN-<slug>.md` to `<semantic-slug>.md`
- Slice directories under `.claude/completed-slices/` use feature-scoped slugs
- Feature registry at `.claude/features/*.yaml` adopts the id/name pattern
- Hook input paths handle the new identifier shape (`scope-guard.sh`, `reality-check.sh`, `reversibility-guard.sh`)
- Commit-message phase templates at `.gitmessage-phase-{1..4}` use the new convention
- CLAUDE.md gained the identifier-scheme summary

## Carry-over debt at close

- **v1-defense-d3/bypass-log-hierarchical-slug** — queued slice. Widens `CLASSIFIED_LINE_RE`, migrates non-conforming `d3-bypasses.log` entries. Narrow-patched ahead of this merge; full schema migration to follow on dev.
- **F1 ADR prose cleanup in 7 ADRs** — folded into the planned `compression` Slice A.
- **F2 `test_phase_rethink.py:30-36` key rekey** — same (compression Slice A).
- **Part 0 ADR (P1–P6 + D1/D2/D3) consolidation** — planned as `compression` Slice B.

## Design & research docs

- [`docs/plans/2026-04-15-identifier-scheme-design.md`](../plans/2026-04-15-identifier-scheme-design.md) — original design
- [`docs/plans/2026-04-16-dogfood-observations.md`](../plans/2026-04-16-dogfood-observations.md) — parallel-execution dogfood findings (migrated from `.claude/plans/` at merge)
- [`docs/plans/2026-04-16-manual-parallel-dogfood.md`](../plans/2026-04-16-manual-parallel-dogfood.md) — dogfood run notes (migrated)
- [`docs/plans/2026-04-16-manual-dogfood-tmux-topology-design.md`](../plans/2026-04-16-manual-dogfood-tmux-topology-design.md) — tmux topology for dogfood
- [`docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md`](../plans/2026-04-18-feature-to-dev-merge-protocol-design.md) — merge protocol this feature instantiates
- [`docs/plans/2026-04-18-feature-to-dev-merge-protocol-plan.md`](../plans/2026-04-18-feature-to-dev-merge-protocol-plan.md) — this merge's execution plan

## Archaeology

```
git log archive/identifier-scheme
```

170 pre-squash commits preserved on the archive branch. See `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` for the archaeology-preservation rationale.
```

**Do NOT commit yet** — Task 11 commits all docs work together.

---

## Task 9: Append lesson L-006 to lessons.md

**Files:**
- Modify: `docs/lessons.md` (append new section)

**Step 1: Read the current tail of lessons.md**

```bash
tail -20 docs/lessons.md
```

**Step 2: Append L-006**

Use `Edit` tool with a final-line anchor (or `Write` with full content if simpler). The entry:

```markdown

## L-006: Identifier renames are feature-scoped, not slice-scoped

**Discovered**: 2026-04-18, during the `feature/identifier-scheme` → `dev` merge protocol design (first feature→dev merge in cairn).

**Pattern**: A scheme-change that spans multiple artifact classes (ADRs, slices, features, tests, prose, hooks) cannot be done as a single slice. The first pass finds one class of residue; the second pass finds residue from a class the first pass didn't cover; the third pass finds prose references both earlier passes missed. Each pass is a real slice — not ceremonial — but the feature boundary is where the pattern *as a whole* is governable.

**Concrete instance**: identifier-scheme ran three sequential slices — `adr-rename-sweep` (ADR files), `slice-and-feature-rename` (slice + feature namespace), `doc-sweep` (residual prose). Each slice closed cleanly and its sweep found residue attributable to the next slice's scope. After `doc-sweep` closed, sweep #17 still flagged two test-schema residues, which motivated a queued fourth slice (`v1-defense-d3/bypass-log-hierarchical-slug`). Four passes, one feature.

**Rule for future `/decision` and `/start-slice` triage**: when the proposed change is an identifier or terminology scheme that touches multiple artifact classes, the triage step routes to a **new feature definition** — not directly to `/start-slice`. The feature's sub-slices are framed by artifact class; a sweep between slices surfaces residue for the next slice; a dedicated doc-sweep slice is expected, not optional. Attempting a single-slice rename either under-scopes (leaves residue) or over-scopes (busts phase-4 invariants).

**Anti-pattern signals**: "the rename is mechanical," "one slice will cover it," "it's just find/replace," "phase-4 integration can absorb the residue." All four were internally plausible before the work started; none prevented the three-slice cascade that actually happened.

**Mechanism**: recorded here as a pattern; the concrete procedure (what a scheme-change feature's slice-sequencing looks like) can be promoted to `commands/claude-code/start-slice.md` or a new `/plan-feature` flow if a second scheme-change feature reproduces the shape.
```

**Step 3: Stage**

```bash
git add docs/lessons.md
```

**Do NOT commit yet.**

---

## Task 10: Memory pass — inspect candidates and graduate

**Files:**
- External (outside repo): `/Users/mohammed.farook/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/memory/*.md`
- Possibly modify (in repo): `CLAUDE.md` (if graduation candidates confirm)

Per design-doc Section **Memory pass** classification table.

**Step 1: Decide classifications (requires reading each entry)**

For each of the 10 memory entries, confirm the Section 5 classification:

1. `gitflow_adoption_deferred.md` → **annotate** (add 2026-04-18 pressure-test datum).
2. `context_discipline_philosophy.md` → inspect content; decide **graduate** or **keep**.
3. `parallelism_scope.md` → inspect; decide **graduate** or **keep**.
4. `brainstorming_formalization_exploration.md` → **keep**.
5. `coordinator_architecture_brainstorming.md` → verify against `docs/plans/2026-04-15-fleet-coordinator-design.md`; if fully covered, **retire**.
6. `v0_reset_commitment.md` → **keep**.
7. `coordinator_polling_must_be_cheap.md` → **keep**.
8. `complex_rag_analysis_consumer.md` → **graduate → CLAUDE.md**.
9. `cairn_efficiency_program_2026-04-18.md` → **retire** (migration already complete).
10. `language_migration_direction.md` → **graduate → CLAUDE.md**.

**Step 2: Apply CLAUDE.md graduations**

If entries 8 and 10 graduate, add two bullets to `CLAUDE.md`. Exact placement: after the **Safety-critical rules** section, as a new section or as two additional Safety-critical bullets.

Example additions (wording may need tuning against the actual memory content):

```markdown
**New-code language policy.** New scripts and hooks are Python, stdlib-only, function-based (one-for-one mapping target for end-of-v1 Python→Rust migration). Existing bash stays until its own migration slice.

**Downstream consumer constraints.** Cairn is consumed by projects with long test suites (complex-rag-analysis: ~917s). Scripts must not hardcode timeouts, sizes, or limits — prefer env-var override with cairn-friendly defaults.
```

Use `Edit` with precise anchor lines from the current CLAUDE.md to insert without disturbing other content.

**Stage CLAUDE.md:**

```bash
git add CLAUDE.md
```

**Step 3: Defer external memory edits until Task 13**

The actual retire/annotate operations on `~/.claude/projects/.../memory/*.md` happen in Task 13 (after the docs commit lands, so CLAUDE.md additions exist before dependent memories retire).

**Do NOT commit yet.**

---

## Task 11: Append CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Read current CHANGELOG**

```bash
head -40 CHANGELOG.md
```

Identify the format convention (Keep-a-Changelog, custom, etc.) and the current `[Unreleased]` location.

**Step 2: Append an entry**

Add under `[Unreleased]` (or dated block per convention):

```markdown
### Changed
- Identifier scheme: every ADR, slice, feature, and decision point now carries both `id:` (immutable) and `name:` (mutable). Prose uses `name`; cross-references, filenames, and hook inputs use `id`. See `docs/features/identifier-scheme.md` for the full feature closeout.
- ADR filenames migrated from `adr-NNN-<slug>.md` to `<semantic-slug>.md`.
- Slice and feature namespaces adopt feature-scoped slugs (`<feature>/<slice-slug>`).

### Added
- `docs/features/identifier-scheme.md` — first feature closeout under the new merge protocol.
- `docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md` — feature→dev merge protocol (first-instance precedent).
- `.gitmessage-phase-{1..4}` — commit-message templates for slice phases.
- `docs/lessons.md` L-006 — identifier renames are feature-scoped.

### Deprecated / Internal
- `.claude/handoff.md` and `.claude/adr-editorial-fixes.log` removed from tracking (`.gitignore` now authoritative).
- `archive/identifier-scheme` preserves the 170 pre-squash feature-branch commits.
```

**Step 3: Stage**

```bash
git add CHANGELOG.md
```

**Do NOT commit yet.**

---

## Task 12: Commit docs-and-closeout bundle on dev

**Step 1: Final pre-commit review**

```bash
git status --short
git diff --cached --stat
```

Expected staged files:
- `CHANGELOG.md`
- `CLAUDE.md` (only if graduations happened)
- `docs/features/identifier-scheme.md`
- `docs/lessons.md`

**Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs: identifier-scheme closeout — L-006, memory pass, CLAUDE.md additions

- docs/features/identifier-scheme.md — first feature closeout; paired
  with the feat: squash that shipped identifier-scheme to dev.
- docs/lessons.md — L-006 "Identifier renames are feature-scoped, not
  slice-scoped" (derived from the adr-rename-sweep →
  slice-and-feature-rename → doc-sweep cascade).
- CLAUDE.md — graduated two cross-cutting rules from memory:
  new-code language policy (Python stdlib-only) and downstream
  consumer constraints (no hardcoded timeouts/sizes).
- CHANGELOG.md — [Unreleased] entry for the identifier-scheme merge.

Follows the protocol at
docs/plans/2026-04-18-feature-to-dev-merge-protocol-design.md.
EOF
)"
```

**Step 3: Verify**

```bash
git log --oneline -2
```

Expected: two new commits on dev — `docs:` (most recent) and `feat:` (prior).

**Step 4: Re-run full verification**

```bash
uv run pytest
uv run ruff check
uv run python scripts/validate_architecture.py
```

Expected: all green. If red, reset this commit only (`git reset --hard HEAD~1`) — the `feat:` squash below stays — and investigate.

**Checkpoint 3 — dev post-docs green.**

---

## Task 13: External memory cleanup

**Files:** external to repo.

**Path:** `/Users/mohammed.farook/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/memory/`

**Step 1: Retire entries that graduated or became stale pointers**

- `cairn_efficiency_program_2026-04-18.md` — delete the file (migration is complete per `docs/plans/2026-04-18-efficiency-program/`).
- `complex_rag_analysis_consumer.md` — delete the file (content graduated to `CLAUDE.md`).
- `language_migration_direction.md` — delete the file (content graduated to `CLAUDE.md`).
- `coordinator_architecture_brainstorming.md` — delete IF Task 10 step 1 verification confirmed full coverage in `docs/plans/2026-04-15-fleet-coordinator-design.md`. Otherwise keep.

Use `Bash` `rm` (outside repo — `.gitignore` doesn't apply; no git involvement).

**Step 2: Annotate gitflow entry**

Edit `gitflow_adoption_deferred.md`. Append (or update the "How to apply" section with):

```markdown
**2026-04-18 update:** Approach B was pressure-tested informally via the `feature/identifier-scheme` → `dev` merge. Directional result: single-squash + archive-namespace branch preservation held without issue. Carry-over debt closure worked via narrow-patch. Recommend re-running `/decision` after one or two more feature merges, when the sample size supports Phase 4 commitment.
```

**Step 3: Update MEMORY.md**

Remove the lines for retired entries. Keep lines for entries still present. Update any wording that references the old state.

Current entries to drop (assuming all four retirements fire):
```
- [cairn efficiency program 2026-04-18]
- [complex-rag-analysis is a downstream cairn consumer]
- [language migration direction 2026-04-18]
- [fleet coordinator epic 2026-04-15]  (only if coordinator_architecture_brainstorming retired)
```

Verify via:

```bash
ls /Users/mohammed.farook/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/memory/
cat /Users/mohammed.farook/.claude/projects/-Users-mohammed-farook-Developer-lab-cairn/memory/MEMORY.md
```

**No git commit here** — these files are outside the repo.

---

## Task 14: Rename feature branch to archive

**Files:** git refs only.

**Step 1: Rename the branch**

From any worktree where the branch is not checked out:

```bash
git branch -m feature/identifier-scheme archive/identifier-scheme
```

If the rename errors with "branch is checked out in worktree X," `cd` to that worktree first, check out a different branch (e.g. `git checkout --detach`), then rename. Re-attach afterward.

**Step 2: Verify**

```bash
git branch -a | grep -E 'feature/|archive/'
```

Expected:
- No `feature/identifier-scheme` reference.
- `archive/identifier-scheme` present.
- Other `feature/*` branches (e.g., `feature/compression`) unchanged.

**Step 3: Verify the archive branch points at the expected commits**

```bash
git log --oneline archive/identifier-scheme | head -3
```

Expected: tip is the `chore:` carry-over-fix commit from Task 2 (or the `docs:` protocol doc commit, depending on ordering). The branch contains all 170+ pre-merge commits.

---

## Task 15: Push dev and archive

**Step 1: Check remote presence**

```bash
git remote -v
```

If no remote: skip the push steps and note in handoff. (Cairn may not have a remote configured yet at this stage of the repo's life — the `gitflow_adoption_deferred` memory notes `no remote` as a past state.)

If a remote exists, proceed.

**Step 2: Push dev**

```bash
git push origin dev
```

Expected: fast-forward push, two new commits delivered.

**Step 3: Push archive branch**

```bash
git push origin archive/identifier-scheme
```

Expected: new branch created on remote.

**Step 4: Verify remote state**

```bash
git branch -r | grep -E 'dev|archive/identifier-scheme'
git log --oneline origin/dev -2
```

Expected: both refs present; dev remote tip matches local.

**Checkpoint 4 — branches and remote correct.**

---

## Task 16: Post-merge handoff

**Files:**
- Modify: `.claude/handoff.md` (in whichever worktree holds the next session's active state — likely the compression worktree once it takes over)

**Step 1: Update handoff**

Since `.claude/handoff.md` is `.gitignore`d after Task 5, this is a local-worktree action only. Write a fresh handoff summarizing:
- Merge completed (commit SHAs for `feat:` and `docs:`).
- Archive branch reachable at `archive/identifier-scheme`.
- Next session's target: compression feature (Slice A).
- Open questions from this merge (if any tree-cleanup decisions were deferred).

**Step 2: Verify compression worktree state**

```bash
cd /Users/mohammed.farook/Developer/lab/cairn/.worktrees/compression
git status
git log --oneline -3
```

Confirm the compression worktree has a clean base for taking over post-merge.

---

## Rollback procedures

| Scenario | Action |
|---|---|
| Checkpoint 1 fails (feature not green) | Stop the plan. Route the failing tests to `v1-defense-d3/bypass-log-hierarchical-slug` slice. Re-run plan after that slice closes. |
| Checkpoint 2 fails (dev post-squash red) | `git reset --hard HEAD~1` on dev. Return to Task 5 — tree cleanup broke something. Iterate. |
| Checkpoint 3 fails (dev post-docs red) | `git reset --hard HEAD~1` on dev (removes the `docs:` commit; `feat:` squash stays). Docs shouldn't break tests — investigate structural cause. |
| Push rejected | Only possible if origin has commits dev doesn't — reconcile by pulling, re-running verification, then re-pushing. Never force. |
| Post-push regret | `git revert <feat-sha>` + `git revert <docs-sha>` on dev; push revert commits. `archive/identifier-scheme` is untouched and retains the work. |

---

## Expected total time

- Task 1–2 (pre-flight narrow patch): 30–60 min
- Task 3–7 (merge + cleanup + green check): 45–75 min
- Task 8–12 (docs bundle + green check): 45–75 min
- Task 13 (memory cleanup): 15–30 min
- Task 14–16 (archive + push + handoff): 15–30 min

**Total:** 2.5–4.5 hours focused work.

---

## Post-plan artifacts

After execution, the repo state should be:

- `dev` ahead of its pre-merge tip by exactly 2 commits (`feat:` squash + `docs:` closeout).
- `archive/identifier-scheme` ref points at the 170-commit pre-merge feature-branch tip.
- No `feature/identifier-scheme` branch.
- `docs/features/identifier-scheme.md` exists.
- `docs/lessons.md` gained L-006.
- `CLAUDE.md` has two new rules (conditional on graduation).
- `CHANGELOG.md` has a new `[Unreleased]` block.
- `MEMORY.md` has 3–4 fewer entries; `gitflow_adoption_deferred.md` is annotated.
- `.claude/handoff.md` (local, ignored) points at the compression feature as next-up.
