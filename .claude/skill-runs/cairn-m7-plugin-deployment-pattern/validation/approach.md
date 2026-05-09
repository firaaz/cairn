# Phase 2 Approach — cairn-m7-plugin-deployment-pattern

## Tests written

**`tests/unit/test_marketplace_schema.py`** — five literal-shape assertions (intent.md §S2):

1. `test_marketplace_source_source_is_github` — ADR D2 / FLI-1.
2. `test_marketplace_source_repo_is_firaaz_cairn` — ADR D2.
3. `test_marketplace_source_ref_is_release` — ADR D2 + D7 / defends S7.
4. `test_marketplace_plugin_entry_omits_version` — ADR D3 / FLI-6.
5. `test_marketplace_source_omits_type_field` — regression guard.

**`tests/unit/test_release_workflow.py`** — four shape assertions (intent.md §S4):

1. `test_release_workflow_exists` — defends M7.2.
2. `test_release_workflow_has_workflow_dispatch_with_version_input` — D5 / FLI-2.
3. `test_release_workflow_uses_force_with_lease_only` — D6 / FLI-3.
4. `test_release_workflow_commit_prefix_is_chore` — S5 / INV-001 / FLI-5.

## Risk Surface coverage

`test_marketplace_source_source_is_github` + `test_marketplace_source_ref_is_release` are the **Risk Surface coverage** category, defending the prerequisite shape M7.5 assumes (intent.md:110, M7.5 prose; intent.md:94, audit check 9 NON-SKIPPABLE). Per ADR D9 the empirical residual is offloaded to audit check 9 — no fabricated unit test pretends to verify the resolver-follow claim itself.

## FLI mapping

- FLI-1 (atomicity) → schema #1 + #5 jointly.
- FLI-2 (cross-check) → workflow #2 (input present; cross-check execution belongs to Phase 4 audit).
- FLI-3 (force-with-lease) → workflow #3.
- FLI-4 (first-party Actions only) → not asserted (string-grep on `uses:` would be brittle; defended at review).
- FLI-5 (chore prefix) → workflow #4.
- FLI-6 (no marketplace version) → schema #4.
- FLI-7 (audit check 9 merge gate) → process invariant; not unit-testable.

## RED verification

`uv run pytest tests/unit/test_marketplace_schema.py tests/unit/test_release_workflow.py -v` → **8 FAILED, 1 PASSED**. The one passing test (`test_marketplace_plugin_entry_omits_version`) holds at HEAD because the legacy `"type":"git"` shape coincidentally omits `version`; the assertion remains load-bearing as a regression guard defending FLI-6 against silent-mask drift post-rewrite. Full-suite run shows 22 FAILED = 14 baseline (per `/tmp/cairn-m7-plugin-deployment-pattern-baseline-failures.txt`) + 8 new; no new regressions.

Per Phase 2 verification language: any failure beyond baseline cites the baseline file as authority.

## Ambiguities resolved

- PyYAML parses bare `on:` as Python `True` (YAML 1.1). Test tolerates either key.
- FLI-4 not encoded as a unit test — string-grep is brittle; review-time defense.
