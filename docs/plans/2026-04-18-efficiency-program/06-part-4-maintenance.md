# Part 4: Maintenance Agents

**Date:** 2026-04-18
**Gates:** Part 0 ADR; F6 daemon (for scheduling)
**Estimated:** ~4 slices
**Deployment:** F6 daemon triggers on schedule or event.

## Intent

Agents that run maintenance work — either on-demand or scheduled by F6's daemon. Cairn's spec corpus grows; without maintenance, drift accumulates invisibly.

## Agents

### `adr-drift-auditor`

**Role:** Periodic scan of `docs/adr/*` for:
- Stale ADRs (referenced nowhere in current code or docs).
- Missing `superseded-by:` pointers (ADR X says "supersedes Y" but Y's frontmatter doesn't reflect it).
- Contradictory invariants across ADRs (detected by shared-keyword pairs).
- ADRs with `firmness: provisional` that have been provisional >90 days without review.

**Return:** Table of findings, priority-ranked.
**Trigger:** Weekly. Also on-demand via `/adr-audit`.

**System prompt (sketch):**
```
Read docs/adr/index.md + every ADR file.
Apply the following checks. Return a table: adr-id | finding-type | severity | suggested action.
Max 30 rows. No prose.
```

---

### `adr-impact-classifier`

**Role:** When a new ADR lands, scan the codebase + slice corpus to identify "files/slices likely affected by this decision." Produces Phase 6 propagation hints.

**Return:** Ranked list of files/slices + one-line rationale per.
**Trigger:** Post-ADR-commit hook (`post-commit` on `docs/adr/*.md` paths). Also `/adr-impact <adr-id>` on demand.

**System prompt (sketch):**
```
You are given a single ADR. Read it.
Scan the codebase and .claude/features/ to identify:
- Files whose invariants the ADR changes.
- Active slices whose envelope overlaps with the ADR's subject area.
- Past ADRs this one supersedes or refines.

Return a ranked list: target | relation (invariant-change / envelope-overlap / supersedes) | action (review-needed / refactor-target / close-old).
Max 25 rows.
```

---

### `lesson-extractor`

**Role:** After slice completion (or batch of completions), read slice artifacts + sweep notes + dogfood log, propose `docs/lessons.md` additions for patterns that surfaced.

**Return:** Draft lesson entries in the existing lessons.md format (L-NNN prefix, Pattern / What happens / Rule / Anti-pattern signals).
**Trigger:** Post-slice-complete. Also `/extract-lessons` on demand.

**System prompt (sketch):**
```
You are given:
- A completed slice's intent.md, handoff-phase-*.md files, validation/approach.md, implementation notes.
- Recent sweep notes.
- Recent dogfood-log entries.

Identify cross-cutting patterns worth naming as lessons:
- Repeated surprises that the existing doctrine doesn't cover.
- Novel gotchas that cost >10 min to diagnose.
- Patterns that recurred across 2+ slices.

Draft entries in lessons.md format. Do NOT commit; return as drafts for human review.
Max 3 draft entries per invocation.
```

---

### `merge-conflict-specialist`

**Role:** Cairn-pipeline-aware merger. Knows the conflict shapes in `handoff.md`, `slice.yaml`, `sweep.yaml`, `d3-bypasses.log`, `features/*.yaml`, `structural-snapshot.json`. Dogfood measured 5–10 min per merge × 4 merges = 20–40 min of coordinator overhead. This agent targets 1–2 min per merge.

**Return:** Resolved file content. Main session reviews and accepts/rejects.
**Trigger:** `/merge-resolve <branch>` on demand. Post-F6: auto-invoked when F6 detects a merge conflict on pipeline-substrate paths.

**System prompt (sketch):**
```
You are given two versions of a cairn pipeline-substrate file (handoff.md, slice.yaml, sweep.yaml, d3-bypasses.log, features/*.yaml, or structural-snapshot.json).

For each file type, apply the appropriate reconciliation:
- handoff.md: merge the more recent phase; keep the merge branch's "Next" line.
- slice.yaml: take the higher phase number; merge `envelope` lists union; resolve `status` to the more-advanced value.
- sweep.yaml: increment `last-sweep-at-slice` to max(both) + merge sweep entries list.
- d3-bypasses.log: concatenate; sort by timestamp; dedupe identical entries.
- features/*.yaml: merge slice lists; resolve duplicate slice IDs by latest status.
- structural-snapshot.json: regenerate (don't merge).

Return the resolved content verbatim. Do not add commentary. If a conflict defies these rules, return the two versions + a specific question.
```

**Scope:** Pipeline-substrate only. Never touches source code or tests.

---

### `cross-repo-awareness`

**Role:** Scan downstream consumers (complex-rag-analysis + future consumers) for cairn API usage. Flag breaking changes before merge.

**Return:** Table of consumer-usage sites that would break given a specific cairn diff.
**Trigger:** On-demand via `/cross-repo <diff>`. Scheduled weekly to catch drift.

**System prompt (sketch):**
```
You are given a cairn diff (or a specific cairn file path).
For each downstream consumer at the paths provided (~/Developer/lab/<consumer>):
- Find usage sites (grep for referenced skills, scripts, hook names, file paths).
- Classify: broken-by-diff / unaffected / possibly-affected.

Return a table per consumer: file:line | usage | classification | one-line rationale.
```

**Requires:** A registry of consumer repos. Initially hardcoded to `~/Developer/lab/complex-rag-analysis`. Later a `cairn-consumers.yaml` file.

---

### `dogfood-interpreter`

**Role:** Run `scripts/dogfood_evaluate.py`, parse output, produce a small action-items list.

**Return:** Action items: item | rationale | suggested-slice.
**Trigger:** After dogfood runs. On-demand via `/dogfood-interpret`.

**System prompt (sketch):**
```
Run scripts/dogfood_evaluate.py.
Parse its output (format documented in the script).
For findings above threshold, propose follow-up slices or ADR amendments.

Return a table: finding | severity | suggested-slice-or-adr | rationale.
Max 10 rows.
```

## Slice breakdown

- **S1** — `adr-drift-auditor` + `adr-impact-classifier`. Both ADR-corpus readers; share patterns.
- **S2** — `lesson-extractor` + `dogfood-interpreter`. Both read slice artifacts and produce human-review drafts.
- **S3** — `merge-conflict-specialist`. Cairn-specific; highest value; own slice.
- **S4** — `cross-repo-awareness`. Requires consumer registry setup.

## Scheduling (F6 daemon)

Post-F6, the daemon schedules these via `scheduled-routines.yaml`:

```yaml
version: 1
routines:
  - name: adr-drift-weekly
    agent: adr-drift-auditor
    schedule: "0 2 * * 1"  # Monday 2am
    alert_on: severity >= "medium"

  - name: cross-repo-drift-weekly
    agent: cross-repo-awareness
    schedule: "0 3 * * 1"

  - name: lesson-extract-post-slice
    agent: lesson-extractor
    trigger: slice-complete
    alert_on: drafts_count > 0

  - name: adr-impact-on-commit
    agent: adr-impact-classifier
    trigger: post-commit docs/adr/*.md

  - name: merge-conflict-on-conflict
    agent: merge-conflict-specialist
    trigger: git-merge-conflict path:pipeline-substrate
```

Pre-F6, these are manual invocations (`/adr-audit`, `/extract-lessons`, `/merge-resolve`, etc.).

## Cross-cutting

1. **Maintenance agents are read-mostly.** Most propose drafts; the human reviews + commits. The one exception is `merge-conflict-specialist` which returns resolved content intended for direct use — but even it goes through human review.
2. **Output to files, not to main session.** Maintenance agents write their findings to `docs/maintenance/<date>-<agent>.md` so the outputs persist without burning main-session context.
3. **Scheduled routines emit events** (post-F6, into the daemon's event log) so patterns over time become visible.

## Success criteria

1. ADR corpus: no ADR goes >90 days provisional without surfacing.
2. New ADRs produce propagation hints automatically.
3. Merge-conflict reconciliation time drops from 20–40 min per parallel merge to <5 min.
4. Lessons.md gains ≥1 entry per month from automated extraction + human review (currently ~1 entry per several months, manually).
5. Downstream consumer compatibility: no surprise breakage; consumer-impact is flagged pre-merge.

## Out of scope

- Scheduled routines that mutate state without human review. Maintenance agents propose; humans dispose.
- External integrations (GitHub, CI) beyond local git. Those are Part 5 open questions.
