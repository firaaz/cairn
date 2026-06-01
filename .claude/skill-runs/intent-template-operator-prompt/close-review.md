# Close-review — intent-template-operator-prompt

Back-loaded reviewer, fresh context. Verdict from live diff + live re-run, not
the construction conversation.

## contract-clause-check

**MS-1 — `## Operator Prompt` precedes `## What`.** PASS.
`templates/intent.md:24` adds `## Operator Prompt`; `## What` is at line 33.
Regression test cursor-walk (`test_template_extraction.py:110-130`) skips the
new heading and still asserts the eight in order.

**MS-2 — guidance states verbatim-pinned + derive-exempt.** PASS.
`templates/intent.md:25` `<!-- VERBATIM, derive-exempt.` and `:28-29` "the one
exception to the derive-don't-fabricate contract above: pinned input, NOT
Phase-1 derivation."

**MS-3 (regression-meta) — eight headings present + in order.** PASS.
`test_template_extraction.py::test_intent_template_shape_and_eight_headings`
GREEN; baseline named in the clause holds.

**MN-1 — INV-003 four-phase contract + the eight's derive-don't-fabricate
untouched.** PASS. `git diff` of `phase-1-tdd.md` is a single line (the Intent
shape paragraph); grep for phase-count/role/INV-003 lines = none touched.
`validate_architecture.py` → ALL CHECKS PASSED, 12 invariants. The carve-out is
scoped to one named section in all three sites: template comment
(`:19` "the section that precedes the eight is the one exception"), section
comment (`:28` "the one exception"), and shape source (`phase-1-tdd.md:13`
affirmatively re-binds: "Derive-don't-fabricate binds only the eight schema
sections that follow"). The `wrong-if` leak (carve-out readable as applying to
any of the eight) does NOT occur — wording is single-section everywhere.

## evidence-adequacy-check

Adequate for the contract depth (one additive section + one shape-source
reconciliation). Live re-run confirms all reported evidence: focused suite 14
passed; `uv run pytest -q` → 640 passed, 2 skipped, 2 xfailed;
`validate_architecture.py` ALL CHECKS PASSED.

The flagged residual (carve-out now in TWO places — template + shape source —
must stay in sync) IS now mechanically guarded, not prose-only:
`test_operator_prompt_reconciled_in_authoritative_shape_source` asserts both
"operator prompt" and "exempt" appear in `phase-1-tdd.md`. Narrow gap: it
checks presence + exempt-marking, not the positive "binds only the eight"
sentence, and matches case-insensitive substrings anywhere in the file — a
future reword could pass the test while weakening the bind. Residual risk, not
a block: the prose currently reads correctly and the leak the intent names is
absent.

## scope-check

Changed files ⊆ `execution-scope`. Diff touches exactly the three listed:
`templates/intent.md`, `.claude/agents/phase-1-tdd.md`,
`tests/unit/test_intent_template_graduated_contract.py`. No out-of-scope file.

Scope-statement honesty: "pin the operator's verbatim framing at the top …"
matches a +13/-0 template change + 1-line shape-source reconciliation + 64 test
lines. No under- or over-claim; contract depth fits diff size (additive, two
must-satisfy + one regression-meta clause for a small additive diff).

## verdict

close-review-pass. Every clause holds against the live diff, evidence is
adequate and re-confirmed, diff stays in scope. One documented residual: the
in-sync guard is presence-based, not bind-wording-based.
