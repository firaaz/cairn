# SLICE-003 Validation Approach

## Test files

- `tests/unit/test_progressive_disclosure.py` — S1–S5 structural tests + CLAUDE.md terseness (V-item 5)
- `tests/unit/test_context_budget.py` — INV-004 live measurement via `claude -p "hi" --output-format stream-json`

## Ambiguity resolutions applied

- **Token counting (A1)**: tiktoken cl100k_base primary, char/word heuristic fallback. Balances accuracy vs resource usage.
- **Diagram detection (R3, expanded)**: S4 generalized beyond Graphviz to cover Mermaid, PlantUML, fenced diagram blocks, box-drawing chars, and ASCII art patterns. Original intent only banned Graphviz — user directed broader enforcement.
- **INV-004 measurement (A2)**: live measurement. Test spawns CC, parses stream-json output for first usage entry, asserts ≤22k.
- **Carried-forward I1/M1 (A3)**: deferred to Phase 4 manual verification, not Phase 2 tests.
- **Measurement file (A4)**: test records to `docs/plans/measurements/2026-04-12-slice-003.txt` as side effect.
- **Subjective triggers**: added S3-supplement test banning common subjective phrases in `## Load full` sections per intent's discrete-predicate requirement.

## RED state (pre-implementation)

| Test | Status | Reason |
|------|--------|--------|
| S1 (≤500 tokens) | FAIL | All 8 lite files 531–3659 tokens |
| S2 (## Load full) | FAIL | No file has the section |
| S3 (predicates resolve) | PASS (vacuous) | No sections to check yet |
| S3 (no subjective triggers) | PASS (vacuous) | Same |
| S4 (no diagrams) | PASS (vacuous) | Current files lack diagram DSL patterns |
| S5 (no H3+) | FAIL | 4 files have deep headers |
| CLAUDE.md terseness | FAIL | Rule not yet present |
| INV-004 (≤22k) | PASS | Current cairn already at ~20k tokens post-SLICE-002 |

## Key finding

INV-004 passes at ~20k tokens WITHOUT progressive disclosure. SLICE-002's ADR-002 context discipline work already compressed turn-1 below the 22k budget. Progressive disclosure (S1–S5) is still needed as structural insurance — commands will grow, and without the ≤500-token cap, a single command rewrite could push past 22k. The INV-004 test serves as a regression guard.

## V1–V7 hard gate

All 7 existing tests in `test_context_discipline_protocol.py` pass. No modification to that file.
