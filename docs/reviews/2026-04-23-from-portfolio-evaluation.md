# Methodology Review — Adoption Evaluation from a Prospective Consumer

Source: evaluation session from `personal-portfolio` (2026-04-23)
Permission: full spec-v1.md read under the CLAUDE.md "adversarial review" carve-out
Audience: cairn maintainers / future cairn Claude sessions

## Context

The consuming project is an AI-adaptive portfolio website (FastAPI + Vite + React 19; hexagonal backend; currently mid-feature on FEAT-002 Agent Content Intelligence). It has a lightweight existing `.claude/skills/` layer (`catchup`, `handoff`, `plan`, `implement`, `review`, `adr`) modelled on `/catchup` as the anchor idea — which is what surfaced cairn for evaluation in the first place.

The question the evaluation answered: **is cairn worth adopting wholesale, partially, or not at all, for a solo portfolio project that is more structured than a CRUD app but is not safety-critical?**

This review is the feedback side of that evaluation, separated out and relayed here because none of it is about portfolio internals — it is about how cairn reads to a first-time consumer and which pieces survive cherry-picking.

## What was read (in the order read)

1. `README.md`
2. `CLAUDE.md`
3. `docs/vision.md`
4. `docs/spec-v1.md` (full, adversarial-review carve-out)
5. `docs/operational-reference.md` (full)
6. `commands/claude-code/{catchup,start-slice,handoff,decision}.md` (thin versions only)
7. `templates/handoff.md`
8. `checks/{scope-guard,reversibility-guard}.sh`
9. `docs/roadmap.md`, `CHANGELOG.md`
10. `docs/reviews/2026-04-11-from-rag-session.md` (to learn review format)

Not read: `.full.md` command variants, ADR bodies beyond titles, `scripts/{dogfood_evaluate,integration_gate,snapshot_diff,verify_handoff}.py`.

## Consumer-side verdict

**Partial adoption, cherry-picked; no symlink.**

Cairn's own spec §1 is explicit about scope — "not for simple software, for CRUD apps, prototypes, AI wrappers… the overhead is pure waste." The portfolio sits between those two poles: more structured than a wrapper (multiple ADRs already, hexagonal backend, walking skeleton across 9 slices) but solo, not safety-critical, and committed to one shippable increment per session. The four-phase-per-slice session split is the central bet of the methodology and is exactly what a solo non-safety-critical project should not pay for. Cairn's own `[ACKNOWLEDGED]` label on "ceremony fatigue" (spec §13) suggests half-adoption is worse than non-adoption — so the path is: take the pieces that stand on their own, leave the pieces that only pay off inside the full discipline.

### What the portfolio plans to port

| Cairn piece | Why it's portable | Integration cost |
|---|---|---|
| `checks/reversibility-guard.sh` (ADR append-only + destructive-op blocks) | Directly closes a known failure mode already captured in portfolio's memory as `feedback_adrs_immutable.md`. The hook turns a discipline-only norm into a mechanical wall. | Minutes. `jq` already present. |
| `checks/scope-guard.sh` | Portfolio's CLAUDE.md already has a "≤5 files or decompose" norm; scope-guard enforces it via intent envelope parsing. | Low. Requires introducing an `intent.md`-like envelope field into the portfolio's lighter planning shape. |
| `checks/reality-check.sh` | Free to add; marginal since portfolio has Biome + ruff in its own pipelines. | Trivial. |
| Handoff-as-pointer (150–400 token cap, four fixed sections, banned-reflection list) | The portfolio's current `STATUS.md` is diary-shaped — the most immediate context-budget win in the entire methodology. | Low. Rewrite one skill. |
| Tiered catchup (Tier 1 ≤5 reads, Tier 2 subagent with ≤200-word return) | Portfolio's catchup already reads ~5 things at Tier 1; the missing discipline is the subagent contract. | Low. |
| Role + anti-behavior labels (Reader / Skeptic / Builder / Auditor) on existing skills | Documentation-only. Gets role purity as naming discipline without requiring session boundaries. | Trivial. |
| `scripts/validate_architecture.py` | Forward/backward/staleness checks on `docs/architecture.md` ↔ ADRs. Catches dead references. | Low after the SLICE-001 symlink fix landed. |

### What the portfolio will not port

- **Four separate fresh sessions per slice.** The load-bearing bet of the methodology, calibrated for safety-critical work per spec §2 and §17. Not worth the ceremony cost for solo non-safety-critical work.
- **`/decision` 8 sub-phases per ADR.** Portfolio's ADR cadence doesn't need forced enumeration + adversarial stress test + independent-verification sessions per decision. The existing lighter `adr` skill suffices.
- **`.slice-system` symlink / submodule consumption.** Cairn is pre-v1 and mid-migration (identifier scheme, phase rethink, parallelism work). Coupling a consumer's tooling to a moving upstream creates drift risk. The portfolio will copy concrete files rather than link.
- **Integration sweeps every N slices.** Portfolio already runs full test suite (168 + 92) on every green; sweep bureaucracy without a failure mode the suite doesn't already cover.
- **Parallelism-native infrastructure.** Solo, one branch at a time. Zero value now.

## Findings relayed to cairn

Not blockers. Reading-order and new-consumer-friction observations that may be worth triaging.

### Finding 1 — `CLAUDE.md` audience split is ambiguous for first-time consumers

**File**: `CLAUDE.md` (whole file)

Cairn's `CLAUDE.md` is written for an agent working **inside cairn itself** (self-consumption via `.slice-system → .`). A first-time external consumer reading this file cannot tell whether rules like "Edit canonical paths only, never via `.slice-system/`" (safety-critical) apply to them or only to cairn maintainers. The same ambiguity affects the `brew install jq && uv tool install ruff` line — is that a prerequisite for consumers, or only for working on cairn?

Suggestion: split `CLAUDE.md` into two files, or add an explicit "Audience" block at top distinguishing `cairn-maintainer` rules from `cairn-consumer` rules. At minimum the `.slice-system/` stripping caveat (currently described as "scope-guard.sh:53 strips as a literal prefix") should be tagged as maintainer-only.

### Finding 2 — `README.md` lacks a reading order for new consumers

**File**: `README.md:31-36`

The README points at four docs (`vision.md`, `roadmap.md`, `spec-v1.md`, `operational-reference.md`) without an ordering. A new reader who opens `spec-v1.md` first (because its filename suggests "the spec") hits a 427-line document that explicitly declares itself "Layer 2, not auto-loaded" — which is only interpretable after reading `CLAUDE.md` or `operational-reference.md` first. The correct entry point for a consumer is `operational-reference.md`, per its own opening sentence.

Suggestion: add a three-line "Reading order" block to README:
```
1. README (you are here) — what cairn is, at a glance
2. docs/operational-reference.md — how to use cairn
3. docs/spec-v1.md — why cairn is shaped this way (pull in when needed)
```

### Finding 3 — Templates directory is a drop-off point for consumers copying the pattern

**File**: `templates/` (contains only `handoff.md`)

The roadmap marks "Template extraction — `intent.md`, `slice.yaml`, ADR frontmatter extracted to `templates/`" as "may-land-before-v1." For a consumer copying cairn's shape without symlinking, templates are exactly the part most valuable to copy — the prose-form specification in `operational-reference.md` §intent.md Template is useful but takes an extra reading pass to convert to a usable skeleton. This may be worth promoting above "may-land" to "must-land": a consumer's first action after deciding to adopt is almost always "give me the file to paste."

### Finding 4 — Phase Skill Guide table is the most portable idea and the hardest to find

**File**: `docs/operational-reference.md:87-96` (the "Phase-to-skill mapping" table)

The explicit mapping from cairn phase → Superpowers skill → how that skill's contract is bisected by the session boundary is one of the strongest packaged ideas in the whole methodology. Specifically, the observation that TDD's red-green cycle is structurally bisected — Skeptic commits RED+Verify RED without touching production code, Builder starts fresh and runs GREEN+REFACTOR from the tests alone — is a non-trivial adaptation that would be useful to projects that use Superpowers but don't (yet) want cairn's full discipline. Currently it's buried mid-file under a `### Phase-to-skill mapping` subheading.

Suggestion: either lift it to its own doc (`docs/phase-skill-mapping.md`) or highlight it in README as "If you use the Superpowers plugin, even partial cairn adoption has this payoff."

### Finding 5 — Handoff-as-pointer is the single most adoptable discipline, and it is easy to miss

**File**: `docs/operational-reference.md:210-227`, `templates/handoff.md`

The Context Discipline Protocol's Layer 1 (handoff is a pointer, not a payload; 150–400 token budget; four fixed sections; explicit banned-sections list) is small, self-contained, and measurably reduces per-session context consumption. It does not depend on the four-phase pipeline, the decision protocol, the hooks, or the substrate validator. Any project with a session-end note can adopt it tomorrow.

Suggestion: consider making this its own promotional artifact — a `docs/adoptable-disciplines.md` listing the pieces of cairn that stand alone, with handoff-as-pointer, tiered catchup, and role-label documentation as the three entries most likely to land in consumer repos without any of the structural commitments.

## Open questions cairn may want to track

1. **Minimum-viable-cairn consumer path.** Is there an intended subset of cairn that a consumer can adopt without the four-phase session split? If yes, it is not currently named anywhere. If no, that is worth saying in README to set expectations.
2. **Reviews directory convention.** This file extends the convention `docs/reviews/2026-04-11-from-rag-session.md` established. The earlier review's own triage note asks whether that convention holds; this file's existence answers "yes" but there is no canonical statement of it.
3. **Role labels without session boundaries — is that legal?** Cairn's `phase-lock-and-role-declaration` ADR ties the role to the phase and the phase to the session. A consumer that wants to adopt the role *labels* without the session *boundary* is operating outside the design. Is that a soft-adoption path cairn wants to endorse, discourage, or leave silent?

## Summary for cairn

Cairn's strongest pieces (handoff-as-pointer, the three hooks, the architecture validator, the Phase Skill Guide) are more portable than the documentation currently promotes. Its weakest adoption friction is reading-order and audience ambiguity for a first-time consumer, not the methodology itself. One prospective consumer has chosen partial, copy-based adoption over symlink consumption — the copying is not a rejection of the methodology; it is a hedge against a pre-v1 upstream still reshaping its own substrate.
