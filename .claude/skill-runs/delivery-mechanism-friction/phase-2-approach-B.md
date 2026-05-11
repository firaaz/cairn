# Phase 2 — Approach B: Friction-down

## One-paragraph statement

Land `using-cairn` SessionStart skill (#33-1) as the next slice and nothing else. The consumer-side floor stays at `jq` + `ruff` + `python3` — no Pyright, no ast-grep, no `ENABLE_LSP_TOOL=1`, no user-scope superpowers. Discoverability is a substrate-cost problem, not a consumer-cost problem: cairn pays it once per session via a small, progressive-disclosure injection that points at canonical surfaces (CONSUMER.md, slash commands, dispatch entry point, envelope semantics, gate behavior). `feature/workflow-subagents` is set aside; capability gains from `pytest-triage` / `root-cause-hunter` / cross-worktree readers are deferred until the substrate-as-pointer model has been measured against actual onboarding traces. `handoff-closer` is the only branch artifact even considered for cherry-pick, because it is the only one that reinforces substrate (commit hygiene) rather than adding setup surface.

## Concrete shape (what actually lands)

- **`using-cairn` SessionStart skill** lives at `dist/skills/using-cairn/SKILL.md` (cairn-canonical path: `.claude/skills/using-cairn/SKILL.md`), shipped via the existing `dist/` payload per `m5-plugin-distribution-and-symlink-retire` D3. Wired through `dist/hooks/hooks.json` as a `SessionStart` hook entry (the same registration channel D4 uses for PreToolUse/PostToolUse), invoking the Skill tool with `using-cairn`. No consumer `.claude/settings.json` merge.
- **What it injects (Tier-1, pointer-not-payload, hard budget ≤2000 tokens against INV-004's 40k ceiling):**
  - One line: "this is a cairn-using repo; substrate is the four-phase TDD pipeline + ADR governance + operator envelope."
  - Slash-command surface as a name list with one-line each: `/cairn-tdd-feature`, `/catchup`, `/decision`, `/new-adr` (skip `.full.md` siblings; those load on demand per soft-constraint #1).
  - Dispatch entry point: literal invocation string `/cairn-tdd-feature docs/plans/<id>.md`.
  - Envelope concept: one paragraph — "if `.claude/active-envelope.yaml` exists with `mode: operator`, writes are gated to `paths:` regex; malformed YAML fails closed."
  - Gate behavior: "hooks enforce role isolation, append-only ADRs, force-push policy; missing `jq`/`ruff` silently no-ops — install both."
  - Pointer-out: "load `CONSUMER.md` for install/quickstart; load `docs/operational-reference.md` for command reference; load `docs/spec-v1.md` for theory."
- **Superpowers SessionStart composition (S2 mitigation):** the skill detects `superpowers` presence via a filesystem probe (`~/.claude/plugins/superpowers/` or equivalent marker); when present, it injects only the cairn-specific delta and emits a one-line note that superpowers methodology citations apply via `docs/phase-skill-mapping.md`. When absent, it injects the same delta plus a one-line hint that superpowers is optional. No double-load of methodology framing in either branch.
- **Branch cherry-picks:** none in this slice. `handoff-closer` is the *only* candidate considered, and only if it can land as a pure substrate-hygiene agent (commit-staging discipline, no `-A`, no `--amend`, no commit-to-dev/main, no push) with zero new deps and zero superpowers cites. If those conditions hold, it lands as a second commit in this slice; otherwise it defers. All other branch agents (`slice-status`, `worktree-map`, `adr-context`, `pytest-triage`, `root-cause-hunter`) defer to a future slice gated on measured onboarding evidence and an explicit deps ADR.
- **New consumer-side requirements:** **zero.** Floor stays `jq` + `ruff` + `python3` exactly as `CLAUDE.md:13-15` documents. No PREREQS.md ships.
- **ADRs this approach commits:** one ADR, `delivery-mechanism-friction`, with three decisions: D1 setup-surface direction is *down* (status quo floor is the cairn position); D2 SessionStart is the discoverability vehicle, governed by a token budget enforced in CI; D3 external-plugin coupling defaults to *no-cite* in cairn-shipped agents (methodology mapping stays in `docs/phase-skill-mapping.md` as operator-facing prose, not agent-prompt-embedded dependency).
- **Out-of-scope-for-this-slice (from #33's 7 candidates):** #2 slash-command discoverability beyond the SessionStart name-list, #3 role_guard heredoc escape removal, #4 `/fix-adr-typo`, #5 id+name scope narrowing, #6 small-change path, #7 commit-prefix-vs-JSON-stdout. Each defers to its own slice with its own constraint check.

## Constraint fit (against Phase 0 hard + soft constraints)

| Constraint | Fit | Evidence |
| --- | --- | --- |
| H1 phase-pipeline shape locked | FIT | SessionStart injects pointers at the four phases; does not modify count/names/roles. |
| H2 plugin distribution locked to release-branch + marketplace | FIT | Skill ships via `dist/`, registered via `dist/hooks/hooks.json` per D4; no install-mechanism change. |
| H3 maintainer dogfood loop intact | FIT | No new indexer/LSP deps means `.slice-system → .` symlink-recursion hazard is not enlarged (CLAUDE.md §Safety-critical rules). |
| H4 role isolation fabrication-blocking | FIT | No agent-prompt or hook changes to role_guard; SessionStart injection is operator-context, not agent-write-path. |
| H5 ADRs append-only | FIT | One new ADR drafted via `/new-adr`; no supersession; consequence section documents reversal cost per S8 mitigation. |
| H6 Conventional Commits binding machine-checkable | FIT | SessionStart skill's slice lands via `feat:` prefix; `_FALLBACK_REGISTRY` unchanged. |
| H7 session-start context ≤40k | FIT (budgeted) | ≤2000-token cap on the SessionStart injection is explicit; CI check measures actual emit and fails on regression (S1/S9 mitigation). |
| H8 handoff context discipline three tiers | FIT | Injection is Tier-1 pointer; CONSUMER.md / operational-reference / spec-v1 stay Tier-2 on-demand. Mirrors `context-discipline-protocol`. |
| Soft #1 progressive disclosure | FIT | SessionStart emits names + one-liners; `.full.md` and prose docs load on explicit request. |
| Soft #2 audience-tagged CLAUDE.md / CONSUMER.md | FIT | No change to either; SessionStart points at them. |
| Soft #3 new deps require ADR | FIT | Zero new deps. |
| Soft #4 structural > prompt enforcement | FIT (with caveat) | SessionStart is itself prose-injection; mitigated by being a *pointer* to structural enforcement (hooks, role_guard) already in place. |
| Soft #5 minimize setup ceremony | FIT | Setup ceremony unchanged. |
| Soft #6 bootstrap autonomy | FIT | SessionStart auto-fires; no operator step required. |

## Pre-mortem exposure (against Phase 1 S1–S10)

- **S1 context-budget breach:** HANDLED. ≤2000-token cap + CI measurement; setup-surface stays at status quo (no PREREQS.md, no eager agent preambles).
- **S2 SessionStart collision with superpowers:** HANDLED. Filesystem-probe + delta-only injection (see Concrete shape).
- **S3 auto-routed agents false-fire cross-repo:** HANDLED. No auto-routed agents land; no cross-repo dispatch surface introduced.
- **S4 superpowers drift cascades into cairn agents:** HANDLED. D3 commits to no-cite; methodology mapping is operator-facing prose in `docs/phase-skill-mapping.md`, not an agent dependency.
- **S5 INV-011 dogfood breakage from setup-surface-up:** HANDLED. No Pyright/ast-grep/LSP added; `.slice-system` recursion surface unchanged.
- **S6 PREREQS.md shifts friction rather than reducing it:** HANDLED. No PREREQS.md ships; install surface unchanged.
- **S7 per-worktree LSP daemons stack memory:** HANDLED. No LSP enablement.
- **S8 reversibility cost of ADR-locking superpowers:** HANDLED. ADR commits to *no-coupling* default; superseding to add coupling later is a forward decision, not an entanglement to unwind. ADR consequences section documents what a reversal (adding setup surface back) would require.
- **S9 SessionStart skill ballooning past INV-004:** PARTIAL. Token cap + CI check addresses ratchet, but progressive disclosure discipline is a recurring vigilance cost; D2 names the budget as a load-bearing invariant on the skill, but enforcement depends on the CI check being maintained. This is the weakest exposure.
- **S10 operators never learn surface because auto-routing hides it:** HANDLED. No auto-routing; SessionStart explicitly names the slash-command surface so operators see what exists.

## Downstream impact

- **`parallelism-v1` workflow:** unchanged. No new per-worktree daemon cost (S7); SessionStart fires per session regardless of worktree count and is bounded.
- **`m5-plugin-deployment-pattern` release surface:** one additional `dist/skills/using-cairn/` directory + one additional hook entry in `dist/hooks/hooks.json`. F3 audit check 9 (manual end-to-end install per D9) gains one verification step: confirm SessionStart fires on consumer-side first session.
- **Consumer time-to-first-dispatch (J1 in Phase 0.5):** collapses from ~20 min prose-reading to a single auto-briefing on session open + targeted Tier-2 reads. J1's highest-friction transition #1 is the primary target.
- **Returning-operator experience (J2):** SessionStart re-injects every session, so the J2 step 2 cold-start ("model has no context") becomes warm-start by default. `/catchup` (when it ships M5.1) still does the deeper handoff read; SessionStart and `/catchup` compose because SessionStart is pointer-only.
- **Maintainer dogfood loop (INV-011):** unchanged. `.slice-system → .` recursion surface unchanged; no new indexers.
- **Future slices:** *opens* — every other #33 candidate (2–7) and every deferred branch agent becomes a separately-considered slice with its own constraint check, rather than being bundled into a single decision. The ADR's no-cite default makes the future "do we adopt superpowers as a hard dep" a clean re-decision rather than an entrenched assumption.

## Evidence (not memory)

- INV-004 40k budget: `docs/ARCHITECTURE.md:51`, Phase 0 §Invariants.
- INV-011 dogfood loop + symlink hazard: `docs/ARCHITECTURE.md:91`, `CLAUDE.md §Safety-critical rules`, Phase 0 §Invariants H3.
- INV-012 distribution locked: `docs/ARCHITECTURE.md:99`, Phase 0 H2.
- Plugin payload + hooks.json mechanism: `m5-plugin-deployment-pattern` D4, Phase 0 §Marketplace.
- `.slice-system → .` recursion hazard: `CLAUDE.md §Safety-critical rules`, Phase 1 S5.
- L-005 prompt-enforcement drift: Phase 0 §Lessons, Phase 1 cross-cutting.
- L-020 non-skippable steps need code: Phase 0 §Lessons, Phase 1 S6.
- J1 highest-friction transition #1 (~20 min prose): Phase 0.5 §Highest-friction transitions #1.
- J1 step 3 no SessionStart wired: Phase 0.5 §Verified.
- `context-discipline-protocol` three-tier: Phase 0 §ADRs.
- Soft-constraint #1 progressive disclosure: Phase 0 §Soft constraints.
- Soft-constraint #3 new deps require ADR: Phase 0 §Soft constraints; `cairn-substrate-and-fastmcp` D2.
- Branch facts (PREREQS.md, 6 agents, superpowers cites): framing §Branch facts, Phase 0.5 §Verified.

## Why this approach beats the alternatives (steelman)

- **A takes a measured-friction problem and answers with unmeasured-friction.** Phase 0 explicit-gap #2 and #4 establish that the magnitude of setup-pain is not measured *and* the Pyright/ast-grep/superpowers capability/friction trade is not evaluated. A ships the answer before the question is quantified; B answers the *measured* gap (J1 #1, ~20 min prose, zero SessionStart) with the minimum-surface fix and leaves capability investments for after evidence.
- **B is the only direction that does not enlarge `.slice-system` recursion surface (INV-011, S5).** Any LSP / indexer dep follows the maintainer symlink loop; cairn's own safety rule already calls this out. B sidesteps the hazard entirely.
- **B's reversibility cost is near-zero; A's is sticky (S8).** A commits cairn to user-scope deps with install-time state on consumer machines that does not auto-uninstall on supersession. B commits cairn to a *removal* of an unbuilt thing — trivially reversible.
- **B respects soft-constraint #3 without ADR ceremony.** A requires an ADR to justify new consumer deps and inherits its own supersession cost; B's ADR is the *absence* of new deps, which is a cheaper commitment.
- **B preserves operator surface visibility (S10).** Auto-routed agents hide the methodology; SessionStart-with-name-list teaches the surface. Discoverability that operators can later invoke by name is more durable than discoverability that fires invisibly.

## What this approach asks the operator to accept

- **No diagnostic capability gain this slice.** `pytest-triage` and `root-cause-hunter` defer; J5 (pytest-fail → root-cause) stays manual until a future slice produces measurement that justifies the setup surface.
- **No cross-worktree readers this slice.** `slice-status`, `worktree-map`, `adr-context` defer; J2 step 3 mid-slice resumption still requires `/catchup` (when it ships) plus operator-driven git inspection.
- **The `feature/workflow-subagents` branch sits unmerged.** 1 commit, +334 LOC of work is parked. The operator accepts that the branch's hypothesis ("capability gain is worth setup-surface cost") is unfalsified rather than wrong — and that confirming or rejecting it requires evidence not yet collected.
- **SessionStart-budget vigilance is a recurring maintainer cost.** S9 is the standing exposure; the CI check must be maintained and the discipline of pointer-not-payload must be enforced on every future addition.
- **Discoverability gain is real but bounded.** SessionStart points at canonical surfaces; it does not summarise them. Operators still need Tier-2 reads of CONSUMER.md / operational-reference for substantive use.
