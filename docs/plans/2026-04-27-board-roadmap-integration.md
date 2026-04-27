# Board ↔ features.yaml ↔ slices integration — design notes for `/decision`

date: 2026-04-27
branch: feature/board-roadmap-integration
status: pre-decision (conversation capture; run `/decision` to ratify)

## Why this exists

The cairn GH Project board (`https://github.com/users/firaaz/projects/4`) was created this session as `/dev-mode`'s GH Projects backing store. During seeding (5 housekeeping items + 4 complex-rag-mcp consumer findings) it became clear the board overlaps three existing cairn primitives — `features/<id>.yaml`, `.claude/current-slice/slice.yaml`, and `docs/lessons.md` — without an explicit contract for how they layer. This doc captures the layering shape that came out of conversation so the next `/decision` run can ratify it as an ADR (working title `board-as-roadmap-substrate`) without having to re-derive the design.

This is **not** an ADR. It is intentionally exploratory: the layering proposed below has not been built against, hooks have not been written, and no invariant references it yet. `/decision` will subject it to Phase-1-through-5 scrutiny before anything firms up.

## Background facts established this session

- The cairn board was created from the **Kanban** preset (15 fields total, including `Backlog / Ready / In progress / In review / Blocked / Done` Status options). User added `Blocked` manually as the sixth Status option to match `/dev-mode`'s bucketing spec.
- The board is owned by the user account `firaaz`; every machine authenticates as `firaaz` via the gh-cli launcher (`commands/claude-code/.local/README.md` §2), so `gh project list --owner @me` resolves to the same project from any machine — no per-machine pointer needed; **board name `cairn` is the cross-machine lookup contract.**
- `commands/claude-code/.local/dev-mode.md:62` reads only the Status field for bucketing; Priority / Size / Estimate / Start date / Target date / Iteration are inert from the briefing's perspective but are available for human use and for any future PM tooling.
- The board carries 9 seed items at time of writing: 3 Ready (worktree removal, PAT rotation, handoff-memory refresh), 6 Backlog (feedback memory on gh-cli wrapper, MCP-disconnect investigation, and 4 complex-rag-mcp orchestrator findings — phase-3 timeout default, no partial-progress carry-over on retry, subprocess reaping, `/start-slice` cwd misroute via `.slice-system` symlink).

## The layering — four stacked substrates

| Layer | Substrate | Cardinality | Lifetime | Mutability |
|---|---|---|---|---|
| **Roadmap / catchment** | GH Project board | Many small items | Hours to weeks | Free (board UI / gh CLI / MCP) |
| **Slice plan** | `.claude/features/<id>.yaml` | Coarser commitments — "ship X across N slices" | Days to months | Append/edit per `feature-slice-model` ADR |
| **Execution** | `.claude/current-slice/slice.yaml` + phase-1-to-4 + sweep | One slice in flight at a time | Hours to days | Phase-locked per `phase-lock-and-role-declaration` |
| **Memory** | `docs/lessons.md` (L-NNN), `.claude/handoff.md`, `~/.claude/projects/.../memory/*` | Outcomes, learnings | Permanent | Append-only (lessons), churning (handoff) |

Each layer has its own substrate, its own lifecycle, and its own consumers. The board is the **front door** (idea capture, prioritization, scheduling). features.yaml is the **commitment register** (what cairn intends to ship). slice.yaml + phases are the **execution engine**. lessons + handoff are the **exhaust** (what we learned so the next slice doesn't have to re-derive it).

The board is the only layer where **anyone (including consumer projects) can drop ideas without ceremony**. Promotion to features.yaml or slice is gated; capture is not.

## Proposed lifecycle — board-item state vs cairn-pipeline state

| Step | Board Status | Item type | Cairn artifacts present | Notes |
|---|---|---|---|---|
| 1. Idea captured | `Backlog` | Draft item | None | `gh project item-create` from anywhere; no issue created |
| 2. Triaged + groomed | `Ready` | Draft | + Priority (P0/P1/P2), Size (XS-XL), Target date | A `/groom` slash command (see PM-session pattern below) is the natural editor |
| 3. `/start-slice` runs | `In progress` | **Issue `#N`** | `slice.yaml` written | **Draft → issue conversion at this point.** Reason: every slice produces a commit chain (Phase 1's intent.md commit, Phase 2's red tests, Phase 3's GREEN impl, Phase 4's sweep) that needs a stable `#N` to reference in commit subjects and the eventual PR body. Promoting later means early commits can't `closes #N` cleanly. |
| 4. Phase 1 completes | `In progress` | Issue | `slice.yaml` + `intent.md` | Board state does NOT move at intent.md. But intent.md is the moment the slice becomes contractually committed — Phase 2 writes failing tests against it, no further design changes allowed without slice-restart. |
| 5. Phase 2-3 cycle | `In progress` | Issue | + red tests, then green impl | |
| 6. Phase 4 + PR open | `In review` | Issue | + sweep.yaml + PR linked to issue | `/close-slice` (or its successor) flips Status |
| 7. Merged + closed | `Done` | Issue | + L-NNN lesson if applicable | Lesson lands in `docs/lessons.md` per existing convention |
| Side state: `Blocked` | (any) → `Blocked` | Draft or Issue | n/a | Used when waiting on external dependency. Re-emerges when unblocked. |

**Key clarification on "draft" semantics.** Two distinct meanings of "draft" intersect here:
- **GH Projects draft item** — board-only entity, no GitHub issue, no `#N`, cheap to create, cannot be cross-linked from PRs/commits. This is the GH-platform meaning.
- **Cairn slice in pre-Phase-1 state** — slice exists as an idea or board item but no `slice.yaml`, no intent.md, no Phase 1 dispatch. Methodology meaning.

The natural mapping: GH-draft ↔ cairn-pre-`/start-slice`. The flip (draft → issue) and the methodology flip (idea → committed slice) coincide at `/start-slice` invocation. **intent.md is not the demarcation** — it's the first artifact of an already-promoted slice.

## Feature ↔ slice hierarchy

`features/<id>.yaml` covers N slices. Mapping to GH:
- **Feature → parent issue.** One GitHub issue per feature, opened when the feature.yaml entry is written. Stays In progress until all child slices are Done.
- **Slice → sub-issue of the parent.** GH Projects v2 has the `Sub-issues progress` field and parent-issue field already (visible in `gh project field-list 4`). Each sub-issue follows the slice lifecycle in the table above. The parent's progress bar updates automatically as children close.
- `/dev-mode` could surface the parent's progress bar instead of N individual rows when all children belong to the same parent — keeps the briefing dense.

Open question: when does the parent issue get created? Two options:
1. **Eager:** at the moment a `features/<id>.yaml` entry lands, even before any slice opens. Pros: parent exists for sub-issues to attach to; can be groomed alongside Backlog children. Cons: creates an issue that may have zero children for a while if the feature is provisional.
2. **Lazy:** at the moment the first slice opens. Pros: no issue without active work. Cons: requires retroactive sub-issue attachment for the first slice if it's the only one for a while.

Default proposal: **eager** — a feature is a commitment, not a hypothesis; if it's in `features/<id>.yaml` it's worth a tracking issue. Run `/decision` to settle.

## PM-session pattern

A focused Claude Code session whose tool surface is intentionally narrow: gh project + read the repo, no edits to code or slice artifacts. The job is grooming, not building. Three concrete shapes were sketched in conversation:

### `/groom`

Read full board, surface:
- Stale Backlog items (>30 days, no Priority set)
- Items with Target date inside 7 days that are still Backlog (impossibility flag)
- Missing estimates on Ready items
- Contradictions between board state and `features/<id>.yaml` (e.g., feature claims Done but no closed slice references it)

Propose batched edits, await approval, apply via `gh project item-edit`.

Belongs in `commands/claude-code/.local/groom.md` as a `.local/` carve-out (matches how `/dev-mode` was introduced — start as `.local/`, promote to ship-grade if it earns its keep).

### `/promote <item-id>`

Interactive: take a Backlog or Ready item → ask design questions to fill in the slice envelope → write a `features/<id>.yaml` entry (or open a slice directly for sub-feature work) → set the board item to In progress → invoke `/start-slice`.

This is the natural integration point with the existing slice pipeline — `/promote` sits upstream of `/start-slice`, not parallel to it. `/start-slice` itself stays unchanged; `/promote` adds the board-aware preamble.

### `/weekly-status`

Generates a Projects v2 status update (the API supports `create_project_status_update`) summarizing:
- What shipped (Done items moved this week)
- What's blocked (Blocked items + reason)
- What's in flight (In progress / In review)
- What's next iteration (Ready, sorted by Priority + Target date)

Posts it to the board so it shows under "Add status update" on the project page. Optional: also write to `docs/plans/<date>-status.md` for git-side persistence.

### Integration with existing pipeline

Two existing slash commands need small additions:

- **`/start-slice`** — when opening a slice whose intent matches a board item (matched by title, by referenced issue, or by an explicit `--board-item <id>` flag): convert that draft to an issue, set Status = In progress, capture the issue `#N` into `slice.yaml` for downstream commit-message use.
- **`/close-slice`** — at the end of slice close: flip the board item to In review (if PR open) or Done (if merged); optionally call `create_project_status_update` if the slice produced a noteworthy lesson (L-NNN).

Both additions are non-load-bearing — if the board lookup fails for any reason (board missing, item not found, MCP down), the slash command continues with a one-line warning. The pipeline doesn't depend on the board.

## Roadmap-handling capability

For completeness, the board's roadmap dimensions and what cairn tooling can do with each:

| Field | gh CLI / MCP access | Useful for |
|---|---|---|
| Status | read+write | bucketing in `/dev-mode`; slice-pipeline state mirror |
| Priority (P0/P1/P2) | read+write | `/groom` triage; ordering in Ready |
| Size (XS-XL) | read+write | rough effort signal; pairs with Estimate |
| Estimate (numeric) | read+write | iteration capacity planning |
| Start date / Target date | read+write | Roadmap view (Gantt); `/groom` overdue flagging |
| Iteration | read+write (if added) | sprint-style grouping |
| Sub-issues progress | read-only (auto) | feature parent-issue progress bar |
| Linked pull requests | read-only (auto) | slice → PR cross-link |

The Gantt rendering is UI-only, but the underlying data is full-fidelity from the API. Cairn tooling can produce equivalent reports ("P0s with target dates in next 30 days", "items missing estimates", "iteration N capacity vs assigned") without touching the visualization.

## What needs `/decision` before this firms up

Run `/decision` to ratify (or reject) each of:

1. **The four-layer model** (board / features.yaml / slice / lessons) as the canonical layering.
2. **Draft→issue conversion at `/start-slice`** as the contract (vs alternative: convert later at Phase 2 commit, or never).
3. **Eager parent-issue creation** for features (vs lazy at first-slice-open).
4. **`/start-slice` and `/close-slice` adding board-side flips** as non-load-bearing additions (failure = warning, not error).
5. **`/groom` / `/promote` / `/weekly-status` as `.local/` carve-outs** for now (matching `/dev-mode`'s introduction path).

Each of these is a real choice with alternatives. The bullets above describe the conversation's preferred shape; `/decision` will surface what it missed.

## Pre-decision risks worth naming

- **Board availability becomes a soft dependency.** Once `/start-slice` knows about the board, what happens when GitHub is down or the MCP is disconnected (as it was for several minutes mid-session today)? The "non-load-bearing" guarantee needs to be stress-tested. Suggested invariant: every board-side flip the pipeline performs must have a corresponding "would-have-flipped" log line so the state can be reconciled offline.
- **Issue spam if Backlog grooming lapses.** Eager parent-issue creation for every features.yaml entry plus draft→issue at `/start-slice` could fill the issue tracker with stale auto-created entries. Mitigation: `/groom` includes a "close unstarted issues older than N days" pass.
- **Cross-machine board drift.** Two machines opening slices nearly simultaneously could produce two issues for the same board item before either flips Status. Single-user mitigation: just don't (the user is alone). Multi-user mitigation needed if cairn ever becomes shared: lock the board item before promoting.
- **Existing project board has a Backlog WIP limit of 5 (red `6/5` observed today).** Before any tooling treats Backlog as the catchment, lift this limit (UI: column settings → Item limit → blank or 50). Backlog is meant to accumulate.

## Pointers

- This doc: `docs/plans/2026-04-27-board-roadmap-integration.md`
- `/dev-mode` spec: `commands/claude-code/.local/dev-mode.md`
- Setup README: `commands/claude-code/.local/README.md`
- Existing related ADRs to reference when running `/decision`:
  - `feature-slice-model` — the features ↔ slices part of the layering
  - `slice-close-contract` — close-side correctness; `/close-slice` board flip must respect this
  - `phase-lock-and-role-declaration` — the slice phases are bound by this; board flips must not bypass it
  - `context-discipline-protocol` — `/dev-mode`'s read-only briefing model; PM-session writes break this and need their own discipline
  - `identifier-scheme` — feature/slice id shape carries to GH issue titles
- Project board: `https://github.com/users/firaaz/projects/4`
- Seeded items as of 2026-04-27: 3 Ready (worktree removal, PAT rotation, handoff-memory refresh), 6 Backlog (feedback memory on gh-cli wrapper, MCP-disconnect investigation, phase-3 timeout, retry partial-progress, subprocess reaping, /start-slice cwd misroute)
