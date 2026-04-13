# SLICE-006 Validation Approach

## Strategy

SLICE-006 produces an ADR, not code. Tests parse the ADR file as text and validate structural properties against intent.md's five verification items. All tests are RED at Phase 2 commit (the ADR doesn't exist yet) and flip GREEN when Phase 3 writes the ADR.

The ADR is located by globbing `docs/adr/*-phase-*.md` and excluding ADR-004 (`004-phase-lock-and-role-declaration.md`), which also matches the pattern.

## Verification item → test mapping

| V# | Intent verification item | Test(s) | Approach |
|----|--------------------------|---------|----------|
| V1 | Addresses all 4 spec items | `TestV1FourSpecItems` (4 sub-tests) | Regex patterns for characteristic phrases per item |
| V2 | Cites ≥3 slices with evidence | `test_v2_cites_three_slices` | Count distinct SLICE-00[1-5] refs appearing in lines with substantive context (>10 chars beyond the ID) |
| V3 | If superseding: file enumeration + migration | `test_v3_supersession_file_enumeration` | Conditional on `supersedes`/`supersedes-sections` containing ADR-004; checks Consequences section for each file from ARCHITECTURE.md:36 |
| V4 | If confirming: justification of re-confirmation | `test_v4_confirmation_justification` | Conditional on NOT superseding; checks for language about what changed since ADR-004 |
| V5 | A2 tripwire evaluated | `test_v5_a2_tripwire_evaluation` | Checks for "A2" + nearby evaluation/finding language |

## Ambiguity resolutions

**A1 — Testing an ADR-producing slice.** Tests validate structural properties of the ADR document (section presence, citation count, conditional path coverage). The envelope's `tests/unit/test_phase_*.py` pattern confirms Python tests are expected. Consistent with spec-v1 §2's principle that the Skeptic defines "correct" before the Builder works.

**A2 — "String-matches on phase names" (V3).** Per ARCHITECTURE.md:36, the exhaustive list is: `catchup.md`, `start-slice.md`, `scope-guard.sh`, `reality-check.sh`, `operational-reference.md`, and the `slice.yaml` status field. These are files/fields whose code performs string matching on phase name literals.

**A3 — Conditional V3/V4.** V3 (supersession) and V4 (confirmation) are mutually exclusive. Tests detect the ADR's path via frontmatter `supersedes`/`supersedes-sections` fields. Amendment (partial supersession via `supersedes-sections`) triggers V3.

**A4 — Citation substantiveness (V2).** A bare SLICE-NNN name-drop is insufficient per intent line 38 ("Claims without slice evidence are assertions, not findings"). Test requires each cited slice to appear in a line with >10 characters of surrounding context beyond the ID itself.

**A5 — Envelope output pattern.** `docs/adr/*-phase-*.md` is the output file for the new ADR. ADR-004 also matches this pattern and is excluded by prefix filter.

**A6 — A2 evaluation with 5 slices.** Intent says "evaluated against available evidence and the finding is recorded." The test verifies the ADR contains an A2 evaluation section with a finding — not that it reaches a specific conclusion. 5 slices is acknowledged as below the 10-slice tripwire window.

**A7 — Ceremony calibration vs D1 lock.** The whole point of SLICE-006 is evaluating whether D1's lock holds. The ADR may recommend supersession. Tests verify the ADR *addresses* ceremony calibration, not that it reaches a specific conclusion.
