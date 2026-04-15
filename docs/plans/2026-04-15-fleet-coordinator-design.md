# Fleet Coordinator — Design Document

**Date:** 2026-04-15
**Status:** Design approved; this is an **epic** spanning multiple features and ADRs. Implementation plan follows separately.
**Brainstorming charter:** `~/.claude/plans/drifting-hopping-dragonfly.md`
**Related ADRs:** ADR-007 (parallelism v1, provisional), ADR-006 (feature-slice model), ADR-004 D4 (partially superseded)

---

## 1. Context

Cairn's slice methodology gives strong per-slice discipline (envelope, phase gates, scope guard, reality-check). Until now, multi-slice and multi-phase work has been driven manually — human orchestrates worktrees, drives each phase through conversation, manages merges by hand. ADR-007 made concurrent slice execution v1-legal but deferred worktree lifecycle and orchestration as implementation concerns, pending a dogfood event.

This design introduces a **coordinator + agent-team harness** that automates the slice system's ceremony. Two axes of automation are unlocked by the same primitive (coordinator + worktree + fresh Claude session per phase):

- **Axis A — Intra-slice phase automation.** Coordinator drives a slice through phases autonomously, pausing only at designed human gates. Hits every slice. Primary value driver.
- **Axis B — Cross-slice parallelism.** When the feature graph has ≥2 slices with satisfied `after` deps, the same coordinator dispatches them concurrently. Emergent from Axis A, not a separate system.

**Reframed value prop:** this harness is slice-ceremony automation with parallelism as a special case. Not a parallelism tool with ceremony as a side-effect.

## 2. Epic scope

This is large. In Scrum terms, it is an **epic**, not a feature. It spans:

1. Spec-level changes to slice identifiers and state taxonomy (pre-existing work in progress; not harness-specific but blocks harness).
2. Multiple ADRs (listed below) establishing the policy surface the harness encodes.
3. The harness code itself (one feature, several slices).
4. Dogfood validation (one feature, its own slices).
5. Graduation decisions and Rust port gate.

Features and ordering are specified in §8. The key ordering principle: **ADRs (policy) precede harness code (mechanism).** The harness is 800 lines of Python that mechanically applies decisions made in ADRs; writing the harness before the ADRs encodes those decisions in code, which is the wrong artifact.

## 3. Architecture

```
┌──────────────────────────────────────────────────────────┐
│ tmux session: fleet-<feature>                            │
│                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │ pane 0      │   │ pane 1      │   │ pane 2      │    │
│  │ coordinator │   │ worker      │   │ worker      │    │
│  │ daemon      │   │ slice-A     │   │ slice-B     │    │
│  │ (Python)    │   │ claude -p   │   │ claude -p   │    │
│  │             │   │ worktree-A  │   │ worktree-B  │    │
│  └─────────────┘   └─────────────┘   └─────────────┘    │
│         │                                                │
│         ▼                                                │
│  .orchestration/             (state cache + audit)       │
│  ├─ events.fifo              (event channel)             │
│  ├─ audit.log                (autonomous transitions)    │
│  ├─ dispatch.log                                         │
│  ├─ pending-gates/                                       │
│  ├─ worker-status/                                       │
│  └─ features-registry/       (cross-feature visibility)  │
└──────────────────────────────────────────────────────────┘

            Human ────▶ `fleet` CLI ────▶ events.fifo
```

### 3.1 Roles

- **Coordinator daemon:** Python 3 process, pane 0 of the fleet's tmux session. Single consumer loop reading from `events.fifo`. Dispatches workers, maintains `.orchestration/` cache, writes audit log. **Pure mechanism — no Claude reasoning.**
- **Worker:** `claude -p "<state-bootstrap-prompt>"` in a tmux pane, cwd = worktree. Runs the slice-methodology protocol for its assigned state. Signals readiness for transition by updating slice.yaml state field. Knows nothing about the coordinator.
- **`fleet` CLI:** Shell wrapper (thin — execs a Python entry point) invoked by the human. Writes a one-line command to `events.fifo` and exits. Never talks to the daemon directly.

### 3.2 Event model (producer-consumer, no polling)

Three producers, one consumer (the daemon), one channel (`events.fifo`):

1. **`fleet` CLI (human → daemon).** Every subcommand writes one line to the FIFO.
2. **File watcher (worker state → daemon).** A `watchdog`-driven subprocess watches every worktree's `slice.yaml`. On change, emits `state-change <slice_id>` to the FIFO.
3. **tmux `pane-died` hook (worker exit → daemon).** On worker process exit, tmux fires the hook; shell snippet writes `worker-exit <pane_id>` to the FIFO.

Daemon is a single `asyncio` consumer loop matching on event type. No polling anywhere in the hot path.

### 3.3 State model

- **Branch state is source of truth.** Each worktree's `slice.yaml` carries current state; the feature file carries the dep graph. Everything in `.orchestration/` is derived cache — rebuildable from scratch on daemon restart.
- **Slice identifier is opaque to the harness.** The slice-methodology spec revision may change slice IDs (removing numbering, adopting a naming convention). The harness treats `slice_id` as an opaque string throughout.
- **State is not coupled to "phase."** The bootstrap unit is a generic *work-state*, whatever the revised spec dictates. `spawn_worker(agent_family, slice_id, state, worktree)` — never `..., phase, ...`.

### 3.4 Transitions engine

- Config-driven via `transitions.yaml`. Each transition has: from-state, to-state, gate type (autonomous | human), preconditions (list of precondition-check-script names).
- Preconditions live in `cairn_fleet/preconditions/` — small Python modules. New precondition types added as new autonomous transitions earn their classification.
- transitions.yaml is ADR-owned, not harness-owned. The daemon executes; the ADR decides.

### 3.5 Human interaction

Fire-and-check register. Human interacts transactionally via `fleet` CLI:

- `fleet start <feature>` — launch daemon for a feature branch, set up worktrees.
- `fleet status` / `fleet status --all` — per-feature / all-features view.
- `fleet approve <slice>` / `fleet reject <slice> <reason>` — resolve pending human gates.
- `fleet pause` / `fleet resume` — escape valve for dynamic graph edits (new slices, re-decomposition, rerun decisions).
- `fleet attach <slice>` — tmux attach to that worker's pane.
- `fleet rollback <slice>` — revert worktree to pre-transition state (requires audit-log SHA).
- `fleet audit <slice>` — read the autonomous-transition audit log.
- `fleet features` — cross-feature registry scan.
- `fleet stop` — graceful shutdown.

No persistent human-facing agent. Interactions are one-shot, queue-mediated.

### 3.6 Agent-family seam

Single function: `spawn_worker(agent_family, slice_id, state, worktree) → worker_pid`.

- v1 implementation: Claude only. `claude -p` with a state-specific bootstrap prompt from `prompts/claude/<state>.md`.
- Contract is real — future terminal-native agents (Gemini CLI, Codex CLI, Aider) slot in by implementing `prompts/<agent>/<state>.md` + extending the spawn function.
- **Windsurf is out of scope indefinitely.** Terminal research confirmed no clean headless mode. If Windsurf ever ships a real CLI, revisit.

### 3.7 Automation-risk safeguards

Autonomous transitions can silently erode slice discipline if transitions.yaml misclassifies. Harness provides three mechanisms:

1. **Audit log.** Every autonomous transition writes to `.orchestration/audit.log` with slice_id, from-state, to-state, preconditions (pass/fail), invariants verified, diff summary. `fleet audit <slice>` reads it.
2. **Rollback.** Daemon snapshots branch HEAD + slice.yaml before each autonomous transition. `fleet rollback <slice>` reverts to pre-transition state — no git surgery required.
3. **Conservative defaults.** transitions.yaml ships maximally gated. Autonomous classification for a transition type requires an ADR-level argument plus observation data. Progressive relaxation ratchet is a protocol (ADR-owned), not harness code.

## 4. Implementation language

**Python 3 + asyncio + watchdog + PyYAML + stdlib.**

- ~900 lines of Python + ~400 lines of pytest tests.
- Stays within cairn's "no build step" rule (scripts are interpreted).
- Cairn already runs Python (pytest under `tests/unit/`); no new language ecosystem.
- Testability is the deciding factor: pytest fixtures + async test support + mocks let us test the event loop, transitions, and graph reconciliation. Bash cannot deliver this.

**Rust port is an explicit v1 gate**, not a "later" item. Gate criteria (themselves an ADR):
- Intra-slice phase automation ADR accepted and stable.
- Slice identifier / state taxonomy spec revision landed.
- ADR-007 graduated from `provisional` to `accepted`.
- Harness has accumulated enough dogfood observations that design shape is not expected to change.

At that point, the Python test suite is the spec for the Rust port.

## 5. Git history strategy

Local-only. No remote required for any of this.

| Merge | Strategy | Who |
|---|---|---|
| Slice → feature (continuous, as each slice lands) | **Preserve commits** (`git merge --no-ff`). Phase-internal commits visible on feature branch. | Daemon triggers after human confirms Phase 4 gate. |
| Feature → dev (at feature completion) | **Human call, default squash** (`git merge --squash` then commit). Override to merge-commit for architecturally-significant features. | Human. Daemon never touches this. |
| Dev → main | Unchanged, pre-existing cairn policy. | Human. |

Squash-merge is fully local-operable: `git merge --squash <branch>` stages the diff, human commits with a chosen message. GitHub's squash button is just UI over this.

## 6. Failure modes

| Failure | Handling |
|---|---|
| Worker crashes | tmux `pane-died` hook → daemon sees worker-exit → marks slice `needs-human-review`, preserves worktree. No auto-retry. |
| Daemon crashes | Supervisor respawns. On restart, rebuild `.orchestration/` from branch state. No data lost. |
| FIFO backs up | Consumer loop just-dispatches; heavy work in awaitable handlers. Reads don't block on work. |
| tmux session killed externally | Daemon detects missing session → logs, writes notice, exits. Human relaunches. |
| Concurrent feature-file edits | `yq -i` atomic (write-to-tmp + rename). Daemon's watcher debounces (500ms quiet). Pause primitive covers non-atomic cases. |
| Worker can't reach Anthropic | Worker exits non-zero → treated as crash. No retry; human decides. |
| Two concurrent slices touch same file | Worker-local. Phase 4 integration catches it at merge time. ADR-007 Risk Register. |

## 7. Out of scope for v0

- Auto-merge at Phase 4 (human runs `/integration-sweep` + merges).
- Autonomous retry of failed workers.
- Cross-family workers beyond Claude (seam exists; implementations don't).
- Global concurrent-worker cap across features (convention-only coordination).
- GUI / TUI dashboard (`fleet status` is shell output).
- Windsurf support.
- Persistent coordinator session with Claude reasoning.
- Auto-handling of state regressions discovered post-merge (always human).

## 8. Epic decomposition — features and ordering

This is the epic-level breakdown. Each feature gets its own feature file; each has multiple slices. Ordering below is a dependency order; later features depend on earlier features being complete.

> **Naming note:** slice and feature identifiers below use placeholder names pending the spec revision that removes numbering / adopts a naming convention. Actual identifiers will be chosen at feature-file creation time.

### Feature 1 — Identifier, naming, and state taxonomy overhaul *(prerequisite)*

**Purpose:** Fix the naming/identifier scheme across the methodology before layering automation on top. The current scheme — numeric ADR IDs (`ADR-007`), numeric decision points within ADRs (`D1`, `D2`), numeric slice IDs — makes tracking, cross-referencing, and mental model-building harder as the repo grows. Naming now is cheaper than renaming later. This is a **full identifier + naming + sanity feature**, not just a slice-ID change.

**Scope:**

*Identifier conventions (all scoped in one ADR):*
- **Slice IDs** — remove numbering, adopt a semantic naming convention (e.g., `slug-case` summary of the slice intent).
- **ADR IDs** — move from sequential numbers (`ADR-007`) to semantic slugs (e.g., `parallelism-v1`, `feature-slice-model`). Filename follows. Frontmatter keeps a stable ID field.
- **Decision-point IDs within ADRs** — replace `D0/D1/D2/…` with semantic labels (e.g., instead of `ADR-007 D2`, use `parallelism-v1/no-global-pointer`). Cross-references in other ADRs and docs update accordingly.
- **Feature IDs** — adopt a consistent semantic convention matching slice and ADR conventions.
- **Commit message / branch naming** — audit for numbered identifiers that should become semantic.

*State taxonomy (for the harness):*
- Enumerate every state a slice can be in.
- Enumerate every legal transition.
- Classify each transition as autonomous-eligible or human-gated-only (the default classification; Feature 2 ADR may override conservatively).
- slice.yaml schema updates to carry explicit state field.
- ADR-006 amendment reflecting slice ID + state additions.

*Migration work:*
- Rename existing ADR files.
- Update all ADR cross-references.
- Update `/new-adr` and `/decision` protocols to emit semantic IDs, not numeric ones.
- Update any index / registry files.
- Sweep for hardcoded references in docs, CLAUDE.md, commands/, scripts/.

**Blocks:** every subsequent feature. The harness cannot be designed against a moving state model; the ADR cascade (Features 2-5, 8) cannot write cross-references using an identifier scheme that's about to change.

**Slice breakdown (illustrative):**
- Slice: identifier convention decisions (ADR for the naming scheme itself).
- Slice: ADR file renames + cross-reference sweep.
- Slice: `/new-adr` + `/decision` protocol updates.
- Slice: state taxonomy ADR (the harness's state model).
- Slice: slice.yaml schema + migration.
- Slice: doc sweep (CLAUDE.md, operational-reference.md, handoff artifacts).

### Feature 2 — Intra-slice phase automation ADR *(primary ADR)*

**Purpose:** The load-bearing policy ADR. Defines what autonomous transitions look like, precondition taxonomy, human-gate rationale, progressive-relaxation ratchet protocol.

**Scope:**
- ADR text.
- transitions.yaml v0 (maximally conservative).
- Precondition script specifications (what each precondition checks).
- Progressive-relaxation protocol (how a transition earns autonomous classification).

**Blocks:** harness implementation. The harness mechanically applies this ADR's decisions; writing harness code before this ADR encodes decisions in the wrong artifact.

### Feature 3 — ADR-007 amendment (process coordinator + worktree lifecycle)

**Purpose:** Update ADR-007 to reflect:
- State vs. process coordinator distinction.
- Worktree lifecycle conventions (naming, creation, cleanup ownership).
- Pause/resume primitive as the dynamic-graph escape valve.
- Parallelism becomes "N-way application of the Feature 2 ADR" — downstream consequence.

### Feature 4 — Agent-family portability contract ADR

**Purpose:** Define the `spawn_worker(agent_family, ...)` contract. Scope: terminal-native agents only (Claude v1, Gemini/Codex/Aider as plausible second implementations). Windsurf explicitly out. Partially supersedes ADR-003 D4's vision commitment #1 for the terminal-native subset.

### Feature 5 — Git history strategy ADR

**Purpose:** Codify slice→feature (preserve), feature→dev (default squash, override to merge-commit) policy. Covers daemon's merge authority (triggers slice→feature after human gate; never touches feature→dev).

### Feature 6 — Fleet harness implementation

**Purpose:** The Python harness itself. This is the feature the user actually sees and runs.

**Scope:**
- `cairn_fleet/` Python package.
- `fleet` CLI.
- transitions.yaml execution engine.
- Event loop, watchers, tmux integration.
- Agent-family seam (Claude implementation).
- Audit log and rollback.
- Test suite.

**Recursive dogfood:** the late slices of this feature should be structured to be runnable through the partially-complete harness. Bootstrap pattern. Failure is tolerated on early dogfood; risky slices stay manual.

### Feature 7 — ADR-007 graduation + Axis A dogfood

**Purpose:** Run enough slices through the harness to either graduate ADR-007 from `provisional` to `accepted`, or surface hazards requiring ADR revision.

**Scope:**
- Axis A primary gate: single slice runs end-to-end through the daemon with only the three designed human gates (intent, skeptic, merge).
- Axis B opportunistic: any naturally-occurring ≥2-slice parallel execution observed.
- Regression-check: compare harness-driven slice outcomes against manual baseline.
- Disposition ADR: either ADR-007 firmness upgrade, or supersession with tighter rules.

### Feature 8 — Rust port gate ADR

**Purpose:** Codify the conditions under which the harness ports to Rust. Explicit, not "later." Writes the v1 commitment.

### Feature 9 — Rust port implementation *(post-gate)*

**Purpose:** Port the stabilized Python harness to Rust when the gate fires.

## 9. Critical path ordering

```
Feature 1 (spec revision) ────┐
                              ▼
                         Feature 2 (phase automation ADR)
                              ▼
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   Feature 3             Feature 4             Feature 5
   (ADR-007 amend)       (portability ADR)     (git strategy ADR)
        └─────────────────────┼─────────────────────┘
                              ▼
                         Feature 6 (harness impl)
                              ▼
                         Feature 7 (dogfood + graduation)
                              ▼
                         Feature 8 (Rust gate ADR)
                              ▼
                         Feature 9 (Rust port, when gate fires)
```

Features 3, 4, 5 can proceed in parallel once Feature 2 lands. Features 1 and 2 are strictly sequential and block everything downstream.

## 10. Verification (epic-level)

- **Feature 1–5 (ADRs):** standard `/new-adr` protocol; each ADR reviewed and committed.
- **Feature 6 (harness):** pytest suite green; E2E smoke test with stub worker passes; manual test with real `claude -p` against a trivial slice succeeds.
- **Feature 7 (dogfood):** single-slice automation observed without incident; human-touch count per slice matches design (intent, skeptic, merge — no others); audit log reviewable; rollback path exercised once deliberately.
- **Whole epic:** ADR-007 graduates or is superseded with data; slice ceremony measurably reduced in human touches per slice; Rust port gate written with concrete criteria.

## 11. Risks

- **Spec revision (Feature 1) stalls.** Everything downstream blocks. Mitigation: treat Feature 1 as a hard prerequisite; do not begin Feature 6 design-review until Feature 2 ADR is accepted.
- **transitions.yaml misclassifies a gate as autonomous, eroding discipline silently.** Mitigation: audit log + rollback + conservative defaults. The progressive-relaxation ratchet (Feature 2) is the long-term control.
- **Python harness becomes permanent despite Rust gate.** Mitigation: Feature 8 is an explicit ADR, not a roadmap item. Feature 9 is scoped as a follow-up epic with firm criteria.
- **Dogfood surfaces shape-level problems.** Mitigation: Python iteration cost is cheap; ADRs are amendable. This is the designed-for outcome of `firmness: provisional`.
- **Cross-feature merge conflicts between parallel features.** Mitigation: ADR-007 already flags this; integration sweeps at feature-end catch it.

## 12. Follow-on work (not in epic)

- Shipping as a cairn skill/command installable by consumers.
- TUI dashboard.
- Global concurrent-worker cap enforcement.
- Windsurf support if Cognition ships a headless mode.
- Additional agent-family implementations (Gemini CLI, Codex CLI, Aider).
