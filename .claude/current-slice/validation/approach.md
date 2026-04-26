# Phase 2 — test-design notes

Slice: `compression/lever-Z-substrate-full-pipeline`. Four RED test files.

## Driving patterns
- **Subprocess-driven role_guard tests** (mirrors `test_role_guard_grep_glob_deny.py`). Same `_run_hook` / `_backup_grant_log` / `_restore_grant_log` helpers, same JSON `tool_input` fixtures. Avoids module-import state across role-flip parametrizations.
- **Parametrized over the three new roles** (`pytest.mark.parametrize("role", NEW_ROLES)`) for D1-D6 — cuts ~5x duplication. D7 is explicit (asserts on the constant directly via `importlib.util.spec_from_file_location`, like `test_read_class_tools_constant_widened_to_three`).
- **Prompt-presence tests** use plain `Path.read_text()` + substring assertions. Substring choice: pair `cairn-knowledge` with `query` (server name shipped in Slice 2 + directive verb) so neither matches accidentally.

## Substring picks for S4
- (a) `cairn-knowledge` + `query` (lowercased)
- (b) `invariant` + `substrate` — `invariant` already present today; `substrate` is the new signal
- (c) `sweep-notes` + `Statement` (case-sensitive on column header) — `sweep-notes` already present; `Statement` is the new signal

## Deliberately NOT covered
- D7 is **smoke-only** for cross-role isolation. The G1-G7 phase-1-writer surface lives in `test_role_guard_grep_glob_deny.py` and is exercised separately as the regression baseline; duplicating it here would couple the two files.
- Bash deny-token coverage uses `cat <path>` only (one form). `_bash_path_tokens` is already exercised exhaustively in Slice-2-fixup tests; this slice's risk is per-role propagation, not token extraction.
- INV-010 prose (S5) and `invariant-check target:` invariance — covered by `validate_architecture.py`, not Phase 2 unit tests.

## Ambiguity resolution
None surfaced — intent §S6 explicitly enumerated D1-D7 and the three prompt files. S4 substring picks are conservative interpretations of intent's "stable enough not to bind to verbatim phrasing but specific enough to fail if absent."
