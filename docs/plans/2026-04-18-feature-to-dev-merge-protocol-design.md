---
id: feature-to-dev-merge-protocol
name: "Feature → dev merge protocol"
status: design
kind: plan
authored: 2026-04-18
author: firaaz
first-instance: identifier-scheme
graduation-target: ADR after N≥2 pressure tests
supersedes: none
---

# Feature → dev merge protocol (first-instance precedent)

## Motivation

This is the first time a feature branch merges into `dev` in cairn. Every decision about history shape, tree cleanup, archaeology preservation, and documentation lands as a precedent the next merge will follow by default. The question is not "how do we merge this one feature" — it is "what shape does a cairn feature→dev merge have, such that the shape is honest about what shipped and cheap to repeat."

The through-line: **dev history is release-narrative; the archive branch preserves raw archaeology; docs carry the interpretive layer.** Each layer is honest about its job.

- `git log dev` answers "what shipped and when." One commit per feature.
- `git log archive/<feature>` answers "how did that feature evolve." Every slice, handoff, and sweep commit preserved.
- `docs/features/<feature>.md` answers "what was this feature, and what debt did it leave." One page per feature.

Conflating these — e.g. merging all 170 intra-feature commits into dev — produces dev-log archaeology that nobody reads while burying the release narrative.

## Scope

**Applies to:** any `feature/*` → `dev` merge in cairn.

**Does not apply to:**
- Slice-internal merges (`slice/*` → `feature/*`) — these are slice-pipeline mechanics, not inter-feature coordination.
- `dev` → `master` merges — deferred until first release prep; will have their own protocol.
- Hotfix flows — no convention yet; defer until needed.

**Status in the cairn pipeline taxonomy:** this operation is a **pipeline-substrate operation**, alongside `/integration-sweep` and `/refresh-architecture`. Per L-001's exception clause, pipeline-substrate operations are not required to flow through `/start-slice`. Direct commits on feature (pre-merge) and dev (post-merge) are named and accepted scars of the same class as sweep commits.

If at any point evidence accumulates that this merge flow *should* run through a slice, the protocol graduates to a `/decision` and the conclusion is revisited. For N=1, the direct-commit framing is the honest minimum.

## Pre-flight requirements

Before any merge action:

- [ ] `feature/*` branch tip passes `uv run pytest` with zero failures.
- [ ] `feature/*` branch tip passes `uv run ruff check` clean.
- [ ] `feature/*` branch tip passes `scripts/validate_architecture.py`.
- [ ] Carry-over debt is catalogued in `.claude/handoff.md` (follow-up slices named).
- [ ] Any pre-existing failures carried into the feature are resolved on the feature branch *before* merge, via narrow-patch commits. No merge-with-known-failures. (See **Pytest gate**.)

If the gate cannot be made green by narrow patching, stop and route the work to a focused slice (e.g., `v1-defense-d3/bypass-log-hierarchical-slug`). Merge-red is not an option.

## Merge shape

**Single squash. No rebase-and-drop. No merge commit preserving archaeology.**

Mechanics:
```
git checkout dev
git merge --squash feature/<feature-id>
# apply staged tree cleanup (see Tree cleanup)
git commit -m "feat: <feature-id> — <short description>"
```

Why single squash and not a preserving merge:
- Intra-feature commits are session-state snapshots (46% of identifier-scheme's 170 commits were `handoff:` — context-save artifacts, not deliverables). Preserving them in dev log is negative-signal.
- The release narrative is feature-level, not slice-level. `git log dev` should read like a changelog, not a diary.
- Archaeology is not destroyed — it lives on the archive branch, reachable forever.

Why not `--no-ff` merge with rebase-and-drop of handoffs:
- Even after dropping handoffs, ~90 commits enter dev per feature. At ten features, dev has 900 commits representing ten user-visible deliverables. `git log dev` becomes unreadable.
- The rebase is mechanical but non-zero cost, and every rebase decision ("drop this, keep that") is a precedent that future merges re-litigate.
- Single-squash makes the commitment clear: once a feature is done, the pattern it followed internally is not what dev cares about.

**Commit message shape:**
```
feat: <feature-id> — <one-line what-shipped>

<one-paragraph summary>

Slices: <slice-id>, <slice-id>, <slice-id>

ADRs touched: <list>

Carry-over: <debt catalogued in closeout doc>

Archive: archive/<feature-id>
Closeout: docs/features/<feature-id>.md
```

Subject uses `feat:` (standard conventional-commits type) — distinct from the custom `slice:`, `sweep:`, `adr:` types used inside feature branches. Rationale: dev commits are feature-level semantic class; feature-branch commits are slice-level or substrate-level.

## Archaeology preservation

After the squash lands on dev:

```
git branch -m feature/<feature-id> archive/<feature-id>
```

Rename the feature branch into the archive namespace. Keeps `git branch -a | grep feature/` focused on live work. Keeps `git branch -a | grep archive/` as the feature history index.

**No tags.** The tag namespace is reserved for release markers (`v0.1.0`, `v1.0.0` eventually consumed by downstream pinning). `pre-merge/*` tags would pollute that namespace linearly with feature count and would require consumers to mentally filter every `git tag -l`.

Branch-namespace preservation is equally ref-cheap, cleaner to filter, and aligned with how cairn uses refs today.

**Deletion policy:** archive branches are preserved indefinitely for now. If they ever become unwieldy, a dedicated slice decides retention rules (e.g., keep N most recent, prune older). Defer.

## Tree cleanup

Cleanup happens in the staged squash on dev, after `git merge --squash` but before `git commit`. Reasoning: cleanup decisions are about what lands on dev, not about the feature's internal evolution.

**Standard cleanup actions:**

- **Grandfathered `.gitignore` entries:** for any file currently in `.gitignore` that is still tracked (added before its gitignore entry), `git rm --cached` in the staged squash. For the first merge, this clears:
  - `.claude/handoff.md`
  - `.claude/adr-editorial-fixes.log`
- **Stale current-slice state:** `.claude/current-slice/slice.yaml` and any phase archives point at whatever slice closed last on the feature branch. Reset to minimal/stub state so dev has no false "active slice."
- **Ephemeral session artifacts:** files that captured one-off context during feature work (e.g., `.claude/slice-<N>-<topic>.md` notes) — inspect; delete if obsolete; move to `.claude/plans/` or `docs/plans/` if durable.
- **Durable research artifacts in `.claude/plans/`:** move to `docs/plans/` when the content is durable research, not session-ephemeral. Heuristic: if a downstream reader would benefit from discovering it, it belongs in `docs/plans/`.
- **Live-doc identifier references:** any live doc that still uses a retired identifier scheme (e.g., `adr-003` after identifier-scheme rename) gets patched. See **Docs audit policy** for live-vs-frozen rules.

**Derived artifacts:** tracking decisions for generated files (e.g., `.claude/structural-snapshot.json`) are out of scope for the merge. Do not force decisions under merge timing — open a dedicated slice if needed.

## Summary documentation artifacts

Three artifacts per merge:

### 1. Feature closeout — `docs/features/<feature-id>.md`

The `docs/features/` directory is created by the first merge. One page per feature. Replaces `git log dev` as the "what was this feature" reference.

Target length: 150–300 lines. Structure:

```
---
id: <feature-id>
name: "<human-readable>"
status: merged
opened: YYYY-MM-DD
merged: YYYY-MM-DD
archive-branch: archive/<feature-id>
---

## What shipped
<one paragraph>

## Slices
<bulleted list: slice-id — dates — outcome>

## ADRs
Created: <list with links>
Touched via propagation: <list>

## User-visible changes
<bullets — mirror CHANGELOG entry>

## Carry-over debt at close
<bullets — follow-up slices named>

## Design & research docs
<links to docs/plans/ entries driving this feature>

## Archaeology
git log archive/<feature-id> — N pre-squash commits preserved.
```

No `_template.md` until a second merge shows the repeating structure is stable.

### 2. CHANGELOG.md entry

Append one `[Unreleased]` block (or dated block per the existing CHANGELOG convention) with user-visible bullets. Keep short. Cross-reference `docs/features/<feature-id>.md` for detail.

### 3. Protocol doc (this document, or its successor)

This doc is the first instance of the protocol. Subsequent merges either follow it unchanged or explicitly revise — in which case the revision lands as a new plan doc or a `/decision` → ADR. See **Graduation path**.

## Docs audit policy

**Rule:** live docs round-trip through the current identifier scheme. Historical plan/review docs stay frozen with the identifiers they were written under.

**Live docs:**
- `docs/ARCHITECTURE.md`, `docs/spec-v1.md`, `docs/operational-reference.md`, `docs/lessons.md`, `docs/roadmap.md`, `docs/vision.md`, `docs/dogfood-log.md`
- `docs/adr/*.md` (every ADR is live — they are the constraint corpus)
- `docs/features/*.md`
- Top-level `CLAUDE.md`, `CHANGELOG.md`

**Frozen (archaeological):**
- `docs/plans/YYYY-MM-DD-*.md` (every dated plan)
- `docs/reviews/YYYY-MM-DD-*.md`

Rewriting frozen docs' identifiers rewrites archaeology for no navigation gain and silently erases evidence of *when* a scheme changed. Their references are correct as-of their authored date; that's the point.

**ADR-level nuance:** for each identifier hit in an ADR, classify:
- **Prose context** ("previously known as adr-003") — leave; deliberate identifier-history.
- **Live cross-reference** (`see: adr-003` pointer) — patch to current slug.

**Frozen-doc filenames:** not renamed even if they encode retired identifiers. Filename is archaeology.

## Learnings & memory pass

The merge is the natural trigger for a lessons/memory audit on the feature's span.

### Lessons pass

Audit the feature's commits for patterns 3×-visible within the feature that aren't yet in `docs/lessons.md`. `lessons.md` bar is "cross-cutting pattern from slice work" — single concrete instances qualify.

`CLAUDE.md` graduation bar is higher: 3×-observed *distilled rule*. Don't promote feature-local patterns to CLAUDE.md.

### Memory pass

For each entry in `MEMORY.md`, classify as:

- **Retire** — content is now captured in code/docs/ADR; delete the memory file and drop its index line.
- **Graduate** — content is a distilled cross-cutting rule ready for `CLAUDE.md`; add the rule to CLAUDE.md, then retire the memory.
- **Keep** — still live project state (parked brainstorms, forward-work plans, user preferences); revalidate for staleness.
- **Annotate** — still live but worth dating with the new evidence this merge provides (e.g., "pressure-tested informally via this merge").

Memory entries that turn out to be **stale pointers to docs** (pointing at a design doc that already captures everything) are prime retirement candidates.

### Where the pass commits land

All learning/memory work commits as a single `docs:` commit on dev after the `feat:` squash:

```
docs: <feature-id> closeout — L-NNN, memory pass, CLAUDE.md additions
```

One commit per feature for interpretive work. Keeps dev tidy: two commits per feature merge — one `feat:`, one `docs:`.

## Pytest gate

**Gate policy:** feature branch tip must be green on `pytest`, `ruff check`, and `scripts/validate_architecture.py` before squash.

**Pre-existing failures:** if a failure was carried into the feature from earlier work (documented in sweeps or handoffs), resolve with a **narrow patch** on the feature branch — minimum-viable change that makes the tests green without committing to the broader fix the queued slice will make.

**Narrow-patch commit shape:**
```
chore: resolve <test-name> carry-over ahead of dev merge
```

**When narrow-patch is insufficient:** stop. Route to a focused slice. Do not merge-red. The cost of delaying the merge for a slice is smaller than the cost of "first commit on dev is a known-broken state."

**Side effect:** any queued successor slice whose motivation was carry-over-failure gets retrimmed — its intent is now scoped to the broader fix, not the failure.

## Sequence & checkpoints

### Pre-flight (on `feature/<feature-id>`)

1. Identify and narrow-patch any pre-existing test failures. Commit as `chore:`.
2. Run full verification: pytest + ruff + validate_architecture. All must pass.
3. Write the protocol doc (if first instance) or update it (if subsequent merge revises the precedent). Commit as `docs:`.
4. Verify green one more time.

**Checkpoint 1 — feature green.** If any red, stop.

### Merge (on `dev`)

5. `git checkout dev`
6. `git merge --squash feature/<feature-id>`
7. Apply staged tree cleanup (see **Tree cleanup**).
8. `git commit` with the `feat:` message (see **Merge shape**).

**Checkpoint 2 — dev post-squash green.** Run pytest + ruff + validate_architecture on dev. If red, `git reset --hard HEAD~1` and investigate. No force-through.

### Post-merge documentation (on `dev`)

9. Write `docs/features/<feature-id>.md` closeout.
10. Append any new lesson(s) to `docs/lessons.md`.
11. Inspect memory pass candidates; apply CLAUDE.md graduations.
12. Append `[Unreleased]` entry to `CHANGELOG.md`.
13. Commit as `docs:` (see **Memory pass** for commit shape).

**Checkpoint 3 — dev post-docs green.** Same verification run. Docs changes shouldn't break tests; if they do, something structural is wrong.

### Memory cleanup (external — `~/.claude/projects/.../memory/`)

14. Retire / annotate / graduate / keep each memory entry per Section 5 rules.
15. Update `MEMORY.md` index to match.

### Archaeology & push

16. `git branch -m feature/<feature-id> archive/<feature-id>`.
17. `git push origin dev`.
18. `git push origin archive/<feature-id>`.

**Checkpoint 4 — branches correct.** `git branch -a` shows `feature/*` clean, `archive/*` populated, dev matches origin.

### Escape hatches

- Checkpoint 1 red → narrow patch failed; route to a focused slice instead.
- Checkpoint 2 red → `git reset --hard HEAD~1`; nothing pushed; iterate on cleanup.
- Checkpoint 3 red → same reset; docs-only changes shouldn't break; something weirder is happening.
- Post-push regret → `revert:` commit on dev; archive branch still holds the work; no force-push.

## Verification matrix

| Checkpoint | pytest | ruff | validator | tree-shape |
|---|---|---|---|---|
| 1 (feature pre-merge) | ✓ | ✓ | ✓ | protocol doc committed |
| 2 (dev post-squash) | ✓ | ✓ | ✓ | one `feat:` commit; cleanup applied |
| 3 (dev post-docs) | ✓ | ✓ | ✓ | two commits; closeout written |
| 4 (post-rename-push) | n/a | n/a | n/a | `archive/*` populated; dev pushed |

## Open questions (not decided by this protocol)

- **Commit-type convention at the feature→dev boundary.** This protocol uses `feat:` for the squash commit, but the deferred gitflow `/decision` left the final convention open. A future `/decision` may prescribe a different type (e.g., `feature:`) or formalize `feat:` as cairn's choice.
- **`.claude/plans/` vs `docs/plans/` boundary.** This protocol names dogfood-style durable research as belonging in `docs/plans/`, but the general rule for what lives where is not fully formalized. A future slice or `/decision` may codify this.
- **Tracking of derived artifacts.** `.claude/structural-snapshot.json` and similar generated files — should they be tracked at all? Deferred.
- **dev → master merge protocol.** Not defined here. Will have its own precedent at first release prep.
- **Archive-branch retention.** Kept indefinitely for now. A future slice may introduce retention rules.

## Graduation path

This protocol is a plan doc, not an ADR. The path forward:

- **N=1 (this merge):** protocol doc exists; precedent set; exceptions are open questions.
- **N=2 (next feature merge):** protocol is applied; any deviations are recorded. If the protocol held without revision, confidence grows. If deviations accumulate, the protocol is revised.
- **N≥3:** the protocol is promoted to a `/decision` → ADR. At that point it binds future merges architecturally, and the open questions are ruled on.

Until N≥2, treat this doc as a strong default with explicit license to deviate when the reason is stronger than the precedent.

## Precedents set by this document

1. **Single squash per feature→dev merge.** No rebase-and-drop. No preserving merge.
2. **Archive namespace for post-merge feature branches.** `feature/<id>` → `archive/<id>`. No tags.
3. **Cleanup lands in the staged squash on dev.** Not on the feature branch. Not in post-merge commits.
4. **Two commits on dev per feature merge.** `feat:` (squash) + `docs:` (closeout, lessons, CLAUDE.md).
5. **Feature closeout at `docs/features/<feature-id>.md`.** New convention, scales with feature count.
6. **Live-vs-frozen doc distinction for identifier audits.** Live docs round-trip; historical docs stay frozen.
7. **Feature→dev merge is a pipeline-substrate operation.** Named and accepted scar per L-001's exception clause. No `/start-slice` ceremony for the merge itself.
8. **Gate must be green before squash.** Narrow-patch carry-overs; slice the rest; never merge-red.
9. **Merge is the trigger for lessons/memory pass.** Audit fires at feature-boundary, not slice-boundary.
10. **dev history is release-narrative; archive branch is archaeology; `docs/features/` is interpretive.** Three layers, each honest about its job.

## Cross-references

- `docs/lessons.md` L-001 — pipeline-bypass temptation; this protocol extends the pipeline-substrate exception.
- `docs/adr/bootstrap-exception.md` — the exception precedent this protocol implicitly follows.
- `~/.claude/projects/.../memory/gitflow_adoption_deferred.md` — deferred `/decision` that would eventually formalize this protocol as an ADR.
- `docs/adr/identifier-scheme.md` — the feature whose first-merge instantiates this protocol.
- `docs/operational-reference.md` — repo layout and commands; may need a new section referencing this protocol once it stabilizes.
