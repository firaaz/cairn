# Phase synthesis — cairn identity /decision arc (2026-05-30)

## Final decision
**Advance `cairn-thin-substrate-direction` (proposed→accepted, firmness stays provisional) as cairn's canonical identity record, amended to fold in this arc's adversarial validation + brainstorm-1's genuine contributions.** Supersede only the 2 provisional ADRs (`slice-intent-contract`, `identity-and-scope-deferral`); **retain** the firm 4-phase core (`phase-lock-and-role-declaration`, `phase-pipeline-evaluation`, `feature-slice-model`) pending the trials thin-substrate already defines.

## How the arc got here
Operator posture: HARDEN+ATTACK; identity starting position COMPLEMENT. The arc then discovered a third input mid-flight: the operator merged `origin/dev`, landing the `cairn-thin-substrate-direction` ADR (proposed, empirically grounded, from the downstream `govllm-trial/CAIRN_PLAN` lineage) — a parallel answer to the same identity question this arc was authoring.

## The 3-way convergence (the load-bearing result)
Three independent derivations land on the same identity:
1. **brainstorm-1 direction** (2026-05-22): infrastructure + intent-file primitive; methodology lighter.
2. **thin-substrate ADR** (2026-05-20, govllm lineage): cairn = layers 1–3 (hooks / contract-grammar+envelope / ADR-corpus); **layer 4 = host tool; "composition, not competition"**; 4-phase **retained** pending trials (D6); slice-#25 counterfactual → no mechanical layer catches semantic-grounding failures → new premise-grounding primitive.
3. **this adversarial arc** (Phases 0–3): infra-identity on the *proven* substrate; don't retire the firm core; methodology stays trial-gated.

Convergence across independent lineages is the strongest correlated-error defense available here. **brainstorm-1's charter cycle is the outlier all three push back on.**

## Why not the charter cycle as brainstorm-1 framed it
- **S1** (pre-mortem): one-way door (retire 3 firm ADRs + INV-003) defended by an **unmeasurable** headline value.
- **S2 + assumption audit**: goal-commitment is *within-cycle*; the cliff is *cross-cycle* — orthogonal axes, not "complement." The reactivity failure mode is **operator-self-reported, zero in-repo evidence** (cliff/drift have logged incidents L-012/L-016/L-022).
- **S3 + slice-#25**: build≠check is role-purity, not decorrelation (~60% shared blind spots, Kim et al.); thin-substrate's slice-#25 counterfactual is the sharper, evidence-backed form — *no* mechanical layer catches semantic grounding. L-016 already fired on this shape downstream.
- **Layer conflict**: thin-substrate D1 says layer-4 methodology belongs to the host; brainstorm-1 wants cairn to *ship* the charter cycle. They compose only under the split below.
- **Unbuilt mechanisms**: the re-injection hook (settings.json wires only Pre/PostToolUse), cross-model verify (no phase agent carries `model:`), and AGENT_ROLE (dead) are all aspirational — like premise_guard.py, they must be build-deliverables, not narrated as live.

## The reconciling split (charter primitive vs charter cycle)
- **Charter PRIMITIVE** = thin-substrate's D2.1 contract grammar (`goal`/`done`/`constraints`/`amendments` ≈ `must-satisfy`/`evidence`/envelope). Cairn owns it (layers 1–3). Uncontested — all three lineages adopt it.
- **Charter CYCLE / orchestration** (formation dialogue, blind-worker dispatch, build≠check sequencing) = layer 4. Host owns it; cairn *documents* it as a preset, does not ship it as identity.
- **goal-commitment-vs-reactivity** = falsifiable SUB-CLAIM with a trigger, not co-equal headline.

## Substrate precision (this arc's net-new finding vs thin-substrate D2)
- **C6 (validator) + C8 (pointer-handoff): VERIFIED, live** — sound identity anchors.
- **C5 (per-role write gating): per-role half is DEAD CODE** — `role_guard.py:137` reads `AGENT_ROLE`, nothing injects it; only the session-global operator envelope is live. thin-substrate D2.2's "mechanically enforced per write" is true for the *envelope*, aspirational for *per-role*.
- **C7 (cross-session /decision blind verify): real but rare** (~1 run / 25 firm ADRs; firm-only). A discipline gap, not a live guarantee.

## Supersession scope (low blast radius — the thin-substrate win)
- Supersede: `slice-intent-contract` (provisional; contract concept survives in the grammar), `identity-and-scope-deferral` (provisional; its D3.4 operator-directive trigger is now invoked).
- **Retain** (NOT superseded): `phase-lock-and-role-declaration`, `phase-pipeline-evaluation`, `feature-slice-model`, INV-003. Dropping the 4 phases stays gated on Trial E + `premise_guard.py` (thin-substrate D6).

## Deferred to the methodology arc (Trial E / future)
Firm-phase drop; the re-injection hook; cross-model verify (to address S3); hardening C3's return-channel into a mechanism — all adjudicated against measured trial results, not committed now.

## Amendment plan for `cairn-thin-substrate-direction.md`
1. Frontmatter: `status: proposed → accepted` (native Edit). `firmness:` stays `provisional` (S1 one-way-door caution; so Phase 5 firm-verification not required). Add `supersedes: [identity-and-scope-deferral, slice-intent-contract]` (needs escape hatch — `supersedes:` not in the guard's allowed first-line set).
2. Body additions (append-only → needs `ADR_EDITORIAL_FIX=1`):
   - **D7 — Relationship to the charter-cycle direction**: the primitive-vs-cycle split; charter cycle as documented layer-4 host preset; goal-commitment-vs-reactivity as falsifiable sub-claim + trigger.
   - **Substrate-precision note** appended to D2: C5 per-role gating dead / C7 rare; C6+C8 the live anchors.
   - **Adversarial-validation note**: the S1/S2/S3 pre-mortem as recorded rationale for D6's trial-gating of the phase drop.
   - Reference this arc's skill-run dir.
3. Supersede the 2 provisional ADRs: each gets `status: superseded` + `superseded-by: cairn-thin-substrate-direction` (native Edits — both first-lines in the allowed set).
4. Propagation: `docs/adr/index.md` already lists thin-substrate (merged); update status there if it carries one; `/refresh-architecture` if any invariant text shifts (none retired here); record the convergence + L-entries in `docs/lessons.md`.

## Residual risks carried forward
- premise_guard.py is unbuilt (thin-substrate honest about it via D6 gating).
- The reactivity sub-claim remains unmeasured — the trigger must define what evidence would promote/kill it.
- C5 per-role enforcement remains aspirational until AGENT_ROLE/per-subagent-scope ships.
