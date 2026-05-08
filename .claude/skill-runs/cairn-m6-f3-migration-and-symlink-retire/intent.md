---
id: cairn-m6-f3-migration-and-symlink-retire
name: Cairn M6 F3 — Migration + Symlink Retire
snapshot-sha: 64ec0a9
invariants-touched:
  - INV-011
---

## What

Land the M6 half of the M5+M6 milestone: ship a migration runbook plus a thin `scripts/migrate_from_symlink.sh` helper that takes the only existing `.slice-system → cairn` consumer (`complex-rag-analysis`) off the symlink and onto `/plugin install cairn@cairn-marketplace`, and retire cairn-the-repo's symlink-era upgrade docs so future downstream consumers reach for plugin install only. INV-011 is preserved verbatim — cairn-the-repo's own `.slice-system → .` self-symlink stays exactly as it is (D8). Three threads land together: M (runbook + helper), R (retire downstream-consumer docs in cairn-the-repo), P (INV-011 prose cite of F3).

## Why

ADR `m5-plugin-distribution-and-symlink-retire` D9 splits M5+M6 into three sequenced features (F1 packaging, F2 consumer-doc surface, F3 migration + retire). F1 (`6e25777`) and F2 (`8ca229f` + fixup `e3d088d`) shipped on `dev`; F3 closes the milestone by enacting the consumer-side cutover and removing the symlink-era guidance F1/F2 superseded. The retire is gated on F2's CONSUMER.md so downstream consumers see exactly one canonical install path. The INV-011 cite (Thread P) makes the bootstrap-exception grep-discoverable for any future migration that might otherwise sweep cairn-the-repo's self-symlink along with consumer ones.

## Boundary

F3 covers only `complex-rag-analysis` (the sole existing symlink consumer) and the cairn-the-repo doc retire. Out of scope per plan: multi-consumer rollout playbook, plugin-uninstall-hygiene tests, settings.json schema validator, end-to-end CI integration test that builds + installs + dispatches, auto-detection of the cairn git URL from the existing symlink target, and any cairn-internal `.slice-system → .` retire (explicitly excluded by D8 / INV-011 — would require a superseding ADR). The helper script is mechanical only: it does not execute slash commands (`/plugin marketplace add`, `/plugin install`) — those remain the operator's session-restart-bound action.

## Specification

**Workspace decision (M.0 Step 3 / R.2).** Verified directly against the landed `CONSUMER.md` at the repo root: it contains an "Install (quickstart)" section but no "Migrating from `.slice-system` symlink" subsection. Per the plan's R.2 contract, the **replace** branch is the chosen path:

- Phase 3 ships `docs/upgrading-from-symlink.md` (≤200 words, deltas + Verify snippets).
- Phase 3 deletes `docs/upgrading-from-pre-compression.md` from `git ls-files`.
- Phase 4 audit confirms exactly one of the two doc-paths exists post-merge (no dual-doc state).

**Deliverable inventory (envelope-bounded).** Phase 3 writes within these paths only (verbatim from the plan's `envelope:`):

- `scripts/migrate_from_symlink.sh` — new, executable, Bash 3.2-compatible.
- `tests/unit/test_migrate_from_symlink.py` — new, four cases (Phase 2 RED).
- `docs/upgrading-from-symlink.md` — new (replace branch).
- `docs/upgrading-from-pre-compression.md` — deleted (replace branch).
- `CONSUMER.md` — no edit at F3 (replace branch keeps runbook in `docs/upgrading-from-symlink.md`).
- `README.md` — rewrite "How to consume cairn" block per R.1.
- `docs/ARCHITECTURE.md` — append F3 cite to INV-011 prose per P.1.

**Script contract (`scripts/migrate_from_symlink.sh`).** Bash 3.2+, POSIX utilities only (`unlink`, `test`, `cat`, `git`, `printf`, `readlink`, `jq`). Exit codes:

- `0` — preflight passed; symlink unlinked; settings.json filtered; banner printed naming the operator's next manual steps (`/plugin marketplace add <git-url>`, `/plugin install cairn@cairn-marketplace`, session restart, smoke test).
- `2` — quiescence failure: `.claude/skill-runs/<id>/integration/sweep-notes.md` missing for one or more dirs (Pre-mortem Scenario 6 defense). Stderr names "in-flight skill-run" and the offending path. State unchanged.
- `3` — cairn-the-repo self-symlink detected: `[ -L .slice-system ] && [ "$(readlink .slice-system)" = "." ]`. Stderr names INV-011 and `docs/ARCHITECTURE.md:91`. State unchanged. (D8 structural enforcement.)

Force override: `CAIRN_MIGRATE_FORCE=1` bypasses exit-2 only (NOT exit-3). Force-mode prints a loud stderr warning naming Pre-mortem Scenario 6 and the orphan-state risk, then proceeds with exit 0.

**Settings.json filter.** The script applies a `jq` filter that drops any hook entry whose `command` field contains `$CLAUDE_PROJECT_DIR/.slice-system/`. Atomic write via `.new` + `mv`. Phase 3 confirms exact `jq` shape against `complex-rag-analysis`'s real settings.json structure.

**Runbook content (`docs/upgrading-from-symlink.md`).** Six sections, each derived verbatim from plan Section M.1–M.6: (1) quiescence preflight (cite Pre-mortem Scenario 6); (2) atomic swap (the four mechanical steps with exact commands, including `unlink .slice-system` NOT `rm -rf`); (3) session restart callout (agent-registry reload); (4) state preservation enumeration (verbatim from plan M.4 — survives: `.claude/handoff.md`, `.claude/active-envelope.yaml`, `.claude/skill-runs/*`, `.claude/learning.md`, `.claude/adr-editorial-fixes.log`, `docs/plans/*`, `docs/adr/*`, `docs/ARCHITECTURE.md`; goes away: the symlink itself + stale settings.json hook entries); (5) rollback path (re-create symlink, `git checkout HEAD -- .claude/settings.json`, relaunch); (6) smoke test (re-run F1's post-install validator, dispatch trivial `cairn-tdd-feature`, confirm `.claude/envelope-grants.log` lands consumer-side per D5).

**README rewrite (R.1).** Three blocks replace today's `ln -s …` instruction: (a) first-time-consumer plugin-install pointer to CONSUMER.md; (b) one-paragraph migration block linking to `docs/upgrading-from-symlink.md`; (c) maintainer carve-out, verbatim: "Cairn-the-repo itself retains a `.slice-system → .` self-symlink for maintainer dogfooding (INV-011, `docs/ARCHITECTURE.md`). This is a one-repo exemption — downstream consumers must NOT recreate it."

**INV-011 prose cite (P.1).** Append to `docs/ARCHITECTURE.md`'s INV-011 prose at the existing cite parenthesis: "M6/F3 explicitly excludes cairn-the-repo from the downstream-consumer migration: the `scripts/migrate_from_symlink.sh` helper aborts with exit 3 if it detects a self-symlink target of `.`, and the retire-docs sweep preserves cairn-the-repo's self-symlink documentation." If `reversibility-guard.sh` denies the body-prose edit, surface to operator (small enough for manual authorship outside the dispatch envelope; note in Phase 4 sweep-notes).

## Verification

Phase 4 audit checks (verbatim from plan §Verification):

1. `scripts/migrate_from_symlink.sh` exists, is executable, and `tests/unit/test_migrate_from_symlink.py` passes all four cases under `uv run pytest tests/unit/test_migrate_from_symlink.py -v`.
2. `README.md`'s consumption block has been rewritten; the maintainer carve-out paragraph is present and cites INV-011.
3. Exactly one of `{docs/upgrading-from-pre-compression.md, docs/upgrading-from-symlink.md}` is tracked by `git ls-files`; per the replace-branch decision, the survivor is `docs/upgrading-from-symlink.md`.
4. `docs/ARCHITECTURE.md` INV-011 prose contains an explicit "F3" or "M6/F3" token referencing `scripts/migrate_from_symlink.sh` and exit 3.
5. `grep -rn "\.slice-system" docs/ README.md CLAUDE.md` returns only INV-011 / self-symlink / bootstrap context lines, or ADR/spec/plan historical references (ADRs are append-only and exempt).
6. INV-011 directly verified: `readlink .slice-system` returns `.` at the cairn-the-repo root, and the existing `invariant-check INV-011` block in `docs/ARCHITECTURE.md` (lines 93–97) continues to validate.
7. `uv run pytest tests/unit/` is green; the new test adds, nothing else regresses relative to the F2-landed baseline (`8ca229f` + `e3d088d`).

Phase 2 RED test cases (Phase 3 makes green):

- (a) Happy-path fixture (symlink to a non-`.` target, fake settings.json with one symlink-anchored hook entry, empty `.claude/skill-runs/`) → exit 0; symlink unlinked; settings.json contains no `"$CLAUDE_PROJECT_DIR/.slice-system/"` substring; stdout names `/plugin marketplace add`.
- (b) In-flight skill-run fixture (one `.claude/skill-runs/<id>/` dir without `integration/sweep-notes.md`) → exit 2; stderr names "in-flight skill-run" and the offending path; symlink and settings.json unchanged.
- (c) Cairn-self fixture (symlink target `.`) → exit 3; stderr names INV-011; no state change.
- (d) Force-mode fixture (in-flight skill-run + `CAIRN_MIGRATE_FORCE=1`) → exit 0; stderr contains the Pre-mortem Scenario 6 warning string.

## Risk Surface

Domain-level wrongness that passes CI:

- **INV-011 silent erosion.** R.3 grep sweep accidentally rewrites a maintainer-context `.slice-system` mention into consumer-context plugin-install prose; tests stay green because no test exercises maintainer-bootstrap onboarding.
- **Settings.json shape drift.** `jq` filter assumes a hook-entries-as-array shape; if `complex-rag-analysis`'s real settings.json carries a different shape (e.g., object-keyed entries, nested matchers), the filter silently no-ops, leaving stale `$CLAUDE_PROJECT_DIR/.slice-system/...` entries that 404 silently post-cutover (Pre-mortem Scenario 2 collapse). Test fixtures may not mirror the real shape.
- **Build-time drift between F1's smoke build and the real plugin install.** Phase 4 verification re-uses `scripts/build_dist.py` smoke output; if the consumer's real `/plugin install` materialises a different tree (cache layout, manifest version), the smoke test passes but post-cutover dispatch fails.
- **Replace-branch dual-doc state.** Phase 3 ships `docs/upgrading-from-symlink.md` but forgets the `git rm` of `docs/upgrading-from-pre-compression.md`; Phase 4 audit check 3 catches this only if the grep is exhaustive.
- **INV-011 ARCHITECTURE.md edit denied silently.** `reversibility-guard.sh` blocks the body-prose append; Phase 3 swallows the denial and Phase 4 sees the cite missing only via grep — preservation breadcrumb absent from the cite chain.
- **Quiescence preflight false-negative.** A consumer with a Phase-4-orphan slice (Phase 3 source mods uncommitted, see operator memory `feedback_phase4_rolelock_fixup.md`) has `integration/sweep-notes.md` present yet a non-quiesced state; helper exits 0 and migration proceeds mid-orphan.

## Feature-Local Invariants

- **FLI-1 (D8 structural).** `scripts/migrate_from_symlink.sh` MUST refuse to run inside cairn-the-repo by self-symlink-target detection (`readlink .slice-system == "."` → exit 3). Phase 2 test (c) is the structural enforcement of D8.
- **FLI-2 (replace-branch atomicity).** Post-Phase-3, `git ls-files` MUST contain `docs/upgrading-from-symlink.md` AND MUST NOT contain `docs/upgrading-from-pre-compression.md`. Both halves of the swap are required; either alone is a defect.
- **FLI-3 (script exit-code surface).** The script's three exit codes (0, 2, 3) are the protocol-level contract Phase 2 tests against; new exit codes added by Phase 3 outside this set are scope-creep.
- **FLI-4 (no slash-command chaining).** The script MUST NOT attempt to invoke `/plugin marketplace add` or `/plugin install` itself; those are operator-bound session-restart-aware actions per Pre-mortem Scenario 2 defense (Section M.2 Step 7). Test (a) asserts stdout names them as the next manual step.
- **FLI-5 (POSIX-only).** Bash 3.2 + POSIX utilities only; no `mapfile`, `readarray`, `[[` extended pattern matching beyond Bash 3.2 surface, or GNU-only flags. macOS default shell must run the script unmodified.
- **FLI-6 (envelope discipline).** All Phase 3 writes land within the plan's `envelope:` regex list; the operator-envelope at `.claude/active-envelope.yaml` (if active) or `role_guard.py` per-phase allowlist enforces this — no scope creep into adjacent paths.

## Explicit Scope-Out

Per plan §Out-of-scope follow-ups and Boundary:

- **Multi-consumer rollout playbook.** F3 covers `complex-rag-analysis` only; a general N-consumer migration playbook with version-skew detection is deferred (track on `docs/roadmap.md`).
- **Plugin uninstall hygiene tests.** Rollback documents `/plugin uninstall` but no clean-uninstall-test ships in F3.
- **Settings.json schema validator (typed).** A pydantic model for settings.json shape would catch drift; out of scope.
- **End-to-end CI integration test.** "Install plugin in fixture repo, dispatch trivial feature, assert clean exit" is M5.1+ work; F1's unit-level post-install validator is the F3-era ceiling.
- **Auto-detection of the cairn git URL.** Operator-supplied per the runbook; future ergonomic improvement.
- **Cairn-internal `.slice-system → .` retire.** Explicitly NOT in scope (D8 / INV-011); requires a superseding ADR.
- **CONSUMER.md edit in F3.** Replace-branch keeps the runbook in `docs/upgrading-from-symlink.md`; CONSUMER.md is untouched. (If any future re-decision picks the delete branch, CONSUMER.md gains the migration subsection — that is NOT this F3.)
- **Slash-command payload (`/catchup`, `/handoff`, `/decision`, `/new-adr`).** Deferred to M5.1 per ADR D3; F3 does not ship them.
