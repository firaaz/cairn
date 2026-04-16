---
slice: identifier-scheme/validator-flat-slug
slice-yaml-id: SLICE-018
date: 2026-04-16
phase: 1-intent
feature: identifier-scheme
invariants-touched: [INV-005]
adrs-referenced: [identifier-scheme]
envelope:
  - "scripts/validate_architecture.py"
  - "tests/unit/test_validate_architecture.py"
out-of-scope:
  - "docs/adr/*.md — no ADR edits; this slice does not rename existing ADR files (that is the deferred Phase 2 one-shot rename sweep per `identifier-scheme` D7)"
  - "docs/ARCHITECTURE.md — no invariant text edits; a follow-on /refresh-architecture run will re-point INV-005 at `identifier-scheme` once this validator widening lands"
  - "checks/*.sh — hook tolerance was completed in SLICE-016 (identifier-scheme/hook-tolerance); not re-opened here"
  - "commands/claude-code/** — slash-command surface is unrelated to validator parsing"
  - ".claude/features/** — feature file is already updated for slice registration; not further touched"
  - "Phase 3 legacy-format removal — identifier-scheme D7 defers this indefinitely; this slice widens tolerance, never narrows it"
v1-scope: "D1, D2 substrate (ADR-003). The validator is the mechanism that makes D1's automated architecture refresh gating meaningful and D2's code↔invariant binding enforceable. Non-v1-scope waiver NOT invoked."
---

## What and Why

`scripts/validate_architecture.py` is the machine check that guards ARCHITECTURE.md / ADR corpus consistency (Check A: every invariant references a valid, non-superseded ADR; Check B: every accepted firm ADR has at least one invariant; Check C: no reference to a superseded ADR; Checks D/E: per-invariant assertion execution and advisory gaps). It predates the `identifier-scheme` ADR and only recognizes legacy `NNN-slug.md` ADR filenames plus `ADR-NNN` reference shape in `**INV-NNN**` invariant lines.

`docs/ARCHITECTURE.md § Current Phase Constraints § Identifier scheme` names this gap explicitly: "Substrate gap: `scripts/validate_architecture.py` does not yet recognize non-numeric ADR IDs in `**INV-NNN**` lines, so INV-005 cites the operationally dependent ADR-006 as a validator-anchored proxy while naming `identifier-scheme` as the authoritative source in prose. Validator widening is queued substrate work for a follow-on slice." This slice is that follow-on.

The target behavior: the validator treats `docs/adr/<id>.md` flat-slug filenames (e.g. `identifier-scheme.md`, `d3-bypass-classification.md`) as first-class ADRs indistinguishable from legacy `NNN-slug.md` files, and recognizes flat-slug `id:` values (e.g. `identifier-scheme`) as valid ADR references inside ARCHITECTURE.md invariant entries, alongside the existing `ADR-NNN` shape. Both naming conventions coexist indefinitely — `identifier-scheme` D7 defers Phase 3 (legacy-format removal) without a target date.

## Specification Detail

**ADR discovery.** Any file under `docs/adr/` matching `*.md` (excluding `index.md` and any file whose frontmatter `status:` is `superseded` or `deprecated`) is an ADR, regardless of whether its filename starts with digits. The validator parses ADR frontmatter (the existing `parse_adr` contract) for every such file.

**ADR `id:` resolution.** An ADR's canonical identifier for cross-reference purposes is the value of its frontmatter `id:` field when present, otherwise the filename-derived legacy ADR number. The two resolution paths:

- Flat-slug ADR (e.g. `docs/adr/identifier-scheme.md` with `id: identifier-scheme`): canonical id is `identifier-scheme`. No `ADR-NNN` alias is synthesized — flat-slug ADRs are addressed by their flat slug only.
- Legacy ADR (e.g. `docs/adr/004-phase-lock-and-role-declaration.md`, no `id:` field): canonical id is `ADR-004`, derived from the filename's leading digits.

**Invariant line reference parsing (Check A).** ARCHITECTURE.md's invariant entries look like `**INV-NNN** ... (ADR-NNN; other-ref; ...)`. The trailing parenthetical enumerates ADR references. The validator accepts each of the following as a valid reference token and resolves it to the corresponding ADR:

- `ADR-NNN` (legacy form — resolves to the ADR whose filename starts with that numeric prefix)
- A flat-slug token matching an existing ADR's `id:` field (e.g. `identifier-scheme`)

Reference tokens that match neither an existing `ADR-NNN` legacy id nor any flat-slug `id:` are reported as invalid references under Check A. Commentary text inside the parenthetical that is not a reference token (e.g. `confirmed by ADR-009`, `partially superseded by ADR-007`) continues to be tolerated at parity with current behavior — this slice does not tighten comment handling.

**Check B (ADR coverage).** Every accepted, non-superseded ADR — whether legacy or flat-slug — must be referenced by at least one invariant. The firmness/status rules are unchanged.

**Check C (no reference to superseded).** If an invariant references a flat-slug id whose ADR has `superseded-by:` set, the validator reports the same error class it currently reports for `ADR-NNN` superseded references.

**Check D (per-invariant assertions) and Check E (advisory gaps).** Unchanged semantically; the assertion runner is independent of ADR reference parsing.

**Exit codes.** Unchanged: 0 = all checks pass, 1 = one or more checks failed, 2 = missing required files or project root could not be resolved.

**CLI contract.** Unchanged: `uv run python scripts/validate_architecture.py`, run from the consumer project root or via `.slice-system/`.

**Environment-variable substrate.** No new env vars introduced.

**Stdout/stderr shape.** Existing human-readable reporting preserved. When a flat-slug reference fails to resolve, the error message names the flat-slug token verbatim (not a synthesized `ADR-NNN` label).

## Boundary

Out of scope is enumerated in the YAML envelope above. Additional clarifications:

- This slice does NOT migrate ARCHITECTURE.md's INV-005 away from its current ADR-006 proxy citation. That re-pointing is a follow-on `/refresh-architecture` concern after this validator widening lands.
- This slice does NOT rename any existing `NNN-slug.md` ADR file to flat-slug form. The one-shot rename sweep is a deferred Phase 2 of `identifier-scheme` D7.
- This slice does NOT add any new ADR. `adrs-created: []`.
- This slice does NOT change hook behavior. Hook tolerance was completed by SLICE-016 (`identifier-scheme/hook-tolerance`).
- This slice does NOT touch the decision-point id shape (`<adr-id>/<decision-slug>`) — only ADR ids.

## Verification

1. **Legacy ADR parity regression.** Running the validator against the current repository (where every invariant in ARCHITECTURE.md cites legacy `ADR-NNN`) continues to exit 0. No false positive under Check A; no false negative under Check B.

2. **Flat-slug ADR discovered and parsed.** With `docs/adr/identifier-scheme.md` and `docs/adr/d3-bypass-classification.md` present (both currently checked in), the validator treats them as first-class ADRs. An invariant referencing `identifier-scheme` as a flat-slug token resolves without error under Check A.

3. **Flat-slug ADR lacking invariant coverage fails Check B.** When a flat-slug ADR with `status: accepted` and `firmness: firm` exists and no invariant references its `id:`, Check B reports it as uncovered. This matches the legacy behavior applied to the widened discovery set.

4. **Flat-slug superseded ADR triggers Check C.** When an invariant's parenthetical contains a flat-slug token whose target ADR has `superseded-by:` set, Check C reports it as a reference-to-superseded error using the flat-slug token as the identifier in the error string.

5. **Unknown flat-slug token fails Check A.** When an invariant's parenthetical contains a token that matches neither an existing `ADR-NNN` legacy id nor any flat-slug `id:`, Check A reports it as an invalid reference. The error names the token verbatim.

6. **Check D/E untouched.** Existing per-invariant assertion execution and advisory-warning behavior is unchanged. Assertion blocks referencing the same invariants behave identically before and after this slice.

7. **Project-root resolution regression bank preserved.** The existing V1–V6 project-root resolution tests in `tests/unit/test_validate_architecture.py` continue to pass. This slice does not modify `_resolve_project_root` behavior.

8. **Full test suite passes.** `uv run python -m pytest` exits 0 at end of Phase 3.

9. **Validator self-check passes.** `uv run python scripts/validate_architecture.py` against the cairn repo itself exits 0 at end of Phase 3 and Phase 4.

10. **INV-005 evidence path prepared.** The validator can accept an ARCHITECTURE.md variant in which INV-005's trailing parenthetical is rewritten to `(identifier-scheme)` instead of `(ADR-006)` without emitting a Check A error. This is verified by fixture (tests construct such an invariant and assert no error), not by editing ARCHITECTURE.md itself — that re-point is out of this slice's envelope.
