# Phase 2 Approach — v1-defense-d2/inv-002-binding-implementation

## Test files authored

1. `tests/unit/test_inv_002_structural_parser.py` — RED tests pinning the
   `structural-parser` validator type (D4): allowlist inclusion, dispatch
   registration, placeholder no-op-with-notice (D3 grandfathering), required-
   section enforcement, forbidden literal section, forbidden regex section,
   forbidden content regex (first-person + test-tally), token-budget
   warn/fail thresholds (bytes/4 per D7), and a happy-path against the live
   `.claude/handoff.md`.
2. `tests/unit/test_catchup_tier1_list_pinned.py` — verbatim five-item Tier-1
   pin (D5) and structural assertion that the three Tier-2 admission criteria
   remain documented.
3. `tests/unit/test_inv_002_inv_008_architecture_blocks.py` — pins the
   ARCHITECTURE.md flip: INV-002 block becomes `type: structural-parser`
   targeting `.claude/handoff.md`; INV-008 block becomes `type: test-ref`
   pointing at `test_close_slice_hardened.py::test_close_slice_twice_is_noop`;
   the old grep proxies (`Token budget: 150 to 400 tokens`, `def close_slice`)
   are gone.

## Substrate landmines covered (per brief)

- `V1_ASSERTION_TYPES` allowlist at `tests/unit/test_invariant_assertions.py:1116`
  is asserted to contain `structural-parser`.
- The literal grep proxy strings for INV-002 + INV-008 are asserted ABSENT
  from ARCHITECTURE.md, blocking the slice-1 "revert under RED pressure" mode.

## Ambiguity flagged (not a guess)

Intent.md §"`test-ref` rebindings (INV-002c, INV-008)" reads as if INV-002's
ARCHITECTURE.md block becomes `test-ref`, contradicting the brief's
"Flip INV-002 assertion block to `type: structural-parser`". Resolved via
ADR D6 piggyback: INV-002(c) is bound transitively through INV-008's
`test-ref`, so INV-002 carries only the structural-parser block. Tests
encode this resolution; if Phase 3 reads it differently, raise an issue
before greening.

## Verifier signature assumed

The verifier consumes a rich nested dict (from a YAML-parsed assertion
body) and returns `str | None`. Tests bypass the parser via `_run_assertion`
to decouple from the parser-upgrade choice.
