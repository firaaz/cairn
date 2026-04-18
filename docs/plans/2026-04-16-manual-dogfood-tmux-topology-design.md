# Manual Parallel Dogfood — tmux Topology Design

**Date:** 2026-04-16
**Status:** Design approved. Companion to `.claude/plans/2026-04-16-manual-parallel-dogfood.md` (which specifies queue items, bootstrap template, and success criteria). This doc specifies the physical tmux layout, worker lifecycle, observability loop, and teardown.
**Epic:** Fleet Coordinator (`docs/plans/2026-04-15-fleet-coordinator-design.md`)
**ADRs referenced:** ADR-007 (parallelism-v1, provisional)

---

## 1. Purpose

The manual Axis-B dogfood spawns 2–4 concurrent `claude` worker sessions in separate worktrees. This doc pins exactly how tmux hosts them so the coordinator (this-session Claude) can observe state, surface gates to the human (firaaz), and deliver resume signals without drift — producing clean observation data for ADR-007 graduation and `transitions.yaml` v0.

The dogfood plan already specified windows-per-worker at a sketch level. This design makes the mechanics concrete and resolves four forks that the sketch left open: worker invocation mode, layout topology, resume-signal delivery, and log capture.

---

## 2. Decisions

### D1 — Worker invocation: interactive `claude`, not `claude -p`

Each worker is a long-lived interactive REPL, one per slice. It runs a phase, commits, emits `/handoff phase`, then sits at the prompt awaiting a resume keystroke.

**Why:** mirrors the human-driven slice pattern (one Claude session per slice, not per phase); keeps conversational context across phases; `/clear` provides the same context-reset lever that one-shot respawn would; a hung worker is debuggable by attaching.
**Rejected alternative:** one-shot `claude -p` per phase. Its claimed advantage (clean context budget per phase) is delivered just as well by `/clear` inside an interactive session. The respawn bookkeeping it would force on the coordinator has no offsetting benefit.

### D2 — Layout: one tmux window per worker (not panes, not multi-session)

Coordinator in `cairn:0`. Workers in `cairn:1..N`. `Ctrl-b <N>` flips to any worker full-screen.

**Why:** at 2–4 workers, full-width claude TUIs render correctly and diffs don't line-wrap. Coordinator terminal stays uncluttered. Observation is `slice.yaml`-mediated and `capture-pane`-mediated, so at-a-glance multi-pane visibility isn't load-bearing.
**Rejected alternatives:**
- Panes in one window: a 237×55 terminal split four ways yields ~118×27 per pane, which makes claude's TUI cramped.
- Dashboard window + dedicated worker windows: more ceremony than a one-shot dogfood warrants.

### D3 — Naming: `<Letter>:<mnemonic>`, coord role explicit

| Window | Name | Role |
|---|---|---|
| `cairn:0` | `coord` | Coordinator Claude session |
| `cairn:1` | `A:stale22k` | Worker — housekeeping/stale-22k-cleanup |
| `cairn:2` | `C:validator` | Worker — identifier-scheme/validator-flat-slug |
| `cairn:3` | `B:d3log` | Optional — v1-defense-d3/bypass-log-reclass |
| `cairn:4` | `D:hookbypass` | Optional — identifier-scheme/hook-relpath-bypass |

**Why:** the letter matches the plan §4 queue so coordinator-speak stays consistent ("SLICE-A reached phase-1"); the mnemonic is for the human at a glance in the tmux status bar. Fits ~60 chars total in status bar with 4 workers.

### D4 — Session: keep `cairn`

Do not rename to `fleet-identifier-scheme`. Eventual daemon uses `fleet-<feature>` per coordinator design §3; manual dogfood uses existing session to avoid disruption.

### D5 — Pane exit: `remain-on-exit on` per worker window

A crashed `claude` leaves its last output visible for post-mortem instead of the window closing instantly.

### D6 — Resume signal: coordinator-driven `send-keys`

Human says "approve A to phase 2" in the coord conversation. Coordinator runs:
```
tmux send-keys -t cairn:<N> -l '<approval+next-phase prompt>'
tmux send-keys -t cairn:<N> Enter
```

**Why:** one control point (this conversation), mirrors eventual daemon dispatch, tests whether `send-keys` is reliable enough for v0 before it's baked into Python.
**Non-violation of plan §2:** plan §2 prohibits coordinator from *editing files* in worker worktrees. `send-keys` sends input to a REPL — same axis as a human typing — and is distinct.
**Escape valve:** human may `Ctrl-b <N>` at any time and hand-drive the worker.

### D7 — Log capture: `pipe-pane` to `/tmp/cairn-fleet/<date>/`

Each worker window pipes its pane output to a log file:
```
tmux pipe-pane -o -t cairn:<N> 'tee -a /tmp/cairn-fleet/2026-04-16/<slice>.log'
```

**Why:** full durable transcript for post-hoc grep; `/tmp` lifetime matches single-day dogfood scope; zero git-pollution risk.
**End-of-dogfood handling:** key excerpts copied by hand into `.claude/plans/2026-04-16-dogfood-observations.md`; raw logs discarded with `/tmp` eventually, or copied to coord worktree under a gitignored path if durable retention is desired.

### D8 — Coordinator observability loop: conversation-turn-paced, not background

On every human turn, coordinator runs this poll sequence before responding to the turn's actual content:

1. For each active worker window, read `<worktree-path>/.claude/current-slice/slice.yaml` — detect `status` or `phase` change since last poll.
2. For each active worker window, `tmux capture-pane -p -t cairn:<N> -S -100` — grab last 100 lines. Scan for permission prompts, error markers, and output-growth-since-prior-poll to detect hung states.
3. Check `/tmp/cairn-fleet/2026-04-16/*.log` sizes against prior-turn sizes — any log that hasn't grown AND whose slice.yaml hasn't changed is flagged "possibly stuck."
4. Any state change or attention-needed signal gets surfaced as a one-liner at the top of the coordinator's response, before addressing the turn's ask.

No cron, no watcher subprocess, no background polling. Conversation cadence IS the poll cadence.

**Why:** piggybacks on the natural rhythm of the session; matches plan §3's intent ("periodically … read each worker's slice.yaml"); avoids introducing a second control loop in what's already a one-shot experiment.

### D9 — Permission prompt handling

Workers are NOT launched with pre-approved tool lists; we want to observe permission friction as data. When `capture-pane` detects a pending prompt:

- Coordinator surfaces: `"SLICE-A awaiting permission on <tool> <command>"` with the prompt quoted verbatim.
- Human replies: `approve A` → coordinator sends `1 Enter`; `deny A` → coordinator sends `2 Enter`; `let me look` → human attaches via `Ctrl-b 1`.
- Every permission event gets a line in the observation log.

### D10 — Teardown: kill-window then worktree-remove, keep branch

On worker Phase-4 integration completion and human-approved merge:
```
tmux kill-window -t cairn:<N>
git worktree remove <worktree-path>
# Branch retained for audit per .claude/plans/2026-04-16-manual-parallel-dogfood.md §7
```

---

## 3. Complete spawn sequence (coordinator executes per worker)

```
# 1. Create the worktree
git worktree add ../<slug> 87ea8b5 -b slice/<feature>-<slug>

# 2. Ensure log dir exists (idempotent; runs once before first worker)
mkdir -p /tmp/cairn-fleet/2026-04-16

# 3. Create named tmux window at worktree cwd
tmux new-window -n '<Letter>:<mnemonic>' -c <worktree-path>

# 4. Configure window — persist on exit, start pipe-pane
tmux set-option -w -t cairn:<N> remain-on-exit on
tmux pipe-pane -o -t cairn:<N> 'tee -a /tmp/cairn-fleet/2026-04-16/<slice>.log'

# 5. Launch interactive claude
tmux send-keys -t cairn:<N> 'claude' Enter

# 6. Wait briefly for claude to finish booting (empirical — start with sleep 2, tune)
# 7. Inject the bootstrap prompt from plan §5, literal mode to preserve special chars
tmux send-keys -t cairn:<N> -l '<rendered bootstrap template>'
tmux send-keys -t cairn:<N> Enter
```

**Rename coord window once, before spawning first worker:**
```
tmux rename-window -t cairn:0 coord
```

---

## 4. Open questions / flagged for later decisions

1. **Eventual daemon location (inside vs outside tmux).** Coordinator design doc §3 currently places the Python daemon in pane 0 of `fleet-<feature>`. Surfaced during this brainstorm: daemon-outside-tmux (standard daemon pattern, survives session kill, spans multiple features per §3's `features-registry/`) vs daemon-inside (single attach target, simpler lifecycle, no supervisor needed). §6's "supervisor respawns" doesn't pin which side. **Resolve during Feature 6 harness ADR, not here.**
2. **Bootstrap injection timing.** Step 6 above uses a hardcoded `sleep 2`. If claude's boot time varies, send-keys may race. Observe during dogfood; if flaky, add a readiness check (e.g. `tmux capture-pane` for the claude prompt marker before injecting).
3. **Log retention after dogfood.** `/tmp` lifetime is session-scoped on macOS; may or may not persist across reboots. If user wants durable logs, move path to `~/.claude/fleet-logs/2026-04-16/<slice>.log`.
4. **Permission-prompt detection markers.** `capture-pane` heuristics in D8 and D9 rely on string-matching claude's current prompt text. Brittle across CC version updates. Observe; record the actual marker strings in the observation log so a future automated harness has a ground-truth sample.

---

## 5. Success criteria (for this topology, distinct from dogfood §8)

- Workers spawn cleanly on the first attempt; no `send-keys` race.
- Coordinator detects every phase boundary from `slice.yaml` within one conversation turn.
- Coordinator detects every permission prompt within one conversation turn.
- `send-keys` approval reliably resumes the worker (no stuck-prompt corruption).
- Worker logs in `/tmp/cairn-fleet/` are complete and greppable.
- Teardown leaves no orphaned tmux windows or worktrees.

Failure of any of these is itself dogfood data — record in `.claude/plans/2026-04-16-dogfood-observations.md` under "Failures / near-misses."
