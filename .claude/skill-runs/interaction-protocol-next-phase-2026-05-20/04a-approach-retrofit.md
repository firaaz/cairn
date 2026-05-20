# Approach RETROFIT — Steelman

## Core idea

RETROFIT applies the now-firm identifier-scheme contract (`docs/adr/identifier-scheme.md:8-13`) to the artifacts violating it: 14 ADRs missing `name:` and 6 slice-ids under `LEGACY_SLICE_ID_BASELINE` (`tests/unit/test_identifier_scheme_contract.py:19-22`). Success is operational: `LEGACY_LABEL_BASELINE` drops from 10 toward 0, every ADR carries `name:`, and the prefix-shape outlier `substrate/orchestrator-paths` (`.claude/features/orchestrator-paths.yaml:2,41`) gets an explicit verdict — D3-rename or watching-mark per `schema-amendment-threshold` D2. RETROFIT is correct when the operator's priority is *closing drift the contract itself flagged* before authoring more contract surface.

## Mechanism

1. **Per-ADR `name:` insertion.** Edit anchors at `status:` or `firmness:` (lines 3–6 in every sampled ADR). Reversibility-guard accepts `old_string` first-line `status:`/`firmness:`/`superseded-by:` (`checks/reversibility-guard.sh:85`). No `ADR_EDITORIAL_FIX=1` needed — the *anchor* is existing, even when the *injected* content is a new key. Trial B used this anchor (`docs/plans/2026-05-14-cairn-adr-contract-trial-b.md`).
2. **Title-collision policy.** For the ADRs with legacy `title:` (`feature-slice-model.md:3`, `semantic-identity.md:3`, plus others), **add `name:` alongside `title:`**. `title:` removal is a body-edit gated by `ADR_EDITORIAL_FIX=1`; D1 reads "human label (name OR title)" (`docs/adr/identifier-scheme.md:8`) — coexistence is in-scope.
3. **Slice-id verdicts.** Five are casing/version-dot violations caught by `HIERARCHICAL_SLUG.match` (`tests/unit/test_identifier_scheme_contract.py:131`). The sixth is the prefix-mismatch in `orchestrator-paths.yaml:41` — `substrate/orchestrator-paths` under feature `id: orchestrator-paths` (line 2). RETROFIT files watching-mark instance 1/3 per `schema-amendment-threshold` D2 (`docs/adr/identifier-scheme.md:10`); D3 rename is a separate decision.
4. **Baseline decrement.** `LEGACY_LABEL_BASELINE = N_remaining` committed in the *same* change as the ADR edits. The test counts files with *neither* `name:` nor `title:` (`tests/unit/test_identifier_scheme_contract.py:80-84`), so coexistence-keeping pushes the count to 0.
5. **Commit shape.** One commit per logical grouping. Envelope (`.claude/active-envelope.yaml`) must include `docs/adr/.*\.md` and `tests/unit/.*\.py`.

## Constraint fit (from 01-constraints.md)

**Honors:**
- INV-005 firmness preserved: no amendment to identifier-scheme ADR's contract block (`01-constraints.md:9`).
- D7 forward-only migration shape (`docs/adr/identifier-scheme.md:121`): adds `name:`, never removes `id:` or `title:`.
- Schema-amendment-threshold N≥3 (`docs/adr/schema-amendment-threshold.md:49-61`): does not invoke schema widening; uses the existing watching-mark slot.
- Reversibility-guard append-only on ADR bodies: every edit is frontmatter-only, anchored on a guard-permitted key.

**Risks violating:**
- D3 immutable-id (`docs/adr/identifier-scheme.md:11`) if slice-id rename is chosen for prefix-mismatch. Mitigation: choose watching-mark, not rename. Make the choice explicit in the commit body.
- Operator-envelope drift if the session leaks into other paths. Mitigation: scope envelope to `docs/adr/.*` + `tests/unit/test_identifier_scheme_contract.py` before dispatch.

## Engagement with pre-mortem attacks (from 03-premortem.md, RETROFIT scenarios)

**1. Edit-anchor exhaustion.** Mitigated by the title-collision policy above. Verification on three sampled ADRs (`bootstrap-exception.md:2`, `feature-slice-model.md:2-3`, `semantic-identity.md:2-3`) shows `status:` or `firmness:` is reliably present on lines 3–6. The Trial B plan codified this anchor pattern. **Residual:** ADRs without `status:` exist hypothetically; verified absent by `grep -L "^status:" docs/adr/*.md` returning only `index.md`. Attack defused.

**2. `name:` text authorship rubber-stamp pit.** Partially accepted, partially mitigated. The attack is real: a Phase-3-style subagent producing `name: "Bootstrap exception"` (slug-restated) is a known LLM failure mode. **Mitigation:** dispatch authorship as a *single Explore-then-Plan agent* (not parallel per-ADR) so the agent reads the ADR body and synthesizes a name from the actual decision content. Operator reviews 15 names in one diff — 15 short strings is review-tractable. **Honest residual:** this is the highest-quality-risk surface of RETROFIT; if the operator's priority is "minimize attention," this attack pressures the approach harder than it admits. The countermeasure is procedural (single-diff review), not structural.

**3. Baseline-decrement race + advisory rot.** Mitigated by atomic commit shape. The test-constant change ships in the *same* commit as the ADR edits (mechanism: rule 4 above). If the operator splits the commit, the race opens. **Mitigation that doesn't rely on discipline:** add a post-commit assertion in the plan that `git show HEAD --stat` includes both `tests/unit/test_identifier_scheme_contract.py` and `docs/adr/*.md` paths before the close handoff is written. **Residual:** symmetric over-decrement (set to 0 then someone lands an unrelated ADR without `name:`) is a CI-catches-it failure, not silent drift — acceptable.

**4. Hidden D3 decision via slice-id violation.** *Accepted as a real implicit decision, not mechanical.* The pre-mortem is correct that `substrate/orchestrator-paths` is structurally distinct from casing/version-dot violations: it's a prefix-mismatch, which silently legitimises hierarchical drift if accepted advisory-style. RETROFIT's response: **surface this as a distinct decision in the commit body and file watching-mark instance 1/3 per `schema-amendment-threshold` D2.** This is not "mechanical cleanup" — it's an explicit choice to defer rename in favour of accumulating evidence. The approach owns the decision rather than hiding it under the baseline constant.

## Implicit decisions surfaced (and how this approach resolves them)

**(a) `title:` → `name:` rename vs. add-alongside vs. leave.** Resolution: **add `name:` alongside `title:`**. Reason: `title:` removal is a body-edit gated behind `ADR_EDITORIAL_FIX=1`; the D1 contract permits coexistence; future `name:` becomes the canonical field, `title:` deprecates by attrition.

**(b) Authorship process for 14 `name:` strings.** Resolution: **one Explore agent reads each ADR body and proposes `name:` from decision content; operator reviews all 15 in one diff before commit.** Not parallel per-ADR (parallelism produces inconsistent voice); not solo-operator (15× context-switch waste).

**(c) `LEGACY_LABEL_BASELINE` decrement strategy.** Resolution: **atomic same-commit decrement to actual remaining count.** If all 14 land, baseline → 0; if a subset, baseline → N_remaining. Not per-ADR ratchet (multiplies commits), not deferred (rot risk per pre-mortem #3).

**(d) Slice-id violation for `substrate/orchestrator-paths` specifically.** Resolution: **watching-mark per `schema-amendment-threshold` D2, not rename.** D3 rename is a separate decision-weight item that should not ride a retrofit commit. Commit body explicitly flags this as instance 1/3.

## Downstream impact

**Makes easier:** TRIAL-C and TIGHTEN-FIRST both inherit a clean `name:`-bearing ADR corpus, so their plan-level contracts can reference the firm contract without legacy carve-outs. The watching-mark slot for slice-id prefix is filed and dated, simplifying the future N≥3 schema-amendment trigger. Any future `Explore` agent reading ADRs gets a one-line semantic label without parsing body H1s.

**Makes harder / forecloses:** RETROFIT does not refine the contract shape — if the "too strict" verdict reflects structural brittleness rather than plan-level execution-scope conflation (a claim the pre-mortem contests, `03-premortem.md:35-37`), TIGHTEN-FIRST is delayed by however long RETROFIT consumes. It also does not test the contract on a *new* surface — the rubber-stamping defeat thesis remains unvalidated against slice intent.

## Honest costs

**Calendar time:** 1 session, possibly 2 if the prefix-mismatch decision goes long. The four ADR title-collision cases plus 11 clean adds is ~30 minutes of agent work plus operator review of 15 short strings.

**Operator attention:** medium-low for ADRs (one diff, 15 names); medium for the prefix-mismatch verdict (one decision that should not be rubber-stamped).

**Decisions resolved:** title-collision policy, baseline-decrement strategy, authorship process, prefix-mismatch verdict. **Decisions punted:** contract-shape "too strict" question; semantic-drift validator class for intent; D3 immutable-id strict-vs-aspirational stance (watching-mark is a deferral, not a resolution).

**Strongest argument against (30 seconds, opposing side):** The operator goal was "do C." RETROFIT is "do A again, more carefully." It applies a proven mechanism to known-broken artifacts and produces *no learning about the protocol*. If the dispatch skill needs to ship to consumers, every session spent retrofitting legacy labels is a session not spent validating the rubber-stamping defeat on intent.md — which is the actual unresolved question. The 14 ADRs have lived without `name:` for months; the slice-id violations have an advisory ceiling that catches worsening. There is no forcing function making this *now*-work except that it is *easy* now-work, and easy work is the wrong selection criterion when the operator is trying to validate a methodology.
