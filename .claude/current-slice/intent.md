---
slice: validator-symlink-fix
date: 2026-04-11
phase: 1-intent
invariants-touched: []
adrs-referenced: [ADR-001]
envelope:
  - "scripts/validate_architecture.py"
  - "tests/unit/test_validate_architecture.py"
  - "CHANGELOG.md"
out-of-scope:
  - "Check A, B, or C logic (invariant/ADR consistency rules themselves)"
  - "ADR frontmatter parsing and ARCHITECTURE.md invariant parsing"
  - "Validator CLI interface, output format, or exit-code semantics beyond the new resolution-failure case"
  - "Any changes to checks/*.sh hooks"
  - "Refactoring scripts/validate_architecture.py beyond PROJECT_ROOT resolution"
  - "The scope-guard canonicalization quirk documented in CLAUDE.md (separate concern)"
  - "Consumer-side workarounds — the fix belongs in cairn"
---

# Intent: SLICE-001 — Correct validator project root resolution across symlinks

## What and Why

The substrate validator (`scripts/validate_architecture.py`) must read the **consumer project's** `docs/ARCHITECTURE.md` and `docs/adr/` when invoked via the `.slice-system` symlink. Today, `Path(__file__).resolve().parent.parent` at module load time canonicalizes the symlink back to cairn's install directory, so every consumer project's validator silently reads cairn's own docs instead of the caller's. This produces false-green validator output in `/status` for every real consumer of cairn — the primary substrate-health signal lies. Cairn's own self-dogfood is the one environment where the bug is latent (cairn validating cairn is a degenerate case where the wrong answer equals the right answer), so the bug was invisible until surfaced from a real consumer project.

The fix belongs in cairn, not in consumer projects: every consumer should be able to drop in `.slice-system` and run the validator without any patching.

## Specification Detail

### Resolution contract

The validator's notion of "project root" — the directory whose `docs/ARCHITECTURE.md` and `docs/adr/` are being validated — must resolve correctly for all four calling contexts below. Exact mechanism is not specified here (Phase 3's choice); only the observable behavior is specified.

1. **Cairn self-dogfood**: `python scripts/validate_architecture.py` invoked from cairn's own repo root → resolves to cairn's own repo root. This is the baseline behavior today and must not regress.

2. **Consumer project, invoked via symlink, from consumer repo root**: a consumer project has `.slice-system` as a symlink pointing to a cairn install. The consumer runs `.slice-system/scripts/validate_architecture.py` with cwd equal to the consumer's repo root. → Must resolve to the consumer's repo root, NOT cairn's install directory.

3. **Consumer project, invoked via symlink, from a subdirectory inside the consumer repo**: same setup as (2), but the process cwd is some subdirectory within the consumer project. → Must still resolve to the consumer's repo root, NOT cairn's install directory, NOT the subdirectory.

4. **Resolution failure — no viable project root**: if none of the available resolution mechanisms can identify a project root with plausible substrate (`docs/ARCHITECTURE.md` present), the validator MUST fail loudly with a stderr message and a nonzero exit code. It MUST NOT fall back to a default that could silently read cairn's own docs or any other unrelated project's docs.

### Invariant the fix establishes

> The validator never silently reads a project whose root the caller did not intend.

This is the core correctness property. A false-green from reading the wrong project's docs is strictly worse than a loud failure — loud failures get fixed, silent false-greens rot. Phase 2's tests must directly verify this property.

### Exit-code contract

Existing exit codes, preserved:

- `0` — all checks passed
- `1` — one or more checks failed (invariant/ADR corpus inconsistent)
- `2` — missing required files (`docs/ARCHITECTURE.md` or `docs/adr/` absent)

New behavior layered onto existing codes:

- A resolution failure (context 4 above) exits with code `2` and writes a diagnostic message to stderr that explains which resolution mechanisms were attempted and why none succeeded. It is treated as a "missing required files" case because the project root cannot be identified and therefore required files cannot even be located.

### What the fix must not change

- CLI invocation pattern: `python scripts/validate_architecture.py` with no arguments, no new flags.
- stdout format when checks pass or fail (the human-readable summary with invariant and ADR counts).
- The semantics of Checks A, B, and C. They operate on whatever docs they're pointed at; only the pointing changes.
- The requirement that `docs/ARCHITECTURE.md` and `docs/adr/` are siblings under the project root.

## Boundary

In scope (the only files Phase 2 and Phase 3 may touch):

- `scripts/validate_architecture.py` — modify `PROJECT_ROOT` resolution only
- `tests/unit/test_validate_architecture.py` — new test file (Phase 2 creates it)
- `CHANGELOG.md` — move the [Unreleased] § Known issues entry to [Unreleased] § Fixed with a reference to this slice

Out of scope (explicitly):

- Check A/B/C logic or their helper functions
- Frontmatter parsing, invariant parsing, ADR index parsing
- The validator's CLI surface (no new flags, no changed flags)
- Any `checks/*.sh` hook — scope-guard's separate canonicalization bug is a different slice
- Any refactoring of `validate_architecture.py` beyond what the resolution fix requires (e.g., no renaming unrelated constants, no extracting unrelated helpers)
- Behavior when `docs/ARCHITECTURE.md` or `docs/adr/` is present but malformed — that path was broken before and stays broken
- Consumer-project workarounds — the fix is cairn-side only

## Verification

Phase 2 must produce pytest-based tests covering each item below. Each test is independent and uses `tempfile.TemporaryDirectory()` for fixture setup so no real consumer project is required.

### V1 — Cairn self-dogfood baseline (regression check)

Running `python scripts/validate_architecture.py` from cairn's own repo root produces `ALL CHECKS PASSED` with the current 1-invariant, 1-ADR state. Exit code 0. Ensures the fix does not regress cairn's own validation.

### V2 — Consumer project via symlink, happy path

Construct a temporary consumer project in a tmp directory:

- `<tmp>/docs/ARCHITECTURE.md` containing a distinct invariant (e.g., `TMP-001`) that references a distinct ADR (e.g., `ADR-042`)
- `<tmp>/docs/adr/042-tmp-decision.md` with `status: accepted`, `firmness: firm`, and the referenced ID
- `<tmp>/docs/adr/index.md` listing ADR-042
- `<tmp>/.slice-system` as an `os.symlink()` to cairn's repo root

Invoke the validator as `<tmp>/.slice-system/scripts/validate_architecture.py` via `subprocess.run()` with `cwd=<tmp>` and `env` including `CLAUDE_PROJECT_DIR=<tmp>` (test the env-var path explicitly).

Assertion: the validator output references `TMP-001`/`ADR-042`, NOT cairn's `INV-001`/`ADR-001`. Exit code 0.

### V3 — Consumer project via symlink, env var unset

Same fixture as V2, but invoke without `CLAUDE_PROJECT_DIR` set in the subprocess environment. The validator must still identify `<tmp>` as the project root (via `git rev-parse --show-toplevel` or equivalent). Requires `git init` on the tmp directory.

Assertion: same as V2. Output references the tmp project's invariants, not cairn's.

### V4 — Consumer project invoked from subdirectory

Same fixture as V3 (tmp is git-initialized). Create a subdirectory `<tmp>/src/submod/`. Invoke the validator from that subdirectory as `<tmp>/.slice-system/scripts/validate_architecture.py` with `cwd=<tmp>/src/submod`.

Assertion: validator still resolves root to `<tmp>`. Output references the tmp project's invariants.

### V5 — Consumer project with deliberately broken substrate

Construct a tmp project whose `ARCHITECTURE.md` references a nonexistent ADR (e.g., `ADR-999`). Invoke via the symlink path as in V2 or V3.

Assertion: validator exits with code 1 (check failure) and the failure message references the tmp project's inconsistency, NOT a false-green from cairn's substrate.

### V6 — Resolution failure, no viable mechanism

Construct a scenario where:

- `CLAUDE_PROJECT_DIR` is unset
- The cwd is outside any git repository
- The validator is invoked through a `.slice-system` symlink in a directory that has no `docs/` of its own

Assertion: validator exits with code 2. Stderr contains a diagnostic that names the resolution mechanisms attempted. stdout contains NO "ALL CHECKS PASSED" or check-failure message — because no checks ran. This is the single most important test: it proves the validator never silently reads the wrong project.

### V7 — Phase 4 integration regression check

Running `uv run python scripts/validate_architecture.py` from cairn's repo root still outputs `ALL CHECKS PASSED` after all implementation changes land. This is redundant with V1 in principle but runs as part of Phase 4's integration sweep, not as a unit test.

---

## Notes on resolution mechanism (non-binding guidance for Phase 3)

The handoff from the prior session suggested a chain: `$CLAUDE_PROJECT_DIR` → `git rev-parse --show-toplevel` → `Path(__file__).resolve().parent.parent` fallback. **Phase 3 is free to implement any chain or mechanism that satisfies V1-V6 above.** The intent commits to the observable behavior, not to a specific resolution sequence. If Phase 3 finds a better mechanism during implementation, it should use it and record the deviation in `implementation/notes.md`.

The one non-negotiable constraint: no silent fallback that could read the wrong project's docs. V6 enforces this directly.
