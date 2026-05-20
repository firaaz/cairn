# Phase 3 — Adversarial Stress Test

Three parallel attacks were mounted on A3 (preferred), plus assumption audit.

---

## Attack 1 — Disconfirming search (`phase-3-disconfirming.md`)

**Verdict: A3 survives, three small amendments required.**

- **Orthogonality holds** (`checks/role_guard.py:43-45,137-167`, `scripts/validate_architecture.py:443-445`, `tests/unit/test_handoff_contract.py`). The three-layer separation between hooks/validators/tests and the four-phase machinery is real and verified — A3's central structural claim is sound.
- **Naming collision**: "mode" is already claimed by `.claude/active-envelope.yaml` (`mode: operator | off`). A3 must use "preset" (which it does) and explicitly disclaim "modes."
- **No hidden spec-v1 §1 dependencies**: scope clause is documentary, not executable. A3's "no amendment" claim is safe.
- **phase-lock collision**: `phase-lock-and-role-declaration.md` asserts four phases are locked, but does NOT assert "the four-phase IS identity." A3's "formal preset = `cairn-tdd-feature` dispatch skill" mapping is compatible if explicitly stated.
- **`/decision`-to-`contracted-preset` mapping ambiguous**: A3 must clarify whether `contracted` names the `/decision` protocol or is a session-level declaration.
- **No detection mechanism for preset-vs-execution-method mismatch**: A3 must document that preset is advisory, enforcement is via commit structure.

Cost-to-revert if A3 lands: trivial (one ADR supersession).

---

## Attack 2 — Steelman of A1 (runner-up)

**Verdict: materially strong. Shifts the preferred approach.**

Key arguments that survive scrutiny:

1. **A3's marginal value over A1 may be ~zero.** A3's own admission: "rebranding, not redesign." The ADR's only function is naming; naming does not need append-only protection (`reversibility-guard.sh` protects ADRs, not docs).
2. **The rev-pref signal (S1) may be right-sizing, not failure.** Examining recent commits on `dev`: `feat(identifier-scheme)` and `test(identifier-scheme) D5/D9` pairs ARE `cairn-tdd-feature` outputs; `/decision` IS used for architectural arcs (schema-amendment-threshold, trial-b); ad-hoc is used for chores. The pre-mortem's S1 framing of "bypass = methodology rot" conflated right-sizing with rot. A1 treats S1 as data; A3 and A2 treat it as a problem requiring identity-level response.
3. **Option value matters more than naming.** Cairn pivoted once (substrate retirement at M4). Likelihood of another pivot in 6-12 months is non-trivial. Every ADR landed creates friction for the next pivot. A1 preserves maximum option value.
4. **The /decision arc record IS the refusal vocabulary.** This persisted skill-run (`.claude/skill-runs/identity-and-scope-2026-05-20/outputs/`) records why A2 was rejected. Future tier proposals can be re-refused by re-reading this; no ADR needed.

The steelman concludes A1 is correct.

---

## Attack 3 — Assumption audit (preferred approach: A3)

| # | Assumption | Status | If wrong, what happens? |
|---|------------|--------|--------------------------|
| 1 | Naming three paths in an ADR is materially different from naming them in `operational-reference.md` | **BELIEVED** (challenged by A1 steelman) | A3 pays an ADR's append-only cost for ~zero mechanical benefit |
| 2 | Orthogonality (infrastructure vs methodology) is durable | **VERIFIED** by disconfirming search | n/a |
| 3 | "Preset" metaphor (operator declares, not scored) is the right framing | **VERIFIED** — no naming collision | n/a |
| 4 | "Formal preset" anchors cleanly to `cairn-tdd-feature` dispatch | **VERIFIED** with explicit ADR clause | n/a |
| 5 | S1 (low `cairn-tdd-feature` utilization) is a problem that framing can solve | **BELIEVED, AND CHALLENGED** | A3's main legitimacy benefit dissolves; A3 collapses to A1 |
| 6 | The identity question is ripe for a decision now | **BELIEVED** | A3 commits prematurely; downstream slices must respect a premature framing |
| 7 | An ADR is more durable than a doc edit for framing claims | **BELIEVED, weakly** | Both decay at similar rates under single-operator authorship |

**Critical assumption: #5 (S1 is a problem).** If false, A3's main argument vs A1 dissolves. Verification attempt: examining the last 10 commits on `dev`, multiple execution paths are visibly active — TDD-skill outputs, /decision arc artifacts, direct chore edits. This **suggests** S1 is right-sizing, not rot. Not a clean falsification (need utilization counts over a longer window), but the prior is now against #5.

**Critical assumption #6 (identity question is ripe).** A1 steelman correctly points out: M4 already supersedes a major architectural framing (substrate retirement). The operator-as-single-user constraint means identity claims accumulate without external pressure. Deferring is itself an answer.

---

## Reshaped preferred approach: **A1+**

A1 (Status Quo Hardened) plus **one explicit capture of the orthogonality finding** in `docs/lessons.md`. The orthogonality between infrastructure and methodology is real and durable (Attack 1 verified it), and worth recording — but as a lesson, not an identity claim.

**Mechanical changes (A1+):**
1. (A1.1) Document three legitimate execution paths in `docs/operational-reference.md:19-29` as co-equal — ad-hoc / /decision / `cairn-tdd-feature`. State explicitly that operator selects by task shape; no path is "the methodology."
2. (A1.2) Close INV-002 `binding-effective-from: <pending-slice-close-sha>` with Trial-A landing SHA.
3. (A1.3) Rebaseline 5 failing tests (Trial-A completion mechanical work).
4. (A1.4) Amend ADR contract grammar (`docs/adr/identifier-scheme.md:6-22`) with `execution-scope:` field — Trial B's narrow lesson formalized. This is itself a small ADR (`adr-contract-execution-scope`).
5. (A1+ new) Add lesson L-NNN to `docs/lessons.md`: "Infrastructure (hooks/validators/handoff/role-guards/identifier-scheme/plan-doc) is orthogonal to methodology (four-phase TDD machinery). This is the durable spine, verified by Phase-0.5 trace + Phase-3 disconfirming search of `.claude/skill-runs/identity-and-scope-2026-05-20/`. Do not pivot identity on this basis alone; the finding is structural, not strategic."
6. (A1+ new) The /decision arc itself — this skill-run — IS the durable record. Phase-4 ADR records that the identity-and-scope question was considered, three approaches enumerated, and A1+ chosen with reasons.

**spec-v1 §1 unchanged. `phase-lock-and-role-declaration` preserved. No tier system. No risk scorer. No identity pivot.**

---

## Pre-mortem re-coverage under A1+

| Failure | A1+ status | Why |
|---------|-----------|-----|
| T1 (tier misclassification) | **Avoided** | No tiers |
| T2 (uncalibrated scorer) | **Avoided** | No scorer |
| T3 (hook discoverability) | **Avoided** | Hooks unchanged |
| S1 (bypass = de facto path) | **Reframed** — recognized as right-sizing per attack-2 evidence; documented in ops-ref | If S1 is right-sizing, "solving" it was the wrong target |
| S2 (doc surface multiplies) | **Avoided** | Net doc surface ≈ today + one section + one lesson |
| S3 (vestigial formal preset) | **Avoided** | No preset framing committed |
| I1 (handoff collision) | **Mitigated** by INV-002 closure | Trial-A landing fix |
| I2 (spec amendment one-way) | **Avoided** | No spec change |
| I3 (market motion masked) | **Avoided** | No adoption framing change |

A1+ avoids 8 of 9 named failures, reframes S1 with evidence, mitigates I1 via Trial-A closure.

---

## Recommendation for Phase 4

Proceed to /new-adr with the following decision recorded:

> **Decision**: Defer Cairn identity pivot. Three approaches enumerated and
> compared; A1+ (status quo hardened, plus orthogonality lesson) chosen.
> Identity question revisits when (a) external adoption pull is
> demonstrated, or (b) revealed-preference data accumulates over 90+ days
> showing utilization signal that distinguishes right-sizing from rot.

ADR firmness: **provisional** (the decision is "defer," not "lock"; revisiting is built into the decision itself).

Phase 5 (independent verification): **skipped** — provisional firmness.
