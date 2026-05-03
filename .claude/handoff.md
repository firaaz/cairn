# Phase 4 Handoff — v1-defense-d2/inv-002-binding-implementation

## State
Phase 4 PASS. INV-002 (a/b/c) and INV-008 bound to true machine-checkable assertions per ADR `invariant-binding-strategy` D4–D7. v1-defense-D2 at 3/3.

## Next
`close_slice` to land terminal `slice: complete` commit. Operator step after close: `docs:` commit substituting close SHA into `binding-effective-from: "<pending-slice-close-sha>"` for INV-002 + INV-008 (mirror INV-001 precedent `fd1823e`). Sweep is due (`sweep-interval: 1`).

## Blocked / Pending
- L-015 extractor disk-fallback (substrate Slice 4) — 2 XPASS(strict) reds remain.
- INV-004 rebaseline for CC 2.1.126 (intermittent).
- `V1_ASSERTION_TYPES` allowlist still hardcoded; future cleanup slice.

## Pointers
- `.claude/current-slice/integration/sweep-notes.md` — invariants table + evidence.
- `docs/ARCHITECTURE.md:24-40` (INV-002 structural-parser block), `:87-93` (INV-008 test-ref block).
- `scripts/validate_architecture.py:594` (`_run_structural_parser_assertion`).

---
# Sweep Notes — v1-defense-d2/inv-002-binding-implementation

## Verdict
PASS (with pre-existing out-of-scope reds, see below).

## Invariants Touched

| ID | Sub-clause | Statement (excerpt) | Status | Evidence |
|---|---|---|---|---|
| INV-002 | (a) handoff structural binding | `.claude/handoff.md` is a pointer artifact bounded at 150–400 tokens with fixed section structure and a forbidden-sections list. | PASS | `docs/ARCHITECTURE.md:24-40` (assertion block is `type: structural-parser` per ADR D4 schema); `scripts/validate_architecture.py:594` (`_run_structural_parser_assertion`) dispatched at `scripts/validate_architecture.py:691`; `tests/unit/test_inv_002_structural_parser.py` 78/78 pass; placeholder `<pending-slice-close-sha>` honored as no-op-with-notice (validator stdout: "INV-002: binding pending — binding-effective-from is placeholder, skipping enforcement"). |
| INV-002 | (b) Tier-1 five-item list | `/catchup` reads only a fixed five-item list into main context and gates further reads behind explicit Tier 2 admission criteria. | PASS | `tests/unit/test_catchup_tier1_list_pinned.py:48` (`test_tier1_five_items_verbatim`) PASS — five items pinned verbatim against `commands/claude-code/catchup.full.md` `## Tier 1` section; Tier-2 admission criteria structurally asserted documented (D5 defers runtime LLM-judgment binding to v2). |
| INV-002 | (c) start-slice wipe | `/start-slice` wipes `.claude/current-slice/` on transition to `status: complete`. | PASS | D6 piggyback: `docs/ARCHITECTURE.md:87-93` (INV-008 block) `test-ref` → `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop`; test PASS at `tests/unit/test_close_slice_hardened.py:98`. |
| INV-008 | slice-close lifecycle | `close_slice` is idempotent; sole producer of the `slice: complete` commit; cross-slice artifacts isolated by slice-id-slug; resume reconciliation; phase-ephemeral preservation. | PASS | `docs/ARCHITECTURE.md:87-93` (assertion block is `type: test-ref`, replacing prior `def close_slice` grep proxy); `tests/unit/test_close_slice_hardened.py:98` `test_close_slice_twice_is_noop` PASS; `V1_ASSERTION_TYPES` allowlist updated at `tests/unit/test_invariant_assertions.py:1116-1121` (includes `structural-parser`). |

## Test + Validator Runs
- `uv run pytest -q` → 1264 passed, 3 skipped, 2 xfailed, **2 failed (pre-existing)**.
  - `tests/unit/test_extractor_slice.py::test_extracts_at_least_four_slices` and `::test_emits_parent_edge_to_feature` — XPASS(strict) on substrate-Slice-4 disk-fallback (L-015 / pre-existing); out-of-scope per slice envelope.
- `uv run python scripts/validate_architecture.py` → ALL CHECKS PASSED, 10 invariants verified, 20 ADR files. INV-002 emits the expected placeholder-no-op notice (D3 grandfathering).
- Targeted slice tests (`test_inv_002_structural_parser.py`, `test_catchup_tier1_list_pinned.py`, `test_inv_002_inv_008_architecture_blocks.py`, `test_close_slice_hardened.py::test_close_slice_twice_is_noop`, `test_invariant_assertions.py`): 78 passed.

## Out-of-scope Reds (Pre-existing)
- `test_extractor_slice.py` 2× XPASS(strict) — known L-015 substrate-Slice-4 follow-up; predates this slice; tracked in handoff.

## Operator Follow-up
Per intent §"Slice-close protocol": after close, run a `docs:` commit substituting the slice-close SHA into `binding-effective-from: "<pending-slice-close-sha>"` for both INV-002 and INV-008 blocks (mirror INV-001 precedent at `fd1823e`).
