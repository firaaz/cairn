---
id: delivery-mechanism-friction
name: Delivery-mechanism friction — SessionStart pointer + reworked nav agents, deferred diagnostics
status: accepted
firmness: provisional
date: 2026-05-11
topic: architecture
invariants-touched: [INV-004, INV-011, INV-012]
supersedes: null
superseded-by: null
---

# delivery-mechanism-friction: Delivery-mechanism friction — SessionStart pointer + reworked nav agents, deferred diagnostics

## Status

Accepted (post-`/decision` Phase 3 adversarial stress test, 2026-05-11; operator-selected C-with-corrections over runner-up B after full A/B/C enumeration). Phase 5 independent verification not required for a provisional ADR; revisit if/when promoted to firm.

## Date

2026-05-11

## Context

Issue #33 ("Reduce incidental friction in delivery mechanism, keep enforcement substrate") and branch `feature/workflow-subagents` (commit `8b680cb`, +334 LOC, unmerged) arrived the same day. The branch ships six auto-routed workflow subagents under `agents/` plus `docs/PREREQS.md` (Pyright + ast-grep + `ENABLE_LSP_TOOL=1` + user-scope `superpowers` + Ruff). The issue lists seven friction-reduction candidates, with `using-cairn` SessionStart bootstrap skill called highest-leverage.

The two artifacts pulled in opposite directions: the branch grows consumer setup-surface in exchange for in-session capability; the issue argues setup-surface should shrink because cost is paid per-machine on every adoption. INV-012 + `m5-plugin-deployment-pattern` (firm, 2026-05-09) lock the *distribution* mechanism (release-branch + marketplace) — so the decision is about setup-surface and discovery within that distribution, not about distribution itself.

Phase 0.5 verified one friction concretely: J1 step 3–5 (fresh consumer → first slice dispatched) costs ~20 minutes of out-of-band prose reading because no `SessionStart` hook is wired in the shipped plugin. Every other claim — that Pyright/ast-grep/superpowers is worth the install ceremony, that auto-routed subagents are a better discovery mechanism than slash commands, that all six branch agents share one substrate-friendly posture — is asserted by the branch author, not measured against onboarding traces.

Phase 3 adversarial pass falsified two load-bearing claims in the leading candidate (C): the four nav agents auto-fire on phrase triggers in their `description:` frontmatter (contradicting "no auto-routing this slice"), and the CI token-budget check the convergence note relied on has no precedent in `.github/workflows/`. Five additional cracks (ast-grep cite in `adr-context`, missing substrate pre-flight, agent-name collision risk, deferral with no trigger, F3 audit surface understatement) required correction before C could lead.

Full decision context: `.claude/skill-runs/delivery-mechanism-friction/` (framing.md, phase-0-constraints.md, phase-0.5-journey.md, phase-1-pre-mortem.md, phase-2-approach-{A,B,C}.md, phase-2-convergence-note.md, phase-3-adversarial.md, phase-3-corrections-applied.md).

## Decision

### D1 — SessionStart bootstrap as pointer, not payload

Ship `using-cairn` SessionStart skill at `dist/skills/using-cairn/SKILL.md`, registered via `dist/hooks/hooks.json` per `m5-plugin-deployment-pattern` D4. Injection is **pointer-only**, hard-budgeted ≤2,000 tokens. Content: one-line substrate description, slash-command name-list with one-line each (no `.full.md` siblings), dispatch entry point literal, envelope-mode paragraph, gate-behavior paragraph, pointers to CONSUMER.md / operational-reference / spec-v1 for Tier-2 reads. Mirrors `context-discipline-protocol` three-tier shape: SessionStart is Tier-1 pointer, not summary.

### D2 — SessionStart composes with superpowers, never double-loads

`using-cairn` MUST detect a `superpowers` presence (filesystem probe of `~/.claude/plugins/superpowers/` or equivalent marker) and emit only the cairn-delta when superpowers SessionStart already injects methodology framing. Integration test against a clean Claude Code session with both plugins installed is an F3 audit acceptance gate; the slice does not ship without it passing.

### D3 — Four nav agents ship, with substrate pre-flight, under `cairn-*` namespace

Ship a reworked subset of `feature/workflow-subagents`:

- `cairn-slice-status` (renamed from `slice-status`)
- `cairn-worktree-map` (renamed from `worktree-map`)
- `cairn-adr-context` (renamed from `adr-context`)
- `cairn-handoff-closer` (renamed from `handoff-closer`)

Required modifications applied in-slice before merge:

- (D3.a) Every agent body opens with a cairn-substrate pre-flight: refuse cleanly (no-op + brief stderr hint) when `.claude/active-envelope.yaml` AND `docs/ARCHITECTURE.md` are both absent. This mitigates S3 + S11 (auto-routing trigger phrases like `"status?"` colliding with operator's natural English in non-cairn worktrees).
- (D3.b) `description:` auto-routing triggers are retained. The slice acknowledges auto-routing as the discovery surface for these four agents — but the agents fail closed in non-cairn contexts. No claim of methodology superiority over slash commands is asserted.
- (D3.c) All four agent prompts strip every external-tool cite (Pyright, ast-grep / `sg`, LSP, `superpowers:*`). `cairn-adr-context` specifically falls back to built-in `Grep` only.

### D4 — Diagnostic two and PREREQS.md are deferred, with a dated trigger

`pytest-triage`, `root-cause-hunter`, and `docs/PREREQS.md` do NOT ship in this slice. They remain on `feature/workflow-subagents` unmerged. A future slice — provisionally named `cairn-diagnostics-with-detection` — owns the contested decisions (auto-routing strategy for diagnostics, `superpowers:systematic-debugging` cite-strength, `.slice-system` LSP exclusion, per-worktree daemon ceiling, version-floor pin).

**Trigger condition (operationally binding):** open `cairn-diagnostics-with-detection` by **2026-09-01** OR after **three operator-field-notes entries** citing J5-style pytest-debug pain that the deferred agents would have collapsed, whichever comes first. If 2026-09-01 passes with no entries, the trigger fails closed: the deferred two agents are honestly closed-as-wontfix and removed from the branch.

### D5 — No hard external-plugin dependency in cairn-shipped agents this slice

No agent shipped in cairn's main payload carries a hard methodology-gate cite to `superpowers:*` or any other external plugin. Cite-strength for the deferred diagnostic two is owned by the `cairn-diagnostics-with-detection` ADR. This is the substrate-shape commitment that makes the diagnostics slice a clean re-decision rather than an entrenched assumption.

### D6 — SessionStart token-budget enforcement

A CI token-budget check on the `using-cairn` SessionStart payload is included as in-slice work, either as a new workflow (`sessionstart-budget.yml`) or as a step merged into `dist-gate.yml`. If the check cannot land in-slice, this ADR's consequences section is updated (via `ADR_EDITORIAL_FIX=1`) to demote S9 from PARTIAL to EXPOSED and to acknowledge L-005 drift exposure as the standing risk.

## Consequences

### Easier

- **J1 first-slice friction collapses from ~20 min to ~3 min** (Phase 0.5 highest-friction transition #1) via SessionStart auto-firing on session-open. Verified at slice acceptance via the F3 audit check 9 manual install.
- **J2 returning-operator cold-start improves** — SessionStart re-injects every session, so the model has cairn-context without operator-prompting. Composes with `/catchup` (M5.1) for deeper handoff reads.
- **J3 ADR-context harvest automates** via `cairn-adr-context` invokable from SessionStart pointer or by phrase trigger. Reduces /decision Phase 0 manual effort.
- **Substrate hygiene gains automation** via `cairn-handoff-closer` encoding stage-by-name, no-`-A`, no-`--amend`, no-commit-to-dev/main/master, no-push as a single dispatch.
- **Cross-worktree state becomes legible** via `cairn-worktree-map` + `cairn-slice-status`, serving `parallelism-v1` workflows directly.
- **Future slices stay clean** — deferring diagnostics + PREREQS leaves the contested decisions (auto-routing cite-strength, `superpowers` coupling, LSP setup surface) for a slice that can answer them with evidence rather than assertion.

### Harder

- **One ADR locks in early.** This slice commits to: SessionStart-is-pointer (D1), no-hard-external-plugin-dep (D5), namespace prefix `cairn-*` (D3), substrate pre-flight on every shipped agent (D3.a). Superseding any of these requires a future ADR; cheaper than A's commitments but not zero.
- **SessionStart drift (S9) is a standing exposure.** Token-budget vigilance is recurring maintainer cost; mitigated by the CI check (D6) or accepted as EXPOSED in the consequences fallback. Cannot be made fully structural without a hard byte cap that may force ugly trade-offs in 6 months.
- **F3 audit surface is materially larger than B.** Five shipped artifacts (SessionStart + 4 agents) vs. one. Each agent prompt + its auto-route trigger + its pre-flight guard adds an F3 acceptance subcheck. Honest cost of choosing C over B.
- **The branch sits in limbo for 2/6 of its agents.** `pytest-triage` and `root-cause-hunter` remain on `feature/workflow-subagents` unmerged pending the dated trigger (D4). If 2026-09-01 passes with no field-note evidence, the trigger fails closed and the work is honestly retired.
- **Highest-leverage claim is accepted as hypothesis the slice tests, not as verified.** Phase 0.5 verified J1 friction is real but did NOT verify that SessionStart is the *highest-leverage* response among unenumerated alternatives. If shipped SessionStart does not visibly collapse J1, a follow-up /decision revisits — no SessionStart-payload accretion as a workaround.

### Reversal cost

Provisional firmness. Reversal of D1–D6 requires a superseding ADR. SessionStart payload retirement is mechanical (one skill file + one hooks.json entry); the four nav agents retire by removing from `dist/agents/` and bumping plugin.json version. No sticky consumer-machine state (no installed external deps, no user-scope plugin requirements introduced). Reversal of D4's deferral trigger is structurally honest — either the diagnostics slice opens, or the deferred agents close-as-wontfix.

## Alternatives Considered

### Approach A — Capability-up (rejected as leader; remains a future option)

Merge `feature/workflow-subagents` substantively as-is. PREREQS.md adds Pyright + ast-grep + `ENABLE_LSP_TOOL=1` + user-scope superpowers. All six agents ship.

**Why rejected:** Pre-mortem scored 5/10 HANDLED with 1 EXPOSED (S7, per-worktree LSP daemons stacking 600MB–1GB across 4–6 concurrent worktrees). Two load-bearing claims unverified: (a) capability gain worth setup-surface cost (S7 cost-side never measured), (b) auto-routed subagents better than slash-command discovery (counter-argued by S10). Locks cairn into sticky external-plugin coupling (S8) on the basis of unvalidated capability claims. Full analysis: `.claude/skill-runs/delivery-mechanism-friction/phase-2-approach-A.md`.

A remains a candidate for `cairn-diagnostics-with-detection` if the dated trigger (D4) fires.

### Approach B — Friction-down (close runner-up)

Ship `using-cairn` SessionStart skill alone. Defer the entire branch. Consider `handoff-closer` cherry-pick only if it can land with zero new deps and no external cites.

**Why rejected as the chosen slice:** Pre-mortem scored 9/10 HANDLED, 1 PARTIAL (S9) — strongest exposure profile. But B leaves three friction transitions un-addressed (J2 mid-slice resumption, J3 manual ADR-harvest, cross-worktree state visibility) that the four navigational agents close at zero new-dep cost. Phase 3 §"Steel-man for B" makes the strongest counter-case: C is scope-creep dressed as synergy. Operator weighed this and chose to absorb the three additional friction-closures into the slice, accepting the larger F3 audit surface as honest cost.

B remains the fallback if Phase 5 independent verification (if/when this ADR is promoted to firm) overturns any D1–D6 commitment. Full analysis: `.claude/skill-runs/delivery-mechanism-friction/phase-2-approach-B.md`.

### Approach C-as-written (corrected, but the uncorrected version was rejected by adversarial pass)

Original C: same shipping shape as accepted C, but with explicit claim of "no auto-routing this slice" and "nav agents have no contested decisions."

**Why rejected:** Adversarial Phase 3 falsified both claims by reading the branch artifacts directly. The accepted C-with-corrections (D1–D6 above) is the same shipping shape with the contested decisions encoded normatively in the ADR rather than waved away. Full analysis: `.claude/skill-runs/delivery-mechanism-friction/phase-3-adversarial.md` and `phase-3-corrections-applied.md`.

## Risk Register

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R1 | S9: SessionStart payload accretes past 2k tokens | Medium | Medium (INV-004 budget pressure) | D6 CI check; failure-mode = honest demotion to EXPOSED in this ADR's consequences |
| R2 | S11: `cairn-*` agents misfire in non-cairn worktrees | Medium (cairn at user scope) | Low (substrate pre-flight makes failure silent) | D3.a substrate pre-flight; F3 audit verifies clean no-op in non-cairn dir |
| R3 | S13: D4 trigger fires never, diagnostic two die unmerged | Medium | Low (branch work is preserved; honest closure) | D4 dated 2026-09-01 fallback; failure-mode = explicit close-as-wontfix |
| R4 | Phase 0.5 J1 highest-leverage claim is wrong | Low | High (slice does not collapse the friction it ships against) | If SessionStart does not collapse J1 friction within 30 days of shipping, open a follow-up /decision; do NOT accrete more SessionStart payload as a workaround |
| R5 | F3 audit surface is materially larger than estimated | Low | Low (one-time slice cost) | Accept honestly per Consequences §Harder |
| R6 | S12: agent-name collision with future Claude Code / superpowers additions | Low (cairn-prefix is uncommon) | Medium (silent wrong-dispatch) | D3 `cairn-*` namespace prefix applied in-slice |

## Invariants touched

- **INV-004** (fresh-session ≤40k tokens): D1's ≤2,000-token budget for SessionStart is the additive cost; D6's CI check is the enforcement. Net headroom remains substantial.
- **INV-011** (maintainer dogfood loop intact): unaffected — no LSP/indexer added, so `.slice-system → .` recursion surface is unchanged.
- **INV-012** (release-branch + marketplace distribution): unaffected — slice ships via `dist/` curation per `m5-plugin-deployment-pattern` D3.

No invariant requires modification. The slice operates within the existing invariant set.
