---
slice: identifier-scheme/hook-relpath-bypass
date: 2026-04-16
phase: 1-intent
invariants-touched: [INV-005]
adrs-referenced: [identifier-scheme]
envelope:
  - "checks/reversibility-guard.sh"
  - "tests/unit/test_hook_relpath_bypass.py"
out-of-scope:
  - "scope-guard.sh relpath false-denial (separate slice; CLAUDE.md already documents the canonical-path workaround)"
  - "reality-check.sh (unaffected by pathprefix semantics)"
  - "changes to the two-field identifier schema in ADR identifier-scheme (frozen)"
  - "new guard categories beyond ADR append-only, .env, and lockfile (existing set)"
  - "redesign of the hook interface (JSON-in / exit-2 contract stays per ADR-003 D1)"
  - "full symlink resolution via readlink -f (consumer .slice-system setups beyond prefix stripping are deferred)"
---

### What and Why

`reversibility-guard.sh` currently applies its ADR append-only deny patterns — `*/docs/adr/index.md` (exempt) and `*/docs/adr/*.md` (deny) — directly against the raw `tool_input.file_path` string. The leading `*/` in those patterns requires at least one path segment before `docs/`, so bare-relative paths like `docs/adr/identifier-scheme.md` match nothing and fall through to `exit 0`. Reproduced against the current tree: `Write` of bare-relative `docs/adr/identifier-scheme.md` returns exit 0; body-prose `Edit` of the same file returns exit 0. Both should deny. This bypass erodes INV-005's commitment that `reversibility-guard.sh` tolerates both legacy and flat-slug ADR filenames during the migration window — tolerance is meaningless if the guard can be skipped by dropping the prefix.

The `.slice-system → .` symlink amplifies the exposure: tools routing an edit through `.slice-system/docs/adr/foo.md` happen to match today's pattern (because `.slice-system` fills the `*`), but a normalized path — what the hook should actually compare against — is `docs/adr/foo.md`, which is exactly the bypassed form. Two input shapes for the same underlying file must produce the same guard verdict.

This slice closes the bypass by normalizing `$FILE` to a project-root-relative canonical form before pattern matching, and by using that canonical form consistently for both pattern comparison and the file-existence probe.

### Specification Detail

1. **Canonical-form derivation.** Before the ADR / `.env` / lockfile case block runs, the hook MUST derive a canonical relative path from `$FILE` using the same project-root discovery that `scope-guard.sh` uses today: `PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"`. If `$FILE` is absolute and begins with `$PROJECT_ROOT/`, strip that prefix. If the remaining path begins with `.slice-system/`, strip that prefix too. The result is the canonical relative path used for pattern matching.

2. **ADR-pattern semantics post-normalization.** The canonical form of any ADR under this repo's control MUST be exactly `docs/adr/<id>.md` (no leading segment, no `.slice-system/` prefix). The guard's ADR clauses MUST trigger on that canonical form. Specifically: the `docs/adr/index.md` exemption, the `docs/adr/*.md` Write-existing deny, and the `docs/adr/*.md` Edit body-deny all MUST fire when the canonical path matches — regardless of whether the original `$FILE` came in as absolute, bare-relative, or `.slice-system/`-prefixed. Equivalently: the three input shapes `docs/adr/foo.md`, `.slice-system/docs/adr/foo.md`, and `$PROJECT_ROOT/docs/adr/foo.md` (or `$PROJECT_ROOT/.slice-system/docs/adr/foo.md`) MUST all produce the same deny/allow verdict for identical tool semantics.

3. **File-existence probe uses an absolute path.** The `[ -f "$FILE" ]` check (Write branch) MUST be computed against a path that resolves correctly independent of the hook's invocation CWD. Use `$PROJECT_ROOT/<canonical>` for the `-f` test. Today's behavior on absolute paths is preserved; today's brittleness on bare-relative paths (existence depending on CWD) is eliminated.

4. **Non-ADR categories preserved.** The `.env`, `.env.*`, `uv.lock`, `package-lock.json`, and `poetry.lock` patterns already match bare-relative paths (`*.env`, `*.lock` — no leading-segment requirement). These MUST continue to match the same set of inputs they match today; any rewriting of the case block MUST NOT narrow the `.env` / lockfile domain. Adding canonical-form entries to the case block is allowed if it does not drop coverage of the existing forms.

5. **Deny-reason strings are byte-identical to today.** The four deny JSON `permissionDecisionReason` strings — `REVERSIBILITY GUARD: rm -rf: ...` etc. (Bash branch, unchanged), `REVERSIBILITY GUARD: blocked write to env file ...`, `REVERSIBILITY GUARD: lock files are auto-generated ...`, `REVERSIBILITY GUARD: ADRs are append-only. ...`, and `REVERSIBILITY GUARD: ADR body is append-only. ...` — MUST match their current text character-for-character. Test V1–V6 from SLICE-016 in `tests/unit/test_hook_tolerance.py` MUST continue to pass unmodified.

6. **Editorial-fix escape hatch extended to canonical form.** `ADR_EDITORIAL_FIX=1` Edits on bare-relative and `.slice-system/`-prefixed ADR paths MUST log a line to `.claude/adr-editorial-fixes.log` the same way today's absolute-path form does. The logged file reference MAY be either the raw `$FILE` or the canonical form; whichever is chosen MUST be used consistently.

7. **Failure modes preserved.**
   - Missing `jq`: exit 0 with the existing stderr warning (unchanged).
   - `CLAUDE_PROJECT_DIR` unset AND not inside a git repo AND no sensible `pwd`: `PROJECT_ROOT` falls back to `pwd`, matching scope-guard's contract. The hook MUST NOT crash under `set -euo pipefail` if project-root discovery yields a non-useful path; pattern matching on the raw `$FILE` continues to protect absolute-path inputs as it does today.
   - Empty `tool_input.file_path`: hook continues to exit 0 (no file to guard).

8. **Scope of change.** Only the `Write` and `Edit` branches of `reversibility-guard.sh` change. The Bash branch (`rm -rf`, `git push --force`, `DROP TABLE`, etc.) is untouched. No new guard categories are introduced. No changes to ADR firmness frontmatter handling, the `superseded-by` / `superseded_by` / `firmness:` frontmatter keys, or the first-line grep for frontmatter edits.

### Boundary

Explicitly out of scope for this slice:

- Fixing the analogous relpath false-denial in `scope-guard.sh` (CLAUDE.md documents a canonical-path workaround; that fix is its own slice).
- `reality-check.sh` behavior (irrelevant to the pattern-prefix issue; lints Python only).
- Any edit to ADR `identifier-scheme` itself or to INV-005's ARCHITECTURE.md text. INV-005 already names `reversibility-guard.sh` as a tolerance target; this slice honors that commitment and does not restate it.
- New guard categories (API keys, credential files, database dumps, etc.).
- Consumer-side `.slice-system → /abs/path/to/cairn` setups where the symlink target is outside the current project root. Basic prefix stripping covers cairn's own `.slice-system → .` loop; richer symlink resolution (`readlink -f`, canonicalization of mid-path symlinks) is deferred.
- Changes to the hook invocation contract (stdin JSON → exit 0/2 → stdout JSON deny reason), which is governed by ADR-003 D1.

### Verification

All checks run the hook via `bash checks/reversibility-guard.sh` with `CAIRN_ROOT` as CWD unless otherwise noted. Payloads are JSON on stdin matching the Claude Code PreToolUse shape. Exit 0 = allow; exit 2 = deny (with JSON deny reason on stdout).

**V1 — Close the bypass: bare-relative flat-slug ADR.**
- `Write` with `file_path: "docs/adr/identifier-scheme.md"` → **exit 2**, stdout deny JSON contains `REVERSIBILITY GUARD: ADRs are append-only`. (Today: exit 0. Bypass reproduced.)
- `Edit` with `file_path: "docs/adr/identifier-scheme.md"`, `old_string: "This ADR introduces a two-field identity model"`, `new_string: "BYPASS"` → **exit 2**, stdout contains `REVERSIBILITY GUARD: ADR body is append-only`. (Today: exit 0.)

**V2 — Close the bypass: bare-relative legacy-shape ADR.**
- `Write` with `file_path: "docs/adr/006-feature-slice-model.md"` → **exit 2**, `ADRs are append-only`.
- `Edit` body-prose on `docs/adr/006-feature-slice-model.md` → **exit 2**, `ADR body is append-only`.

**V3 — `.slice-system/`-prefixed paths deny consistently.**
- `Write` with `file_path: ".slice-system/docs/adr/identifier-scheme.md"` → **exit 2**, `ADRs are append-only`. (Today: exit 2 — preserved.)
- `Edit` body-prose on `.slice-system/docs/adr/identifier-scheme.md` → **exit 2**. (Today: exit 2 — preserved.)
- `Write` with `file_path: ".slice-system/docs/adr/006-feature-slice-model.md"` → **exit 2** (legacy shape via symlink).

**V4 — Frontmatter-only Edit allowed on every input shape.**
Parametrized over the four frontmatter keys `status:`, `firmness:`, `superseded-by:`, `superseded_by:` and the three input shapes (absolute path, bare-relative, `.slice-system/`-prefixed), flat-slug and legacy ADR: `Edit` with `old_string` starting with the key → **exit 0**.

**V5 — New-ADR Write allowed on every input shape.**
- `Write` to a non-existent `docs/adr/future-unused.md` (bare-relative) → **exit 0**.
- `Write` to a non-existent `.slice-system/docs/adr/future-unused.md` → **exit 0**.
- `Write` to a non-existent absolute path `$PROJECT_ROOT/docs/adr/future-unused.md` → **exit 0** (today's behavior; regression).
Same three shapes for legacy filename `docs/adr/999-future.md`.

**V6 — `index.md` remains exempt under all input shapes.**
- `Write` / `Edit` on `docs/adr/index.md` (bare-relative) → **exit 0**.
- Same on `.slice-system/docs/adr/index.md` → **exit 0**.
- Same on absolute `$PROJECT_ROOT/docs/adr/index.md` → **exit 0** (regression).

**V7 — Editorial-fix escape hatch covers canonical forms.**
- `Edit` body-prose with `ADR_EDITORIAL_FIX=1` on `docs/adr/identifier-scheme.md` (bare-relative) → **exit 0**, appends one line to `.claude/adr-editorial-fixes.log` referencing the ADR.
- Same with `.slice-system/docs/adr/identifier-scheme.md` → **exit 0**, logs.

**V8 — `.env` and lockfile denies unchanged (regression).**
- `Write` with `file_path: ".env"` (bare-relative) → **exit 2**, deny JSON contains `blocked write to env file`.
- `Write` with `file_path: "uv.lock"` (bare-relative) → **exit 2**, `lock files are auto-generated`.
- Same two cases via absolute path → **exit 2**.

**V9 — SLICE-016's full V1–V6 suite (`tests/unit/test_hook_tolerance.py`) still passes.**
The entire `test_hook_tolerance.py` file MUST run green after this slice's changes, with no edits to that file. This guards against accidental regression of hook-tolerance semantics.

**V10 — Missing-jq contract preserved.**
Invoke the hook with `PATH` stripped of `jq` — hook MUST exit 0 and emit the existing stderr warning `WARNING: reversibility-guard hook skipped — jq not found in PATH`. Skipped with a `pytest.skip` if `jq` cannot be PATH-stripped cleanly in the test environment.

**V11 — No-crash contract under indeterminate project root.**
Invoke the hook with `CLAUDE_PROJECT_DIR` unset, CWD a temp directory outside any git repo, and a bare-relative `file_path: "docs/adr/identifier-scheme.md"`. Expected outcome: hook returns either exit 0 or exit 2 cleanly (does not crash with `set -u` / `set -e` failure). The deny verdict is not asserted here — only that the hook terminates within 10 seconds with a defined exit code and no Python-style traceback / bash stack trace on stderr.

**V12 — Verdict symmetry across input shapes.**
For the canonical ADR `docs/adr/identifier-scheme.md`, the hook's exit code MUST be identical across the three input shapes (absolute, bare-relative, `.slice-system/`-prefixed) for each of: Write existing, Edit frontmatter, Edit body-prose, Edit body-prose with `ADR_EDITORIAL_FIX=1`, Write non-existent. Four tool-scenarios × three shapes = twelve assertions; all exit codes must be equal within each scenario group. This is the core behavioral invariant the slice introduces.

### adrs-referenced rationale

`identifier-scheme` is cited because its D1/D2 establish the two-field schema and its text is the origin of the INV-005 tolerance clause that this slice extends from "filename shape" to "input path shape". No new ADR is created; no existing ADR is superseded.
