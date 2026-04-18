# Lessons

Cross-cutting patterns discovered during slice work, referenced by `/decision` Phase 0 (Constraint Harvest) and `/integration-sweep` recommendations.

## L-001: Pipeline-bypass temptation — "just write it down" before opening a slice

**Discovered**: 2026-04-11, first integration sweep after the `validator-symlink-fix` slice.

**Pattern**: a real bug is discovered in the middle of another session (often while consuming cairn from a downstream project). The urge is to *write it down somewhere* — a CHANGELOG entry, a known-issues note, a docs paragraph — before opening a slice to fix it. The bug feels too concrete to leave in working memory and too specific to lose to a session boundary. A tiny direct commit feels justified because "it's just docs."

**What happens**: the direct commit lands. It is a three-line addition, well-written, cleanly scoped. It is also a bypass of `/start-slice` and a violation of the invariant that requires all post-bootstrap work to flow through the pipeline. The first cross-slice integration sweep finds it. By then it is already in the permanent history.

**Concrete instance**: `f531087 docs: record validator symlink-resolution bug in Known issues` (2026-04-11). Three-line CHANGELOG edit recording the `scripts/validate_architecture.py:22` symlink bug that the `validator-symlink-fix` slice subsequently fixed. Intent was honest; the act was a violation. After the first cross-sweep surfaced it, the remedy was **option 3 — accept as a scar**: leave INV-001 unchanged, record this lesson, let the violation stand in history as evidence that the pipeline is not mechanically enforced and the maintainer's own discipline is the only barrier.

**Why option 3 and not a new ADR**: rewriting the invariant to excuse the commit would hide the lesson. bootstrap-exception already says "there is no second exception" and "future attempts must go through supersession, not quiet repetition." A supersession to retroactively regularize the bypass would be quiet repetition in a different form. The honest answer is: the bypass happened, it should not have happened, and the cost of recording that is carrying one un-remediated violation in the `git log` forever.

**Recursive consequence**: `/integration-sweep` step 6.5 itself produces a commit that is not a slice phase commit and not a decision commit. Under a strict reading of INV-001, every sweep commit is also a violation of the same class. Option 3 accepts this too — sweep commits are scars of the same kind, landed deliberately, each one an audit-trail artifact of an honest check rather than a shortcut. This is the consequence of not writing an context-discipline-protocol that names sweep commits as pipeline-substrate operations.

**Rule for future Claude sessions (and future me)**: if you are about to make a direct commit to cairn and you are not in the bootstrap commit, stop. The options are (1) open a slice via `/start-slice`, (2) run `/decision` if the change is architectural, or (3) write nothing to the repo and carry the information forward to the next session via `/handoff`. The temptation to "just write it down quickly" is the pattern this lesson names. Holding that information in `/handoff` state is strictly better than a direct commit, because a handoff does not pollute the audit trail.

**Exceptions**: `/integration-sweep` and `/refresh-architecture` commits are pipeline-substrate operations whose exclusion from `/start-slice` is a known scar (see the recursive consequence above). They are not a license for other kinds of direct commits.

**Anti-pattern signals**: "it's just docs," "it's only three lines," "I'll open the slice right after," "the invariant doesn't really mean this." All of these were internally true in the concrete instance. None of them prevented the violation.

## L-002: Route-before-run — triage, framing, and analysis are three distinct steps

**Discovered**: 2026-04-11, during the phase rethink `/decision` session (P0a from the cliff-failure-mode-and-v1-defenses v1 execution plan). Observed while comparing cairn's `/decision` against Superpowers' `brainstorming` skill and RIPER-5's capability-gated modes; formalized in the same session.

**Pattern**: Every incoming unit of work answers three questions in order, and each question can be revisited when the next one reveals the prior answer was wrong.

**Step 0 — Triage (which flow(s), how many, in what order?)**: classify the work against cairn's current flow corpus:

- `superpowers:brainstorming` — framing-only; output is a spec, no commitment to a direction
- `/decision` — architectural commitment; output is an ADR
- `/start-slice` — implementation under existing constraints; output is a 4-phase passage
- `/integration-sweep` — cross-slice audit; output is sweep notes + possibly new slices
- `/refresh-architecture` — derived-view regeneration; output is `docs/ARCHITECTURE.md`
- Direct ADR editorial fix (`ADR_EDITORIAL_FIX=1`) — frontmatter or typo patch

Triage outputs **a sequence** of one or more flows. Examples: a code-local bug report → `/start-slice` alone (1 flow). An architectural question with a clear framing → `/decision` alone (1 flow). An architectural question arriving cold → `brainstorming` → fresh session → `/decision` (2 flows). A feature request that implies both a decision and an implementation → `/decision` → fresh session → `/start-slice` (2 flows). An exploratory "I'm not sure what I want yet" → `brainstorming` alone, the session itself is the output (1 flow, no downstream commitment). A cross-project observation from integration-sweep that needs a new invariant → sweep findings → `/decision` → `/start-slice` (3 flows). The scope of triage is expected to expand as cairn's flow corpus grows.

**Step 1 — Framing (does a framing artifact already exist?)**: a framing artifact is any document that maps the constraint space and enumerates candidate approaches — exploration note, plan doc, RFC, ADR predecessor, prior brainstorming output. If yes → feed it directly to the next flow's entry point (`/decision` Phase 0, `/start-slice` Step 5). If no → run `superpowers:brainstorming` in a **fresh session** to produce one. The session boundary between framing and the next flow is load-bearing — it extends context-discipline-protocol's session-isolation principle from slice-phase boundaries to decision-framing boundaries.

**Step 2 — Analysis/execution**: run the chosen flow in its own fresh session. Standard flow rules apply. No framing work happens inside `/decision` Phase 0; no `/decision`-flavored adversarial analysis happens inside brainstorming. Each phase does its own job.

**Triage is a classifier, not a commitment. Flows are open to change mid-run:**

- **Downshift** (spec-v1 §4 already implements this): `/decision` started, work turns out to be trivial → demote by marking the ADR `firmness: provisional` and skipping Phase 5. The Phase 0 constraint harvest and Phase 2 enumeration remain valuable even for trivial work.
- **Upshift** (spec-v1 §5; `docs/reviews/2026-04-11-from-rag-session.md` Finding 2): `/start-slice` started, architectural invariant discovered mid-slice → fail the slice, restart with a `/decision` that produces the ADR, then re-enter the slice with the new constraint as input. Do NOT patch around the discovery inside the slice — that routes around the verification layer.
- **Reframe** (applies to any flow, any phase): if triage was wrong, return to triage. The cost of a mis-triage caught early is small; the cost of running the wrong flow to completion is the cost of all the work done under the wrong discipline.

**Concrete instance**: the phase rethink `/decision` session on 2026-04-11 ran as a clean 1-flow path (`/decision` alone) because (a) triage routed the work to `/decision` per cliff-failure-mode-and-v1-defenses D4's "standalone `/decision`, not a slice" and the v1 execution plan's P0a, and (b) `.claude/current-slice/exploration-notes.md` (two 2026-04-11 exploratory sessions) was the framing artifact — brainstorming was correctly skipped. The session boundary between the exploratory sessions and today's `/decision` preserved isolation for free.

**Anti-pattern signals**: "I'll just start a slice and figure out the decision as I go" (upshift-in-denial), "this is obviously an [X]" (triage skipped under false certainty), "we already know what we want so skip brainstorming" (framing confused with approval), "I'll run `/decision` to confirm what I already decided" (analysis used as theater). All four are internally plausible; none prevent the routing error.

**Refinements upstream, not downstream**: "one question at a time, multiple choice preferred" and "incremental approval gates" from Superpowers' `brainstorming` skill belong in the framing step (Step 1), not inside `/decision`'s analysis phases. If framing happens in brainstorming and analysis happens in `/decision`, neither phase has to re-do the other's work.

**Scope note**: this lesson captures the pattern as a mental routing rule. Promotion to a dedicated `/triage` skill is deferred — the scope will be cleaned up and pressure-tested through use before earning its own command.

## L-003: Phase 5 Independent Verification — index-row leak from Phase 4 draft commit

**Discovered**: 2026-04-11, during the phase-lock-and-role-declaration phase rethink `/decision` session (P0a from the cliff-failure-mode-and-v1-defenses v1 execution plan). Observed when the Phase 5 verification subagent read `docs/adr/index.md` as part of its mandated Phase 0 Constraint Harvest inputs and saw the new phase-lock-and-role-declaration title row that had been committed one step earlier in Phase 4 alongside the ADR body.

**Pattern**: The `/decision` protocol's Phase 4 step ("Commit the ADR draft") currently includes the `docs/adr/index.md` row update alongside the new ADR file. For firm decisions, Phase 5 Independent Verification spawns a fresh subagent instructed to read `docs/adr/index.md` during Phase 0 Constraint Harvest to discover the ADR corpus. As a result, the new ADR's title row is visible to the subagent **before** it enumerates approaches, partially pre-anchoring the enumeration to whatever the title reveals. This does not invalidate Phase 5 — the subagent still runs constraint harvest, pre-mortem, enumeration, and stress test independently — but the enumeration's starting position is no longer clean.

**Concrete instance**: phase-lock-and-role-declaration landed with the title "Four-Phase Pipeline Lock and Role Declaration." The Phase 5 subagent honestly flagged the leak in its return ("I noticed from the index the title contains 'Four-Phase Pipeline Lock and Role Declaration' — this is a minor, unavoidable leak") and compensated by genuinely enumerating 3-phase, two distinct 5-phase shapes, and an independently-derived 3-phase collapse variation. Its constraint envelope, pre-mortem, stress test, assumption audit, and rationale were all derived from first principles. But the Phase 2 enumeration's anchor point was the leaked phase count (4) and the leaked commitment class ("lock"). A less disciplined subagent could have collapsed the enumeration around the leaked answer.

**Rule for future `/decision` runs on firm ADRs**: at Phase 4 (Decision Record), commit the ADR body file but **do not** update `docs/adr/index.md`. The index update is Phase 6 (Propagation) work — `/refresh-architecture` Step 3 regenerates the index from the ADR corpus naturally at Phase 6 and the new row appears there. Splitting the commits preserves Phase 5's isolation: the verification subagent reads the old index without the new row, and the ADR body is inaccessible to it by explicit instruction.

**For provisional ADRs**: Phase 5 is skipped per the `/decision` protocol ("For `firmness: provisional` decisions, skip Phase 5 — provisional decisions are expected to be revisited as the project learns more"), so the index row leak has no consequence. Index update at Phase 4 remains acceptable for provisional decisions.

**Mechanism**: requires a small protocol refinement to `commands/claude-code/decision.md` Phase 4 instructions, splitting "commit the ADR draft" into two distinct sub-steps for firm ADRs: (a) commit the ADR body file alone; (b) at Phase 6, run `/refresh-architecture` which handles the index regeneration. This refinement is a protocol-skill edit that runs through a normal slice (not captured as this `/decision` session's output, since this session is scoped to phase-lock-and-role-declaration, not to protocol refinements).

**Anti-pattern signals**: "the index row is just metadata, it won't affect the subagent's reasoning," "the subagent is instructed to compensate for contamination," "Phase 5 already acknowledges same-family verification is partial per `docs/spec-v1.md` §7." All three are internally true. None of them eliminated the partial anchoring in the concrete instance above.

## L-004: Inherited threshold — a counter reused across defenses may not measure what its warning text claims

**Discovered**: 2026-04-16, during the `d3-bypass-classification` `/decision` session.

**Pattern**: A threshold rule and counter are extended from one defense to another by surface-level reuse (same rolling window, same count, same warning text) without re-examining whether the underlying failure classes are the same shape. In the source defense, the counter is well-aligned with its warning text because the bypass domain is naturally single-class. In the target defense, the bypass domain has multiple structurally distinct classes, and the single counter conflates them — firing the warning on signals the warning text does not actually describe.

**Concrete instance**: cliff-failure-mode-and-v1-defenses D3 inherited the `3-in-10 bypasses → design-review-recommended` rule from D1 (cliff-failure-mode-and-v1-defenses:82). D1's bypass domain is validator false-positives — naturally single-class. D3's bypass domain has three classes (slice-caused, pre-existing, false-positive). The threshold fired at `housekeeping/inv004-rebaseline` on three pre-existing-drift bypasses (`v1-defense-d3/automated-backstop` ruff debt, `v1-defense-d3/ruff-cleanup` parallel-session doc, `housekeeping/inv004-rebaseline` CC binary drift) — none of which were D3 false-positives. The warning text "gates producing more noise than signal" didn't match the situation; the actual signal was "carry-over debt is accumulating." Remedy landed as the `d3-bypass-classification` ADR (provisional): three-class reason schema; rolling window counts only `false-positive`.

**Rule for future defense-extension ADRs**: when reusing another defense's escape hatch, counter, or threshold, verify explicitly that the failure classes being counted are the same kind of thing. The surface rule (e.g., "3-in-10 → review") can be reused; the *semantic claim the warning text makes* must be re-checked against the new domain. "D1 uses this, so D3 can too" is not enough — the question is "does the counter measure what the warning says it measures, in the target defense's failure space."

**Anti-pattern signals**: "we'll reuse the D1 convention," "the rolling-window rule is proven," "3-in-10 is the standard threshold in this codebase." All three are internally plausible. None verify that the classes being counted are comparable across defenses.

**Mechanism**: this lesson names the pattern; the concrete remedy for D3 lives in the `d3-bypass-classification` ADR. Future defense-extension ADRs should re-run this check at Phase 3 (Adversarial Stress Test): if any mechanism is imported from another ADR, audit its assumption set against the new domain's failure classes.

## L-005: Parallelism substrate works; skill-level coordination is the actual tax

**Discovered**: 2026-04-16, during the manual Axis-B parallel dogfood run from `87ea8b5` through merge commit `b5a853e` + coord sweep `fc27e6d`. Four workers (A/B/C/D) each ran a full Phase 1→4 pipeline concurrently on separate worktrees + tmux windows + branches, all picked slice number 18 (legacy numeric-id scheme) independently, all merged into `feature/identifier-scheme` with per-merge reconciliation of 4–6 pipeline-substrate files. Full write-up: `.claude/plans/2026-04-16-dogfood-observations.md`.

**Pattern**: When a system gets its first real parallel-execution test, the framing question is usually "does the branching model hold?" In practice the substrate (worktrees, branches, merges, per-branch state) turns out to be robust — the predicted collision modes (parallel SLICE-ID claims, sweep-counter contention, sister-branch state conflicts at merge) resolve at merge time with bounded cost paid in pipeline-substrate files (`handoff.md`, `slice.yaml`, sweep notes, feature files) rather than code. **The unexpected cost is at the skill layer**: slash commands whose side-effects are prose-specified (the skill *says* "also flip status and write archive") execute them inconsistently under context pressure; bootstrap-autonomy contracts ("run X before stop") get verbally acknowledged but not executed. Debugging this is hard because each individual skill run looks plausible — the failure only shows up as a gap between what the protocol promised and what the tree reflects.

**Concrete instance**: The `/handoff` skill on worker A at P2, P3, and P4 boundaries reproducibly committed `handoff.md` + the handoff-commit but **skipped** flipping `slice.yaml` `status:` and **skipped** writing the `handoff-phase-N.md` archive. B's, C's, and D's `/handoff` invocations completed both side-effects correctly. Same skill, same bootstrap, same branch-structure — divergent side-effect execution. Independently, three of four workers (A at P2, B at P3, D at P2) stopped after their phase-commit and *recommended* running `/handoff` verbally rather than running it autonomously, breaking the "autonomous handoff before stop" bootstrap contract. The cost was real: ~5 minutes per manual nudge, multiplied by the 3 affected boundaries, plus the opportunity cost of the coord tracking which worker was stopped at what boundary. In parallel, the parallelism-v1 D2 prediction (parallel SLICE-ID + sweep-ID collision is safe at merge time) held cleanly across all four workers; merge reconciliation averaged ~5–10 minutes per merge for the 4–6 conflict files, zero content loss, with merges auto-resolving on code files and conflicting only on pipeline-substrate.

**Rule for future parallel-execution work**: when planning a multi-worker run, budget separately for (a) the branching/merge mechanics and (b) the skill-layer execution contracts the protocol relies on. (a) is predictable and bounded; (b) is the latent cost. Before spawning ≥3 concurrent workers, dogfood the `/handoff` + bootstrap-autonomy sequence on a single branch first and confirm every protocol-declared side-effect actually lands — if any step is prose-specified ("also write X", "run Y before stop"), either (i) make it a non-skippable step in the skill (code the action, not just describe it), or (ii) accept that coord must verify it post-hoc and budget the verification cost. The branching substrate is not where to focus pre-flight effort; the skill contracts are.

**Anti-pattern signals**: "the skill description is clear about what to do," "the bootstrap prompt tells the worker to auto-run /handoff — it will," "the parallel-execution risk is merge conflicts," "we validated /handoff on a single slice, it works." All four were internally plausible going into the dogfood. None prevented the observed gaps.

**Mechanism**: three follow-up slices drop out of this lesson — (a) harden `/handoff`: make `slice.yaml` status transition + phase-archive write non-skippable (code, not prose), covering `commands/claude-code/handoff.full.md`; (b) harden bootstrap-autonomy: either instruct "run /handoff before stop" more forcibly or wrap the worker lifecycle so `/handoff` fires on phase-commit detection; (c) add subagent-progress visibility so coord can detect stalls like the 28-minute A subagent block without needing to capture-pane. parallelism-v1 graduates `provisional → accepted` after (a) and (b) land; the "parallelism-native" vision (commitment #2) passes its first real execution gate with those hardenings in place. Full pain-point catalogue in `.claude/plans/2026-04-16-dogfood-observations.md` §8.

## L-006: Identifier renames are feature-scoped, not slice-scoped

**Discovered**: 2026-04-18, during the `feature/identifier-scheme` → `dev` merge protocol design (first feature→dev merge in cairn).

**Pattern**: A scheme-change that spans multiple artifact classes (ADRs, slices, features, tests, prose, hooks) cannot be done as a single slice. The first pass finds one class of residue; the second pass finds residue from a class the first pass didn't cover; the third pass finds prose references both earlier passes missed. Each pass is a real slice — not ceremonial — but the feature boundary is where the pattern *as a whole* is governable.

**Concrete instance**: identifier-scheme ran three sequential slices — `adr-rename-sweep` (ADR files), `slice-and-feature-rename` (slice + feature namespace), `doc-sweep` (residual prose). Each slice closed cleanly and its sweep found residue attributable to the next slice's scope. After `doc-sweep` closed, sweep #17 still flagged two test-schema residues, which motivated a queued fourth slice (`v1-defense-d3/bypass-log-hierarchical-slug`). Four passes, one feature.

**Rule for future `/decision` and `/start-slice` triage**: when the proposed change is an identifier or terminology scheme that touches multiple artifact classes, the triage step routes to a **new feature definition** — not directly to `/start-slice`. The feature's sub-slices are framed by artifact class; a sweep between slices surfaces residue for the next slice; a dedicated doc-sweep slice is expected, not optional. Attempting a single-slice rename either under-scopes (leaves residue) or over-scopes (busts phase-4 invariants).

**Anti-pattern signals**: "the rename is mechanical," "one slice will cover it," "it's just find/replace," "phase-4 integration can absorb the residue." All four were internally plausible before the work started; none prevented the three-slice cascade that actually happened.

**Mechanism**: recorded here as a pattern; the concrete procedure (what a scheme-change feature's slice-sequencing looks like) can be promoted to `commands/claude-code/start-slice.md` or a new `/plan-feature` flow if a second scheme-change feature reproduces the shape.
