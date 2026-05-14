# Phase 5 — Independent Verification

Reasoning from first principles. Did not read prior synthesis (`00`–`05`) or the draft ADR. The draft ADR title leaked via `docs/adr/index.md:30` and `docs/ARCHITECTURE.md:67` (both reference `schema-amendment-threshold/D1`/`D2`). Per L-003, I treated the leak as a known anchor and enumerated independently before re-checking.

## Phase 1 — Pre-mortem

**S1 — Migration churn cascades.** Any decision requiring all 10 feature files to conform to a richer schema creates a no-code edit sweep; spurious diffs hide intent in `git log`. **Likely / medium / loud.**

**S2 — Schema fragmentation under N=10→N=30.** D5 enumerates 4 fields; operational reality already added 6 on one outlier. Without a written threshold rule, each new operator-driven pattern is either a one-off `/decision` or quiet drift. **Likely / large / silent** (`test_feature_file_schema.py` only checks `id`/`intent`/`created`; Trial B's `test_d2_strict_id_shape_for_adrs_and_features` at line 102 doesn't gate extra fields).

**S3 — D5 firmness erosion.** D5 is `firm` and explicitly rejects `epic:` (`identifier-scheme.md:91`). Quietly admitting 6 fields without ADR action treats firm decisions as advisory under pressure, eroding the firm/provisional distinction. **Possible / large / quiet.**

**S4 — Lost replanning context if outlier is normalised backward.** `orchestrator-paths.yaml`'s `predecessor`/`lesson`/`audit-findings`/`out-of-scope` are operationally load-bearing forensic context — the L-020 compound-failure recovery breadcrumbs (`docs/lessons.md:380-398`). Stripping them is the only structured trace of why this slice exists. **Possible / medium / silent.**

**S5 — Hook/validator coupling assumption.** Any "strict schema" decision assumes hooks read feature files. Verified: `scripts/validate_architecture.py` doesn't parse feature-file schema (grep returned no field references); `cairn-tdd-feature/SKILL.md:91` explicitly excludes `.claude/features/`. Only `tests/unit/test_feature_file_schema.py` and the WIP contract test enforce anything. A strict-schema ADR with no test edit changes nothing in practice. **Likely / small / silent.**

## Phase 2 — Forced enumeration

### A — NARROW-pure (migrate outlier to D5 strictly)

**Core.** Rename `charter:` → `intent:`; add `shaped-from:` pointing at issue #24 or the L-020 archive; drop the 6 extras + `status`. Fold context into commit body.

**Fit.** D5 (`identifier-scheme.md:82-91`) honored exactly. Trial B `test_d1_features_have_name` (line 88) passes since `name:` is already present.

**Exposure.** Triggers S4 (loses L-020 trail); doesn't address S2 (next operator rediscovers the gap).

**Impact.** One file edit, zero code. Sets precedent that operationally-needed fields get hand-stuffed into prose — exactly the "reach-into-prose anti-pattern" `identifier-scheme.md:28` names as broken.

### B — NARROW+lesson (migrate AND record)

**Core.** Same migration, plus a `docs/lessons.md` entry naming the pattern: "operational fields drifting onto a single outlier indicate a real gap; record, don't quietly amend D5."

**Fit.** Same D5 fit. Lesson layer is the documented home for cross-cutting patterns (per `lessons.md` header).

**Exposure.** Mitigates S2 (next occurrence surfaces the threshold question) and S3 (firm decision honored). Still triggers S4.

**Impact.** One file edit + one lesson. Zero code.

### C — WIDEN-supersede (amend D5 to default-permit + N-trigger)

**Core.** New ADR declares D5 read default-permit-with-named-rejection (not strict-allowlist). Threshold: N≥3 unrelated features needing the same field promotes it to required. Outlier stays as-is; conforming files untouched.

**Fit.** D5's `epic:` rejection preserved (named-rejection is the escape). INV-006 (`ARCHITECTURE.md:67`) is amended to reflect the reading. Compatible with `feature-slice-model/D2` (`feature-slice-model.md:54-66`), which only requires `id`/`intent`/`created`.

**Exposure.** Resolves S2 (named threshold). Resolves S3 (D5 amended through proper supersession). Mitigates S4 (fields stay). Still exposes S5 unless paired with a test edit.

**Impact.** One new ADR, one index row, one test edit (default-permit + denylist), zero feature-file edits, ARCHITECTURE.md INV-006 prose update.

### D — DEFER-and-spike

**Core.** Leave outlier alone; add a `# schema-pending-N3` comment; wait for a second feature wanting the same fields before deciding.

**Fit.** No ADR action; D5 unchanged. Avoids over-fitting to N=1.

**Exposure.** Trades S2/S3 risk for time; exposes S5; requires operator to resist adding more fields meanwhile.

**Impact.** A YAML comment + watch-list entry. Zero ADR cost; one deferred state to remember.

## Phase 3 — Adversarial stress test on strongest

**Strongest = C (WIDEN-supersede with default-permit + N-trigger).**

### Attacks

**A1 — "Default-permit is D5 abandoned with extra steps."** D5 stays as a positive contract for the 4 required fields; default-permit changes the schema's *closure*, not the required floor. `epic:` rejection is preserved as named-rejection. D5 rejected `epic:` for principled reasons (Shape Up vs Scrum, `identifier-scheme.md:91`), not to enforce a closed schema. Attack defeated.

**A2 — "N≥3 has no empirical basis."** Genuine. N=3 is a heuristic balancing speed-to-act vs single-operator capture. Mitigation: ADR records N=3 provisional with a dogfood revisit, mirroring `cliff-failure-mode-and-v1-defenses` provisional firmness.

**A3 — "WIDEN sets precedent that drift wins."** Strongest attack. If we widen because one operator drifted, future operators learn drift→retroactive-ratification is cheapest. Counter: pairing WIDEN with a written threshold *raises* the bar — today drift is silently tolerated because no test catches it. The decision *adds* governance. But the ADR text must explicitly require *independent unrelated demand* (not single-operator preference) as the trigger, or this attack lands.

**A4 — "ARCHITECTURE.md/index leak — circular evidence."** Contamination, not validation. Approach C was reachable from constraint+failure analysis alone before re-checking the leaked references.

### Steel-man runner-up (B: NARROW+lesson)

Strong. Honors firm D5 without reopening; captures the gap in cairn's documented cross-cutting-pattern home; forces the next occurrence into a real `/decision`. The L-020 trace argument is weaker than it looks — that context could equally live in commit bodies, a `docs/plans/orchestrator-paths.md` plan doc (the cairn-tdd-feature plan-doc-as-input pattern), or in `lessons.md` directly. Feature files are intent + decomposition per `feature-slice-model/D2`, not incident logs.

Decisive factor for choosing C over B: S2 + S3 together. NARROW+lesson keeps D5 as a closed schema in principle but doesn't define what happens when the next field appears. The lesson is a tripwire-without-action. WIDEN names the threshold and the answer.

### Assumption audit

- **Verified:** D5 rejects `epic:` (`identifier-scheme.md:91`).
- **Verified:** `validate_architecture.py` doesn't parse feature schema (grep).
- **Verified:** `cairn-tdd-feature/SKILL.md:91` excludes `.claude/features/`.
- **Verified:** Outlier fields trace to L-017/L-019/L-020 (`lessons.md:325-398`).
- **Believed:** N≥3 is reasonable (heuristic; ADR should mark provisional).
- **Believed:** "Named-rejection" will be respected as the principled escape (no test enforces until contract test grows).

## Conclusion

WIDEN with default-permit + N≥3 trigger: (a) honors D5's named-rejection as the principled gate, (b) surfaces schema evolution as a proper ADR rather than a recurring drift-vs-cleanup choice, (c) preserves forensic context the L-020 lesson explicitly says we lack today, (d) is consistent with the framing already in ARCHITECTURE.md INV-006 (same-direction signal, not proof). Confidence modulated by A3: ADR must require *independent multi-feature demand*, not single-operator drift, as the trigger.

`RECOMMENDED: WIDEN-supersede`
