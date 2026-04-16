# Validation Approach — SLICE-016 hook-tolerance

## Ambiguity enumeration

Four ambiguities identified; all resolved by reference to ARCHITECTURE.md, the identifier-scheme ADR, or subagent source reads. No human escalation required.

1. **V6 gap confirmation**: scope-guard.sh and reality-check.sh confirmed to have zero identifier-shape-matching code. Both are purely path-based. No changes needed; tests verify no-regression only.
2. **index.md false positive**: `docs/adr/index.md` is not an ADR. Must remain unmatched by the widened glob. Regression test added.
3. **Flat-slug boundary**: ADR D2 defines flat slugs as kebab-case semantic strings (e.g. `identifier-scheme`, `parallelism-v1`). Distinguished from legacy by not starting with `[0-9]`.
4. **GREEN-for-wrong-reason tests**: Some V3/V4 tests on flat-slug ADRs pass currently because the guard ignores the file entirely (exit 0). After Phase 3, they pass because the guard recognizes the file and allows the action (also exit 0). Same observable exit code; different mechanism. Acceptable for TDD — these are regression tests, not RED tests.

## Test strategy

Tests invoke hooks via subprocess with synthesized JSON payloads on stdin (`{"tool_name": ..., "tool_input": ...}`), following the pattern established in `test_feature_scope_guard.py`.

### RED tests (fail until Phase 3)
- **V1**: Write to existing `docs/adr/identifier-scheme.md` blocked with `REVERSIBILITY GUARD: ADRs are append-only` message
- **V3 partial**: Edit body prose on flat-slug ADR blocked (non-zero exit)
- **V4 partial**: Editorial-fix bypass on flat-slug ADR logs to `.claude/adr-editorial-fixes.log`

### GREEN regression tests
- **V2**: Legacy ADR Write protection unchanged
- **V3 partial**: Frontmatter-only Edit allowed on both forms (4 prefix variants × 2 shapes)
- **V3 partial**: Body Edit on legacy ADR still blocked
- **V4 partial**: Editorial-fix bypass on legacy ADR still allowed
- **V5**: Write to non-existent ADR paths allowed for both shapes
- **V6**: scope-guard allows flat-slug ADR writes/edits; reality-check ignores non-Python files
- **index.md regression**: Write/Edit on `docs/adr/index.md` not caught by widened pattern

## Envelope coverage
- `reversibility-guard.sh`: V1, V2, V3, V4, V5, index.md regression
- `scope-guard.sh`: V6
- `reality-check.sh`: V6
- V7 (full suite passes) is a Phase 4 gate, not a Phase 2 test
