# Approach C — HYBRID: Advocacy

## Pre-mortem response

**Scenario 1 (test extension breaks NARROW live files silently):** HYBRID migrates orchestrator-paths.yaml now, so the `missing required field: intent` failure never happens. The file is conformant before the test is extended.

**Scenario 2 (slice-entry `status: phase-1` is a live bug under either option):** HYBRID fixes this independently as part of the migration — the slice-entry violation is removed alongside the `charter:` → `intent:` rename. L-024 does not address it; the fix does.

**Scenario 3 (WIDEN opens ad-hoc field proliferation):** HYBRID avoids this entirely. D5 stays minimal. L-024 adds the N≥3 trigger so that future authors see a documented threshold, not a blank wall. Without the lesson, the next author is likely to repeat orchestrator-paths.yaml's drift — they have no signal that one instance was judged insufficient for schema amendment. With L-024, the precedent is explicit.

**Scenario 4 (NARROW loses `audit-findings` provenance):** HYBRID does not solve this better than pure NARROW. See §4 below. This is HYBRID's clearest gap.

**Scenario 5 (Trial B methodology claim undermined):** HYBRID strengthens the methodology story by converting the reconciliation into a documented meta-decision. It demonstrates that D5 firmness can coexist with empirical openness — the lesson is the evidence.

**Scenario 6 (`charter:` alias ambiguity):** HYBRID avoids this. No alias is introduced; `charter:` disappears.

---

## 1. What does L-024 look like?

```
## L-024: Single-feature schema drift is insufficient signal to amend a firm ADR — require N≥3 before widening

**Discovered**: 2026-05-14, during feature-schema-d5-reconciliation /decision arc.

**Pattern**: A feature file (orchestrator-paths.yaml) accumulated 6 fields not in
identifier-scheme/D5 (`charter:`, `status:`, `tracking:`, `predecessor:`, `lesson:`,
`audit-findings:`, `out-of-scope:`). Operator reflex: "maybe D5 needs widening." Counter:
9 of 10 live feature files conform to D5; the outlier arose in a single Phase-2 commit
with no rationale (`01-constraints.md:42`). One data point cannot distinguish "D5 is too
narrow" from "this file was drafted under context pressure."

**Load-bearing directive**: Before invoking WIDEN on a firm schema ADR, require N≥3
independent features that each need the same non-schema field(s) AND cannot satisfy their
need via an adjacent artifact (slice metadata, lessons.md, an ADR note). "Need" means the
field carries data with no canonical alternative home, not that an author found it
convenient. Single-feature drift is a migration problem, not a schema problem.

**Rule**: log the candidate field and count in a watching-mark when the first
non-conforming feature appears. Promote to /decision when a second independent feature
needs the same field. Trigger WIDEN consideration when a third independent feature does.

**Anti-pattern signals**: "this field is intuitively useful," "the author added it for
good reasons," "most features will eventually need this," "migrating it away loses data."
All four apply to orchestrator-paths.yaml's extra fields; none of them is schema-amendment
evidence. Data preservation (audit-findings) is a relocation problem; useful fields that
appear in one file are a watching-mark, not a WIDEN trigger.
```

---

## 2. Why N≥3?

N=1 (the current state) cannot distinguish context-pressure drift from genuine schema shortfall — established by `01-constraints.md:41-43` (no commit message explains the deviation; single-commit origin under Phase-2 pressure).

N=2 is still within the noise band of two authors independently drafting under pressure or two slices in the same feature arc sharing vocabulary. Two instances give correlation, not pattern.

N=3 across independent features (different author contexts, different slice arcs) makes coincidental co-drift implausible. This mirrors cairn's own recurrence threshold in lessons.md: L-011 (`docs/lessons.md:223`) is promoted for mechanical fix at recurrence count 3.

Three is not sacred — it's the minimum that makes "pattern" defensible against a skeptic who will challenge whether any two instances are truly independent.

---

## 3. The migration of orchestrator-paths.yaml

Mechanical steps (NARROW-shaped):
1. Rename `charter:` → `intent:` (value is the same prose; `02-journey.md:8` confirms the content satisfies D5's "short prose statement of what the feature delivers").
2. Add `shaped-from: null` — or `shaped-from: "docs/lessons.md#L-017"` if L-017 is treated as the design artifact. `01-constraints.md:52` notes `predecessor:` may be equivalent to `shaped-from:`; the `predecessor: substrate/root-resolver` line can supply the value.
3. Remove `status: in-progress` from top level (not in D5; no D5 rejection exists, so it can stay as an unvalidated advisory field, but removal is cleaner).
4. Remove `status: phase-1` from the slice entry (`02-journey.md:30-34` — independent violation of `validate_feature_file()` line 73-76 regardless of HYBRID/NARROW/WIDEN choice).
5. The 6 extra fields: leave `tracking:`, `predecessor:`, `lesson:`, `out-of-scope:` as unvalidated prose (D5 does not name them; no code reads them; `01-constraints.md:10` — D5 rejects fields via named rejection statements only, and these are not named). Relocate `audit-findings` — see §4.

Why NARROW + lesson beats NARROW + nothing: without L-024, the next feature author sees orchestrator-paths.yaml's extra fields in git history, infers they were acceptable, and repeats the drift. The lesson converts a silent migration into an explicit meta-decision with a documented threshold. The migration alone is a fix; the lesson is the explanation that makes the fix generative.

---

## 4. The `audit-findings` data loss risk

HYBRID does not address Scenario 4 better than pure NARROW. Honest assessment: the `audit-findings: [F-039…F-050]` cross-reference has no canonical home in D5's schema, and HYBRID does not create one.

The relocation options within HYBRID:
- Leave the field as an unvalidated advisory comment in orchestrator-paths.yaml (no code reads it; no D5 named rejection applies). This preserves the live cross-reference at zero cost.
- Or move it to the slice-entry metadata or the feature's plan doc.

The "leave as unvalidated advisory field" option is available under HYBRID and covers Scenario 4 without requiring WIDEN. It is the right call: `01-constraints.md:10` establishes that D5 only rejects fields via explicit named-rejection statements. `audit-findings:` has no such rejection. Keeping it while conforming `charter:` → `intent:` + adding `shaped-from:` satisfies D5 without data loss.

---

## 5. Feature author drift — how L-024 helps

Without L-024, a future author who wants richer fields sees: (a) D5 says minimal schema, (b) orchestrator-paths.yaml has extra fields in git history, (c) no documented threshold for when WIDEN is appropriate. Rational response: add the fields by analogy.

With L-024, the same author sees a watching-mark protocol: log the field + count, bring it back if a second independent feature needs it, trigger /decision at three. This routes the author's legitimate need into evidence-gathering rather than ad-hoc drift. The lesson turns "no" into "not yet, here's what would change the answer."

---

## 6. Why HYBRID is superior to pure NARROW or WIDEN

**vs. pure NARROW:** NARROW migrates the file and records nothing. The methodology gains conformance but loses the meta-decision. The next audit of feature files has no standing reference for why orchestrator-paths.yaml's extra fields were not generalized. L-024 converts the migration into a documented institutional decision with a replicable threshold.

**vs. WIDEN-via-supersession:** WIDEN is disproportionate. `01-constraints.md:25` establishes that no code in `checks/` or `scripts/` reads feature-file fields at runtime — D5 is purely advisory. Amending a firm ADR for a purely advisory schema that has zero mechanical consumers, on the basis of one file, is a credibility cost with no offsetting mechanical benefit. `03-premortem.md:72` puts the risk asymmetry clearly: NARROW's worst case is medium-cost data loss with a clear fix; WIDEN's worst case is large-cost methodology credibility damage with no retroactive fix. HYBRID takes NARROW's safe path and acknowledges the legitimate kernel in the WIDEN impulse via the lesson.

Specific Phase 0/0.5/1 support:
- `01-constraints.md:41-43` — single commit, no rationale: insufficient basis for WIDEN.
- `02-journey.md:66-78` — all six extra fields are unused at every automated stage: no mechanical pressure to canonize them now.
- `03-premortem.md:8-12` — Scenario 1 (test extension) is "likely": HYBRID eliminates it by migrating now.
- `03-premortem.md:38-43` — Scenario 4 (`audit-findings` loss) is "possible" and addressed by the "unvalidated advisory field" relocation option available within HYBRID.

---

## 7. Where HYBRID falls short

1. **L-024 is prose, not enforcement.** N≥3 is a watching-mark threshold with no mechanical gate. A future author who adds non-D5 fields in a second feature file and does not log the watching-mark makes L-024 invisible. There is no hook or validator that counts non-D5 fields across feature files and emits a warning.

2. **`audit-findings` as "unvalidated advisory field" is fragile.** If a future automated consumer reads feature files and validates strictly against D5, the retained `audit-findings:` field will fail. The lesson does not address this forward risk.

3. **The N=3 threshold is a convention, not derived.** It matches cairn's recurrence pattern but is not grounded in empirical evidence about schema stability — it is a judgment call that could be wrong in either direction.

4. **HYBRID requires the operator to file the watching-mark.** If no watching-mark is filed after this decision, the counting mechanism that makes L-024 operative never starts.

---

## 8. Implementation steps

1. Edit `.claude/features/orchestrator-paths.yaml`: rename `charter:` → `intent:`, add `shaped-from: substrate/root-resolver` (predecessor as provenance; satisfies D5's provenance intent), remove `status: phase-1` from slice entry, retain `audit-findings:` and other extra fields as unvalidated prose.
2. Append L-024 to `docs/lessons.md` (next available id after L-023).
3. File a watching-mark in `.claude/` or `docs/watching-marks.md` (or inline in L-024's mechanism section): "orchestrator-paths is instance 1/3 of features needing fields beyond D5 — field: audit-findings, tracking, predecessor, lesson, out-of-scope."
4. Add a commit-body note in the migration commit referencing this /decision arc and L-024.
5. Reaffirm D5 via an in-ADR comment or a one-line status note (no supersession needed — NARROW does not amend D5).
