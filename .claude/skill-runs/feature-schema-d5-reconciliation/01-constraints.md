# Phase 0 — Constraint envelope

## Invariants

- **INV-006** (`docs/ARCHITECTURE.md:67`) — "Each feature has a file at `.claude/features/<id>.yaml` carrying the slice list with `after` dependency fields, feature intent, and creation date." Uses prose "feature intent" — does not name the specific YAML key. Does not constrain field name to `intent:` vs `charter:`.
- **INV-007** (`docs/ARCHITECTURE.md:75`) — feature files are Tier 2 context; no field-name dependency.

## ADR commitments

- **identifier-scheme/D5** (`docs/adr/identifier-scheme.md:82-91`) — Normative schema: `id`, `name`, `intent`, `shaped-from`. D5's stated purpose: `intent:` is "short prose statement of what the feature delivers (the why and the boundary)"; `shaped-from:` is "provenance." D5 explicitly rejects `epic:` but makes no mention of `status`, `tracking`, `predecessor`, `lesson`, `audit-findings`, or `out-of-scope` — neither allows nor prohibits them.
- **identifier-scheme/D5** (`:91`) — "Explicit rejection of an `epic:` field." Pattern: D5 rejects fields via named rejection statements. The six extra fields in `orchestrator-paths.yaml` carry no such rejection.
- **identifier-scheme/D2** — governs `id:` shape (flat semantic slug). Not at issue here.
- **feature-slice-model/D0** (`docs/adr/feature-slice-model.md:58`) — "Required fields: `id`, `intent`, `created`." `name` and `shaped-from` absent here (pre-dates D5). orchestrator-paths.yaml satisfies `id` and `created` implicitly via git; violates `intent:` (uses `charter:` instead).

## Documented schema (operational-reference.md)

- `docs/operational-reference.md:182` — Documents `shaped-from:` as "append-only to the feature file at creation." No mention of `charter:`. Canonically names `intent:` / `shaped-from:` only.

## Hook + script usage (what code reads feature files)

- `checks/reversibility-guard.sh` — no reads of feature file fields.
- `checks/reality-check.sh` — no reads of feature file fields.
- `checks/role_guard.py` — reads `intent.md` (skill-runs artifact), not `.claude/features/*.yaml`.
- `scripts/validate_architecture.py:393` — references "feature/slice level" in comments; no field reads.
- **No code in `checks/` or `scripts/` reads any feature-file field at runtime.** D5 schema is purely advisory.

## Skill/command usage

- `commands/claude-code/start-slice.md` — references `intent.md` (Phase 1 output artifact), not feature file fields.
- `cairn-tdd-feature` skill — reads plan docs at `docs/plans/<date>-<id>.md`, not `.claude/features/*.yaml`.
- Neither command/skill reads feature-file fields at runtime.

## Lessons relevant

- **L-012** (`docs/lessons.md:225`) — schema drift between hook and orchestrator stays silent until a tier-sensitive consumer hits it. Analogous risk: if a future tool consumes feature files expecting `intent:`, `charter:` would be the silent drift.
- **L-006** (`docs/lessons.md:106`) — scheme changes touching multiple artifact classes need feature-scoped migration, not a single slice. Relevant if WIDEN requires retroactive migration.

## Provenance of orchestrator-paths.yaml's schema choice

- Single commit: `df8ba20` — "test(orchestrator-paths): phase 2 RED suite + feature file (orchestrator staging recovery)". Author: firaaz. The feature file and the RED test suite were created together in a single Phase-2 commit. **No commit message explains the schema deviation.** Likely drafted under context pressure during Phase 2.

## Conformance audit (all 10 feature files)

9 of 10 use `intent:` + `shaped-from:`. Only `orchestrator-paths.yaml` uses `charter:` and omits `shaped-from:`. The 6 extra fields exist only in `orchestrator-paths.yaml`.

## Constraints that NARROW would satisfy / violate

- Satisfies: D5 (identifier-scheme), feature-slice-model D0, operational-reference.md.
- Satisfies: 9/10 precedent; no migration of other files.
- Violates: nothing structural. Migration cost: one YAML edit (rename `charter:` → `intent:`, add `shaped-from: null`, drop or relocate 6 extra fields).
- Risk: 6 extra fields carry real operational data (`audit-findings` F-039–F-050, `out-of-scope` exclusions, `tracking`, `predecessor`). Dropping = data loss; would need a home.

## Constraints that WIDEN would satisfy / violate

- Satisfies: preserves orchestrator-paths.yaml as-is; accommodates future features needing richer metadata.
- Violates: requires D5 amendment of a firm ADR.
- Risk: opens schema to unbounded field proliferation. D5's design principle is minimal; WIDEN inverts that. Precedent: every future feature author can add ad-hoc fields.
- L-012 pattern: if WIDEN formalizes `charter:` as alternative to `intent:`, any consumer coded to `intent:` breaks silently.

## Open questions

1. Where do the 6 extra fields live under NARROW? `audit-findings` is load-bearing.
2. Is `predecessor:` equivalent to `shaped-from:`? If so, NARROW may be a rename, not data loss.
3. Does D5's firmness permit amendment without supersession ADR?
