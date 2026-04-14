# SLICE-012 Implementation Notes

## Decisions not pinned by intent

1. **CLAUDE_PROJECT_DIR passthrough**: `integration_gate.py` sets `CLAUDE_PROJECT_DIR` to CWD when calling `validate_architecture.py`. This is necessary because validate_architecture.py resolves project root via env var or git, and test fixtures run in tmp_path (not a git repo). The intent specified "delegates to validate_architecture.py" but didn't specify the invocation mechanism (ambiguity A6 from Phase 2).

2. **Snapshot entry structure**: Used `{"size": <int>, "hash": "<hex>"}` dict per file. Intent required size and SHA-256 hash but left key names as implementation choice (A5).

3. **Envelope parsing**: `snapshot_diff.py` parses intent.md's YAML envelope section by scanning for `envelope:` followed by `- "glob"` lines. Stops at the next YAML key. Uses `fnmatch.fnmatch` for glob matching.

4. **Output routing**: `integration_gate.py` prints pass results to stdout, fail results to stderr. This keeps the pass/fail separation clean for callers that want to suppress noise.
