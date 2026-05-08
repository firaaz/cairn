# Phase 2 Approach — cairn-m5-f2-consumer-doc-surface

## Tests authored (13 total, all RED)

**`tests/unit/test_consumer_doc_surface.py`** (7)

- `test_claude_md_cross_cutting_sections_carry_both_tag` — F2.1 Step 1; allows `[both]` or `[maintainer]` per the enumerated lines, accepting same-line or predecessor placement (intent L23).
- `test_consumer_md_anchors_resolve_into_claude_md` — FLI-1 (L46); slugify collects ATX headings and bold-lead callouts so CLAUDE.md `**Operator envelope**`-style anchors resolve.
- `test_consumer_md_word_count_within_budget` — FLI-6 (L51).
- `test_phase_skill_mapping_doc_exists` — F2.4 Step 1 (Verification L35).
- **`test_phase_skill_mapping_doc_preserves_validator_regex_anchors` — RISK SURFACE COVERAGE TEST.** Covers intent L40-42 + FLI-3 (L48). Beyond existence: each `phase-N-tdd` slug and its role must co-occur in a 4-line window so the table-row binding INV-003's `validate_phase_topology` keys on survives the T4 relocation.
- `test_operational_reference_phase_skill_guide_is_a_pointer` — FLI-4 (L49); ≤5 non-empty body lines + link literal.
- `test_adoptable_disciplines_lists_four_disciplines` — F2.5 Step 1.

**`tests/unit/test_template_extraction.py`** (5)

- `test_feature_plan_template_shape`, `test_intent_template_shape_and_eight_headings` (FLI-2 — eight ordered headings), `test_sweep_notes_template_body_sections`, `test_adr_frontmatter_template_keys`, `test_active_envelope_template_default_mode_off_and_self_pattern` (FLI-5 — self-pattern in commented block, not active default).

**`tests/unit/test_readme_reading_order.py`** (1)

- `test_readme_has_four_step_reading_order` — F2.3 Step 1; contiguous 1-4 numbered list naming README / CONSUMER / operational-reference / spec-v1.

## Ambiguities resolved

- **Tag placement**: plan F2.1 Step 1 says same line or above; test scans both.
- **Self-pattern locus**: FLI-5 says "commented example block"; test requires comment-prefix.
- **`mode: off`**: PyYAML resolves `off` to `False`; test accepts both.
- **Slugify**: per FLI-1 (lowercase; `[`/`]` and spaces -> `-`; strip non-alphanumeric except `-`; collapse repeats).

## Flagged for operator

None blocking. Risk Surface now under contract test; Phase 4 must RAISE_ISSUE if `validate_architecture.py` still hard-codes `operational-reference.md` (intent L59 keeps that script outside envelope).

## RED confirmation

`uv run pytest` on the three files: **13 failed, 0 passed** — missing-file + content-shape failures, exactly as intent Verification (L35-37) anticipates.
