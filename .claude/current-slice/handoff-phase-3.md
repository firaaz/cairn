---
slice: validator-symlink-fix
phase: 3-implementation
date: 2026-04-11
status-at-handoff: implementation → integration
---

# Phase 3 → Phase 4 Bridge — SLICE-001

## Gate status

**PHASE 3 GATE MET.** Implementation committed to git.

- Implementation commit: `d06fb64` — `slice: validator-symlink-fix — phase 3 implementation`
- Files in the commit: `scripts/validate_architecture.py`, `tests/unit/test_validate_architecture.py`, `CHANGELOG.md`, `.claude/current-slice/implementation/notes.md`
- Validation suite state at commit time: **6 passed / 0 failed** via `uvx pytest tests/unit/test_validate_architecture.py -v`.
- Working tree is clean except `docs/2026-04-11-review-from-rag-session.md`, which is explicitly out of envelope and must remain untouched by Phase 4.

## What Phase 4 receives as input

Per `docs/operational-reference.md` §Phase 4, load ONLY these:

- `.claude/current-slice/intent.md` — the slice contract
- `docs/ARCHITECTURE.md` — invariants to verify
- The implementation source files in the envelope — `scripts/validate_architecture.py`, `tests/unit/test_validate_architecture.py`, `CHANGELOG.md`

Do NOT load:

- `.claude/current-slice/implementation/notes.md` — Phase 3's reasoning. Phase 4 checks the code against the intent, not against Phase 3's justification for why the code looks the way it does.
- `.claude/current-slice/validation/approach.md` — Phase 2's reasoning. Phase 4 is not re-reviewing test design.
- `handoff-phase-1.md`, `handoff-phase-2.md`, `handoff-phase-3.md` (this file) beyond the contract section below. Read this file for the gate state and the test-command contract; do not use it as a reasoning substitute for reading the source.
- `docs/2026-04-11-review-from-rag-session.md` — external, out-of-envelope.

## Test-command contract

Phase 4 must run, in order, from cairn's repo root:

1. `uvx pytest tests/unit/test_validate_architecture.py -v` — slice-specific suite. Expected: **6 passed**, same as Phase 3's exit state.
2. `uvx pytest` — full test suite. Expected: **6 passed** (cairn has no other tests today). If new tests appear, the slice did not cause them; investigate but do not extend this slice's scope.
3. `uv run python scripts/validate_architecture.py` from cairn's repo root — the validator against cairn's own substrate (V7 in intent.md, the integration regression of V1). Expected: `ALL CHECKS PASSED` with `Invariants verified: 1`, `ADR files checked: 1`, exit 0. Note: cairn has no `pyproject.toml`, so `uv run python ...` will prompt for project initialization; use `uv run --no-project python scripts/validate_architecture.py` or plain `python3 scripts/validate_architecture.py` if that is friction. The observable contract (exit 0, `ALL CHECKS PASSED`) does not depend on which Python runner is used.

## Invariants declared in intent.md

`intent.md` declares `invariants-touched: []` — this slice touches no architectural invariants. Phase 4's per-invariant verification table is therefore empty; the integration check reduces to (a) test suite passes, (b) validator self-dogfood still passes, (c) the scope-bounded changes did not regress adjacent modules.

`adrs-referenced: [ADR-001]` — ADR-001 is the bootstrap exception (self-symlink). Phase 4 should read it briefly to confirm the resolution mechanism does not contradict it, but no new ADR is created.

## Envelope summary

In scope and touched this phase:

- `scripts/validate_architecture.py` — added `_resolve_project_root()` function, replaced the module-level `PROJECT_ROOT = Path(__file__).resolve().parent.parent` line with a call to it, added `os` and `subprocess` imports, updated the module docstring's exit-code description to mention "project root could not be resolved". No changes to `validate()`, `parse_*`, or `main()`.
- `tests/unit/test_validate_architecture.py` — fixture correction only (see "off-intent decisions" below). No test assertion changes. No new test functions.
- `CHANGELOG.md` — moved the validator symlink entry from `[Unreleased] § Known issues` into `[Unreleased] § Fixed` with a reference to this slice and a summary of the resolution chain.
- `.claude/current-slice/implementation/notes.md` — new file (default allowlist, not in envelope).

In scope but NOT touched: none remaining.

Out of scope (per intent `out-of-scope`): left alone — Check A/B/C logic, invariant/ADR parsers, CLI surface, `checks/*.sh` hooks, `validate_architecture.py` refactors beyond resolution, consumer-side workarounds.

## Off-intent decisions Phase 4 should be aware of

**Phase 3 edited the Phase 2 test fixture, not just the implementation.** This is worth flagging explicitly because it crosses a soft line.

- What was edited: `_make_consumer_project()` in `tests/unit/test_validate_architecture.py` — the invariant prefix and an ADR-sweep rule when `adrs > invariants`.
- Why: after the resolution fix landed, V2/V3/V4 failed with a new signature — the validator was now correctly reading tmp's `ARCHITECTURE.md`, but the parser rejected it because the fixture used `**TMP-NNN**` while the parser (explicitly out of scope) only matches `**INV-NNN**`. And with `invariants=2, adrs=3`, the extra ADR was orphaned, tripping Check B. Phase 2 could not have detected either issue without reading the parser source, which context isolation forbade.
- What is unchanged: every assertion in every test. The count-based distinguisher (`count == 2` for tmp vs `count == 1` for cairn), the exit-code checks, the anti-leak string check, and the tmp-marker check in V5 all fire on the same semantics they had before.
- Phase 4's responsibility: verify the edit did not weaken what the tests observe. Specifically, check that V2 still asserts `count == 2`, V6 still asserts `"Invariants verified: 1" not in stdout`, and V5 still asserts nonzero exit with tmp-side markers in output.

**Other decisions unpinned by intent and made during implementation:**

- `CLAUDE_PROJECT_DIR` as the env var name (intent used it as a non-binding hint; V2 made it a de facto contract).
- Diagnostic format on resolution failure — multi-line `ERROR:` stderr block listing attempted mechanisms. V6 asserts the property, not the wording.
- Subprocess error handling — both `FileNotFoundError` (git not installed) and `CalledProcessError` (not a git repo) caught, each reported distinctly in the diagnostic.
- Resolution runs at module load time, so failures fire before `main()` prints anything. This is load-bearing for V6's anti-leak assertion.
- Pre-existing missing-files inconsistency (docstring said exit 2, `main()` uses `sys.exit(1)`) — left as-is, not this slice's scope.

## Phase 3 anti-pattern NOT taken

Considered and rejected: dropping only `.resolve()` from the original `Path(__file__).resolve().parent.parent`. That is a one-character fix and was suggested by some earlier reasoning. It does not work: without `.resolve()`, `Path(__file__)` still routes through the `.slice-system` symlink at filesystem read time, because the kernel follows the symlink when the validator opens `docs/ARCHITECTURE.md` regardless of whether the Python path object was canonicalized. The real leak is at file-open time, not at path-construction time. Any correct fix has to identify the consumer root by a mechanism that does not traverse `.slice-system`. The env-var-then-git chain does exactly that.

## Runtime / environment notes

- Suite runs via `uvx pytest` (ephemeral uv tool runner). Cairn has no `pyproject.toml` and should not acquire one as part of this slice.
- The reality hook (`ruff format` + `ruff check --fix`) fired on `scripts/validate_architecture.py` during this phase and left the file unchanged — the new code was already formatted-clean.
- Scope-guard did not fire once. All writes were in-envelope or under `.claude/current-slice/`.
