# Phase 2 — Forced Enumeration

Three genuinely viable approaches, each developed in depth by a parallel
Plan agent with file-evidence citations. Full per-approach analyses in this
file's referenced section; comparison table at the end.

---

## Approach A1 — Status Quo Hardened

**Identity:** "high-consequence four-phase methodology" (status quo, per
`docs/spec-v1.md:25-29`).

**Core idea.** The named failures on `dev` are not identity drift — they
are doc gaps (S1), mechanical Trial-A debt (failing tests, INV-002 binding),
and a single missing ADR contract-grammar clause (Trial B). Fix surgically.

**Concrete moves:**
1. Add "three legitimate paths" section to `docs/operational-reference.md:19-29`
   naming ad-hoc / /decision / cairn-tdd-feature as co-equal.
2. Close INV-002 `binding-effective-from: <pending-slice-close-sha>` with
   Trial-A landing SHA.
3. Rebaseline the 5 failing tests (Trial-A completion mechanical work).
4. Amend ADR contract grammar (`docs/adr/identifier-scheme.md:6-22`) with
   `execution-scope:` field alongside existing `must-satisfy/...`.
5. spec-v1 §1 unchanged.

**Honest weakness:** Documents the bypass as legitimate but does nothing to
change the empirical signal — if `cairn-tdd-feature` utilization stays low,
the machinery rots regardless. Trial B's lesson may need broader contract
restructure than one clause.

---

## Approach A2 — Adaptive Tier Model (Direction-Doc Pole B)

**Identity:** "adaptive reliability layer for AI-assisted development."
spec-v1 §1 amended.

**Core idea.** Four tiers (0 hygiene / 1 scoped / 2 contracted / 3 formal),
deterministic risk scorer, hard-overrides for security/irreversible/invariant/
incident. Tier 3 = current four-phase preserved byte-for-byte.

**Concrete moves:**
1. New ADR `adaptive-reliability-tiers`, firmness: provisional. Carries a
   partial supersession of INV-003 phrasing ("every slice" → "every Tier-3
   slice").
2. `scripts/assess_risk_tier.py` — stdlib + pyyaml. Nine triggers from
   direction doc lines 158-176 + four hard-overrides at 178-182. Advisory;
   break points env-var-overridable.
3. `templates/task-contract.yaml` — Tier-1/Tier-2 lightweight contract.
4. Per-tier `.claude/active-envelope.yaml` schema extension; `role_guard.py`
   relaxes enforcement at lower tiers; Tier 3 path byte-identical to today.
5. `docs/spec-v1.md:23-29` amendment — drop "not for simple software"
   absolutism; keep §2 Core Thesis verbatim.
6. `docs/operational-reference.md:1-29` rewrite to tier-selection-first;
   existing per-phase guides move under "Tier 3 reference."
7. `docs/ARCHITECTURE.md` INV-003 — add `binding-effective-from` partial
   supersession.

**Honest weakness (from own analysis):** "The pivot solves a problem the
operator has (S1) by importing problems the operator does not have (I2, I3,
S2). A minimal alternative — formalize the three existing execution paths as
named modes *without* a fourth tier above or hygiene tier below — would
address S1 with strictly less surface area." This points back at Approach 3.

---

## Approach A3 — Infrastructure Identity, Methodology as Named Preset

**Identity:** "governance infrastructure for AI-assisted development" —
hooks, validators, append-only ADRs, handoff contract, identifier scheme,
role guards, plan-doc shape. Four-phase TDD is **one named preset**.

**Core idea.** Leverage Phase 0.5's orthogonality finding (`phase-0.5-journey.md:120`):
all three poles can drop the four-phase machinery without breaking hooks,
invariants, or handoff — they are orthogonal. So the durable spine IS the
infrastructure, not the methodology. Name the three existing de facto paths
as presets: `ad-hoc | contracted | formal`. No tiers, no scorer, no spec
amendment.

**Concrete moves:**
1. New ADR `cairn-identity-infrastructure-and-presets`, firmness: provisional.
   Declares infrastructure is identity; methodology is preset. Sits beside
   `phase-lock-and-role-declaration` (no supersession).
2. `docs/operational-reference.md:19-29` rewrite naming the three presets;
   operator-declared, not scored.
3. `docs/spec-v1.md:25-29` UNCHANGED.
4. **Optional** `/preset <name>` slash command at
   `commands/claude-code/preset.md`; writes session marker, used by
   `/catchup` for display. Hooks do NOT branch on it. If too much
   ceremony, omit and ship as doc-only.
5. No changes to `phase-lock-and-role-declaration.md`,
   `.claude/skills/cairn-tdd-feature/SKILL.md`, `.claude/agents/phase-*-tdd.md`,
   `checks/*`, or `scripts/validate_architecture.py`.

**Honest weakness (from own analysis):** "This is rebranding, not redesign…
If documentation alone solves the identity question, **Approach 1 (doc-only,
no ADR) does it cheaper**." What naming buys is (a) append-only commitment
via the ADR being protected by `reversibility-guard.sh`, (b) refusal-
vocabulary for future tier proposals, (c) explicit retirement path for
`formal` if it ever needs to go. Whether that's worth one ADR is the live
question.

---

## Comparison table

| Aspect | A1 — Status Quo Hardened | A2 — Adaptive Tiers | A3 — Infra Identity + Presets |
|---|---|---|---|
| **Identity claim** | Methodology IS the identity | Reliability layer IS the identity | Infrastructure IS the identity; methodology is one preset |
| **spec-v1 §1 (scope)** | Unchanged | Amended (one-way door) | Unchanged |
| **`phase-lock-and-role-declaration` (firm)** | Preserved | Partial supersession of INV-003 phrasing | Preserved |
| **New artifacts** | 0 ADRs, doc edits + test fixes + 1 contract field | 1 ADR + 1 script + 1 template + role_guard ext + spec amend + ops-ref rewrite | 1 ADR + ops-ref edit (+ optional slash cmd) |
| **Mechanical enforcement change** | None (one new contract field) | Per-tier hook relaxation at Tiers 0-2 | None |
| **Risk scorer** | No | Yes (defensible-a-priori; break points env-var) | No |
| **T1 (tier misclassification)** | Avoided (no tiers) | Partial mitigation (hard-overrides + commit-trailer audit; ambiguous cases still leak) | Avoided |
| **T2 (uncalibrated scorer)** | Avoided | Partial mitigation (triggers a-priori-defensible; break points TBD) | Avoided |
| **T3 (hook discoverability)** | Avoided (no à la carte) | Avoided | Avoided |
| **S1 (bypass = de facto)** | Mitigated by documentation; no mechanical defense | **Avoided** — bypass becomes the spec | Mitigated by ADR-level legitimacy |
| **S2 (doc surface multiplies)** | Avoided | Inherited; mitigated by keeping tier docs thin | Avoided (net surface ≈ today) |
| **S3 (vestigial formal preset)** | Avoided | Inherited; defended by hard-override + 12-mo sunset clause | Partial — ADR firmness ≠ silent rot |
| **I1 (handoff collision)** | Mitigated by INV-002 closure | Mitigated by schema extension (`tier:` field) | Mitigated; pointer schema already accepts non-skill-run targets |
| **I2 (spec amendment one-way)** | Avoided | **Inherited — hardest exposure** | Avoided |
| **I3 (market motion masked as reliability)** | Avoided | Mitigated by dropping adoption-motion framing | Avoided |
| **Pre-mortem total avoided/mitigated** | 7 avoided / 2 mitigated / 0 inherited | 1 avoided / 5 mitigated / 4 inherited | 7 avoided / 2 mitigated / 1 partial |
| **Cost-to-revert** | Trivial | High (spec amendment + ADR supersession) | Low (ADR supersession only) |
| **Solves rev-pref signal (S1 root cause)** | No — only legitimizes it in doc | Yes — codifies bypass as legitimate work | Partial — names bypass without rewriting identity |

---

## Selection for Phase 3 stress test

**Strongest approach: A3 (Infrastructure Identity + Presets).**

Rationale:
- **Pre-mortem dominance.** A3 avoids 7 failures + mitigates 2 + 1 partial.
  A1 avoids 7 + 2 mitigated but does nothing about S1's root cause.
  A2 mitigates more failures but *inherits* I2 (one-way door) and pays the
  highest cost-to-revert. A3 sits at A1's safety with one extra
  append-only commitment.
- **A2's own honest critique points to A3.** A2's weakness section
  explicitly recommends "formalize the three existing execution paths as
  named modes without a fourth tier above or hygiene tier below" — that is
  A3 verbatim.
- **Leverages Phase 0.5's structural finding.** The orthogonality between
  infrastructure and methodology is the real discovery. A3 is the only
  approach that names it directly.
- **Preserves the firm constraint set without partial supersession.** A2
  must amend INV-003's "every slice" phrasing; A3 does not.

The honest live question between A1 and A3: **is one ADR worth the
"append-only refusal-vocabulary" benefit?** Phase 3 must attack A3 here.
