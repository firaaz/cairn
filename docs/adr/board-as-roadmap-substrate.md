---
id: board-as-roadmap-substrate
name: "Board as roadmap substrate — four-layer model + declarative reconciliation"
status: accepted
carrier: rationale-only
firmness: provisional
supersedes: []
supersedes-sections: []
superseded-by: null
topic: process
adrs-referenced: [bootstrap-exception, context-discipline-protocol, feature-slice-model, context-tiers-integration, phase-lock-and-role-declaration, identifier-scheme, slice-close-contract, cliff-failure-mode-and-v1-defenses]
invariants-touched: []
date: 2026-04-28
---

# board-as-roadmap-substrate: Board as roadmap substrate — four-layer model + declarative reconciliation

## Status
Accepted (provisional)

## Date
2026-04-28

## Context

The cairn GitHub Project board (`https://github.com/users/firaaz/projects/4`, name `cairn`) was created on 2026-04-27 as `/dev-mode`'s GH Projects backing store. During seeding (5 housekeeping items + 4 complex-rag-mcp consumer findings) it became clear the board overlaps three existing cairn primitives — `.claude/features/<id>.yaml`, `.claude/current-slice/slice.yaml`, and `docs/lessons.md` — without an explicit contract for how they layer.

`docs/plans/2026-04-27-board-roadmap-integration.md` captured an exploratory four-layer design and named five ratification questions for `/decision`. This ADR resolves them, and surfaces three additional gaps the plan-doc papered over.

The decision matters because the board's "anyone can drop an idea" property is what `feature-slice-model` (`feature-slice-model/d0-features-and-slices`) structurally cannot have: feature.yaml writes are pipeline-routed per `bootstrap-exception/inv-001`. Without an explicit roadmap substrate, any cairn-side capture of un-committed ideas would either accumulate as L-001-style pipeline bypasses or get lost. The board solves the capture problem; the question is how the capture surface composes with the existing substrate without duplicating state.

**The five plan-doc ratification questions:**

1. The four-layer model (board / features.yaml / slice / lessons) as the canonical layering.
2. Draft → issue conversion timing.
3. Eager vs lazy parent-issue creation for features.
4. `/start-slice` and `/close-slice` adding board-side flips as non-load-bearing additions.
5. `/groom` / `/promote` / `/weekly-status` as `.local/` carve-outs.

**Three gaps surfaced during user-journey trace:**

- **B1** — `/promote`'s features.yaml write authority. Plan-doc proposed `/promote` writes `features/<id>.yaml` directly, which is the L-001 anti-pattern unless explicitly authorized.
- **B2** — Board-flip trigger points. Plan-doc lumped PR-open and merge under `/close-slice` but `slice-close-contract/inv-008-a` commits `slice: complete` BEFORE PR is opened.
- **B3** — Failure-path issue handling. Plan-doc didn't specify what happens to the GH issue when a slice fails.

**Constraint envelope** (Phase 0 harvest):

| # | Source | Binding rule | Implication |
|---|---|---|---|
| C1 | INV-001 (`bootstrap-exception`) | All cairn dev flows through `/decision` or `/start-slice` | PM-session writes that touch cairn artifacts (features.yaml, lessons.md) are pipeline bypasses unless authorized as a named non-slice commit class or routed through `/start-slice` |
| C5 | INV-006 (`feature-slice-model/d4-status-derived`) | Slice status derived from observable state, not stored | Mirroring cairn-state to a stored Status field creates a duplicate-state hazard |
| C7 | INV-008 (`slice-close-contract/d2-sole-commit-source`) | `close_slice` is sole producer of `slice: complete` commit | Any `/close-slice` board flip must be a fire-and-forget side effect, not a load-bearing step |
| C8 | L-001 | "Just write it down" without a slice is forbidden | `/promote` writing features.yaml directly is the L-001 trap |
| C9 | `cliff-failure-mode-and-v1-defenses/d4-time-box` | Pre-v1 slices declare D0/D1/D2/D3 implementation OR mark non-v1-scope | This ADR is non-v1-scope (operational improvement, not defense) |
| C10 | `.local/` carve-out semantics | `.local/` = cairn-the-project, doesn't ship to consumers | PM commands start in `.local/` |

## Decision

Cairn commits to seven decisions, each addressing a specific question or gap. Decisions D1–D5 are the plan-doc's five ratification questions; D6–D7 close the journey-trace gaps.

### D1 — Four-layer model is canonical

Cairn's planning substrate is four stacked layers, each with its own substrate, lifetime, and consumers:

| Layer | Substrate | Cardinality | Lifetime | Source of truth |
|---|---|---|---|---|
| **Roadmap / catchment** | GH Project board (name `cairn`) | Many small items | Hours to weeks | The board itself |
| **Slice plan** | `.claude/features/<id>.yaml` | Coarser commitments | Days to months | The yaml file (cairn repo) |
| **Execution** | `.claude/current-slice/slice.yaml` + 4-phase pipeline | One in flight at a time | Hours to days | slice.yaml + git branch state |
| **Memory** | `docs/lessons.md` (L-NNN), `.claude/handoff.md`, operator memory | Outcomes, learnings | Permanent (lessons) / churning (handoff) | Their respective files |

Each layer has non-overlapping authority. The board is the **front door** — capture without ceremony, including from consumer projects. Promotion to features.yaml or slice is gated; capture is not.

The board is **never** a mirror of cairn-side state. It is the cairn-side committed answer to "what could be worked on" — not "what is being worked on" (which derives from branch state per `feature-slice-model/d4-status-derived`). This separation is load-bearing for D4.

### D2 — Draft → issue conversion at `/start-slice`

When `/start-slice` opens a slice whose intent matches a board item (matched by explicit `--board-item <id>` flag or, secondarily, by title match):

1. Convert the board draft to a GitHub issue via `gh project item-edit` + `gh issue create`.
2. Capture the resulting `#N` into `slice.yaml` under a new field `issue-number:`.
3. Append a flip event to the local board-pending log (D4).

The conversion happens at `/start-slice` because every slice produces a commit chain (Phase 1's intent.md, Phase 2's red tests, Phase 3's GREEN impl, Phase 4's sweep) that needs a stable `#N` to reference. Promoting later means early commits cannot `closes #N` cleanly.

**Re-entry path for board-down case (F3 mitigation).** If draft → issue conversion fails (board unreachable, MCP disconnected, `gh` errors), `/start-slice` continues without `issue-number:` set, and writes a one-line warning to stderr. A separate command `/start-slice --link-issue <N>` (or manual `gh issue edit` followed by editing slice.yaml) retroactively populates `issue-number:`. This addresses the F3 pre-mortem: per-slice commits made before the link is established lack `closes #N`, but the slice itself proceeds and the link is recoverable post-hoc.

`slice.yaml` schema gains:

```yaml
issue-number: 42      # optional; populated when board-driven
board-item-id: PVTI_… # optional; original draft id if known
```

Both fields are optional; slices opened without board context omit them.

### D3 — Lazy parent-issue creation

Parent issues for features are created **lazily** at first-slice-open, not eagerly at features.yaml write. Specifically: when `/start-slice` opens the first slice belonging to a feature whose features.yaml exists, it creates the parent issue and attaches the slice's child sub-issue to it. Subsequent slices for the same feature attach to the existing parent.

**Diverges from plan-doc default (eager).** Rationale: cairn-side commitment is the features.yaml file landing in git; the GH issue is downstream tracking, not the commitment itself. The plan-doc's argument for eager ("parent exists for sub-issues to attach to") is solved by lazy-with-retroactive-attach using one `gh sub-issue add --parent <N>` call per child. The pre-mortem F2 (issue spam) is real today — 8 features in `.claude/features/` would create 8 parent issues immediately on landing, which exceeds INV-007's named ~5-feature soft cap. Lazy keeps the issue tracker scoped to actively-worked features.

**Retroactive-attach assumption.** Per A8 in the assumption audit, `gh sub-issue add --parent <N> <child>` on an existing issue is believed to work; verification is part of the implementation slice's Phase 2. If wrong, the strategy reverts to eager — the choice is not load-bearing on the broader ADR.

### D4 — Declarative log + reconciler (board flips are structurally non-load-bearing)

Cairn commands never call `gh project item-edit` directly. Instead, `/start-slice` and `/close-slice` append a flip event to a local log file at `.claude/board-pending.log`, and a separate reconciliation command (`/board-sync`, in `commands/claude-code/.local/`) reads the log and pushes the events to GH.

**Diverges from plan-doc default (direct flip with warning).** The plan-doc framed flips as "non-load-bearing — if the board lookup fails, slash command continues with one-line warning." That guarantee holds protocol-level but is a discipline commitment, not a structural one. Pre-mortem F5 (soft-coupling becomes hard-coupling drift) names the failure mode: a year from now, somebody files a bug "I missed a slice because the dashboard was wrong"; the reflexive fix is to tighten the warning to an error; INV-001's substrate guarantee is silently revoked. D4 makes non-load-bearing **structural** rather than discipline-level.

**Log file format** — append-only, one event per line, JSONL:

```jsonl
{"slice_id":"compression/slice-3-…", "event":"in-progress",  "timestamp":"2026-04-28T10:14:22Z", "issue_number":42, "board_item_id":"PVTI_…"}
{"slice_id":"compression/slice-3-…", "event":"in-review",    "timestamp":"2026-04-28T14:02:11Z", "issue_number":42, "board_item_id":"PVTI_…"}
{"slice_id":"compression/slice-3-…", "event":"done",         "timestamp":"2026-04-28T16:30:05Z", "issue_number":42, "board_item_id":"PVTI_…"}
{"slice_id":"compression/slice-3-…", "event":"blocked",      "timestamp":"2026-04-28T18:00:00Z", "issue_number":42, "board_item_id":"PVTI_…", "reason":"Phase 4 invariant breach"}
```

Allowed `event` values: `in-progress`, `in-review`, `done`, `blocked`. Other values are reserved.

**Log file is gitignored.** Per assumption A7, the log is operator-local state; cross-machine reconciliation routes through GH itself (which is the cross-machine source of truth for board state per `.local/README.md` §5). Adding `.claude/board-pending.log` to `.gitignore` is part of the implementation slice's envelope.

**Reconciler contract.** `/board-sync` (in `.local/`) reads `.claude/board-pending.log`, applies each event to the cairn board via `gh project item-edit`, and on success removes the processed lines from the log. On per-line failure: leave the line in place, continue with subsequent lines, exit non-zero. The reconciler is idempotent: re-running with the same log produces the same final board state.

**Why not invoked from `/dev-mode`.** `/dev-mode` is contractually read-only (`commands/claude-code/.local/dev-mode.md` §"What this command does NOT do"). Invoking the reconciler from `/dev-mode` would break that contract. `/board-sync` is its own command, manually invoked or wired via a separate hook.

### D5 — PM-session commands stay in `.local/`

`/groom`, `/promote`, `/weekly-status` (and `/board-sync` from D4) all begin life in `commands/claude-code/.local/` per the `/dev-mode` precedent. They are cairn-the-project tooling, not cairn-the-methodology. They depend on cairn-specific assumptions (board name `cairn`, GH account `firaaz`, repo paths) that consumers cannot inherit.

This ADR commits to the **pattern** — that PM-session tooling lives in `.local/` until it earns generalization — not to immediate implementation of the four commands. None of the four are required by this ADR. They are described in `docs/plans/2026-04-27-board-roadmap-integration.md` as design sketches and remain there until built.

**Promotion path** to top-level (cairn-the-methodology) requires:
1. Generalization (no hardcoded `cairn` board name; `firaaz` account assumption removed; repo paths derived).
2. A new ADR or an amendment to this one explicitly authorizing the top-level move.
3. Feature.yaml entry + formal slice ceremony at promotion time, per `.local/README.md` §"Future-packaging path".

### D6 — `/promote`'s features.yaml writes (deferred)

The plan-doc proposed `/promote` writes `features/<id>.yaml` directly. Per C8, this is the L-001 anti-pattern unless explicitly authorized.

This ADR **defers** the resolution. Three options remain on the table:

- **Option A** — `/promote` is a wrapper that opens a `/start-slice` for a "design-the-feature" slice; features.yaml is the slice's Phase 3 deliverable. INV-001-clean. Heavy ceremony.
- **Option B** — features.yaml writes are added as a named non-slice commit class, parallel to `/refresh-architecture` and `/integration-sweep`. Documented exception. Lightweight.
- **Option C** — `/promote` is never built; features.yaml authoring stays manual or routes through `brainstorming` → `/start-slice`.

The choice depends on operational evidence (does `/promote` actually get used?) which doesn't exist yet. **Until `/promote` is actually being implemented, this ADR commits only to: D6.1 — features.yaml writes outside `/start-slice` are not currently authorized; any future slash command that writes features.yaml lands via a new ADR or an amendment to this one.**

### D7 — Three board-flip trigger points and failure-path handling

Composing D4's log with the slice lifecycle:

| Trigger | Cairn event | Log event | Board target Status |
|---|---|---|---|
| `/start-slice` opens | slice.yaml written | `in-progress` | `In progress` |
| `/close-slice` runs | `slice: complete` commit | `in-review` | `In review` |
| Phase 4 fails (slice marked `failed`) | `.claude/completed-slices/<id>-failed/` populated | `blocked` | `Blocked` |
| PR merged / slice fully done | (post-cairn-pipeline event) | `done` | `Done` |

The first three triggers are cairn-pipeline events and produce log entries from inside the relevant commands. The fourth (`done`) is a post-pipeline event — PR merge is not a cairn-managed event today. The implementation slice may add either: (a) a manual `/board-mark-done <slice-id>` command in `.local/` that appends the `done` event; or (b) a GH-side hook (e.g., GitHub Action on PR-merge that writes the event back via `gh`). Choice deferred to implementation; either is structurally compatible with D4.

**Failure-path comment.** When the `blocked` event is written, the reconciler additionally posts a comment to the parent issue (or sub-issue if individual) summarizing the failure reason from the log line's `reason` field. This makes failures visible in the dashboard without the operator having to dig into `.claude/completed-slices/<id>-failed/`.

## Consequences

**Made easier:**

- **Pre-spec idea capture has a structural home.** The board is the front door; consumers and operators can drop ideas there without ceremony. The cairn pipeline doesn't need to absorb every passing thought.
- **Feature ↔ slice hierarchy renders in GH UI.** Sub-issues progress bar updates automatically as child slices close; `/dev-mode` can surface the parent's progress instead of N individual rows.
- **Pipeline correctness is fully decoupled from GH availability.** D4's log + reconciler ensures `/start-slice` and `/close-slice` succeed even when GH is down. The cairn pipeline runs offline-clean.
- **Dashboard dishonesty is visible.** Pending unprocessed log entries are operator-readable; the `/dev-mode` briefing can surface "N pending board-sync events" as a section if useful.
- **The board can be entirely abandoned later** without touching the cairn pipeline. If consumer projects don't want a GH Projects dependency, they don't take one — the board is opt-in via the `.local/` carve-out.

**Made harder:**

- **Two-step board updates.** Cairn-side state changes don't immediately appear on the board; the operator must run `/board-sync` (or wire a hook). Adds latency between cairn truth and board display. Mitigation: reconciler is fast (gh CLI calls); can be batched or wired into a periodic hook.
- **Cross-machine reconciliation routes through GH, not git.** Each machine has its own `.claude/board-pending.log`; if Machine A appends a flip but Machine B runs `/board-sync` first, the events from A may sit unprocessed until A also runs. Acceptable for single-user use; multi-user use would need per-event ack tracking.
- **Eager parent-issue creation is rejected.** Existing `.claude/features/*.yaml` files (8 today) do not get retroactive parent issues. The first time each feature opens a slice, the parent issue is created lazily. This means features that have not yet had a slice opened are invisible to the board. Acceptable per D1's "board ≠ mirror of cairn-state" rule.
- **The board name `cairn` is now a load-bearing cross-machine contract** for any cairn-the-project tooling that talks to the board. Already documented in `.local/README.md` §5; this ADR formalizes it.

**Invariant impact:**

- **No new invariants.** This ADR is `firmness: provisional` and explicitly does not declare an invariant. The dogfood gate (below) determines whether D1–D7 firm up enough to warrant invariant promotion.
- **INV-001 (bootstrap-exception) is unaffected.** D6 explicitly defers `/promote`'s features.yaml write authority; no new pipeline-bypass path is opened.
- **INV-002 (context-discipline-protocol) is unaffected.** The board-pending log is at `.claude/board-pending.log`, not under `.claude/current-slice/`; it is not subject to the wipe-on-close rule. Consumers reading the log do not load any of its content into main context.
- **INV-006 (feature-slice-model D4 — status derived from state) is preserved by D1's "board ≠ mirror" rule.** Cairn slice status remains derived from observable state; the board carries the board's own state, not cairn's.
- **INV-008 (slice-close-contract) is unaffected.** D4's log append happens before or after `close_slice`'s `slice: complete` commit, not as part of it; close_slice remains the sole producer of the commit.

**Operational envelope:**

- `.claude/board-pending.log` is reserved as cairn-substrate for the board reconciliation queue. **Gitignored.** Written by `/start-slice` and `/close-slice` (and any future failure-path handler); read and emptied by `/board-sync`. Other commands MUST NOT read or write this file.
- `slice.yaml` schema additively gains optional `issue-number:` and `board-item-id:` fields. Slices opened without board context omit them. No existing slice is migrated.
- `.gitignore` gains `.claude/board-pending.log` as part of the implementation slice's envelope.

**Non-v1-scope declaration.** Per `cliff-failure-mode-and-v1-defenses/d4-time-box`, this ADR does not contribute to D1, D2, or D3. It is operational improvement, not defense. The implementation slice's `intent.md` MUST mark itself as a non-v1-scope waiver. The cliff-failure-mode-and-v1-defenses dogfood window (10 slices by 2026-10-11) is not delayed by this ADR — the implementation slice is non-blocking on the dogfood gate.

**Dogfood gate (provisional firmness).** This ADR is provisional with an explicit dogfood gate: 10 slices using D2/D4/D7 (board-driven `/start-slice`, log + reconciler, three trigger points), OR 2026-10-11 (the cliff-failure-mode-and-v1-defenses dogfood deadline), whichever first. At the gate, the ADR is reviewed for promotion to `firm` or for amendment. Specific signals to watch:

- F1 (duplicate-state drift): ≥1 instance of dashboard ≠ cairn-truth observed in real use → amend toward stronger reconciler discipline or invariant.
- F2 (issue-tracker spam): >50 stale issues at the gate → amend D3 toward eager-with-aggressive-grooming, or accept and build close-stale automation.
- F3 (board-down per-slice loss): ≥1 instance where re-entry path was inadequate → amend D2 toward idempotent retry.
- F4 (cross-machine race): ≥1 instance observed → amend toward optimistic-concurrency check on `gh project item-edit` Status transitions.
- F5 (hard-coupling drift): D4's "warning never escalates to error" rule holds → confirm by inspection of `/start-slice` and `/close-slice` source at gate.
- F6 (`/promote` becomes new L-001 trap): if `/promote` is built before the gate, verify it landed via D6.1 (new ADR or amendment), not as a silent bypass.

If 3+ signals fire, this ADR enters supersession review.

## Alternatives Considered

### Q1 — Layer model

| Approach | Core idea | Why rejected or chosen |
|---|---|---|
| **1A — chosen: four layers** (board / features.yaml / slice / lessons) | Each substrate has non-overlapping role | Selected. Capture-cost asymmetry between board (free) and features.yaml (pipeline-routed) is the load-bearing distinction |
| 1B — three layers (collapse board into features.yaml `status:`) | features.yaml gets a `status: idea/committed` field | Rejected: violates C8 — features.yaml writes are pipeline-routed; "anyone can drop an idea" then becomes "anyone can edit features.yaml" |
| 1C — two layers (board only, no features.yaml in the loop) | Slices reference board items directly | Rejected: regression vs `feature-slice-model/d0-features-and-slices` — features are the unit of intent |

### Q2 — Draft → issue conversion timing

| Approach | Core idea | Why rejected or chosen |
|---|---|---|
| **2A — chosen: convert at `/start-slice`** | Issue created when slice opens; `#N` captured into slice.yaml | Selected. Aligns "GH-draft ↔ cairn-pre-`/start-slice`"; first commit can `closes #N` |
| 2B — convert at Phase 2 commit (later) | Draft stays through Phase 1; issue created when first failing test commits | Rejected: Phase 1's intent.md commit can't `closes #N`; asymmetric cross-link integrity |
| 2C — never auto-convert; manual | Operator manually converts when ready | Rejected: high discipline cost, low automation benefit; F1 (dashboard drift) high |

### Q3 — Eager vs lazy parent-issue creation

| Approach | Core idea | Why rejected or chosen |
|---|---|---|
| 3A — eager (plan-doc default) | Parent issue at features.yaml write | Rejected: F2 issue spam high (8 features today); exceeds INV-007 ~5-feature soft cap immediately |
| **3B — chosen: lazy** | Parent issue at first-slice-open | Selected. Cairn-side commitment is features.yaml in git, not the GH issue. Retroactive sub-issue attach (A8) keeps parents coupled to actively-worked features |
| 3C — hybrid (eager only within N days of features.yaml creation) | Time-windowed | Rejected: arbitrary threshold with no empirical basis; adds complexity for no clear benefit |

### Q4 — Board flips structurally non-load-bearing

| Approach | Core idea | Why rejected or chosen |
|---|---|---|
| 4A — direct flip with warning (plan-doc default) | `/start-slice` and `/close-slice` call `gh project item-edit` directly; failure = stderr warning | Rejected: F5 (soft-coupling becomes hard-coupling drift) addressable only by discipline, not structure. Year-2 hardening risk too high to leave protocol-level |
| **4B — chosen: declarative log + reconciler** | Cairn commands append to `.claude/board-pending.log`; `/board-sync` (separate) pushes to GH | Selected. Makes non-load-bearing structural. Cairn pipeline runs offline-clean; reconciliation is a separate concern |
| 4C — no cairn-side flips at all | Board for human grooming only; dashboard derives from cairn-side truth ignoring board Status | Rejected: bifurcates PM and cairn views; loses the "board as honest dashboard" benefit |

### Q5 — PM-session commands' home

| Approach | Core idea | Why rejected or chosen |
|---|---|---|
| **5A — chosen: `.local/`** | `/groom`, `/promote`, `/weekly-status`, `/board-sync` start in `commands/claude-code/.local/` | Selected. Honors C10 cleanly; matches `/dev-mode` precedent; promotion path exists if any earns its keep |
| 5B — top-level (cairn-the-methodology) | Ship them to consumers | Rejected: violates C10; board name `cairn`, GH account, repo paths all hardcoded today; premature abstraction without consumer evidence |
| 5C — defer all PM-session work entirely | Build only when empirical demand exists | Partially adopted: this ADR ratifies the *pattern* but does not mandate immediate construction. Each command is built when needed, in `.local/`, per D5 |

### Q6 (B1) — `/promote`'s features.yaml write authority

| Approach | Core idea | Why rejected or chosen |
|---|---|---|
| 6A — `/promote` writes features.yaml directly (plan-doc implicit) | One-step | Rejected: C8 / L-001 violation; F6 sets future-bypass precedent |
| 6B — `/promote` invokes `/start-slice` for a design-the-feature slice | Wrapper around existing pipeline | Considered for future; heavy ceremony. Ratification deferred to D6.1 |
| 6C — features.yaml writes as named non-slice commit class | Documented exception parallel to `/refresh-architecture` | Considered for future; lightweight. Ratification deferred to D6.1 |
| **D6.1 — chosen: defer** | This ADR commits only that features.yaml writes outside `/start-slice` are not currently authorized; future authorization requires new ADR/amendment | Selected. No `/promote` exists today; deciding without operational evidence would be premature |

### Q7 (B2) — Board-flip trigger points

Selected: D7 — three cairn-pipeline triggers (`in-progress` at `/start-slice`, `in-review` at `/close-slice`, `blocked` on Phase-4 fail) + one post-pipeline trigger (`done` via manual or PR-merge hook). All routed through D4's log.

### Q8 (B3) — Failure-path handling

Selected: D7 + reconciler comment posting. `blocked` event includes `reason` field; reconciler posts comment to parent (or sub-) issue with the reason on push. Makes failures visible in dashboard.

## Risk Register

The Phase 1 pre-mortem produced six failure scenarios. Each is addressed below.

- **F1 — Duplicate-state drift (dashboard ≠ cairn truth).** Addressed by D1's "board is not a mirror of cairn-state" rule + D4's reconciler log (pending entries are operator-visible). Residual risk: dashboard latency between cairn-event and reconciler-run. Mitigation: reconciler can be invoked from any `.local/` aid or wired into a periodic hook. **Tripwire:** ≥1 observed dashboard-truth divergence in real use → amend toward stronger reconciler discipline.

- **F2 — Eager parent-issue spam.** Addressed by D3 (lazy creation). Residual risk: features that retire before opening any slice never get parent issues; their existence is invisible to the board. Acceptable per D1's "board ≠ mirror" rule. **Tripwire:** >50 stale parent issues at dogfood gate → amend D3.

- **F3 — `/start-slice` board-coupling failure (board down).** Addressed by D2's re-entry path (`/start-slice --link-issue <N>` post-hoc). Residual risk: per-slice commits made before link is established lack `closes #N`; the cross-link is complete but each-commit cross-link is not. Acceptable. **Tripwire:** ≥1 instance where re-entry path was inadequate → amend D2 toward idempotent retry.

- **F4 — Cross-machine race (single-user, multi-machine).** Not addressed structurally; relies on single-user discipline ("just don't"). Residual risk: two machines simultaneously open slices for the same board item → two slice branches, last-write-wins on board Status. **Tripwire:** ≥1 instance observed → amend toward optimistic-concurrency on `gh project item-edit`.

- **F5 — Soft-coupling becomes hard-coupling drift.** Addressed structurally by D4 (cairn never directly calls gh CLI; reconciler is separate). Residual risk: future slice author "simplifies" by inlining the gh CLI call back into `/start-slice`. **Tripwire:** at dogfood gate, inspect `/start-slice` and `/close-slice` source — confirm no gh CLI calls; warning never escalated to error.

- **F6 — `/promote` becomes new L-001 trap.** Addressed by D6.1 (deferral). Residual risk: someone builds `/promote` without ADR amendment. **Tripwire:** if `/promote` is built before the dogfood gate, verify it landed via new ADR or amendment to this one.

### Assumption audit

| # | Assumption | Status | Degradation | Mitigation |
|---|---|---|---|---|
| A1 | `gh project item-edit` is idempotent (same edit re-applied is no-op) | Believed | Graceful | Reconciler removes processed lines after success; re-run is safe |
| A2 | Board name `cairn` resolves uniquely under `gh project list --owner @me` from any machine | **Verified** (`.local/README.md` §5; `gh project field-list 4` confirms) | N/A | — |
| A3 | GH Projects v2 has `Sub-issues progress` and `Parent issue` fields | **Verified** (`gh project field-list 4` output captures both) | N/A | — |
| A4 | `gh project item-create` for draft items can be promoted to issues without losing board-item-id | Believed | Graceful | Implementation slice's Phase 2 verifies; if wrong, draft is deleted and replaced (acceptable per-slice cost) |
| A5 | `.claude/board-pending.log` writes don't conflict with `scope-guard.sh` envelope | Believed | Catastrophic during slice (would deny log writes) | Implementation slice's intent.md adds explicit allowlist entry |
| A6 | Reconciler runs as its own command, not as `/dev-mode` side effect | **Resolved by design** — `/dev-mode` is read-only per its spec | N/A | `/board-sync` is a separate `.local/` command |
| A7 | `.claude/board-pending.log` is gitignored (operator-local queue), not committed | **Resolved by D4** — log is gitignored; cross-machine sync routes through GH | N/A | Implementation slice adds `.gitignore` entry |
| A8 | Lazy parent-issue creation works via `gh sub-issue add --parent <N> <child>` (post-hoc attach) | Believed | Graceful | Implementation slice verifies; if wrong, fall back to eager (D3 reverses) |
| A9 | The `Blocked` Status option (added manually) persists across machines | **Verified** (Status options are board metadata, not per-machine) | N/A | — |
| A10 | Log file writes are local I/O — no network dependency | **Verified** (filesystem operations only) | N/A | — |

### Load-bearing belief and tripwire

This ADR rests on **A_LB**: *D4's structural decoupling (log + reconciler) is materially better than D4-alternative (direct flip with warning) at preventing F5 (hard-coupling drift).*

If A_LB is wrong, the substrate file + reconciler are pure overhead and the simpler 4A approach would have served. The dogfood gate (10 slices or 2026-10-11) is the validation event:

- If `/start-slice` and `/close-slice` source at the gate contain no `gh` CLI calls AND the operator reports no friction from running `/board-sync` separately, A_LB is operationally validated and this ADR can promote toward firm.
- If the operator routinely forgets `/board-sync` and the log queue grows unbounded, OR if the source has acquired direct gh CLI calls (D4 violation), A_LB is in question and the ADR is amended toward 4A with an explicit "non-load-bearing-warning-never-escalates" invariant clause instead.

## Consequences for in-progress work

- **No active slice today** — this ADR's land does not require any in-progress slice migration.
- **The implementation slice for D2/D4/D7** (working title `board-as-roadmap-substrate/log-and-reconciler`) is non-blocking on the cliff-failure-mode-and-v1-defenses dogfood gate. Its intent.md MUST declare non-v1-scope waiver.
- **Pre-existing `.claude/features/*.yaml` (8 files)** are not retroactively given parent issues per D3. They get parents on next-slice-open per their respective features.
- **The 9 seed items on the cairn project board** (3 Ready + 6 Backlog as of 2026-04-27) remain board-resident. Any that progress to slices will land via the D2 path once the implementation slice ships.
- **Plan doc `docs/plans/2026-04-27-board-roadmap-integration.md` is superseded** by this ADR. Its status line moves to `superseded by ADR board-as-roadmap-substrate` as part of this ADR's commit.
