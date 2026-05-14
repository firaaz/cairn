# Phase 1 — Pre-mortem

## Scenarios per option

### Scenario 1: Test extension breaks NARROW live files silently
- Option: NARROW
- What fails: `test_feature_file_schema.py` currently operates on synthetic fixtures only. When it is extended to scan live `.claude/features/*.yaml` (likely, since the test module's docstring already frames it as "Phase 2 validation"), orchestrator-paths.yaml would fail on `missing required field: intent` — immediately and loudly. But until extension, the violation is invisible.
- When: Next slice that extends the test to live files (no scheduled date, but the pattern in `test_identifier_scheme_contract.py` shows cairn does extend schema tests to live files).
- Plausibility: likely
- Cost: small (one YAML edit fixes it; the risk is the surprise, not the fix)
- Detectability: silent now → loud the moment the test runs live files

### Scenario 2: Slice-entry `status: phase-1` is a live bug under either option
- Option: BOTH
- What fails: `validate_feature_file()` line 73–76 explicitly rejects any slice-entry `status` other than `"dropped"`. orchestrator-paths.yaml has `status: phase-1` in its only slice entry. If the test is extended to live files, this fails regardless of whether NARROW or WIDEN is chosen — WIDEN does not address slice-entry status rules.
- When: Same trigger as Scenario 1.
- Plausibility: likely
- Cost: small (delete or rename the slice-entry status key)
- Detectability: silent now → loud on test extension

### Scenario 3: WIDEN opens ad-hoc field proliferation across 20+ features
- Option: WIDEN
- What fails: D5's explicit design principle is minimal schema (its only named rejection is `epic:`). Canonizing `charter:`, `status`, `tracking`, `predecessor`, `lesson`, `audit-findings`, `out-of-scope` as optional fields removes the "you need a named rejection to add a field" norm. When 20+ features exist, each author imports their own project-management vocabulary. Catchup/handoff commands that begin reading feature files (plausible next tooling) encounter an unbounded field space with no canonical shape to iterate over.
- When: Second or third feature added after WIDEN; compounds with each new author.
- Plausibility: likely at scale
- Cost: medium (future tooling cost, retroactive normalization)
- Detectability: quiet (individual files look fine; aggregate drift is invisible until tooling tries to normalize)

### Scenario 4: NARROW loses `audit-findings` provenance permanently
- Option: NARROW
- What fails: `audit-findings: [F-039, F-040, F-041, F-042, F-048, F-049, F-050]` in orchestrator-paths.yaml is a cross-reference to findings that motivated the feature. Under NARROW these fields are dropped or "relocated to slice metadata" — but slice metadata has no canonical home for findings-level cross-refs, and `docs/lessons.md` references go in lesson entries, not slice files. The data is not destroyed (git history), but the live cross-reference is severed, and future `/decision` or lesson-capture flows that join findings→feature cannot find it.
- When: At migration time under NARROW.
- Plausibility: possible
- Cost: medium (loss of findings→feature traceability; affects audit trail)
- Detectability: quiet (no tool enforces the cross-reference exists; loss only noticed when a human tries to trace F-039 back to a feature)

### Scenario 5: Trial B methodology claim undermined by either option's implementation quality
- Option: BOTH
- What fails: Trial B's contract protocol claims "D5 is a firm contract; contracts are enforced." NARROW enforces the contract by migrating the outlier — consistent with the claim. WIDEN amends the contract — also defensible, but only if the amendment is itself treated as a firm decision (new ADR or D5.1). If WIDEN is implemented without a supersession ADR (just editing D5 in place), the methodology claim becomes "firm ADRs are firm until inconvenient," which is the exact failure mode L-012 warns against. The risk is not the schema change but the amendment process.
- When: At implementation of WIDEN if done as an in-place edit rather than a supersession.
- Plausibility: possible (in-place edits to firm ADRs have happened — see `cairn-substrate-and-fastmcp-superseded` pattern)
- Cost: large (credibility of the firmness claim underlies the whole methodology)
- Detectability: quiet (the ADR looks fine; the process failure is invisible without reading commit history)

### Scenario 6: `charter:` alias ambiguity causes future consumer bugs
- Option: WIDEN
- What fails: If WIDEN accepts `charter:` as an alias for `intent:`, any future code that reads feature files (automation, handoff summarizer, query surface) and branches on the key name must handle both. Alias aliasing is a classic "temporary" compatibility shim that outlasts the feature that needed it (L-006 pattern). If the code checks `data.get("intent")` and `charter:` is the only key, it gets `None` silently.
- When: First tool that reads feature-file `intent:` field.
- Plausibility: possible
- Cost: medium (silent wrong behavior in tooling)
- Detectability: silent

---

## Failure modes BOTH options share

- Slice-entry `status: phase-1` is a live bug regardless of top-level schema choice; must be fixed independently.
- Both options require a process action on a firm ADR (NARROW: reaffirm; WIDEN: amend/supersede). If either is done silently (no ADR update, no commit-body rationale), the firmness infrastructure is weakened identically.
- Neither option addresses the absence of `created:` in orchestrator-paths.yaml — a `feature-slice-model D0` required field also missing from the live file.

## Disconfirming evidence I'd want

- Evidence that `test_feature_file_schema.py` will NOT be extended to live files (e.g., a comment or ADR saying it stays synthetic) would lower Scenario 1 from likely to edge case.
- Evidence that a second feature has already added non-D5 fields informally (beyond orchestrator-paths) would raise Scenario 3 from possible to likely and strengthen the WIDEN case.
- Evidence that `audit-findings` has a canonical alternative home (e.g., slice-level YAML or a findings registry file) would remove Scenario 4 entirely.
- A precedent in cairn where a firm ADR was amended in-place without a supersession and the methodology survived intact would lower Scenario 5.

## Pre-mortem summary

- The most consequential failure mode for NARROW is: permanent loss of findings→feature cross-reference traceability if `audit-findings` has no canonical relocation target (Scenario 4).
- The most consequential failure mode for WIDEN is: undermining the firmness claim if the amendment is done as an in-place ADR edit rather than a proper supersession (Scenario 5) — plus long-term alias ambiguity (Scenario 6).
- The risk asymmetry favors: NARROW — its worst case is medium-cost data loss with a clear fix (define a relocation target before migration); WIDEN's worst case is large-cost methodology credibility damage with no clean retroactive fix.
