# SLICE-010 Phase 3 Implementation Notes

## Decisions not pinned by intent

1. **Assertion block parser uses simple line-by-line key:value parsing** — no YAML library dependency. Fields are extracted via `str.partition(":")` with quote stripping. This keeps the validator stdlib-only.

2. **Glob resolution via `Path.glob()`** — target fields in assertions are resolved relative to project root using `pathlib.Path.glob()`. This handles both literal paths and glob patterns uniformly.

3. **Check E output goes to stderr** — warnings for missing assertion blocks print to stderr so they don't pollute the structured stdout output (which contains PASS/FAIL results). Tests verify via `result.stdout + result.stderr`.

4. **V2 reserved type warnings also go to stderr** — consistent with check E's warning channel.

5. **Grep assertion short-circuits on first match** — for `expect: match`, stops reading files once any match is found. For `expect: no-match`, also stops on first match (to report failure).
