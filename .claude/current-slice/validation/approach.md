# SLICE-018 — Phase 2 Approach

Skeptic's notes for the RED-side of the TDD cycle on
`tests/unit/test_hook_relpath_bypass.py`. This file is Phase 2 reasoning
and MUST NOT be read by Phase 3.

## Bypass reproduction — baseline

Verified pre-slice against the current `checks/reversibility-guard.sh`:

```
$ echo '{"tool_name":"Write","tool_input":{"file_path":"docs/adr/identifier-scheme.md","content":"overwrite"}}' \
    | bash checks/reversibility-guard.sh
$ echo $?
0
```

Same for `Edit` body-prose. Case pattern `*/docs/adr/*.md` does not match a
bare-relative path because `*/` requires at least one segment before `docs/`;
mechanically verified by `case` in bash (see Phase 1 intent §Why).

`.slice-system/docs/adr/identifier-scheme.md` matches today because
`*/` consumes `.slice-system`. That path is the protected half of the
asymmetry the slice closes.

## Ambiguity enumeration

Intent `.claude/current-slice/intent.md` specifies V1–V12 with unusual
precision. The enumeration below records the few points where judgement
entered, plus one arithmetic typo flagged rather than patched.

### A1 — Relative paths with `./` prefix

Intent names three input shapes: absolute, bare-relative, `.slice-system/`-
prefixed. A fourth shape — `./docs/adr/foo.md` — is not listed. Resolution:
out of scope for verification. The test suite does not assert on `./`-
prefixed paths; Phase 3 may choose to normalize them or not. If the
implementation accidentally catches `./`-prefixed paths via the canonical
form, no test fails; if it does not, no test fails. Flag if user brings
up this shape later.

### A2 — Absolute path outside `PROJECT_ROOT`

Intent §1 says strip `$PROJECT_ROOT/` only if `$FILE` is absolute and
begins with it. Intent §7 says "pattern matching on the raw `$FILE`
continues to protect absolute-path inputs as it does today". Resolution:
an absolute path outside PROJECT_ROOT keeps today's behavior — the old
`*/docs/adr/*.md` pattern still catches it via the `*/` prefix. No new
test; absolute-path denies (V3/V6 absolute shape) already cover this.

### A3 — PROJECT_ROOT resolution outside a git repo with `CLAUDE_PROJECT_DIR` unset

Intent §7 mandates the hook MUST NOT crash under `set -euo pipefail`.
V11 is the crash guard. Resolution: test runs the hook with `cwd` a
tempdir outside any git repo, `CLAUDE_PROJECT_DIR` forcibly unset, and
asserts exit in {0, 2} within 10 s. The deny verdict is deliberately not
pinned — either exit is legal, only the absence of a crash is asserted.

### A4 — V10 missing-`jq` testability

V10 requires invoking the hook with `jq` absent. Approach: set `PATH` to
`/usr/bin:/bin` (no `jq` installed there on macOS or Linux defaults).
Pre-flight check: `subprocess.run(["command","-v","jq"], env={"PATH":...})`
— if it still resolves `jq`, `pytest.skip` with the reason that the
environment cannot strip `jq` cleanly. Matches intent's explicit skip
guidance.

### A5 — V12 scenario count (intent typo)

Intent prose reads "Four tool-scenarios × three shapes = twelve
assertions", but the enumerated list contains five scenarios:

1. Write existing
2. Edit frontmatter
3. Edit body-prose
4. Edit body-prose with `ADR_EDITORIAL_FIX=1`
5. Write non-existent

Resolution: implement all five enumerated scenarios (5 × 3 = 15
parametrized equality checks). The enumeration is the source of truth;
the count is treated as an arithmetic typo rather than a spec dispute.
Not escalated — this is below the bar for human resolution, and Phase 3
is unaffected by the count discrepancy.

### A6 — Editorial-fix log line format

Intent §6 permits the log line to reference either the raw `$FILE` or
the canonical form, as long as the choice is consistent. Test assertion
mirrors `test_hook_tolerance.py`'s V4 log test: assert a new line
appears in `.claude/adr-editorial-fixes.log` and that the line contains
`identifier-scheme`. Format-agnostic to give Phase 3 freedom.

## Test file structure

One file: `tests/unit/test_hook_relpath_bypass.py`. Helpers inline (do
not import from `test_hook_tolerance.py` — V9 requires that file to run
unmodified, and cross-file imports would couple the two suites). Helper
`_run_hook` follows the pattern in `test_hook_tolerance.py:54`.

### Test classes, one per verification item

- `TestV1BareRelativeFlatSlugBlocked` — RED
- `TestV2BareRelativeLegacyBlocked` — RED
- `TestV3SliceSystemPrefixedDeniesConsistently` — GREEN (regression)
- `TestV4FrontmatterEditAllowedAllShapes` — parametrized 4 keys × 3 shapes × {flat, legacy}
- `TestV5NewAdrWriteAllowedAllShapes` — 3 shapes × {flat, legacy}
- `TestV6IndexExemptAllShapes` — 3 shapes × {Write, Edit}
- `TestV7EditorialFixCoversCanonicalForms` — bare-relative log entry RED;
  `.slice-system/` GREEN
- `TestV8EnvAndLockfileRegressions` — `.env`, `.env.local`, `uv.lock`,
  `package-lock.json`, `poetry.lock`; bare-relative + absolute
- `TestV10MissingJqContract` — conditional skip
- `TestV11NoCrashUnderIndeterminateProjectRoot` — tempdir + env override
- `TestV12VerdictSymmetry` — parametrized 5 scenarios × equality across
  3 shapes (single assertion per scenario)

### V9 handling

V9 requires `tests/unit/test_hook_tolerance.py` to stay green unmodified.
This is a Phase 4 full-suite check, not a unit-test assertion. Not
enforced inside `test_hook_relpath_bypass.py`; Phase 4 `uv run pytest`
on the whole tests/ tree verifies it as a side effect. Documented here
so Phase 3 does not misread "V9" as a missing test case.

## Verify RED protocol

Before handoff to Phase 3, run:

```
uv run pytest tests/unit/test_hook_relpath_bypass.py -v
```

Expected: RED cases fail (V1 all, V2 all, V7 bare-relative log assertion,
several V12 subcases). GREEN cases pass (V3 all, V4 all, V5 all, V6 all,
V8 all, V10 conditional, V11 no-crash, V12 absolute-shape baseline).

A Phase 2 test that passes immediately is either testing existing
behavior or wrong. Anything that surfaces as a false-GREEN gets demoted
to a regression guard with a comment or removed.

## Out of scope for Phase 2

- `checks/scope-guard.sh` changes (separate slice per boundary in intent).
- Phase 3 implementation details: how canonical-form derivation is
  spelled in shell, which `case` entries are added, whether an early-
  exit `FILE=<canonical>` rewrite or a parallel-case approach is used.
- The full-suite run is deferred to Phase 4; Phase 2 verifies only that
  the new tests fail for the right reason.
