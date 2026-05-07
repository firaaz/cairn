---
id: orchestrator-observability
name: "Orchestrator observability — JSON canonical, MD derived, forward-compat schema, deferred retention"
status: superseded
superseded-by: orchestrator-observability-superseded
firmness: provisional
supersedes: []
supersedes-sections: []
topic: process
adrs-referenced: [context-discipline-protocol, identifier-scheme, cliff-failure-mode-and-v1-defenses, parallelism-v1, slice-close-contract]
invariants-touched: [INV-002]
date: 2026-04-20
---

# orchestrator-observability: Orchestrator observability-artifact shape and schema

## Status
Accepted

## Date
2026-04-20

## Context

`scripts/slice_orchestrator.py` currently produces phase-transition stderr output, per-failure log files at `.claude/orchestrator-debug/<slug>-phase-{N}-{role}-{ts}.log`, and nothing else. Post-close state is unavailable to consumers: neither the markdown `/catchup` consumes nor a future fleet-coordinator can tell what happened inside a slice beyond what `git log` shows.

The session that produced this ADR also produced `docs/plans/2026-04-20-observability-and-close-slice-design.md` (the design) and `docs/plans/2026-04-20-observability-and-close-slice-brainstorm.md` (the reasoning archive). This ADR codifies the observability-shape commitments as provisional — a distinct firmness from the companion slice-close-contract ADR, which is firm.

**Why provisional, not firm.** The observability shape (JSON vs MD, placement, schema fields) is a representation choice with no current consumers. The first real consumer (fleet-coordinator epic, per memory record `coordinator_architecture_brainstorming.md`) will surface schema requirements we cannot fully anticipate. Provisional firmness lets this ADR iterate on consumer evidence rather than lock speculative shape.

**Placement supersession note.** The earlier `docs/plans/2026-04-20-compression-pipeline-hardening-design.md:201,250,257` placed `orchestrator-result.json` in `.claude/current-slice/`. This ADR supersedes that placement.

## Decision

### D1 — Placement: `.claude/orchestrator-debug/`

Observability artifacts live in `.claude/orchestrator-debug/`, not `.claude/current-slice/`. Three reasons:

1. **Scan-surface containment.** Agents routinely list or grep `.claude/current-slice/`. Moving observability out of that scope reduces incidental context pollution.
2. **Cross-slice persistence.** Post-close consumers (`/catchup phase N`, fleet-coordinator history read) require state to survive slice close. `.claude/current-slice/` is wiped by slice-close-contract D3; `.claude/orchestrator-debug/` is not.
3. **Fleet-coordinator future.** A stable outside-slice path is a precondition for the fleet-coordinator epic's read pattern.

### D2 — JSON canonical + MD derived (DC-1)

`<slug>-result.json` is the canonical state. `<slug>-result.md` is generated deterministically from the JSON by a pure function `_generate_result_md(state: dict) -> str`. There is no independent MD write path.

This eliminates drift by construction: every MD update is a projection of the latest JSON. The projection is a stdlib string-formatting function; no templating dependency. Per CLAUDE.md's stdlib-only constraint for new code.

### D3 — Heartbeat and state decoupled (DC-2)

Two threads touch observability:
- **Main thread** — writes `<slug>-result.json`, `<slug>-result.md`, `index.jsonl`. Never writes `.heartbeat`.
- **Heartbeat thread** — writes only `.heartbeat`. Never reads or writes state dict, JSON, or MD.

No shared lock between the threads. They touch disjoint files. Subprocess children (agent dispatches) do not touch observability files; their writes are bounded by `checks/scope-guard.sh` and `checks/role_guard.py`.

### D4 — Schema (B2/B3 hybrid)

The state dict written to `<slug>-result.json` carries a stable shape with a forward-compat contract.

**Firmly committed fields** (internally motivated; shape is driven by our own observability needs, not consumer speculation):

```python
{
    "schema_version": "1.0",          # bump only on field removal or retyping
    "slice_id": str,                  # from slice.yaml
    "started_at": str,                # ISO 8601 UTC
    "ended_at": str | None,
    "status": str,                    # see Status enum below
    "exit_code": int | None,
    "current_phase": int,             # 1..4
    "phases_completed": list[int],
    "phase_timings": dict,            # {phase_str: {"started_at": str, "ended_at": str, "duration_seconds": float}}
    "retries_by_phase": dict,         # {phase_str: int} — B14/B15 counts
    "cluster_dispatches": list[dict], # phase-3 fan-out trail
    "degradation_reason": str | None, # append-preserving; see D7
    "observability_errors": dict,     # per-writer failure counts
    "final_commit": str,              # set by close_slice on OK
    "summary": str
}
```

**Additive-safe fields** (forward-compat for fleet-coordinator; consumer pattern not yet known):

```python
"worktree_path": str,   # absolute path to the worktree
"orchestrator_pid": int # process PID
```

**Additive-safe contract.** Adding a new optional field to the schema is a non-breaking change and does NOT bump `schema_version`. Consumers code defensively: read with `.get(key, default)`, ignore unknown fields. Only field removal or retyping bumps `schema_version`.

**Status enum.**
- Non-terminal: `IN_PROGRESS`, `DEGRADED`
- Terminal: `OK`, `FAILED`, `ABORTED`, `ESCALATED`, `SIGNALED`

`DEGRADED` replaces `IN_PROGRESS` when an observability write has exhausted its retry budget (see D6). On terminal transition, `status` moves to a terminal value; `degradation_reason` persists (see D7).

### D5 — Artifact file set and write cadence

| File | Writer | Cadence | Atomic? |
|------|--------|---------|---------|
| `.claude/orchestrator-debug/<slug>-result.json` | main thread | every state transition + final `atexit` | tempfile + `os.rename` in same directory |
| `.claude/orchestrator-debug/<slug>-result.md` | main thread | terminal transitions only | same |
| `.claude/orchestrator-debug/index.jsonl` | main thread | every failure log + every phase-3 cluster dispatch | `O_APPEND` |
| `.claude/current-slice/.heartbeat` | heartbeat thread | every `CAIRN_HEARTBEAT_INTERVAL` seconds | same-directory tempfile + rename |
| `.claude/orchestrator-debug/<slug>-phase-{N}-{role}-{ts}.log` | main thread | on failed agent dispatch | existing writer unchanged |

**MD cadence is close-only, not per-transition.** Per-transition MD regeneration costs cycles and produces churn with no consumer benefit; close-only matches the expected read pattern (humans read MD after close, machines read JSON).

### D6 — Error policy (three-level retry → degrade → fail)

**Strict lifecycle.** Wipe failures, commit failures, resume divergence exit the slice non-zero (governed by slice-close-contract). No retry on these paths.

**Observability writes use a three-level model:**

1. **Level 1 — Bounded retry.** `_atomic_write()` retries once with no delay on `OSError`. One stderr log on first failure; second failure raises.
2. **Level 2 — Degraded mode.** If the retry also fails, the slice enters `status=DEGRADED`, populates `degradation_reason`, and continues. Consumers see the status change on the next successful persist.
3. **Level 3 — Strict failure.** If the `DEGRADED` state write itself fails (cannot even record degradation), the orchestrator exits `FAILED` with explicit stderr: `orchestrator: observability fully unwritable; cannot continue`.

Heartbeat-thread writes are self-healing: internal try/except with one stderr log per unique error class. Heartbeat thread death is detected by main-thread periodic sampling; one restart attempt, then `status=DEGRADED`.

### D7 — Degradation persistence contract

`degradation_reason` is **append-preserving**. Once set during a slice, it persists through every subsequent state transition — including terminal transitions. Setting it to `None` after non-None is a contract violation. Writing a new reason when one is already set overwrites (the most-recent root cause wins; `observability_errors` counters still reflect the prior history monotonically).

This ensures post-close consumers can see "this slice ran degraded at some point" even after a successful close. Fleet-coordinator observability-health monitors depend on this property.

### D8 — Retention policy (deferred with tripwire)

No retention policy lands in this ADR. `.claude/orchestrator-debug/` grows unboundedly.

**Tripwire.** A follow-up slice implementing retention is required when either:
- `.claude/orchestrator-debug/` exceeds 100 files, OR
- `index.jsonl` exceeds 1 MB.

The tripwire is observable at integration-sweep time. When it fires, a new ADR or a superseding of this ADR's D8 is required.

### D9 — Heartbeat cadence defaults

- `CAIRN_HEARTBEAT_INTERVAL` — touch `.heartbeat` every N seconds. Default: `10.0`.
- `CAIRN_HEARTBEAT_STALE` — readers consider heartbeat stale if mtime is older than N seconds. Default: `30.0`.

Both follow the cairn env-var convention at `docs/operational-reference.md:339-344` and `scripts/slice_orchestrator.py:135,774`.

## Consequences

**Made easier:**

- `/catchup phase N` gains a stable path to per-slice history (`<slug>-result.md`).
- Fleet-coordinator era gets a substrate it can read: JSON stream + per-slice detail.
- Observability failures are surfaced explicitly (DEGRADED), not masked.
- Agents scanning `.claude/current-slice/` do not pull in historical state.

**Made harder:**

- Two new file classes (`-result.json`, `-result.md`) plus one stream (`index.jsonl`) plus one ephemeral (`.heartbeat`) — more concepts operators must understand.
- `_atomic_write` with tempfile + rename in same directory is required for every state write; deviations produce torn-read bugs.
- No rotation → `.claude/orchestrator-debug/` grows. Tripwire eventually forces a follow-up slice.
- Provisional firmness means this ADR is expected to iterate. Supersession is cheap but still requires the `/decision` protocol.

**Invariant impact:**

- **INV-002 operational envelope** expands: `.claude/orchestrator-debug/**` is reserved as orchestrator-owned substrate (analogous to `.claude/d1-bypasses.log` reserved by cliff-failure-mode-and-v1-defenses). `/integration-sweep` does not trim this directory. No INV-002 text change; the reservation is absorbed at the next `/refresh-architecture`.

## Alternatives Considered

### Observability shape alternatives (A1–A4)

| Approach | Core idea | Why rejected |
|----------|-----------|--------------|
| **A1 — Exit-only JSON in current-slice** | Single JSON file, `atexit` writer only, wiped on close | SIGKILL leaves no trail; post-close consumers see nothing; requires wipe exemption or disappears |
| **A2 — Incremental JSON + index, no MD** | Everything A3 has minus the MD sidecar | Humans must parse JSON directly; `/catchup phase N` less readable |
| **A3 — Chosen** | Incremental JSON + MD derived + index + heartbeat | Human + machine readable; decoupled threads; drift-free via pure-function projection |
| **A4 — JSON-only, no separate index** | Cluster dispatches and failures as arrays inside result.json | Fleet-coordinator would need fanout per-slice reads instead of stream tail; deferred for when read pattern is known |

### Schema alternatives (B1–B4)

| Approach | Core idea | Why rejected |
|----------|-----------|--------------|
| **B1 — Minimal now** | Only fields with current consumers; no worktree_path, orchestrator_pid | Internally-motivated fields (phase_timings, retries_by_phase) are driven by real observability needs and should not be deferred |
| **B2 — Speculative forward-compat** | Commit full forward-compat schema firmly at v1.0 | worktree_path and orchestrator_pid shapes are speculative; committing firmly risks F1 migration cost |
| **B3 — No schema commit** | Mark internal-only, negotiate on first consumer | Pushes all observability-schema work to fleet-coordinator slice; too late to catch design issues |
| **B4 — Chosen: B2/B3 hybrid** | Internal-motivation fields firmly committed; forward-compat fields additive-safe | Captures the real distinction: we know our own needs, we guess consumer needs |

### Error policy alternatives (E1–E4)

| Approach | Core idea | Why rejected |
|----------|-----------|--------------|
| **E2 — No retry, degrade on first** | Simpler code; more DEGRADED events | False positives on ms-scale filesystem contention |
| **E3 — N configurable retries** | `CAIRN_OBS_RETRIES=N` | Over-engineered for local FS; retry count is not a downstream-tunable knob |
| **E4 — Best-effort** | Log and continue; no DEGRADED | Masks real observability failures at scale; violates "observability is the system's eyes" premise |
| **E1 — Chosen: three-level** | retry → degrade → fail | Matches observed transient pattern; surfaces persistent failures; strict on self-observation |

### Retention alternatives (F1–F4)

| Approach | Core idea | Why rejected |
|----------|-----------|--------------|
| **F1 — Commit rotation now** | `CAIRN_ORCHESTRATOR_DEBUG_RETAIN=50` default | Pre-dogfood; no consumer pattern to optimize for |
| **F3 — Unbounded + operator cleanup** | Document `find ... -mtime -delete` pattern | Relies on operator discipline; silent until fs fills |
| **F4 — Rotate index.jsonl only** | Asymmetric; per-slice files stay | Partially handles F4 risk; still leaves long-tail file count growth |
| **F2 — Chosen: defer with tripwire** | Explicit follow-up condition | Actionable deferral; most honest given pre-dogfood state |

## Risk Register

- **F1 — Schema forward-compat bet missed.** Addressed by D4's B2/B3 hybrid: additive-safe fields accommodate unknown shape changes without version bump.
- **F3 — DEGRADED signal collapse.** Addressed by D7's append-preserving contract.
- **F4 — Debug-dir growth.** Addressed by D8's tripwire; expected to fire during the dogfood window if pace is high.
- **F5 — Idempotency corner cases.** Covered by slice-close-contract D3 (file-already-absent tolerance). This ADR is unaffected.

### Assumption audit

This ADR is provisional; formal Phase 5 verification is not required. Primary believed assumptions:

- Fleet-coordinator consumer pattern matches our schema shape in ≥80% of fields — **Believed**; B3 additive-safe mitigates wrongness cheaply.
- Heartbeat thread under laptop-sleep conditions stays correct-enough — **Believed**; advisory-only use (slice-close-contract D4) makes it non-blocking.
- F4 tripwire (100 files / 1 MB) fires before operator pain — **Believed**; dogfood pace unknowable pre-v1.

## Consequences for in-progress work

- **Compression Slice 3 (observability + close_slice hardening)** implements this ADR alongside slice-close-contract.
- **Fleet-coordinator epic (future)** reads `<slug>-result.json`; expected to either ratify schema v1.0 or propose v2.0 via supersession.
