# Manual Parallel Dogfood — Fleet Coordinator Epic, Axis B

**Date:** 2026-04-16
**Status:** Plan handed off from context-full session; next session executes.
**Epic:** Fleet Coordinator (`docs/plans/2026-04-15-fleet-coordinator-design.md`)
**Provisional ADR:** `docs/adr/007-parallelism-v1.md` (firmness: provisional → this run produces graduation data)
**Starting commit:** `87ea8b5` (post-sweep #12)

---

## 1. Purpose

Run 2–4 disjoint queue items as **concurrent manual slices in separate worktrees** before the Python harness (Feature 6) exists. Goals, in order:

1. Produce **dogfood observations** that feed ADR-007 graduation (currently `provisional`).
2. Surface preconditions and human-gate moments that will populate `transitions.yaml` v0 under Feature 2 (intra-slice phase automation ADR).
3. Exercise the claim that feature-file `after` dependencies + branch-local state are sufficient for v1 parallelism (ADR-007 D1/D2).
4. Validate the merge-ordering story (§5 of the design doc: slice→feature merge preserves commits).

**Out of scope:** writing any Python harness code, modifying ADR-007 during the run (record findings; propose amendments after).

---

## 2. Coordinator role — what the next session does

Coordinator Claude (next session, after `/clear`) runs **in this worktree** (`/Users/mohammed.farook/Developer/lab/cairn/.worktrees/identifier-scheme/`, tmux session `cairn`).

**Coordinator DOES:**
- Set up N worktrees under `/Users/mohammed.farook/Developer/lab/cairn/.worktrees/<slice-id>/`.
- Create a new tmux window per worker; run interactive `claude` in each and inject the slice-bootstrap prompt via `send-keys` (see `docs/plans/2026-04-16-manual-dogfood-tmux-topology-design.md` — decisions D1 and D6).
- Periodically (every few operator messages) read each worker's `slice.yaml` **and** `tmux capture-pane` output to detect state transitions, permission prompts, and hung states.
- Surface gate moments to the human (firaaz) with one-line asks — "SLICE-X reached Phase-1 intent boundary; approve?".
- Append observations to `.claude/plans/2026-04-16-dogfood-observations.md` (create on first observation).

**Coordinator does NOT:**
- Run any slice phase itself. All Phase 1–4 work happens inside worker sessions.
- Edit files in worker worktrees (strictly read-only).
- Auto-advance any gate. Every phase boundary is human-approved.
- Touch `main` or `feature/identifier-scheme` branches directly.

**Escape valves:**
- If a worker crashes, leave its worktree intact, log it, continue others.
- If two workers produce a file-level merge conflict at integration, stop and escalate. That's exactly the Risk Register case in ADR-007.

---

## 3. tmux topology

Detailed spec: `docs/plans/2026-04-16-manual-dogfood-tmux-topology-design.md`. Summary:

| Window | Name | Role |
|---|---|---|
| `cairn:0` | `coord` | Coordinator Claude session (this-session after `/clear`) |
| `cairn:1` | `A:stale22k` | Worker — housekeeping/stale-22k-cleanup |
| `cairn:2` | `C:validator` | Worker — identifier-scheme/validator-flat-slug |
| `cairn:3` | `B:d3log` | Optional — v1-defense-d3/bypass-log-reclass |
| `cairn:4` | `D:hookbypass` | Optional — identifier-scheme/hook-relpath-bypass |

Human stays attached in `cairn:0` and flips to any worker with `Ctrl-b <N>`. Worker output is pipe-paned to `/tmp/cairn-fleet/2026-04-16/<slice>.log`. Full spawn sequence (worktree → window → `remain-on-exit` → `pipe-pane` → `claude` → bootstrap injection via `send-keys -l`) is in the topology design §3.

---

## 4. Queue items — disjoint file sets

Start with **A + C** (lowest-risk pair: different directories, different mental models). Expand to B/D only if first pair completes cleanly.

| ID | Slice intent | Files touched | Feature | Branch from |
|---|---|---|---|---|
| **A** | `housekeeping/stale-22k-cleanup` — replace stale `22k` ref in `docs/ARCHITECTURE.md:46` and `tests/unit/test_context_budget.py:103` docstring with `30k`/`30,000`. Preserve regression-assertion lines 121/148/149. | `docs/ARCHITECTURE.md`, `tests/unit/test_context_budget.py` | housekeeping | `87ea8b5` |
| **C** | `identifier-scheme/validator-flat-slug` — widen `scripts/validate_architecture.py` to recognize flat-slug ADR filenames in addition to `NNN-slug.md` (closes identifier-scheme follow-on). | `scripts/validate_architecture.py` (+ tests) | identifier-scheme | `87ea8b5` |
| **B** | `v1-defense-d3/bypass-log-reclass` — one-time migration of legacy `.claude/d3-bypasses.log` lines (SLICE-012/014/016) to `<class>: <reason>` format per d3-bypass-classification ADR. | `.claude/d3-bypasses.log` only | v1-defense-d3 | `87ea8b5` |
| **D** | `identifier-scheme/hook-relpath-bypass` — update `checks/reversibility-guard.sh` to handle relative-path edits via `.slice-system/` symlink (follow-on finding from scope-guard.sh:53). | `checks/reversibility-guard.sh` (+ tests) | identifier-scheme | `87ea8b5` |

**Overlap matrix** (verified disjoint):

|   | A | B | C | D |
|---|---|---|---|---|
| A | — | ok | ok | ok |
| B | ok | — | ok | ok |
| C | ok | ok | — | ok |
| D | ok | ok | ok | — |

**Do not parallel-dispatch the d3-bypass-classification substrate slice** alongside these — it overlaps with B (log) and D (hook).

---

## 5. Per-worker bootstrap prompt (template)

Each worker needs a self-contained starting prompt. Use this shape:

```
You are a cairn slice worker. Working directory: <worktree-path>. Branch: <slice-branch>.

You will run the cairn slice methodology (/start-slice … /handoff … close) for this slice:
  - feature: <feature-id>
  - slice intent: <one line>
  - envelope files: <list>
  - invariants touched: <list>

Start by invoking /start-slice. When you reach a phase boundary, commit, run /handoff phase,
and STOP. A human coordinator will approve you to proceed. Do not continue past a phase
boundary on your own. Do not touch files outside the envelope.

The coordinator session is in tmux window 0. You are in window <N>. Do NOT send tmux
commands; communicate only by committing + updating slice.yaml.
```

Keep workers terminal-native; no fancy IPC. The daemon design (§3.2) uses a FIFO — for manual dogfood, the equivalent is the coordinator reading slice.yaml periodically.

---

## 6. Observation log — what to record

Create `.claude/plans/2026-04-16-dogfood-observations.md` with these sections:

1. **Setup log** — timestamps for worktree creation, worker spawn, first state change.
2. **Per-slice timeline** — for each worker, record phase-boundary times and human-touch count.
3. **Coordinator overhead** — how many operator messages were consumed by coordination (vs. actual slice work).
4. **Gate candidacy** — for each observed transition, classify: *autonomous-eligible* (could a precondition script verify this?) or *human-gated-only* (required human judgment). Feeds Feature 2 ADR.
5. **Failures / near-misses** — any merge conflict, invariant violation, scope-guard denial, or surprise.
6. **ADR-007 signals** — does the `after`-dependency model hold? Did any state corruption happen? Any stale-handoff-pointer issues (Risk Register item 2)?

---

## 7. Merge / close protocol per worker

When a worker completes its Phase 4 integration commit:

1. Coordinator verifies the slice.yaml status field reads complete.
2. Human runs `/integration-sweep` in that worker's window (or coordinator runs it read-only from outside).
3. If PASS: human merges the worker's branch into `feature/identifier-scheme` with `git merge --no-ff` (per §5 of the design doc — preserve commits).
4. Delete the worktree via `git worktree remove <path>`; keep the branch for audit.
5. Coordinator logs the merge + timestamp.

**Do NOT** fast-forward; the merge commit is the audit artifact.

---

## 8. Success criteria for this dogfood

Minimum:
- [ ] At least 2 concurrent workers reached Phase 4 without unresolved interference.
- [ ] No file-level merge conflict required manual resolution.
- [ ] Observation log captured ≥5 distinct transition events.

Stretch:
- [ ] All 4 workers ran concurrently for at least one phase boundary.
- [ ] At least one precondition was identified as autonomous-eligible (seed for `transitions.yaml`).
- [ ] Coordinator overhead ≤30% of total operator messages.

On completion (success or informative failure), coordinator writes a closing note appended to `docs/lessons.md` as `L-005 — manual Axis-B dogfood findings` and hands off to a human-run slice that decides ADR-007 graduation.

---

## 9. First concrete coordinator steps (checklist for the next session)

1. `/catchup` to load handoff.
2. Read this file top-to-bottom.
3. Read `docs/plans/2026-04-16-manual-dogfood-tmux-topology-design.md` — the topology spec you're about to execute.
4. Read `docs/plans/2026-04-15-fleet-coordinator-design.md` §3–6 for framing.
5. Read `docs/adr/007-parallelism-v1.md` end-to-end (it's the contract being tested).
6. Confirm with firaaz: "start with A+C only, or include B/D?"
7. Prep session once: `tmux rename-window -t cairn:0 coord` and `mkdir -p /tmp/cairn-fleet/2026-04-16`.
8. Create `.claude/plans/2026-04-16-dogfood-observations.md` with empty section headers (per §6 of this doc).
9. Spawn worker A using the full sequence from topology design §3:
   - `git worktree add ../stale-22k-cleanup 87ea8b5 -b slice/housekeeping-stale-22k`
   - `tmux new-window -n 'A:stale22k' -c <worktree-A-path>`
   - `tmux set-option -w -t cairn:1 remain-on-exit on`
   - `tmux pipe-pane -o -t cairn:1 'tee -a /tmp/cairn-fleet/2026-04-16/A-stale22k.log'`
   - `tmux send-keys -t cairn:1 'claude' Enter`, wait ~2s for claude boot
   - `tmux send-keys -t cairn:1 -l '<rendered §5 bootstrap>'` then a separate `Enter`
10. Spawn worker C by repeating step 9 with: worktree `../validator-flat-slug`, branch `slice/identifier-scheme-validator`, window `C:validator`, target `cairn:2`, log file `C-validator.log`.
11. Begin the observability loop (topology design D8): every human turn, for each active worker, poll `slice.yaml`, `capture-pane -S -100`, and log-size-delta; surface state changes, permission prompts, and hung-state signals as a one-liner preamble before addressing the turn's ask.
