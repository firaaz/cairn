# SLICE-004 Implementation Notes

## Decisions not pinned by intent

1. **Verdict priority order**: FP threshold breach > unclear entries > catch criterion > slice-count gate > insufficient data. Intent listed the criteria but didn't specify evaluation order when multiple conditions overlap. Tests from Phase 2 implied this ordering (e.g. FP breach overrides a valid catch on a different defense).

2. **YAML parsing**: Used regex-based key:value parsing (stdlib only). Handles the simple flat YAML the log and sweep.yaml use. No support for nested structures, arrays, or multi-line values — not needed for the specified formats.

3. **Duplicate detection key**: (slice, defense, date) tuple. Intent didn't specify what constitutes a duplicate; Phase 2 tests defined it as same slice+defense+date.

4. **Missing log file vs empty log**: Both exit 2. Missing file skips evaluation entirely; empty log (frontmatter but no entries) enters evaluation and reaches insufficient-data verdict.
