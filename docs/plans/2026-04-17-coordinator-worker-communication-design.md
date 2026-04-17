# Fleet Coordinator ↔ Worker Communication Protocol — Design Document

**Date:** 2026-04-17
**Status:** Design approved (brainstorming complete). Input to Feature 2 ADR (phase automation) and Feature 6 (harness implementation).
**Epic:** Fleet Coordinator (`docs/plans/2026-04-15-fleet-coordinator-design.md`)
**Related ADRs:** ADR-007 (parallelism-v1, provisional), ADR-006 (feature-slice model)
**Dogfood evidence:** `.claude/plans/2026-04-16-dogfood-observations.md` §5b, §6, §8.1

---

## 1. Context and scope

### 1.1 Why this design exists

The April 16 manual Axis-B dogfood shipped 4 concurrent workers through a full slice pipeline and merged cleanly, but surfaced 15 pain points concentrated in **how the coordinator communicates with workers** (obs §8.1). The two dominant costs were:

- **Per-turn polling cost.** With 4 workers, `tmux capture-pane` across all panes on every coordinator turn dumped ~400 lines of ANSI-laden noise into the coordinator's context. User feedback (firaaz, 2026-04-16 13:26): *"We need a better way than this polling. This adds context switching and is wasteful of tokens."* Polling is O(N) per turn; does not scale past ~4 workers.
- **Human-attention burn from routine prompts.** ~20 Claude Code permission prompts per slice (read-only `cat`, `sed`, `awk`, `pytest`, etc.), dozens of `1 Enter` keystrokes, no useful signal.

Separately: the manual coordinator (Claude-as-coordinator) attempted to "understand what every worker is doing" to decide what to raise. This is quadratically bad (N workers × per-worker context). At 10+ workers it collapses.

This design defines the event-driven substrate that replaces polling, moves context ownership to workers, auto-handles routine decisions, and surfaces only genuinely novel/destructive signals to the human.

### 1.2 Scope

**In scope:**
- Transport: hooks → FIFO → asyncio daemon
- Event schema (structured, context-enriched, urgency-tagged)
- Two layers of auto-handling (Layer 1 noise suppression, Layer 2 autonomous transitions)
- Worker-side discipline (`focus.md` self-narrative, bootstrap conventions)
- Daemon → worker direction (tmux send-keys + inbox file)
- Failure/recovery semantics
- `fleet` CLI surface

**Out of scope:**
- Full Python package internals beyond high-level shape
- Rust port (Feature 8/9)
- Progressive-relaxation ratchet protocol itself (Feature 2 ADR owns)
- Cross-feature coordination (`features-registry/` — v1)
- Claude-in-the-daemon synthesis
- GUI / TUI dashboard

### 1.3 Positioning in the epic

- **Feature 1 (identifier scheme):** in flight; this design assumes opaque-string slice IDs.
- **Feature 2 (phase automation ADR):** consumes `transitions.yaml` shape and precondition taxonomy from §4.
- **Feature 6 (harness implementation):** consumes the full protocol as the walking-skeleton spec.

This design becomes the input artifact that unblocks Features 2 and 6.

---

## 2. Architecture

### 2.1 Diagram

```
 ┌─────────────────────────────────────────────────────────────────┐
 │ tmux session: fleet-<feature>                                   │
 │                                                                 │
 │ pane 0 (coord)     pane 1..N (workers)                          │
 │ ┌──────────┐       ┌──────────┐  ┌──────────┐  ┌──────────┐     │
 │ │ daemon   │       │ claude   │  │ claude   │  │ claude   │     │
 │ │ asyncio  │       │ worker A │  │ worker B │  │ worker C │     │
 │ │ reader   │       │ worktree │  │ worktree │  │ worktree │     │
 │ └────▲─────┘       └────┬─────┘  └────┬─────┘  └────┬─────┘     │
 │      │                  │             │             │            │
 │      │        hooks: Notification, PreToolUse, PostToolUse,      │
 │      │               SubagentStart/Stop, SessionEnd              │
 │      │                  │             │             │            │
 │      │         ┌────────▼─────────────▼─────────────▼────────┐   │
 │      └─────────┤ .orchestration/events.fifo                  │   │
 │                └──────────────────────────────────────────────┘  │
 │                                                                  │
 │   .orchestration/                                                │
 │   ├─ events.fifo                                                 │
 │   ├─ audit.log                          ← autonomous actions     │
 │   ├─ permission-policy.yaml             ← Layer 1 classifier     │
 │   ├─ transitions.yaml                   ← Layer 2 classifier     │
 │   ├─ worker-<id>/                                                │
 │   │   ├─ focus.md                       ← worker self-narrative  │
 │   │   ├─ events.log                     ← append-only audit copy │
 │   │   ├─ inbox.yaml                     ← daemon → worker queue  │
 │   │   └─ pending-gates/                                          │
 │   └─ snapshots/<slice>-<ts>/            ← rollback checkpoints   │
 └──────────────────────────────────────────────────────────────────┘

        human ─▶ `fleet` CLI ─▶ events.fifo  ─▶  daemon  ─▶  tmux send-keys / inbox
```

### 2.2 Key properties

- **Push-only event plane.** Workers push via hooks; daemon never polls, never scrapes panes. Event load is O(1) per event regardless of N workers.
- **Context stays with workers.** Each worker owns a 5-line `focus.md` self-narrative; daemon holds zero per-worker context. Daemon is a structured-message router, never a world model.
- **Two automation layers, both policy-driven.**
  - **Layer 1** (noise suppression) in `permission-policy.yaml`: pattern-matched auto-approve/deny in the worker's own hook script. Runs before the daemon sees anything.
  - **Layer 2** (transitions) in `transitions.yaml`: daemon-side classifier for state transitions, dispatch, teardown.
- **Both policy files ADR-owned, not daemon-owned.** Changes are ADR amendments, not code edits.
- **Conservative-by-default, progressively ratcheted.** Nothing silently autonomous. Every auto action hits the audit log; rollback path exists for any branch-state change.
- **Branch state is the source of truth.** `.orchestration/` is derived cache; rebuildable on daemon restart from worktree `slice.yaml`s + each worker's `events.log` tail since last audit entry.

### 2.3 Event-rate reality check

From dogfood observations, per-worker per-slice:

| Event | Rate |
|---|---|
| `state-change` | 4–6× (phase boundaries) |
| `gate-pending` (after Layer 1) | ~3× (down from ~20 raw prompts) |
| `worker-question` | 0–2× |
| `subagent-start/stop` | 2–4× each |
| `session-end` | 1× |

Aggregate at 10 concurrent workers, steady-state: **~0.1 events/sec**. Trivial for asyncio. Throughput is not the risk — backpressure and atomicity are.

---

## 3. Event protocol and worker contract

### 3.1 Event schema

One line of JSON per event, hard cap 400 bytes (PIPE_BUF-safe on macOS).

```json
{
  "v": 1,
  "ts": "2026-04-17T13:42:31Z",
  "worker": "A",
  "slice": "validator-flat-slug",
  "event": "gate-pending",
  "urgency": "HIGH",
  "payload": { "tool": "Bash", "command": "rm -rf tmp/", "path": "/Users/.../worktree-A" },
  "focus": "Rewriting callsite #2 in analyzer.py"
}
```

- `v` — schema version; future-proofs changes.
- `ts` — RFC3339 UTC.
- `worker` — short ID (`A`, `B`, …) matching tmux window name.
- `slice` — opaque string from `slice.yaml`.
- `event` — one of the event types below.
- `urgency` — `HIGH` | `MED` | `LOW`.
- `payload` — event-type-specific fields (bounded).
- `focus` — tail of the worker's `focus.md` at emit time; pre-enriched context.

### 3.2 Event types (v0)

| Event | Source | Payload |
|---|---|---|
| `state-change` | `PostToolUse` on Edit/Write to `slice.yaml` | `from_state`, `to_state`, `commit_sha` |
| `gate-pending` | `Notification:permission_prompt` (Layer 1 didn't clear) | `tool`, `command`, `path` |
| `gate-auto-approved` | Layer 1 hook cleared a prompt | `tool`, `command`, `rule_matched` |
| `gate-auto-denied` | Layer 1 hook denied a prompt | `tool`, `command`, `rule_matched` |
| `worker-question` | `PreToolUse:AskUserQuestion` | `question`, `options` |
| `worker-idle` | `Notification:idle_prompt` | (empty) |
| `subagent-start` | `SubagentStart` | `description` |
| `subagent-stop` | `SubagentStop` | `description`, `duration_ms` |
| `session-end` | `SessionEnd` | `exit_reason` |
| `pane-died` | tmux `pane-died` hook | (no CC context — raw tmux) |

### 3.3 Worker-side `focus.md` contract

5 lines, hard-capped at 500 bytes. Worker is expected (per bootstrap prompt) to overwrite it at three moments:

1. Every phase transition.
2. Before any destructive or scope-expanding tool call.
3. Whenever the current step changes materially (new file, new subagent dispatch, blocker hit).

Shape:
```
Phase: <state>
Intent: <one-line slice intent>
Last step: <what just finished>
Current: <what's being attempted now>
Risk: <anything notable — blank if routine>
```

No skill, no ceremony — just a file the worker agrees to keep current. The bootstrap prompt embeds the convention. If a worker slips, events still fire but `focus` carries the previous line — never empty (bootstrap writes an initial line at spawn).

### 3.4 Urgency tagging (hybrid)

Worker tags events at emit time per bootstrap convention:
- `HIGH` — destructive, scope-expanding, or worker is stuck/unrecoverable.
- `MED` — default judgment call.
- `LOW` — routine, read-only, or within a known-safe family.

Daemon applies `permission-policy.yaml` overrides on receipt (e.g., `rm*` always HIGH regardless of worker tag). Worker-tag is a hint; policy file is authority. Hybrid gives uniformity without killing adaptive cases.

### 3.5 Daemon → worker direction (dual channel)

- **`tmux send-keys`** for gate approvals. Literally sends `1\n` / `2\n` to the active CC prompt. Proven in dogfood D6. Synchronous enough.
- **Worker inbox** (`.orchestration/worker-<id>/inbox.yaml`) for richer dispatch — e.g., "advance to phase 3", "re-run phase 2 RED", "abandon slice". Worker reads at phase boundaries via a bootstrap-enforced convention; daemon writes atomically (write-to-tmp + rename).

Rule of thumb: if CC has a blocking prompt active → send-keys. Otherwise → inbox. No ambiguity.

### 3.6 Hook config delivery

Workers get a shared `settings.local.json` snippet at spawn time. Daemon templates it into `<worktree>/.claude/settings.local.json` before launching `claude`. The snippet registers:

- `Notification` (matchers: `permission_prompt`, `idle_prompt`)
- `PreToolUse` (matchers: `AskUserQuestion`)
- `PostToolUse` (matchers: `Edit`, `Write`; filtered on `file_path` ending in `slice.yaml`)
- `SubagentStart`, `SubagentStop`
- `SessionEnd`

Each hook is a shell `command` that: (1) reads the hook JSON from stdin, (2) reads `focus.md`, (3) optionally applies Layer 1 classification, (4) writes one JSON line to `events.fifo` with a 100ms timeout, (5) appends the same line to `worker-<id>/events.log`.

Single source of truth for the template lives in the cairn repo (`cairn_fleet/hooks/settings.template.json`). Uniform across workers; deterministic.

### 3.7 Atomicity and backpressure

- Writes ≤ 400 bytes are atomic on macOS (`PIPE_BUF` = 512). No interleaving between concurrent writers. Design constraint: every event payload stays under 400 bytes; oversized payloads (e.g., long commands) are truncated with `truncated: true`.
- Hook's FIFO-write has `timeout 100ms`. If daemon isn't draining, hook writes to a fallback `events-dropped.log` and exits non-blocking. Workers never stall on daemon slowness.
- Daemon's asyncio drain loop does only `readline → parse → enqueue`. All real work happens in downstream coroutines; drain never blocks.

---

## 4. Orchestrator behavior

### 4.1 Layer 1 — Noise suppression (worker-local)

Runs inside the worker's own `Notification:permission_prompt` hook script. Fast, deterministic, no daemon round-trip.

**Hook script logic:**
```
1. Read permission-policy.yaml (cached; ~20-50 rules)
2. For each rule in order, match tool + command + path against pattern
3. First match wins:
     - "auto-approve" → send-keys "1\n" to own pane, emit gate-auto-approved
     - "auto-deny"    → send-keys "2\n" to own pane, emit gate-auto-denied
     - "raise"        → emit gate-pending (urgency from rule or worker tag)
     - "raise-if-unmatched" (default) → emit gate-pending (MED)
```

**`permission-policy.yaml` shape:**
```yaml
version: 1
rules:
  - name: read-only-project-ops
    tool: Bash
    command: '^(cat|sed -n|awk|grep|rg|ls|git (status|log|diff))\s'
    path: '(^\.)|(^/Users/.*/Developer/.*)'
    action: auto-approve
    urgency: LOW

  - name: destructive-always-raise
    tool: Bash
    command: '(rm\s|mv\s|git push|git reset --hard)'
    action: raise
    urgency: HIGH

  - name: test-runners
    tool: Bash
    command: '^(pytest|uv run pytest|ruff check)'
    action: auto-approve
    urgency: LOW

  - name: default
    action: raise
    urgency: MED
```

Rules are ordered; first match wins. Starting set is small (~20 rules). Additions are ADR amendments backed by observation data.

**Why worker-local (per-hook) rather than daemon-side:**
- Zero daemon-round-trip latency (~10ms/prompt saved)
- Workers on different timelines run concurrently without daemon serialization
- Daemon sees fewer events; less load, less noise in audit
- Trade-off accepted: classifier runs N times (once per worker). Cost is negligible (~1ms of regex matching per prompt).

### 4.2 Layer 2 — Autonomous transitions (daemon-side)

Runs inside the daemon's event handler when `state-change` arrives or when an `after:` dep gets satisfied. For each transition: look up classification in `transitions.yaml`. If autonomous + preconditions pass → take action, write audit entry, snapshot for rollback. If human-gated → queue in `pending-gates/`, present via `fleet status`.

**`transitions.yaml` shape:**
```yaml
version: 1
transitions:
  - from: unassigned
    to: phase-1-intent
    gate: autonomous
    action: spawn-worker
    preconditions: [deps-satisfied, worker-slot-available]

  - from: phase-1-intent
    to: phase-2-validation
    gate: human
    rationale: "Intent review is irreducibly human in v0"

  - from: phase-2-validation
    to: phase-3-implementation
    gate: human          # v0 conservative; may earn autonomous upgrade post-data
    preconditions: [tests-red, scope-locked, fork-log-empty]

  - from: phase-3-implementation
    to: phase-4-integration
    gate: human
    preconditions: [tests-green, scope-unchanged, snapshot-clean]

  - from: phase-4-integration
    to: merged
    gate: human
    rationale: "Integration sweep and merge are human-gated in v0"

  - from: any
    to: needs-review
    gate: autonomous
    trigger: [worker-crash, precondition-fail]
    action: preserve-worktree-notify
```

### 4.3 v0 autonomous set (deliberately small)

- `spawn-worker` — dispatch a slice whose `after:` deps are satisfied to a free pane.
- `teardown-worker` — after human-approved merge.
- `rebuild-derived-state` — on daemon restart.
- `preserve-worktree-notify` — on worker crash or precondition failure.
- Layer 1 auto-approves per `permission-policy.yaml`.

Everything else (phase 2→3, 3→4, 4→merge, retries, conflict resolution, `AskUserQuestion`) is human-gated. Progressive relaxation is an ADR-amendment path, not a daemon knob.

### 4.4 Audit log

Append-only, line-per-event, grep-able. `.orchestration/audit.log`:
```
2026-04-17T13:42:31Z  worker=A  action=auto-approve-gate  rule=read-only-project-ops  tool=Bash  cmd="cat foo.py"  urgency=LOW
2026-04-17T13:43:10Z  worker=B  action=state-change       from=phase-1-intent to=phase-2-validation commit=abc123 gate=human-approved
2026-04-17T13:44:01Z  worker=C  action=spawn-worker       slice=validator-flat-slug worktree=../validator deps=[]
2026-04-17T13:51:22Z  worker=A  action=rollback           target=phase-2-validation reason=precondition-fail:tests-red
```

`fleet audit <worker>` filters by worker. Retained indefinitely (small; text-only).

### 4.5 Rollback

Before any autonomous action that mutates branch state, daemon writes `.orchestration/snapshots/<slice>-<ts>/` containing git HEAD SHA + `slice.yaml` copy + `focus.md` copy. `fleet rollback <slice>` restores via `git reset --hard <sha>` + file restore. No complex git surgery; no remote interaction.

---

## 5. `fleet` CLI surface

All commands are one-shot, write-to-FIFO-and-exit (except `start`, which also launches the daemon process).

```
fleet start <feature>              # launch daemon + configure tmux session
fleet status [--all]               # print pending gates + focus.md tails
fleet approve <worker>             # resolve HIGH/MED gate
fleet approve --all LOW            # batch-clear low urgency
fleet reject <worker> <reason>     # worker recovers / abandons
fleet snooze <worker> <duration>   # suppress prompts from worker
fleet attach <worker>              # tmux attach to worker pane
fleet pause / resume               # dynamic graph edits
fleet rollback <slice>             # restore from snapshot
fleet audit <worker>               # grep audit log
fleet stop                         # graceful shutdown
```

`fleet status` output shape (example):
```
[HIGH] A: gate pending — Bash `rm -rf .claude/current-slice`
       context: cleanup before /start-slice scaffolding (Phase 1 pre)
       waiting 7m      [fleet approve A] [fleet attach A] [fleet reject A "..."]

[MED]  C: worker question — AskUserQuestion: "Use flat slug or nested?"
       context: ADR-006 is ambiguous on this; Phase 2 RED test design
       waiting 2m      [fleet approve C] [fleet attach C]

[LOW]  B, D: 7 routine gates queued (cat/sed/awk). auto-approved.

idle: none.  in-flight: 4.  stalled: 0.  pending-gates: 2.
```

---

## 6. Daemon implementation shape

### 6.1 Package layout

```
cairn_fleet/
├─ __main__.py                    # entry: `python -m cairn_fleet start`
├─ daemon.py                      # asyncio main loop
├─ events/
│   ├─ reader.py                  # FIFO drain → in-memory deque
│   ├─ handlers.py                # one coroutine per event type
│   └─ schema.py                  # dataclasses + JSON (de)serialization
├─ state/
│   ├─ worker.py                  # per-worker state object (in-memory)
│   ├─ rebuild.py                 # restart: re-scan worktrees + events.log
│   └─ audit.py                   # append-only audit writer
├─ policy/
│   ├─ permission.py              # permission-policy.yaml loader + matcher
│   ├─ transitions.py             # transitions.yaml loader + classifier
│   └─ preconditions/             # pluggable precondition check modules
├─ tmux.py                        # spawn, send-keys, pane-died registration
├─ cli.py                         # `fleet` subcommands
├─ hooks/
│   └─ settings.template.json     # hook snippet templated per worker
└─ tests/
    ├─ test_event_schema.py
    ├─ test_permission_policy.py
    ├─ test_transitions.py
    ├─ test_rebuild.py
    └─ test_daemon_e2e.py         # stub worker, real FIFO
```

Estimated ~600 LOC Python + ~400 LOC pytest.

### 6.2 Main loop (two-stage drain)

```python
async def main():
    fifo = await open_fifo_async(".orchestration/events.fifo")
    queue = asyncio.Queue()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(drain_fifo(fifo, queue))      # dumb + fast
        tg.create_task(process_events(queue))        # dispatch to handlers
        tg.create_task(tmux_pane_watcher())          # pane-died fallback
```

Drain never blocks on work; downstream coroutines handle policy, audit, snapshots, send-keys.

---

## 7. Failure modes and recovery

| Failure | Detection | Recovery |
|---|---|---|
| Worker crashes (SIGKILL, OOM, panic) | tmux `pane-died` hook → FIFO | Daemon marks `needs-review`, preserves worktree, emits HIGH notice |
| Daemon crashes | Supervisor respawns | `state.rebuild` re-scans each worktree's `slice.yaml` + `events.log` tail since last audit entry; workers unaffected |
| FIFO write fails (daemon down / missing) | Hook's 100ms timeout | Hook writes to `events-dropped.log`, exits non-blocking; daemon replays on restart |
| Hook script errors (bad regex, missing `jq`) | Exit code non-zero | Worker sees stderr warning, proceeds unhooked for that event; next state-change re-syncs |
| Concurrent FIFO writes | N/A | Writes ≤ 400 bytes are atomic per PIPE_BUF |
| `focus.md` stale | N/A | Event carries previous focus; never empty (bootstrap seeds initial) |
| tmux session killed externally | Next send-keys fails | Daemon logs, exits gracefully; human relaunches `fleet start` |
| Invalid `permission-policy.yaml` / `transitions.yaml` | Loader validates at startup | Daemon refuses to start, prints failed rule; no silent misclassification |
| Hook config missing (fresh worktree) | Daemon's spawn step validates template | Spawn aborts; no partial hook setup |

### 7.1 Blocking duration for workers

Workers sit cheaply while blocked: ~50–100 MB RAM, zero inference cost, no timers. Typical waits:

| Scenario | Typical wait |
|---|---|
| Human at keyboard, HIGH gate | 5–30 s |
| Context-switching between workers | 1–10 min |
| Away briefly | 10–60 min |
| Overnight | 8+ h |
| Abandoned | indefinite |

Daemon tracks `pending_since` per event; `fleet status` surfaces waits so nothing silently rots. CC's internal TUI idle timeout for multi-day waits is untested — non-issue for single-session use.

---

## 8. Testing strategy

1. **Unit tests.** Schema (de)serialization, policy matcher correctness, transitions classifier, precondition modules.
2. **Integration tests** with a stub worker (shell script that writes fake events to FIFO). Verifies event handlers, audit-log shape, rollback path.
3. **E2E smoke test** with real `claude` against a trivial slice (e.g., "add one comment to README.md"). Verifies hook templating, FIFO wiring, send-keys delivery, `SessionEnd` handling under real conditions.
4. **Dogfood comparison.** Re-run the April 16 manual-parallel-dogfood equivalent under the daemon. Compare:
   - Human-touch count per slice (baseline ~40 prompts/slice → target <5)
   - Coordinator context cost (baseline 400 lines/turn of ANSI → target ~0, since no polling)
   - `/handoff` skill divergence (baseline reproducible on A at P2/P3/P4 → target zero, since daemon drives phase dispatch)

---

## 9. v0 scope boundaries (explicitly deferred)

- No GUI / TUI dashboard — `fleet status` is plaintext.
- No auto-merge at Phase 4 — human runs `/integration-sweep` + `git merge`.
- No auto-retry of failed workers.
- No cross-feature coordination — `features-registry/` is v1.
- No Claude-in-the-daemon synthesis — `fleet status` concatenates `focus.md` files, no AI pass.
- No Windsurf / Gemini / Codex workers — agent-family seam exists; implementations don't.
- No durable FIFO (Kafka-style) — replay from `events.log` + `slice.yaml` is enough.
- No horizontal daemon scaling — single daemon per fleet.

---

## 10. Exit criteria

Design is real when:

1. This doc is committed.
2. Feature 2 ADR is written consuming `transitions.yaml` shape + precondition taxonomy from §4.
3. A new `permission-policy` ADR (or section within Feature 2) consumes the Layer 1 shape.
4. Feature 6 walking skeleton implements event schema + FIFO + one stub handler end-to-end.
5. E2E smoke test passes with a real one-slice run.
6. Re-dogfood at ≥2 workers, compare human-touch count to April 16 baseline; target <5 prompts/slice.

---

## 11. Open decisions for Feature 2 ADR

Items this design surfaces but defers to Feature 2 ADR ownership:

- **Precondition taxonomy.** `tests-red`, `tests-green`, `scope-locked`, `scope-unchanged`, `fork-log-empty`, `snapshot-clean`, `deps-satisfied`, `worker-slot-available` — each needs a precondition script spec (how it checks, what it returns, how it reports failure).
- **Initial `transitions.yaml` content.** This design sketches the shape and v0 autonomous set; the actual ADR writes the binding version.
- **Initial `permission-policy.yaml` content.** Same — shape defined here, binding rules in ADR.
- **Progressive-relaxation ratchet protocol.** How a transition moves from human-gated to autonomous based on observation data. Not a daemon feature — an ADR-amendment procedure.

---

## 12. Open decisions for Feature 6 implementation

- **Daemon inside-tmux vs outside-tmux.** Coordinator design §3 places it in pane 0; supervisor pattern could put it outside tmux and have it span features. Resolve during Feature 6 walking-skeleton.
- **`fleet` CLI packaging.** Console-script entry in `pyproject.toml` vs. shell wrapper script. Convenience detail.
- **Permission-policy cache invalidation.** Currently "read once at hook load"; if policy changes mid-run, hooks use stale rules until next worker spawn. Acceptable for v0; may need reload-signal later.
- **events.log rotation.** Per-worker append-only; needs size-based rotation eventually. Not a v0 correctness concern.
