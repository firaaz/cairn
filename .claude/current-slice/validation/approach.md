# SLICE-001 Phase 2 — Validation Approach

## Inputs Loaded

- `.claude/current-slice/intent.md` — V1-V6 spec
- `.claude/current-slice/handoff-phase-1.md` — Phase 1 ambiguities A1-A4
- `docs/ARCHITECTURE.md` — fixture format reference
- `docs/adr/001-bootstrap-exception.md` — ADR frontmatter format reference
- `docs/2026-04-11-review-from-rag-session.md` — external evidence; see A3

## Inputs Deliberately NOT Loaded

- `scripts/validate_architecture.py` internals (A4 of handoff — modification slice, out-of-envelope reasoning)
- `CLAUDE.md` — would leak project orientation into test design
- `.claude/handoff.md` reasoning body — orientation only

## Ambiguities and Resolutions

### From Phase 1 handoff (A1-A4)

- **A1** — V6 diagnostic wording is over-specified for some implementation choices. **Resolved:** test the property (`returncode != 0`, no `ALL CHECKS PASSED`, no cairn-count leak), not the wording. Any Phase 3 mechanism satisfying the resolution contract passes V6.
- **A2** — V2 and V5 need independent fixtures. **Resolved:** each test function takes pytest's `tmp_path` built-in, which is function-scoped with automatic cleanup.
- **A3** — External review load decision. **Resolved: loaded.** The review predates the slice and is external evidence, not Phase 1 reasoning. Its captured output format (`Invariants verified: N`) is load-bearing for assertion design — loading it prevents writing tests that inadvertently bind to a specific Phase 3 mechanism.
- **A4** — `CHANGELOG.md` in envelope but Phase 2 must not touch. **Honored.** Phase 2 writes only `tests/unit/test_validate_architecture.py` and this `validation/approach.md`.

### Discovered during Phase 2 enumeration (B1-B8)

- **B1** — V2's "test the env-var path explicitly" could bind tests to `CLAUDE_PROJECT_DIR` as a required mechanism. **Resolved:** V2 sets the env var but asserts only observable substrate identity (parsed count). Any mechanism that produces the correct substrate passes, whether it honors the env var or not.
- **B2** — How to locate cairn's own repo root inside the test file. **Resolved:** `Path(__file__).resolve().parent.parent.parent`. The test file uses `.resolve()` intentionally — we are locating the test's own repo for invocation paths, not testing the bug fix. The fix is exercised via `subprocess` against a symlink in a tmp directory.
- **B3** — V1 intent pins "current 1-invariant, 1-ADR state." **Resolved:** V1 asserts only `returncode == 0` + `ALL CHECKS PASSED` in stdout. Does not bind to cairn's count, so cairn's substrate can grow without breaking the regression check.
- **B4** — What observationally proves "validator read the tmp substrate, not cairn's"? **Resolved:** tmp fixtures declare **2 invariants / 3 ADRs**. V2-V4 parse `Invariants verified: N` from stdout (format captured in the review) and assert N == 2. Cairn has 1 — mis-resolution produces 1, so the assertion catches it. The format binding is acceptable because intent explicitly lists "stdout format when checks pass or fail" as what-the-fix-must-not-change.
- **B5** — pytest fixture style. **Resolved:** `tmp_path` built-in (wraps `tempfile.TemporaryDirectory()` internally).
- **B6** — V3 `git init` mechanism. **Resolved:** `subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)`. No extra dependencies.
- **B7** — V5 broken-fixture distinguishability. **Resolved:** V5's fixture invariants reference `ADR-999` (absent from the fixture's ADR corpus). Assertion: `returncode != 0` + no `ALL CHECKS PASSED` + at least one of `TMP-` / `ADR-9` appears in combined output. Any of these markers is tmp-specific and cannot appear in cairn's output.
- **B8** — V7 is integration-only. **Honored.** V7 runs in Phase 4's integration sweep, not as a pytest unit test. Phase 2 writes V1-V6 only.

## Test-to-Verification Mapping

| Test function | Intent ID | Assertion kernel |
|---|---|---|
| `test_v1_cairn_self_dogfood_baseline` | V1 | exit 0 + `ALL CHECKS PASSED` from cairn root |
| `test_v2_consumer_via_symlink_with_env_var` | V2 | exit 0 + parsed count == 2 (not cairn's 1) |
| `test_v3_consumer_via_symlink_no_env_var` | V3 | same as V2, env var unset, tmp is git-initialized |
| `test_v4_consumer_invoked_from_subdirectory` | V4 | same, cwd = `<tmp>/src/submod` |
| `test_v5_consumer_with_broken_substrate` | V5 | exit != 0 + no false-green + tmp marker in output |
| `test_v6_resolution_failure_no_viable_root` | V6 | exit != 0 + no `ALL CHECKS PASSED` + no `Invariants verified: 1` leak |

## Expected Red/Green Transition

On the current (unfixed) validator:
- V1 **green** (self-dogfood is already correct)
- V2-V6 **red** (validator silently reads cairn's substrate via `Path(__file__).resolve().parent.parent`)

After any Phase 3 fix satisfying the resolution contract:
- V1-V6 all **green**

The red→green transition on V2-V6 is what proves the fix works. Phase 3 must not rely on running these tests incrementally during implementation — the `.slice-system` symlink is cairn itself, and mid-fix iterations will shift between red and green as the resolution mechanism changes. Run the full suite at logical-unit boundaries only.

## Phase 3 Free Parameters

Phase 3 chooses the resolution mechanism. Candidates this test design preserves:

- **Option 1** — drop `.resolve()` from the `__file__` chain (review Finding 1 Option 1). Minimal, single-line fix.
- **Env → git → `__file__` fallback chain** — the handoff's original multi-mechanism suggestion.
- **Anything else** satisfying V1-V6.

Phase 3 must record the chosen mechanism and the reasoning in `.claude/current-slice/implementation/notes.md`.

## Runtime Note for Phase 4

cairn has no pyproject.toml. Phase 4 should invoke the tests via `uvx pytest tests/unit/test_validate_architecture.py` (ephemeral pytest install via uv's tool runner) to avoid an accidental envelope expansion into project-manifest territory. If `uv run python -m pytest` is preferred for consistency with operational-reference.md's Phase 4 command, adding a minimal pyproject.toml belongs in a separate slice, not in this one.
