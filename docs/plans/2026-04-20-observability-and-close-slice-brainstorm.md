# Observability and close_slice Hardening — Brainstorm

---
date: 2026-04-20
design-doc: docs/plans/2026-04-20-observability-and-close-slice-design.md
status: brainstorm record (reasoning archive)
---

## Purpose of this document

This is the reasoning archive for the design decisions in the paired design doc. It preserves the questions asked, options considered, rejected paths, and feedback that shaped the design — context that is otherwise lost when the design doc compresses to "this is what we're building."

The design doc answers **what** we're building and **which rules** it must satisfy. This brainstorm doc answers **why those rules and not others**, and preserves the rejected alternatives so future-us can decode references like "DC-3" or "D1" back to the reasoning that produced them.

Future readers: if the design doc says "see brainstorm §N for rejected alternatives," this is that §N.

---

## Context — what prompted this brainstorm

Coming out of Slice 2 (`compression/slice-2-state-machine`, closed at commit `9b34f44`):

- Learnings L1 through L8 + C1–C2 captured in `.claude/learning.md`.
- Handoff flagged `close_slice` as "the weakest link in the pipeline across two consecutive slices" (C2).
- Ruff F841 leftover at `tests/unit/test_post_timeout_reconcile.py:101` (unrelated housekeeping).
- Original plan doc (`docs/plans/2026-04-20-compression-pipeline-hardening-plan.md §3.0`) specified Slice 3 as "multi-instance + observability" — E1 worktree lock, E2 PID-scoped role_guard, structured JSON exit, debug log index, parallel-worktree integration test.

User reopened the session with: "I want to do a fix from the learnings of the previous session as well as observability. I found the restart of orchestrator and the permission issues as a problem that will become bigger."

This shifted the slice away from the original §3.0 scope (multi-instance) and toward close_slice hardening + observability. The "will become bigger" framing — applied to the restart pain and permission pain — became the primary justification for forward-compat investment (**D3** below).

---

## Scope question — Approach A vs. B vs. C

Three candidate scopes were offered:

**A. Observability + close_slice fixes only.** Drop multi-instance entirely from this slice.

**B. Observability + close_slice fixes + cheap multi-instance bits** (E1 lock, E2 PID scope; skip the expensive parallel-worktree integration test).

**C. Original §3.0 scope + close_slice fixes bolted on.** Full multi-instance + observability + close_slice fixes.

**User chose A.** Rationale (from the conversation): close_slice was flagged as the weakest link; contamination risk (multi-instance amplifies it) means the wipe should land **before** running two orchestrators in parallel. Multi-instance was deferred to a later slice.

Rejected:
- **B** — mixes concerns; scope bloat; E1/E2 would invite arguments about how much integration testing they need.
- **C** — too large; increases blast radius if something breaks; multi-instance can wait.

---

## Pain-point selection — Minimal vs. Broader vs. Wide

Within Approach A, the specific pain points to fix were up for choice. Candidates from Learnings L1–L8 + C1–C2:

**Restart-adjacent:**
- **R1** — `close_slice` is not idempotent (crash between its three steps leaves partial state).
- **R2** — `close_slice` wipe gap (L8; already implied by scope A).
- **R3** — Redundant-commit race (C2): Phase-4 agent commits `handoff: phase 4 complete`, then `close_slice` commits `slice: complete`.
- **R4** — Resume-after-mid-slice-crash: no mechanism today to reconcile `orchestrator-result.json`, `slice.yaml`, and `git HEAD`.

**Permission-adjacent:**
- **P1** — Codify the Bash-heredoc write-escape (L3) into agent prompts.
- **P2** — Codify "always attempt the tool call; don't refuse preemptively based on prior-art docs" (L4) into agent prompt preambles.
- **P3** — Path C (orchestrator-owned writes) full design — queued per handoff, separate slice.
- **P4** — C1: agents committing `.claude/sweep.yaml` updates is ADR-scoped, not slice-scoped.

Three pick-tiers offered:

- **Minimal (recommended at the time):** R1 + R3 + P1 + P2, with R2 already in.
- **Broader:** Minimal + R4 (resume-reconcile test).
- **Wide:** Broader + P3 (Path C design-doc only).

**User chose Broader.** Locked in: R1, R2, R3, R4, P1, P2. P3 (Path C) stays deferred to its own slice. P4 (sweep.yaml ADR caveat) stays as a future `/decision` consideration — not in this slice.

Rejected:
- **Minimal** — would omit R4 (resume reconciliation), leaving a known gap.
- **Wide** — P3 adds significant design weight; better isolated.

---

## Observability shape — the O3 decision

Three shapes for the observability layer were offered:

**O1. Exit-only JSON** (original §3.0 verbatim). `orchestrator-result.json` written on exit via `atexit`; `orchestrator-debug/index.jsonl` appended per failure log.
- **Rejected because:** `atexit` doesn't fire on SIGKILL → no trail when the process hard-dies.

**O2. Incremental JSON + index.** JSON written on every phase transition plus final atexit. `index.jsonl` appended on all dispatch events.
- **Strong option.** Survives SIGKILL for the last-completed phase.

**O3. O2 + human-readable sidecar.** Incremental JSON + markdown sidecar (`orchestrator-result.md`) written alongside.
- **User chose O3.** Reasoning: keeps orchestrator state up to date for consumers (fleet-coordinator, `/catchup`) without requiring them to parse JSON. But user flagged the cost: "will load the agent with unnecessary information."

That concern triggered the ultrathink on tradeoffs below.

---

## The O3 tradeoff ultrathink — six forks

User asked for enumeration of the tradeoffs in picking O3. Six were laid out, and they collapsed into three macro decisions (D1, D2, D3):

### T1. Placement: `.claude/current-slice/` vs. `.claude/orchestrator-debug/`
- Current-slice: discoverable, co-located, but visible to any agent that lists the slice dir; must be wiped at close or exempted.
- Debug-dir: survives across slices (good for `/catchup phase N` historical reads and fleet-coordinator), outside every phase's envelope gate, but feels category-wrong (historically "debug" = failure logs only).

### T2. Wipe scope vs. cross-session utility
- If result.md lives in current-slice and gets wiped: useless for next-session `/catchup`.
- If exempted from wipe: the wipe-exemption list grows; every future feature lobbies for exemption (protocol leak).

### T3. Single source of truth vs. two formats
- Dual independent writes: JSON writer + MD writer; drift risk.
- JSON primary, MD derived: single writer plus a pure-function generator; drift impossible by construction.

### T4. Tier discipline
- If `/catchup` Tier-1 reads result.md: convenient, but re-invents `handoff.md` with different framing (violates context-discipline-philosophy memory).
- If result.md stays Tier-2: humans need one extra step; fleet-coordinator needs a stable path anyway.

### T5. Schema early-commitment vs. YAGNI
- Invest now: add `worktree_path`, `orchestrator_pid`, `phase_timings[]`, `retries_by_phase{}` for future fleet-coordinator consumption.
- YAGNI: keep minimal; pay a one-migration cost later.

### T6. Write atomicity vs. partial-write race
- Atomic pattern (tempfile + `os.rename`): protects readers from torn files.
- Non-atomic: simpler but racy; torn-read bugs surface under multi-instance concurrency.

### T7 (bonus). Scan-surface containment
- LLM agents grepping `.claude/` recursively find every file regardless of naming. Real containment = place outside slice dir; name-hiding is a fragile defense.

### How these collapsed into macro decisions

- **T1 + T2 + T7 → D1** (placement in debug-dir vs. current-slice).
- **T3 → D2** (JSON primary vs. dual independent).
- **T4 + T5 + T6 → D3** (forward-compat posture).

---

## The three macro decisions (locked in)

### D1 — Placement: `.claude/orchestrator-debug/`
- **Chosen:** debug-dir (cross-slice persistent, outside scan path).
- **Why:** user's stated concern was agent scan-surface pollution; debug-dir solves that directly. Cross-slice survival is a free bonus for `/catchup` history and fleet-coordinator.
- **Rejected:** current-slice co-location — forces either wipe-it-is-useless-post-close, or grow-the-wipe-exemption-list (protocol leak).

### D2 — Source model: JSON primary, MD derived
- **Chosen:** JSON is canonical; MD is a pure-function projection.
- **Why:** eliminates drift by construction. Generator is stdlib string formatting — no templating engine. Test surface smaller (one writer, one generator, one cross-check test).
- **Rejected:** dual independent writes — demands ongoing discipline we won't maintain; every new field needs touching two writers; one will inevitably lag.

### D3 — Forward-compat posture: invest now
- **Chosen:** `worktree_path`, `orchestrator_pid`, `phase_timings[]`, `retries_by_phase{}` in schema from day one; atomic-write helper adopted universally.
- **Why:** user's "will become bigger" framing implicates fleet-coordinator. Retrofitting after consumers exist forces a migration and bikeshedding. Atomic-write specifically: once multi-instance reads concurrently, torn files become bugs, and retrofitting across many writers is expensive.
- **Rejected:** YAGNI — defers a cheap one-migration cost we'll pay with interest.

---

## Liveness signal — heartbeat decision (Option B)

User pushed back on the observability design: "we need ways to see if its still running."

Two options offered:

**Option A (embedded heartbeat):** Add `last_heartbeat_at` field to `orchestrator-result.json`; background thread updates every N seconds with atomic rewrite.
- **Rejected because:** heartbeat cadence (seconds) and phase-transition cadence (minutes) share a write path → lock contention; frequent full-file rewrites for a timestamp.

**Option B (separate file) — chosen:** two files — `orchestrator-result.json` for state (written on phase transitions) + `.claude/current-slice/.heartbeat` for a single ISO timestamp (touched every 10 seconds by a daemon thread).
- **Why:** different cadences → different files. Heartbeat thread crashing doesn't corrupt result.json. Cheap reads. Supports **DC-2** (heartbeat/state decoupled).

---

## Context-preservation concern — the "what does I2 mean" problem

User flagged: "We do lose a lot of context and reasoning this way. How do we handle to make sure we properly get the questions, why things matter, what the decision is? Some words like 'this fixes the I2 issue' does not make sense if we do not know."

Three mechanisms, layered:

1. **Glossary-first design doc** — first section defines every short code. Done; see design doc §Glossary.
2. **Decision log section inside design doc** — each fork shows options / chosen / why / rejected. Done.
3. **Companion brainstorm doc** — this document. Full reasoning preserved.

Each decision carries back-links: design doc references brainstorm doc via frontmatter; design doc entries name the learning (L3, L4, L8) or failure-mode code (R1, R3) that motivated them.

---

## Async-communication feedback (now a memory)

User said: "Imagine this is async communication and use the best practices for that. In the sense of the app 'twist' and team async, not coding async."

This was feedback about how to structure live user-facing messages — assume the user reads hours later with no memory of the thread, always expand short codes inline, use self-contained TL;DR-first structure.

Saved as `async_communication_style.md` memory. Glossaries remain for doc readers; live user messages need full context every time.

---

## Invariants namespace collision — DC-1..DC-7 rename

I drafted what I called "Invariants I-1 through I-7" for the slice. User asked: "do we not already have invariants set up in the project?"

Yes — cairn has `INV-001` through `INV-007` in `docs/ARCHITECTURE.md`, each backed by an ADR, each with a machine-checked `invariant-check` block validated by `scripts/validate_architecture.py`. That's the project-wide canonical invariant registry.

Three options were offered:

1. **Keep all seven as slice-local, rename them to "Design contracts."**
2. **Elevate the architecturally significant ones (I-3, I-4, I-7) to real INVs via a new ADR.**
3. **Rename now, defer INV elevation to a follow-up.**

**User chose option 3.** All seven renamed to **DC-1** through **DC-7** (Design Contracts). Three (DC-3, DC-4, DC-7) flagged as candidates for eventual INV elevation in a follow-up `/decision` run. The design doc's Future Work section names them explicitly.

Rejected:
- **Option 1** — loses machine-checkable enforcement for the architecturally significant ones.
- **Option 2** — adds a new ADR + three new INV entries to this slice's scope; `/decision` is the right venue for those commitments, not a brainstorming doc.

---

## Decision-tagging convention + `/decision` before `/start-slice`

After the DC rename, user said: "This slice might need a decision at this rate. Let us make sure we properly do this."

Interpretation: the architectural weight is real; the formal `/decision` protocol should lock commitments before `/start-slice` executes.

Agreed flow:

1. Brainstorm → design doc + this brainstorm doc
2. **`/decision`** — reads both docs, formalizes architectural commitments, produces an ADR codifying at minimum: D1, D2, D3, DC-3, DC-4, DC-7, state-schema v1.0 field set, heartbeat cadence defaults, DC-6 matrix row set, DC-4 enforcement mechanism, observability retry strategy, MD cadence, status=DEGRADED enum modeling.
3. `writing-plans` skill → detailed implementation plan
4. `/start-slice` → executes plan through the compression pipeline

Tag convention: `[DECISION]` as a plain-text ASCII prefix. Locked items are tagged so they're greppable in the design doc. Future `/decision` run is scoped to resolve every tagged item.

---

## Section-by-section design review — what was refined

The design doc's five sections were presented in chat with user approval gates. Significant refinements:

**Section 1 (Architecture, Invariants, Decision Log):**
- Initially drafted with `I-1..I-7` naming. Renamed to `DC-1..DC-7` after discovering the project's `INV-NNN` namespace.
- Added explicit "candidates for INV elevation" note for DC-3, DC-4, DC-7.
- Glossary formalized; every short code defined.

**Section 2 (Components):**
- State-dict schema fields locked: `schema_version`, `slice_id`, `worktree_path`, `orchestrator_pid`, etc.
- `_persist_state` signature chosen as caller-supplied state (more testable) over module-global side-effect (simpler).
- Heartbeat cadence decision deferred to `/decision` (user: "decide skill will read the entire thing").

**Section 3 (Data Flow):**
- MD write cadence locked to **close-only** (user choice). JSON writes on every transition; MD only at terminal.
- Signal handler does not duplicate atexit writes — atexit is the single terminal writer.
- Resume reconciliation matrix drafted with one row added post-review: `IN_PROGRESS / complete / commit present = JSON lagged after close, fix up in place, exit 0`. This handles the legitimate partial-close-persist-failure scenario.

**Section 4 (Error Handling) — revised mid-section:**
Initial draft positioned observability writes as "best-effort: log and continue." User pushed back: "at scale observability is the thing that makes the system run." Revised to three-level model:
- **Level 1 (retry)** — bounded retry inside `_atomic_write`; transient hiccups handled invisibly.
- **Level 2 (degrade)** — retry exhausted → `status=DEGRADED`, `degradation_reason` populated, slice continues. Consumers see degraded state and can respond.
- **Level 3 (strict)** — degraded state write itself fails → exit FAILED. Cannot observe self → cannot continue.

Separate `degraded: bool` flag rejected; `status=DEGRADED` as enum value chosen instead. `degradation_reason` persists through terminal transition.

**Section 4 retry strategy revision:**
Initial proposal was exponential backoff (1s, 2s, 4s). User asked for simpler. Three options offered:
- **Option A** — no retries, degrade on first failure.
- **Option B** — one retry, no delay (two attempts total). **Chosen.**
- **Option C** — N fixed-delay retries (configurable via env var).

Option B rationale: local filesystem writes <1KB that transiently fail succeed >99% on second attempt; two attempts hit the sweet spot; simple code (try/except wrapping a try/except).

**Section 5 (Testing):**
- Per-concern file organization (matches cairn convention), not per-DC.
- 35 unit tests + 3 integration tests across 8 test files.
- Grep-based tests for agent prompts accepted as practical despite being brittle to rewording.
- End-to-end observability smoke test added as a new Phase 4 gate.

---

## What's explicitly **not** in scope (and why)

- **Multi-instance hardening** (E1 worktree lock, E2 PID-scoped role_guard, parallel-worktree integration test) — original §3.0 scope; deferred because close_slice correctness should land first (contamination risk under multi-instance makes wipe-gap worse).
- **Path C** (orchestrator-owned writes for `.claude/**` sensitive-file gate) — substantial design scope; its own slice.
- **New ADR for DC-3 / DC-4 / DC-7 elevation** — queued for a follow-up `/decision` run.
- **Ruff F841** at `tests/unit/test_post_timeout_reconcile.py:101` — housekeeping, unrelated to scope.
- **Sweep.yaml-agent-commit ADR caveat** (C1 learning) — ADR-level, not slice-level.
- **Superseding the original plan doc's §3.0** — that doc stays as-is; this new design doc is the authoritative spec for what gets built.

---

## Appendix — rejected options catalog (for searchable archive)

**Observability shape:** O1 (exit-only JSON) rejected — SIGKILL leaves no trail.
**Observability shape:** O2 (incremental JSON + index, no MD) rejected — user wanted human-readable progress. Could be revisited if MD cost becomes problematic.

**Placement:** current-slice + wipe rejected — useless for post-close consumers.
**Placement:** current-slice + exempt-from-wipe rejected — protocol leak; every future artifact lobbies.

**Source model:** dual independent MD + JSON writers rejected — drift.

**Forward-compat:** YAGNI / minimal schema rejected — migration cost at fleet-coordinator slice.

**Liveness mechanism:** embedded `last_heartbeat_at` field in result.json rejected — lock contention between cadences.

**Invariants:** project-wide INV elevation (Option 2) rejected for this slice — scope creep; `/decision` is the right venue.

**Error handling:** best-effort observability (silent log-and-continue) rejected — "at scale observability runs the system."

**Retry strategy:** exponential backoff rejected — over-engineered for local FS writes.
**Retry strategy:** no retries at all rejected — false degradation on milliseconds-scale contention.
**Retry strategy:** N fixed-delay retries with env-var tuning rejected for now — observability retry count isn't a downstream-tunable knob.

**DC-4 enforcement:** orchestrator-side reconciliation of redundant commits rejected — more code, less discipline; prompt-change is simpler.

**Status representation:** `degraded: bool` flag rejected — redundant with status enum; `status=DEGRADED` + `degradation_reason` is cleaner.

**Signal handler:** duplicate state write rejected — atexit is single terminal writer; avoid double-write.

---

## What future-us should remember about this brainstorm

- The decision driver for Approach B (two Phase-3 clusters in one slice) was **"fleet dogfood rehearsal"** — two parallel cluster agents are the closest current approximation to the eventual two-orchestrators-in-parallel-worktrees experience. Not my reason; user's.
- The decision driver for D3 (forward-compat now) was user's framing that restart + permission pain **"will become bigger."** That's fleet-coordinator shape; paying schema + atomic-write cost now buys a no-migration future slice.
- DC-4 (Phase-4 does not self-commit) removes the R3 race by eliminating the race, not by coordinating around it. Simpler invariant.
- The revised Section 4 severity line exists because observability at fleet scale is the system's eyes; silent failure there would mislead the coordinator. `status=DEGRADED` is honest about degradation rather than hiding it.
- `/decision` runs before `/start-slice` for this slice. That's a protocol choice captured here so future slices don't accidentally ship without it when the scope similarly spans architectural + implementation surface.
