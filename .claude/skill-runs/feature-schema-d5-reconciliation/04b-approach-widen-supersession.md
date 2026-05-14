# Approach B — WIDEN via supersession: steelman

## Pre-mortem scenario handling

**Scenario 1 (test extension breaks NARROW live files):** Under WIDEN, `charter:` is canonized as D5' primary or dual-key, so `orchestrator-paths.yaml` passes when tests extend to live files. No YAML edit required at migration time. The surprise is eliminated.

**Scenario 2 (slice-entry `status: phase-1` is live bug):** Shared with NARROW; independent of schema choice. D5' does not canonize slice-entry `status:` values — `validate_feature_file()` line 73–76 enforcement is left intact. Fixing the slice entry in `orchestrator-paths.yaml` is still required, and D5' makes this clear by not touching that sub-schema.

**Scenario 3 (ad-hoc field proliferation):** D5' enumerates the permitted optional fields exhaustively. D5 already established the "named rejection" pattern for `epic:`; D5' extends that pattern to make the enumerated list the complete allowed set. Future authors who want a new field must bring it through a D5'' amendment. This bounds the schema to the 10 fields (4 required/primary + 6 optional) without prohibiting evolution.

**Scenario 4 (NARROW loses `audit-findings` provenance):** Not applicable under WIDEN. `audit-findings: [F-039–F-050]` in `orchestrator-paths.yaml` stays in place; D5' recognizes it as a permitted optional field. The findings→feature cross-reference is preserved at zero migration cost.

**Scenario 5 (in-place firm-ADR edit undermines methodology):** This is exactly the scenario WIDEN-via-supersession is designed to avoid. The new ADR `identifier-scheme-v2` is authored per identifier-scheme D3 — the old `id:` freezes, the new ADR carries the version suffix, and the firmness infrastructure is visibly intact. `reversibility-guard.sh` allows `Write` on new ADRs; the creation of `docs/adr/identifier-scheme-v2.md` is a clean new file, not an overwrite.

**Scenario 6 (`charter:` alias ambiguity):** D5' resolves this by canonizing `charter:` as the primary key for the intent field (or equivalently: demoting `intent:` to documented alias with `charter:` as canonical). The decision text explicitly states that any tooling reading this field MUST check `data.get("charter") or data.get("intent")`. The dual-key path is documented at the decision level, not left implicit. The ambiguity risk is turned into a documented compatibility contract.

---

## 1. Supersession ADR sketch

```yaml
---
id: identifier-scheme-v2
name: "Identifier scheme v2 — widened feature metadata"
status: accepted
firmness: firm
supersedes: [identifier-scheme]
supersedes-sections: [D5]
superseded-by: null
topic: naming
date: 2026-05-14
---
```

**D5' decision text (draft):**

Feature files carry these fields:

- **`id:`** — required. Flat semantic slug, per D2.
- **`name:`** — required. Human-facing label, per D1.
- **`charter:`** — required. Short prose statement of what the feature delivers (the why and the boundary). Replaces `intent:` as canonical key. `intent:` is a recognized alias; any reader MUST check both (`data.get("charter") or data.get("intent")`).
- **`shaped-from:`** — optional. Path or URL to design artifact (retains D5 semantics when present).
- **Optional operational fields** (any subset, all optional): `status`, `tracking`, `predecessor`, `lesson`, `audit-findings`, `out-of-scope`.

No fields beyond this enumerated set are permitted without a D5'' amendment. `epic:` rejection from D5 is carried forward.

---

## 2. Why supersession, not in-place edit

identifier-scheme/D3 (`:62-65`):

> "When an ADR is superseded by a new ADR that re-decides on the same topic, the new ADR's `id:` carries an explicit version suffix and the old ADR's `id:` freezes."

D5 is firm (`firmness: firm`, `:6`). Editing it in place would be Scenario 5 — the methodology claim "firm ADRs are firm" collapses. The parallelism-v1 precedent shows the versioned suffix pattern in practice: `cliff-failure-mode-and-v1-defenses D4` was partially superseded by `parallelism-v1` which explicitly states what it supersedes (`:6-9`). `identifier-scheme-v2` follows the same form: supersedes identifier-scheme D5 specifically, leaves D1–D4, D6–D9 intact.

---

## 3. Legacy 9 features

No update required. D5' is a strict superset of D5. A feature file using `intent:` + `shaped-from:` satisfies D5' because `intent:` is a recognized alias for `charter:` and `shaped-from:` is a permitted optional field. All 9 conforming files (`01-constraints.md:9`) are valid under D5' without modification.

---

## 4. `charter:` alias risk (Scenario 6)

D5' names the dual-key requirement explicitly in the decision text ("any reader MUST check both"). This converts a silent API assumption into a documented contract. The risk is not eliminated but is surfaced: tooling authors have a spec to follow. Optional: a helper function in `scripts/_feature.py` that returns `feature.get("charter") or feature.get("intent")` would enforce the contract mechanically at the one call site.

---

## 5. Ad-hoc field proliferation (Scenario 3)

D5' closes the open set. The ADR body states: "No fields beyond this enumerated set are permitted without a D5'' amendment." This replicates the `epic:` rejection pattern (`identifier-scheme.md:91`) but generalizes it: the named rejection becomes a closed enumeration. An author wanting `risk:` or `dependencies:` must bring it through `/decision`.

---

## 6. Why WIDEN-via-supersession beats NARROW

- **01-constraints.md:51** documents that NARROW's cost is data loss risk for `audit-findings` — the only load-bearing pointer to F-039–F-050. No canonical relocation target exists. WIDEN avoids this loss entirely.
- **02-journey.md:10** shows that under NARROW the migration cost is one YAML edit; but the pre-mortem notes the real cost is creating a relocation target for 7 cross-references that currently have no home.
- **03-premortem.md:70-72** concludes NARROW's worst case is medium-cost data loss with "a clear fix (define a relocation target before migration)" — a fix that is itself undesigned. WIDEN avoids the need to design that relocation target.
- **01-constraints.md:25** confirms no code reads feature-file fields at runtime. The risk of widening is future tooling, which is bounded by D5' closing the open set.

---

## 7. Where WIDEN-via-supersession falls short

- **Slice-entry `status: phase-1`** (Scenario 2) is not fixed by D5'. Must be cleaned up independently.
- **`created:` missing** from `orchestrator-paths.yaml` (`03-premortem.md:59`) is not addressed by D5' either.
- **`charter:` canonization** is a naming divergence from 9 existing files. If tooling is eventually built, the dual-key check must be implemented correctly everywhere. The "alias" approach adds permanent complexity vs. a clean rename.
- **D5' is looser than D5.** The minimal-schema philosophy of D5 (`01-constraints.md:10`) is not preserved. Future features that don't need the optional fields still live under a wider-than-necessary schema norm.

---

## 8. Implementation steps

1. Author `docs/adr/identifier-scheme-v2.md` with frontmatter and D5' text as sketched above.
2. Edit `docs/adr/identifier-scheme.md` frontmatter: set `superseded-by: identifier-scheme-v2` (frontmatter-only edit, permitted by `reversibility-guard.sh`).
3. Fix `orchestrator-paths.yaml` slice entry: remove `status: phase-1` from the slice entry (Scenario 2 fix — independent).
4. Add `created:` field to `orchestrator-paths.yaml` (`03-premortem.md:59`).
5. Update `docs/operational-reference.md:182` to document `charter:` as canonical and `intent:` as alias.
6. Update feature file creation template in `commands/claude-code/start-slice.full.md:130-149` to use `charter:`.
7. Optionally: add `_feature_intent()` helper to `scripts/` returning `charter or intent` to prevent future silent bugs.
