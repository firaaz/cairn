# Phase 2 Validation Approach — INV-001 Binding (slice 1 of 2)

## Stated intent (from intent.md / plan §Phase 2)

Bind INV-001 to a true `git-log-walk` validator: walker reads
`.claude/pipeline-substrate-registry.yaml`, classifies each commit in
`<binding-effective-from>..HEAD` against a registry prefix, and runs a
per-prefix Python verifier. The literal `<pending-slice-close-sha>` is
no-op-with-notice (D3 grandfathering).

## RED test set (verbatim from plan §Phase 2)

T1 registry-loads/schema-checks; T2 every-prefix-has-verifier;
T3 placeholder→noop+notice; T4 unregistered-prefix reported with SHA;
T5 sweep-missing-touch reported; T6 sweep-with-both-touches passes;
T7 feat: pass-through (F2 residual); T8 end-to-end validator exit 0.

## Resolved ambiguities

- **Import path.** Plan snippet uses `from scripts.validate_architecture
  import …`. cairn's `pyproject.toml [tool.pytest.ini_options]` declares
  `pythonpath = ["scripts"]`, and the precedent slice
  `tests/unit/test_inv_003_phase_topology.py` imports as
  `from validate_architecture import …`. Tests use the precedent form;
  Phase 3 must define symbols on that module.
- **Symbol names.** `_load_substrate_registry`, `_SUBSTRATE_VERIFIERS`,
  `_run_git_log_walk_assertion`. Plan §Phase 2 explicitly authorises a
  T2 micro-edit if Phase 3 renames — recorded here, not flagged.
- **T8 RED-ness.** Asserts `validator exits 0`. Currently passes under
  the legacy `file-exists` block; functions as a regression guard once
  Phase 3 swaps to `git-log-walk` + placeholder. Documented in the test
  docstring.

## Expected RED signature at Phase 2 commit

T1–T3, T7 RED via `ImportError` on the three private symbols.
T4–T6 RED via `FileNotFoundError` from `_init_repo_with_registry`
(real registry not yet created). T8 likely GREEN today (regression
guard); turns into a real binding test once the block is swapped.

## Out of scope (slice 2 territory)

INV-002 / INV-008 assertion blocks; `structural-parser` validator type;
`templates/handoff.md`; `commands/claude-code/handoff.full.md`;
`scripts/slice_orchestrator/` (D3 grandfathering uses post-close `docs:`,
not lifecycle code).

## Anti-behaviour adherence

No production code written. No source reads beyond `intent.md`,
the design/plan documents, and the existing
`tests/unit/test_inv_003_phase_topology.py` precedent for fixture style.
