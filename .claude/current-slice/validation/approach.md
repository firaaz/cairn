# Phase 2 Validation Approach — compression/lever-2-orchestrator-split

## Gate-to-test map

| Intent gate | Test(s) in `tests/unit/test_slice_orchestrator_package_split.py` |
|---|---|
| V2 public-surface re-export (intent.md:81-90, 133) | `test_v2_public_surface_reexport[<name>]` parametrized over 13 public defs + 10 named constants + 58 underscore helpers; plus `test_v2_pricing_table_lexical_pattern` for the `^PRICING_TABLE_\d{4}_\d{2}_\d{2}$` pattern. |
| V3 CLI parity (intent.md:94-97, 135) | `test_v3_cli_dash_m_legacy_exits_zero`; `test_v3_cli_main_path_legacy_exits_zero`; `test_v3_cli_brief_argparse_no_error` (uses `--help` dry-run; never spawns a real slice). |
| V4 filesystem shape (intent.md:137) | `test_v4_filesystem_shape` — old file gone, package dir present, all 8 files present. |
| V5 architecture validator (intent.md:139) | `test_v5_architecture_validator_post_split` — see inversion strategy below. |
| V6 path-string sweep (intent.md:141) | `test_v6_path_string_sweep` — grep over `commands/`, `docs/ARCHITECTURE.md`, `docs/operational-reference.md`; `docs/adr/` excluded per ADR append-only exemption. |

## Inversion strategy notes (gates already-passing pre-split)

- **V2**: Pre-split `import slice_orchestrator as so; so.<name>` resolves all S3 names because the single file defines them. To force RED today the test additionally asserts `hasattr(so, "__path__")` — only true once the module becomes a package.
- **V3 form 1 (`python -m`)**: Already exits 0 pre-split (verified manually: rc=0 on `--legacy`). Test couples to the post-split filesystem by asserting `scripts/slice_orchestrator/__main__.py` is a file before invoking the CLI.
- **V3 form 2 (`__main__.py` direct path)**: Naturally RED today (file doesn't exist; `python … __main__.py` exits 2 with "can't open file").
- **V3 `--brief` argparse**: Couples to `__main__.py` existence; `--help` dry-run avoids creating a transient slice.
- **V5 validator**: Validator currently exits 0 (verified: 9 invariants verified, 15 ADRs checked). Test couples to V4 filesystem shape so it can only PASS once the package is in place AND the validator still exits 0.
- **V4 / V6**: Naturally RED today (legacy file present; ~24 path-string hits found).

## Ambiguity log

1. **OQ2 / V3 forms** — operator-resolved: test BOTH `python -m slice_orchestrator` and direct `__main__.py` path. Encoded as two separate tests.
2. **§S3 drift clause (intent.md:79)** — operator-resolved: assertions use `slice_orchestrator.<name>` only, never submodule-pathed.
3. **PRICING_TABLE_ enumeration (intent.md:87)** — operator-dismissed for enumeration; encoded as optional lexical-pattern test (`test_v2_pricing_table_lexical_pattern`) requiring at least one `PRICING_TABLE_<YYYY>_<MM>_<DD>` constant.
4. **V3 `--brief` dry-run** — intent.md offers "argparse-only OR run-and-rollback"; chose `--help` dry-run since it guarantees zero filesystem mutation and zero git ops, satisfying "must not leave a transient slice committed".
5. **V5 standalone-pass risk** — intent.md flags this as a known issue; inversion encoded by coupling to V4 filesystem shape and documented in the test's docstring.
6. **V6 ADR exemption** — intent.md:141 explicit; `docs/adr/**` not in the grep target list.

## RED verification (run output excerpt)

```
$ uv run pytest tests/unit/test_slice_orchestrator_package_split.py 2>&1 | tail -10
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v2_public_surface_reexport[_read_slice_state_strict]
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v2_public_surface_reexport[_write_slice_state]
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v2_pricing_table_lexical_pattern
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v3_cli_dash_m_legacy_exits_zero
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v3_cli_main_path_legacy_exits_zero
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v3_cli_brief_argparse_no_error
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v4_filesystem_shape
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v5_architecture_validator_post_split
FAILED tests/unit/test_slice_orchestrator_package_split.py::test_v6_path_string_sweep
============================== 90 failed in 0.24s ==============================
```

Sample failure reasons (one per gate):

- V4: `AssertionError: /…/scripts/slice_orchestrator.py must NOT exist post-split (intent.md:137)`
- V6: `V6 path-string sweep found scripts/slice_orchestrator.py references that must be updated… these hits live in in-envelope files: …/operational-reference.md:372:| CAIRN_PHASE_1_TIMEOUT_HARD …`
- V3 form 2: `…/scripts/slice_orchestrator/__main__.py must exist post-split (intent.md S1)`
- V5: `…/scripts/slice_orchestrator must exist; V5's validator-pass requires the package to be in place…`
- V2: forces RED via `assert hasattr(so, "__path__")` before name-presence check (pre-split single-file module has no __path__).

All 90 tests RED for reasons consistent with each gate's post-split contract.
