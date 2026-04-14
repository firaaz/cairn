# SLICE-010 Phase 2: Validation Approach

## Ambiguities in intent.md

### A1: Field requirements per assertion type
**Question:** Are all fields (type, pattern, target, expect, description) required for every type?
**Resolution (from intent type descriptions):** Type-specific. `grep` uses pattern+target+expect. `file-exists` uses target (+expect: exists). `test-ref` uses pattern (test path). Extra fields ignored.

### A2: test-ref validation depth
**Question:** Does test-ref verify file existence only, or also specific test function existence?
**Resolution (from intent):** "The assertion runner verifies the test exists." INV-004 example cites a file, not a function. File existence only — function-level validation would require AST parsing (v2-reserved).

### A3: Check D reporting scope
**Question:** Does check D report all failing invariants or stop at first?
**Resolution (from intent):** "Reports per-invariant PASS/FAIL" — plural, per-invariant. All failures reported.

### A4: Block content parsing
**Question:** Strict YAML or simple key-value text?
**Resolution:** Format is YAML-compatible (`key: "value"`). Tests generate valid YAML. Phase 3 picks parser; tests verify behavior.

### A5: Regex backslash escaping
**Question:** How are `\s`, `\w` etc. represented inside YAML-quoted assertion blocks?
**Resolution:** Not specified in intent. Tests avoid backslash sequences (use `def .+validate` not `def\s+validate`). **Phase 3 must document the escaping convention in implementation/notes.md.**

### A6: Multiple assertion blocks per invariant
**Question:** Can an invariant have more than one assertion block?
**Resolution:** Intent shows one per invariant. Tests assume one. Follow-on concern if needed.

## Test Strategy

All tests run the validator as subprocess with `CLAUDE_PROJECT_DIR` pointing at a `tmp_path` fixture. This matches existing test patterns (`test_validate_architecture.py`) and avoids coupling to internal function names.

### Coverage matrix

| Test class | Count | What it covers | Verification items |
|---|---|---|---|
| TestAssertionParser | 3 | Block parsing via check D output | V6 |
| TestGrepAssertion | 6 | grep: match/no-match, regex, glob | V1, V2 |
| TestFileExistsAssertion | 3 | file-exists: found/not-found, glob | V1, V2 |
| TestTestRefAssertion | 2 | test-ref: file exists/missing | V1, V2 |
| TestV2ReservedTypes | 2 | ast + custom skip-with-warning | V4 |
| TestCheckD | 5 | All-pass, failure naming, evidence, multi-fail, short-circuit | V1, V2 |
| TestCheckE | 3 | Missing-assertion warning, no-warn when present, exit 0 | V3 |
| TestEndToEnd | 4 | Mixed types, broken ref, no-block, ast | V1–V4 |
| TestCairnSelfDogfood | 1 | Regression guard | — |
| **Total** | **29** | | |

### RED state summary

12 failed, 17 passed. All failures are because check D/E don't exist yet — the validator ignores assertion blocks. The 17 passes are coincidental (valid A/B/C fixtures pass the existing checks). No test errors.

## Unresolved for Phase 3

- **A5**: Phase 3 should document the regex escaping convention for YAML assertion blocks in `implementation/notes.md`.
