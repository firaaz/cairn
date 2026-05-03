# Intent — v1-defense-d2/inv-002-binding-implementation

## What
Bind INV-002 (sub-clauses a, b, c) and INV-008 to true machine-checkable assertions
in `docs/ARCHITECTURE.md`, closing v1-defense-D2 at 3/3 firm invariants bound.

- INV-002(a): introduce a new `structural-parser` validator type in
  `scripts/validate_architecture.py`; assert `.claude/handoff.md` shape.
- INV-002(b): pin Tier-1 five-item list verbatim in
  `commands/claude-code/catchup.full.md` via a unit test; structurally assert
  the three Tier-2 admission criteria are documented.
- INV-002(c): bind via `test-ref` to existing
  `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop`.
- INV-008: upgrade grep-on-`def close_slice` proxy to the same `test-ref`
  (D6 piggyback — eliminates duplicated proxy).

## Why
ADR `invariant-binding-strategy` D4–D7 mandates true bindings for every firm
invariant. Slice 1 (`inv-001-binding-implementation`) closed INV-001;
this slice closes INV-002 and INV-008, retiring the last grep proxies on
firm invariants and discharging cliff-failure-mode-and-v1-defenses D2.

## Boundary
**In scope:** new `structural-parser` validator type + dispatch registration;
INV-002 + INV-008 assertion-block flips in `docs/ARCHITECTURE.md`;
`V1_ASSERTION_TYPES` allowlist update at
`tests/unit/test_invariant_assertions.py:1116`; new
`tests/unit/test_catchup_tier1_list_pinned.py`; reuse of
`test_close_slice_hardened.py::test_close_slice_twice_is_noop`;
post-close `docs:` SHA-substitution commit (operator step, mirrors
INV-001 precedent at fd1823e).

**Out of scope:** real-tokenizer integration (D7 rejects byte/4 approximation
remains); Tier-2 runtime LLM-judgment binding (D5 defers to v2);
pipeline-substrate-registry edits (slice-1 territory; closed);
INV-001 walker (already firm at e025714).

## Specification

### `structural-parser` validator (INV-002a)

Schema fields per ADR D4:

```
type: structural-parser
target: .claude/handoff.md
required-sections:    [State, Next, "Blocked / Pending", Pointers]
optional-sections:    [Features]
forbidden-sections:
  literal:  ["What This Session Was About", "What Was Accomplished",
             "Surprises or Discoveries", "Self-Check"]
  regex:    ['^##\s+(Lessons|Reflection|Notes)\b']
forbidden-content:
  regex:    ['I (was|am|will|just) ',
             '\d+\s*/\s*\d+\s+(passed|failed|tests)']
token-budget:
  approximation: bytes-per-token-4
  warn-at: 360
  fail-at: 440
binding-effective-from: <pending-slice-close-sha>
```

Verifier contract (public interface only — no implementation here):
- Loads target file UTF-8.
- Parses ATX `##` headings; case-sensitive literal compare.
- Required missing → fail with section name; forbidden present → fail
  with offending heading + line.
- Regex matches against full file body (not section-scoped) for
  `forbidden-content`.
- Token budget: `ceil(len(file_bytes) / 4)`; emit warn or fail per threshold.
- `<pending-slice-close-sha>` placeholder ⇒ no-op-with-notice
  (D3 grandfathering, mirrors INV-001 walker).

Dispatch registration: extend the existing branch table in
`_run_assertion` so `type: structural-parser` routes to the new verifier.
Additions only — no signature changes to existing verifier branches.

### Tier-1 verbatim pin test (INV-002b)

`tests/unit/test_catchup_tier1_list_pinned.py::test_tier1_five_items_verbatim`:

- Reads `commands/claude-code/catchup.full.md`.
- Asserts the literal five Tier-1 items appear in order:
  1. `.claude/handoff.md`
  2. `.claude/current-slice/slice.yaml`
  3. `.claude/sweep.yaml`
  4. `git log --oneline -5`
  5. `git status --short`
- Asserts the three Tier-2 admission criteria are present as documented
  text (structural assertion only — Tier-2 runtime LLM-judgment binding
  is explicitly v2 per D5).

### `test-ref` rebindings (INV-002c, INV-008)

Both invariants’ assertion blocks in `docs/ARCHITECTURE.md` become:

```
type: test-ref
test: tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop
binding-effective-from: <pending-slice-close-sha>
```

`test-ref` is already in `V1_ASSERTION_TYPES`; no allowlist change for
these two. The `structural-parser` addition for INV-002a is the only
allowlist edit.

### Substrate landmines (enumerate before Phase 3)

Phase-2 RED tests must not coerce Phase 3 to revert the spec. Known
string-match hot-spots:

1. `tests/unit/test_invariant_assertions.py:1116` — `V1_ASSERTION_TYPES`
   allowlist; add `"structural-parser"`.
2. Any test asserting INV-002’s current
   `type: grep / pattern: "Token budget: 150 to 400 tokens"` block in
   `docs/ARCHITECTURE.md` — must be updated to match the new
   `structural-parser` shape.
3. Any test asserting INV-008’s current
   `type: grep / pattern: "def close_slice"` block — update to the
   `test-ref` shape.
4. Any test enumerating allowed validator `type:` values in fixtures
   or schema docs.

Phase 1 must produce a complete enumeration in handoff so Phase 2 RED
covers all four classes and Phase 3 has no “revert under RED pressure”
escape (per the slice-1 lesson at memory `phase_3_revert_under_red_pressure`).

### Post-close SHA substitution

Mirror INV-001 precedent (fd1823e): a single `docs:` commit after slice
close substitutes the closing slice SHA into `binding-effective-from`
for all three assertion blocks (INV-002, INV-008). Operator step,
not in slice envelope. Walker / structural-parser both treat the
literal placeholder as no-op-with-notice, so the substrate is
self-consistent during the gap.

## Verification (Phase-4 evidence checklist)

1. `structural-parser` branch present in
   `scripts/validate_architecture.py` `_run_assertion` dispatch.
2. `V1_ASSERTION_TYPES` allowlist contains `"structural-parser"`
   at `tests/unit/test_invariant_assertions.py:1116`.
3. `docs/ARCHITECTURE.md` INV-002 block is `type: structural-parser`
   with the schema fields above; INV-008 block is `type: test-ref`.
4. `tests/unit/test_catchup_tier1_list_pinned.py::test_tier1_five_items_verbatim`
   passes against `commands/claude-code/catchup.full.md`.
5. `tests/unit/test_close_slice_hardened.py::test_close_slice_twice_is_noop`
   referenced from both INV-002(c) and INV-008 — green in suite.
6. Validator end-to-end exit 0 on full repo (placeholder SHAs
   no-op-with-notice).
7. Full suite green minus pre-existing known-XPASS / housekeeping reds
   tracked on `post-inv008-tech-debt`.
8. Post-close `docs:` SHA-substitution commit lands separately
   (out-of-envelope operator step) — verified by Phase 4 only as
   “placeholder remains until that commit”.

## References

- ADR `docs/adr/invariant-binding-strategy.md` — D4 (structural-parser
  schema), D5 (Tier-1 verbatim + Tier-2 deferral), D6 (piggyback),
  D7 (tokenizer rejection).
- ADR `docs/adr/cliff-failure-mode-and-v1-defenses.md` — D2 closure
  criterion.
- Slice-1 precedent: closing commit 2fb83f6; post-close SHA
  substitution fd1823e.
- Substrate-discipline memory: `phase_3_revert_under_red_pressure`,
  `V1_ASSERTION_TYPES_allowlist`.
