# Manual Axis-B Dogfood — Observations

**Date:** 2026-04-16
**Coordinator session:** `cairn:1` (coord)
**Starting commit:** `87ea8b5`
**Workers launched:** A (housekeeping/stale-22k), C (identifier-scheme/validator-flat-slug), B (v1-defense-d3/log-reclass), D (identifier-scheme/hook-relpath-bypass)
**Companion plan:** `.claude/plans/2026-04-16-manual-parallel-dogfood.md`
**Topology design:** `docs/plans/2026-04-16-manual-dogfood-tmux-topology-design.md`
**ADR under test:** `docs/adr/007-parallelism-v1.md` (firmness: provisional)

---

## 1. Setup log

| Timestamp (local) | Event | Notes |
|---|---|---|
| 2026-04-16 13:15:03 +04 | coord window renamed (`cairn:1` → `coord`), `/tmp/cairn-fleet/2026-04-16/` created, observations file opened | Base-index is 1 (not 0 as plan assumed) — workers will spawn at `cairn:2..5` |
| 2026-04-16 13:17 +04 | Worker A spawned — worktree, window, pipe-pane, `claude` launch, bootstrap injected | Boot time ~5s (plan's `sleep 2` was too short; the capture was visible only by ~5s mark). Bootstrap injected via `tmux send-keys -l "$(cat bootstrap-A.txt)"` then separate `Enter`. Worked cleanly. |
| 2026-04-16 13:18 +04 | Worker A reached first permission prompt (single-line `rm slice.yaml && rmdir … && mkdir -p …`) as part of `/start-slice` cleanup | Reading the capture revealed the prior attempt had been `rm -rf` which `reversibility-guard.sh` blocked; worker adapted to explicit-path form and then asked for approval — so the prompt was already the recovered form. |
| 2026-04-16 13:19 +04 | Workers C, B, D spawned concurrently (batched worktree adds then tmux window+claude launches) | Initial `capture-pane` showed blank because the TUI pads empty-prompt lines with spaces; `awk 'NF>0'` reveals the content. Log-file tail with ANSI stripping is a reliable fallback. |
| 2026-04-16 13:20 +04 | Approved A (`send-keys '1' Enter` to `cairn:2`); `rev-guard` had already caught and reshaped the original `rm -rf`; explicit-path `rm` ran; `rmdir` failed (`.gitkeep` present); worker recovered with `mkdir -p` separately | Worker A now **writing Phase 1 intent** (`◼ Phase 1: Write intent.md`). Functioning as designed: guard blocked, worker adapted, human approved the adapted form. C/B/D still reading context files in `/start-slice` exploration; no permission prompts yet. |

---

## 2. Per-slice timeline

### Worker A — housekeeping/stale-22k-cleanup

| Timestamp | Phase | State change | Human-touch count |
|---|---|---|---|
| 2026-04-16 13:17 +04 | bootstrap | spawn complete | 0 |
| 2026-04-16 13:18 +04 | Phase 1 pre | `/start-slice` skill loaded; requested Bash permission | 0 |
| 2026-04-16 13:20 +04 | Phase 1 pre | approved (1); `rm -rf` originally proposed was rev-guard-blocked; adapted + resumed | 1 |
| 2026-04-16 13:20 +04 | Phase 1 | writing intent.md | 1 |
| 2026-04-16 13:24 +04 | Phase 1 | Write(intent.md 103 lines) approved; Update(sweep.yaml) hit read-before-write error; recovered | 2 |
| 2026-04-16 13:29 +04 | Phase 1 boundary | 2 commits (`5a85197` intent, `cf4519a` handoff); handoff-phase-1.md present; stopped per protocol | 2 |
| 2026-04-16 13:32 +04 | Phase 1→2 transition | `/clear` + `/catchup` → 30.6k tokens (Mode A orientation clean) | 2 |
| 2026-04-16 13:34 +04 | Phase 2 advance | `/start-slice phase 2` → loaded start-slice skill, reading operational-reference.md | 3 |
| 2026-04-16 13:39 +04 | Phase 2 boundary | validation suite committed at `ac4bd8e`; slice.yaml unchanged (status: validation) — autonomous pre-commit without new handoff yet | 3 |

### Worker C — identifier-scheme/validator-flat-slug

| Timestamp | Phase | State change | Human-touch count |
|---|---|---|---|
| 2026-04-16 13:19 +04 | bootstrap | spawn complete | 0 |
| 2026-04-16 13:22 +04 | Phase 1 pre | mkdir permission prompt (sensitive-path wording) | 0 |
| 2026-04-16 13:24 +04 | Phase 1 pre | approved mkdir; read-before-write errors on slice.yaml/sweep.yaml; recovered | 1 |
| 2026-04-16 13:26 +04 | Phase 1 | Edit(identifier-scheme.yaml feature file — added slice entry per ADR-006) approved | 2 |
| 2026-04-16 13:33 +04 | Phase 1 boundary | 2 commits (`c670b58` intent, `87e9ede` handoff); handoff-phase-1.md present; stopped per protocol | 2 |
| 2026-04-16 13:37 +04 | Phase 1→2 transition | `/clear` + `/catchup` → 30.5k tokens (Mode A orientation clean) | 2 |
| 2026-04-16 13:37 +04 | Phase 2 advance | `/start-slice phase 2` | 3 |
| 2026-04-16 13:41 +04 | Phase 2 | Gate: awk signature-extraction command (read-only exploration); pending approval | 3 |

**Note:** C's slice.yaml `status:` is `2-validation` (prefixed form); A/B/D wrote just `validation`. Inconsistency in cairn's `/handoff` output — worth a consistency pass.

### Worker B — v1-defense-d3/bypass-log-reclass

| Timestamp | Phase | State change | Human-touch count |
|---|---|---|---|
| 2026-04-16 13:19 +04 | bootstrap | spawn complete | 0 |
| 2026-04-16 13:22 +04 | Phase 1 pre | `/start-slice` exploration; read-before-write errors recovered autonomously | 0 |
| 2026-04-16 13:23 +04 | Phase 1 | Write(intent.md 6.0k), Write(slice.yaml) approved | 1 |
| 2026-04-16 13:26 +04 | Phase 1 boundary | two commits (61d2664 intent, 5f48721 handoff); slice.yaml→validation; handoff-phase-1.md (952 chars); stopped per protocol | 1 |
| 2026-04-16 13:29 +04 | Phase 1→2 transition | `/clear` + `/catchup` cycle: 65.8k → 31.4k tokens (−52%). Tier 1 discipline held (read only handoff+slice+sweep+git). Mode A orientation produced. Waiting on `/start-slice phase 2`. | 1 |

### Worker D — identifier-scheme/hook-relpath-bypass

| Timestamp | Phase | State change | Human-touch count |
|---|---|---|---|
| 2026-04-16 13:19 +04 | bootstrap | spawn complete | 0 |
| 2026-04-16 13:22 +04 | Phase 1 pre | ls + git log permission prompt (benign reads) | 0 |
| 2026-04-16 13:24 +04 | Phase 1 pre | approved reads; heavy context exploration — ARCHITECTURE.md, completed-slices, test_hook_tolerance.py (409 lines); token load climbed to 67k | 1 |
| 2026-04-16 13:30 +04 | Phase 1 boundary | 2 commits (`d0118bb` intent, `90c0868` handoff); handoff-phase-1.md present; stopped per protocol | 1 |
| 2026-04-16 13:32 +04 | Phase 1→2 transition | `/clear` + `/catchup` → 30.6k tokens; accept-edits mode auto-enabled in D only (not A) | 1 |
| 2026-04-16 13:34 +04 | Phase 2 advance | `/start-slice phase 2` | 2 |

---

## 3. Coordinator overhead

Operator messages spent on coordination (surfacing gates, answering status questions) vs. actual slice work:

| Turn # | Coord-only | Slice-work | Notes |
|---|---|---|---|
| | | | |

---

## 4. Gate candidacy

For each observed transition, classify: *autonomous-eligible* (could a precondition script verify this?) or *human-gated-only*. Feeds Feature 2 ADR.

| Slice | Transition | Classification | Evidence / precondition shape |
|---|---|---|---|
| | | | |

---

## 5. Failures / near-misses

Any merge conflict, invariant violation, scope-guard denial, `send-keys` race, hung worker, or surprise.

| Timestamp | Slice | Failure mode | Resolution |
|---|---|---|---|
| 2026-04-16 13:20 +04 | A | `reversibility-guard.sh` blocked `rm -rf .claude/current-slice` on a cleanup path used by `/start-slice` | Worker auto-adapted to explicit `rm <path> && rmdir …`; `rmdir` then failed because `.gitkeep` was present; worker recovered with `mkdir -p` separately. Net: 2 extra tool calls, guard fired correctly. Signals that `/start-slice` scaffolding logic assumes an empty `.claude/current-slice/` directory but encounters `.gitkeep`. |
| 2026-04-16 13:22–24 +04 | A, B, C (repeated) | CC 2.1.110 Write tool now enforces "File has not been read yet. Read it first before writing to it." on any Write without a prior Read (new behavior vs older CC versions) | Every worker hit this at least once when authoring `slice.yaml` and/or `sweep.yaml`. Auto-recovered with a Read then Write. Adds ~1–2 extra tool calls per affected Write. Candidate **autonomous-eligible precondition** for Feature 2: "before Write, ensure Read of same path has occurred this session." |

---

## 5b. Coordinator design feedback (in-flight, not end-of-dogfood)

**Per-turn full `capture-pane` polling is wasteful.** The topology design §D8 prescribes: on every human turn, for each active worker, `tmux capture-pane -p -t cairn:<N> -S -100`. With 4 workers this dumps ~400 lines of raw ANSI-laden terminal output into coordinator context every turn — most of it repeats unchanged content and the non-text markers. Real cost: large context bump per turn, token burn on every coordinator reply, and context switching between four disjoint state trees degrades the coordinator's synthesis quality.

**User feedback (firaaz, 2026-04-16 ~13:26 +04):** "We need a better way than this polling. This adds context switching and is wasteful of tokens." Record this as a load-bearing constraint for Feature 6 harness design.

**Better shapes to evaluate:**
1. **Tiered polling.** Poll `slice.yaml` every turn (tiny, structured, detects phase transitions cleanly). Poll log-file *size delta* every turn (one `ls -la` call). Only `capture-pane` when a signal fires (new prompt marker, log growth without slice.yaml change, or user asks).
2. **Prompt-marker grep on log tail.** Instead of dumping the full pane, grep just the last ~40 non-whitespace lines of each worker log for known markers (`Do you want to proceed?`, `Do you want to create`, `which is a sensitive file`). Returns a single line per worker-with-pending-gate.
3. **Worker-side marker files.** Not feasible for permission prompts (worker is blocked waiting), but useful for phase transitions: worker writes `.claude/current-slice/.state` with `phase=N; awaiting=yes` on reaching each boundary. Coordinator reads four small files, no `capture-pane` needed for phase state.
4. **User-driven polling only.** Drop per-turn polling entirely; only poll when the user asks for status or when the coordinator needs to answer an explicit question. Trade-off: phase transitions may go unnoticed for a turn or two. Acceptable given conversation cadence.

**Decision for remainder of this dogfood:** Adopt shapes 1 + 2. Per turn: check `slice.yaml` + log-size delta for all four workers (cheap). Only dump `capture-pane` output when log-tail grep finds a new prompt marker. Continue recording observations in this file. Shape 3 (marker files) is deferred to Feature 6 harness ADR.

---

## 6. ADR-007 signals

- Does the `after`-dependency model hold? _(pending — no cross-branch dependency exercised yet)_
- State corruption between concurrent branches? _(none so far — each worker's slice.yaml is clean and independent; branch-local state working as designed)_
- Stale handoff pointers across merges (Risk Register #2)? _(pending — no merges yet)_
- Any need to tighten concurrency constraints? _(no — all four started concurrently without contention; rev-guard and Write-read-before-write preconditions each fired independently per worker)_
- **Parallel-branch SLICE-ID collision:** all four workers independently picked SLICE-018. Expected per ADR-007 D2 (no global pointer). At merge time, slice-ID becomes a branch-local label only; commit graph + feature-file `slice-yaml-id` pointers are the cross-branch identity. Confirms the model.
- **Clear+catchup between phases works cleanly:** B's Phase 1→2 transition via `/clear` + `/catchup` produced correct Mode A orientation from handoff+slice.yaml+sweep alone, with no leak of Phase 1 context. Token cost dropped 52%. Strong signal that branch-local handoff artifacts are sufficient context for phase continuity under parallelism.

---

## 7. Permission-prompt detection markers (topology §4 OQ4)

String-matching ground-truth samples for future harness automation:

| Slice | Prompt text (verbatim) | Coordinator detection signal |
|---|---|---|
| A | `Bash command\n  rm .claude/current-slice/slice.yaml && rmdir .claude/current-slice && mkdir -p .claude/current-slice/validation .claude/current-slice/implementation .claude/current-slice/integration && ls -la .claude/current-slice/\n  Recreate current-slice dir structure\nDo you want to proceed?\n❯ 1. Yes\n  2. Yes, and don't ask again for similar commands in <worktree>\n  3. No` | `capture-pane` contained the literal line `Do you want to proceed?` and the numbered choices — reliable grep targets for future automation. |

---

## 8. Closing note

_(To be written at end of dogfood — will be copied to `docs/lessons.md` as `L-005 — manual Axis-B dogfood findings` per plan §8.)_
