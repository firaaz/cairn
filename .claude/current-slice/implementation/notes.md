---
slice: validator-symlink-fix
phase: 3-implementation
date: 2026-04-11
---

# Phase 3 Implementation Notes — SLICE-001

## Red baseline observed before any code change

`uvx pytest tests/unit/test_validate_architecture.py -v` → **1 passed / 5 failed**. V1 (cairn self-dogfood) was green as expected; V2-V6 failed with `Invariants verified: 1` in stdout — cairn's count leaking through the canonicalized `.slice-system` symlink. This matched the failure signature the intent was written to catch.

## Resolution mechanism chosen

Two-step chain, no silent fallback:

1. `CLAUDE_PROJECT_DIR` environment variable, if set → used directly.
2. `git rev-parse --show-toplevel` from the process's current working directory.
3. If neither succeeds: write a diagnostic to stderr listing the attempted mechanisms and `sys.exit(2)`.

There is deliberately no fallback to `Path(__file__).parent.parent` (or any variant). That was considered — it is a one-character change from the buggy code — but it fails V2-V5: without `.resolve()`, `Path(__file__)` still crosses the `.slice-system` symlink at filesystem read time when the validator opens `docs/ARCHITECTURE.md`. The kernel-level symlink traversal is the real leak; removing `.resolve()` does not stop it. Any correct fix has to identify the consumer project root by a mechanism that does not route through `.slice-system`.

The resolution function runs at module load time (before `ARCHITECTURE_FILE` and `ADR_DIR` are computed), so a resolution failure fires before `main()` ever prints `Validating ARCHITECTURE.md...`. That satisfies V6's anti-leak assertion (`Invariants verified: 1` must not appear on stdout).

## Decisions not pinned down by intent

- **Env var name.** The intent alludes to `$CLAUDE_PROJECT_DIR` in a non-binding note. V2's test fixture sets `CLAUDE_PROJECT_DIR` explicitly, so the name is a de facto contract with the test suite. Used verbatim.
- **Diagnostic format on resolution failure.** Intent requires "a diagnostic message to stderr that explains which resolution mechanisms were attempted and why none succeeded." Implemented as a fixed-format list prefixed with `ERROR: cannot identify project root for architecture validation.` and an instruction line `Set CLAUDE_PROJECT_DIR ... or invoke from inside a git repository.` Test V6 asserts the property (nonzero exit, no success string, no `Invariants verified: 1`), not any specific wording, so this is free to evolve.
- **Exit code for resolution failure.** Intent says `2`, docstring now says `2`, implementation uses `sys.exit(2)`. Pre-existing missing-files path still uses `sys.exit(1)`; that's out of scope for this slice.
- **Subprocess error handling.** `git rev-parse` can fail with `FileNotFoundError` (git not installed) or `subprocess.CalledProcessError` (not a git repository). Both are caught, reported separately in the diagnostic, and fall through to exit 2. No timeout set — local git invocations are bounded.

## Test fixture correction (off-intent but in-envelope)

After the resolution fix, V2/V3/V4 still failed — but with a new, diagnostic failure mode: the validator correctly reached tmp's `ARCHITECTURE.md` but produced `No invariants found in ARCHITECTURE.md ## Invariants section` plus Check B failures for orphaned ADRs. Root cause: Phase 2's fixture builder used `**TMP-NNN**` as the invariant prefix and declared 3 ADRs against only 2 paired invariants. The validator's parser hard-codes `**INV-NNN**` (explicitly out of scope for this slice per intent), and Check B requires every firm/accepted ADR to be referenced by at least one invariant.

Phase 2 could not have caught this without reading the parser source, which context isolation forbade. Phase 2's red run verified the fixture was *red in the expected way* (`Invariants verified: 1` leak), so the fixture construction was never exercised against a validator that actually reached it.

Corrections applied to `_make_consumer_project` in `tests/unit/test_validate_architecture.py`:

1. Invariant prefix `**TMP-NNN**` → `**INV-NNN**` so the parser actually matches. Also updated the ADR frontmatter `invariants-touched: [TMP-NNN]` → `invariants-touched: [INV-NNN]` for internal consistency (the parser does not currently cross-check this field, but the mismatch was a latent quality issue).
2. When `adrs > invariants`, the first invariant now sweeps up the extras — i.e., invariant 1 references its paired ADR plus all ADRs beyond the invariant count — so Check B finds every firm/accepted ADR referenced. Preserves the `adrs=3` signal in V2/V3/V4/V5 without orphaning ADR-903.

Assertions were not touched. The `count == 2` distinguisher still fires; V5's broken-substrate failure still exits nonzero with ADR-9 markers present.

## Green state after fix

`uvx pytest tests/unit/test_validate_architecture.py -v` → **6 passed / 0 failed** in ~0.4s. V1-V6 all green.

## What the fix does NOT touch

- Check A/B/C logic — untouched (out of scope).
- `parse_invariants`, `parse_adr`, `parse_frontmatter` — untouched (out of scope).
- CLI surface — untouched (no new flags).
- `checks/*.sh` hooks — untouched (the scope-guard canonicalization bug documented in CLAUDE.md remains latent; a separate concern).
- Pre-existing missing-files exit-code inconsistency (docstring said `2`, main used `sys.exit(1)`) — left as-is. The new resolution-failure path correctly uses `sys.exit(2)`; reconciling the older path is not in this slice's scope.
