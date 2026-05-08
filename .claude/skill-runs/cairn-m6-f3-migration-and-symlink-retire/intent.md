---
id: cairn-m6-f3-migration-and-symlink-retire
name: Cairn M6 F3 — Migration + Symlink Retire
snapshot-sha: 05e4768
invariants-touched:
  - INV-011
---

## What

Land the M6 half of the M5+M6 milestone: ship a migration runbook plus a thin `scripts/migrate_from_symlink.sh` helper that takes the only existing `.slice-system → cairn` consumer (`complex-rag-analysis`) off the symlink and onto `/plugin install cairn@cairn-marketplace`; retire cairn-the-repo's symlink-era upgrade docs so future downstream consumers reach for plugin install only; resolve F1's leftover `<marketplace-url>` placeholders in `CONSUMER.md` and `README.md`; and drop README's "fallback while plugin marketplace stabilises" framing so plugin install is the unambiguous primary path post-F3. INV-011 is preserved verbatim — cairn-the-repo's own `.slice-system → .` self-symlink stays exactly as it is (D8). Three threads land together: M (runbook + helper), R (retire downstream-consumer docs + placeholder fixes), P (INV-011 prose cite of F3).

## Why

ADR `m5-plugin-distribution-and-symlink-retire` D9 splits M5+M6 into three sequenced features (F1 packaging, F2 consumer-doc surface, F3 migration + retire). F1 (`6e25777`) and F2 (`8ca229f` + fixup `e3d088d`) shipped on `dev`; F3 closes the milestone by enacting the consumer-side cutover and removing the symlink-era guidance F1/F2 superseded. F1 deferred two literal-string commitments (`<marketplace-url>` in `CONSUMER.md:14` and `README.md:21`) plus left a "fallback while plugin marketplace stabilises" hedge at `README.md:23` that pre-dates F3's primary-path repositioning; the operator's interview-style review of the prior intent (`d640ac6`) flagged that the silent inheritance of these placeholders would leave the M5+M6 milestone visibly half-shipped at the consumer-doc surface. F3 absorbs the fixes in the same dispatch that retires the symlink, so post-merge there is exactly one canonical install path with one literal URL, not a placeholder-shaped commitment. The INV-011 cite (Thread P) makes the bootstrap-exception grep-discoverable for any future migration that might otherwise sweep cairn-the-repo's self-symlink along with consumer ones.

## Boundary

F3 covers `complex-rag-analysis` migration only (the sole existing symlink consumer), the cairn-the-repo doc retire, and the F1-followup `<marketplace-url>` placeholder + README fallback-framing fixes. Out of scope per plan: multi-consumer rollout playbook, plugin-uninstall-hygiene tests, settings.json schema validator, end-to-end CI integration test, auto-detection of the cairn git URL from the existing symlink target, and any cairn-internal `.slice-system → .` retire (explicitly excluded by D8 / INV-011 — would require a superseding ADR). The validator-stdout-literal placeholder at `CONSUMER.md:21-22` (the `# F1-followup: validator stdout literal lands in F1's PR.` comment + `uv run python scripts/validate_plugin_install.py` line) is **separately tracked F1-followup** and stays as documented; F3's R.4 edit fixes only the `<marketplace-url>` placeholder. The helper script is mechanical only: it does not execute slash commands (`/plugin marketplace add`, `/plugin install`) — those remain the operator's session-restart-bound action.

## Specification

**M.0 Step 3 / R.2 redecision (replace branch picked).** Per the amended plan, CONSUMER.md is mutated regardless of branch (R.4 Step 16.5 fixes the URL placeholder either way), so the replace/delete decision is freshly contested. Verified directly against the landed `CONSUMER.md` at the repo root (read in full, 81 lines): it has an "Install (quickstart)" block (lines 9–25), a "First dispatch in 10 minutes" block (lines 27–32), troubleshooting (lines 61–67), and a "Where to next" reading-order block (lines 69–76) — but no "Migrating from `.slice-system` symlink" subsection.

**Decision: replace branch.** Reasoning: CONSUMER.md's audience-shape per ADR D6 is the consumer entry doc — quickstart, install, dispatch, troubleshooting, anchor links into `CLAUDE.md` `[both]` sections. It is deliberately steady-state, not transitional. A `.slice-system → plugin` migration runbook is a one-shot, time-bounded artefact aimed at the single existing symlink consumer (`complex-rag-analysis`); embedding it inside CONSUMER.md would (a) clutter the steady-state quickstart for every future first-time consumer who never had a symlink, (b) couple the consumer-entry-doc lifecycle to a transitional concern that should age out of the documentation surface, and (c) split runbook content across two doc-classes (CONSUMER.md and the not-yet-deleted `docs/upgrading-from-pre-compression.md`'s historical sibling slot under `docs/upgrading-*.md`). The replace branch is the principled co-location: `docs/upgrading-from-symlink.md` lives adjacent to `docs/upgrading-from-pre-compression.md` (which it git-rm-supersedes), inheriting the existing `docs/upgrading-*.md` doc-class for transitional migration content. CONSUMER.md gets a mechanical URL fix only (R.4) and is left lean; the README's R.1 migration-block paragraph carries the discovery breadcrumb to the new doc.

**Deliverable inventory (envelope-bounded).** Phase 3 writes within these paths only (verbatim from the plan's `envelope:`):

- `scripts/migrate_from_symlink.sh` — new, executable, Bash 3.2-compatible.
- `tests/unit/test_migrate_from_symlink.py` — new, four cases (Phase 2 RED).
- `docs/upgrading-from-symlink.md` — new (replace branch).
- `docs/upgrading-from-pre-compression.md` — `git rm`'d (replace branch).
- `CONSUMER.md` — mechanical URL fix per R.4 Step 16.5: replace the F1-followup comment block at lines 13–16 with the canonical two-step install (`/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`). The validator-stdout-literal placeholder at lines 20–22 is OUT OF SCOPE per the operator amendment and stays as a documented F1-followup.
- `README.md` — rewrite "How to consume cairn" block per R.1 (four bullets, see below).
- `docs/ARCHITECTURE.md` — append F3 cite to INV-011 prose per P.1.

**Script contract (`scripts/migrate_from_symlink.sh`).** Bash 3.2+, POSIX utilities only (`unlink`, `test`, `cat`, `git`, `printf`, `readlink`, `jq`). Exit codes:

- `0` — preflight passed; symlink unlinked; `.claude/settings.json` filtered; banner printed naming the operator's next manual steps (`/plugin marketplace add https://github.com/firaaz/cairn`, `/plugin install cairn@cairn-marketplace`, session restart, smoke test).
- `2` — quiescence failure: `.claude/skill-runs/<id>/integration/sweep-notes.md` missing for one or more dirs (Pre-mortem Scenario 6 defense). Stderr names "in-flight skill-run" and the offending path. State unchanged.
- `3` — cairn-the-repo self-symlink detected: `[ -L .slice-system ] && [ "$(readlink .slice-system)" = "." ]`. Stderr names INV-011 and `docs/ARCHITECTURE.md:91`. State unchanged. (D8 structural enforcement.)

Force override: `CAIRN_MIGRATE_FORCE=1` bypasses exit-2 only (NOT exit-3). Force-mode prints a loud stderr warning naming Pre-mortem Scenario 6 and the orphan-state risk, then proceeds with exit 0. The cairn-the-repo abort is non-overridable.

**Settings.json filter.** The script applies a `jq` filter that drops any hook entry whose `command` field contains `$CLAUDE_PROJECT_DIR/.slice-system/`. Atomic write via `.new` + `mv`. Phase 3 confirms exact `jq` shape against `complex-rag-analysis`'s real settings.json structure.

**Runbook content (`docs/upgrading-from-symlink.md`).** Six sections, each derived verbatim from plan Section M.1–M.6:

1. **Quiescence preflight.** Cite Pre-mortem Scenario 6; verbatim warning ("Before migrating, complete in-flight `cairn-tdd-feature` runs to Phase 4 close. Migration mid-dispatch will orphan `.claude/skill-runs/<feature-id>/intent.md`…").
2. **Atomic swap.** The four mechanical steps with exact commands. Step-2 inline literal: `/plugin marketplace add https://github.com/firaaz/cairn` (sourced from `.claude-plugin/marketplace.json:12`'s `"url": "https://github.com/firaaz/cairn.git"` — runbook drops the `.git` suffix per the slash-command convention used in the rest of the doc surface). Step 1 is `unlink .slice-system` NOT `rm -rf` (the latter follows the symlink and deletes cairn). Step 3 is `/plugin install cairn@cairn-marketplace`. Step 4 is the `jq` filter for stale `.slice-system/` hook entries in `.claude/settings.json`.
3. **Session restart callout** — agent-registry reload requirement (Phase 0.5 Role 2 trace lines 33, 43).
4. **State preservation enumeration** (verbatim from plan M.4 — survives: `.claude/handoff.md`, `.claude/active-envelope.yaml`, `.claude/skill-runs/*`, `.claude/learning.md`, `.claude/adr-editorial-fixes.log`, `docs/plans/*`, `docs/adr/*`, `docs/ARCHITECTURE.md`; goes away: the symlink itself + stale settings.json hook entries).
5. **Rollback path** (re-create symlink with absolute path, `git checkout HEAD -- .claude/settings.json`, relaunch; rollback before quitting if at all possible).
6. **Smoke test** (re-run F1's post-install validator, dispatch trivial `cairn-tdd-feature`, confirm `.claude/envelope-grants.log` lands consumer-side per D5).

**README rewrite (R.1).** Four bullets replace today's `ln -s …` instruction at `README.md:17-33`:

1. **First-time-consumer block** with the literal install commands inline: "Run `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. See `CONSUMER.md` for the full quickstart." This supersedes the F1-followup `<marketplace-url>` placeholder comment at the current `README.md:21`.
2. **Migration block** (one paragraph): "If you currently consume cairn via `.slice-system → cairn` symlink, see the migration runbook at `docs/upgrading-from-symlink.md`." (Path is the replace-branch survivor.)
3. **Maintainer carve-out**, verbatim: "Cairn-the-repo itself retains a `.slice-system → .` self-symlink for maintainer dogfooding (INV-011, `docs/ARCHITECTURE.md`). This is a one-repo exemption — downstream consumers must NOT recreate it."
4. **Drop the fallback framing.** The current `README.md:23` reads `Symlink-based consumption is kept as a fallback while the plugin marketplace stabilises:` followed by a `cd /path/to/your/project && ln -s …` block (lines 25–29) and a hook-configuration paragraph (line 31) and an `F3-followup:` comment (line 33). The R.1 rewrite removes the fallback prose, the `ln -s` block, and the now-resolved `F3-followup:` comment in the same edit. Plugin install is the primary path post-F3; the maintainer carve-out (bullet 3) is the only surviving symlink mention in the consumption block.

**CONSUMER.md placeholder fix (R.4).** Replace the block at `CONSUMER.md:13-16`:

```
# F1-followup: marketplace git URL literal lands in F1's PR.
claude plugin install <marketplace-url>/cairn
```

with the canonical two-step:

```
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

The literal URL is sourced from `.claude-plugin/marketplace.json:12`. The validator-stdout-literal placeholder at `CONSUMER.md:21-22` is left as a separately tracked F1-followup per the operator amendment (the dual-placeholder state post-F3 is intentional under the replace branch — Phase 4 audit recognises this).

**INV-011 prose cite (P.1).** Append to `docs/ARCHITECTURE.md`'s INV-011 prose at the existing cite parenthesis (line 91): "M6/F3 explicitly excludes cairn-the-repo from the downstream-consumer migration: the `scripts/migrate_from_symlink.sh` helper aborts with exit 3 if it detects a self-symlink target of `.`, and the retire-docs sweep preserves cairn-the-repo's self-symlink documentation." If `reversibility-guard.sh` denies the body-prose append (the hook only allows `Edit` whose `old_string` first line begins with `status:`/`superseded-by:`/`firmness:` — INV-011 is body prose, not frontmatter), surface to operator: the edit is small enough for manual authorship outside the dispatch envelope; note in Phase 4 sweep-notes.

## Verification

Phase 4 audit checks (the prior 7 plus an implicit 8th per the operator amendment):

1. `scripts/migrate_from_symlink.sh` exists, is executable, and `tests/unit/test_migrate_from_symlink.py` passes all four cases under `uv run pytest tests/unit/test_migrate_from_symlink.py -v`.
2. `README.md`'s consumption block has been rewritten; the maintainer carve-out paragraph is present and cites INV-011; the "fallback while plugin marketplace stabilises" prose is gone (`grep -n "fallback while" README.md` returns nothing).
3. Exactly one of `{docs/upgrading-from-pre-compression.md, docs/upgrading-from-symlink.md}` is tracked by `git ls-files`; per the replace-branch decision, the survivor is `docs/upgrading-from-symlink.md`.
4. `docs/ARCHITECTURE.md` INV-011 prose contains an explicit "F3" or "M6/F3" token referencing `scripts/migrate_from_symlink.sh` and exit 3.
5. `grep -rn "\.slice-system" docs/ README.md CLAUDE.md` returns only INV-011 / self-symlink / bootstrap context lines, or ADR/spec/plan historical references (ADRs are append-only and exempt).
6. INV-011 directly verified: `readlink .slice-system` returns `.` at the cairn-the-repo root, and the existing `invariant-check INV-011` block in `docs/ARCHITECTURE.md` (lines 93–97) continues to validate.
7. `uv run pytest tests/unit/` is green; the new test adds, nothing else regresses relative to the F2-landed baseline (`8ca229f` + `e3d088d`).
8. `grep -n "<marketplace-url>" CONSUMER.md README.md` returns zero hits post-F3 (operator-amendment new check). The validator-stdout-literal placeholder at `CONSUMER.md:21-22` is documented as an unresolved F1-followup in Phase 4 sweep-notes; this is intentional under the replace branch.

Phase 2 RED test cases (Phase 3 makes green):

- (a) Happy-path fixture (symlink to a non-`.` target, fake settings.json with one symlink-anchored hook entry, empty `.claude/skill-runs/`) → exit 0; symlink unlinked; settings.json contains no `"$CLAUDE_PROJECT_DIR/.slice-system/"` substring; stdout names `/plugin marketplace add https://github.com/firaaz/cairn`.
- (b) In-flight skill-run fixture (one `.claude/skill-runs/<id>/` dir without `integration/sweep-notes.md`) → exit 2; stderr names "in-flight skill-run" and the offending path; symlink and settings.json unchanged.
- (c) Cairn-self fixture (symlink target `.`) → exit 3; stderr names INV-011; no state change. **Non-overridable** (force-mode does NOT bypass).
- (d) Force-mode fixture (in-flight skill-run + `CAIRN_MIGRATE_FORCE=1`) → exit 0; stderr contains the Pre-mortem Scenario 6 warning string.

## Risk Surface

Domain-level wrongness that passes CI:

1. **INV-011 silent erosion.** R.3 grep sweep accidentally rewrites a maintainer-context `.slice-system` mention into consumer-context plugin-install prose; tests stay green because no test exercises maintainer-bootstrap onboarding.
2. **Settings.json shape drift.** `jq` filter assumes a hook-entries-as-array shape; if `complex-rag-analysis`'s real settings.json carries a different shape (e.g., object-keyed entries, nested matchers), the filter silently no-ops, leaving stale `$CLAUDE_PROJECT_DIR/.slice-system/...` entries that 404 silently post-cutover (Pre-mortem Scenario 2 collapse). Test fixtures may not mirror the real shape.
3. **Build-time drift between F1's smoke build and the real plugin install.** Phase 4 verification re-uses `scripts/build_dist.py` smoke output; if the consumer's real `/plugin install` materialises a different tree (cache layout, manifest version), the smoke test passes but post-cutover dispatch fails.
4. **Replace-branch dual-doc state.** Phase 3 ships `docs/upgrading-from-symlink.md` but forgets the `git rm` of `docs/upgrading-from-pre-compression.md`; Phase 4 audit check 3 catches this only if the grep is exhaustive.
5. **INV-011 ARCHITECTURE.md edit denied silently.** `reversibility-guard.sh` blocks the body-prose append; Phase 3 swallows the denial and Phase 4 sees the cite missing only via grep — preservation breadcrumb absent from the cite chain.
6. **Quiescence preflight false-negative.** A consumer with a Phase-4-orphan slice (Phase 3 source mods uncommitted, see operator memory `feedback_phase4_rolelock_fixup.md`) has `integration/sweep-notes.md` present yet a non-quiesced state; helper exits 0 and migration proceeds mid-orphan.
7. **CONSUMER.md edit collides with R.2 branch state — dual-placeholder confusion.** The replace branch leaves the validator-stdout-literal placeholder at `CONSUMER.md:21-22` unresolved post-F3 by design (operator amendment scope). If a future maintainer interprets the surviving F1-followup comment as "F3 forgot one", they may submit a one-off cleanup that lands the validator stdout literal incorrectly (without coordination with F1's actual stdout shape). Phase 4 sweep-notes must explicitly call out the dual-placeholder state as intentional + tracked, citing this intent's Boundary section. The audit (check 8) recognises only the `<marketplace-url>` placeholder is in F3 scope; the `<...>` validator-stdout-literal sentinel is not in the same syntactic class and so the grep in check 8 will not hit it.

## Feature-Local Invariants

- **FLI-1 (D8 structural).** `scripts/migrate_from_symlink.sh` MUST refuse to run inside cairn-the-repo by self-symlink-target detection (`readlink .slice-system == "."` → exit 3). Phase 2 test (c) is the structural enforcement of D8. Force-mode does NOT bypass this exit; only exit-2 (quiescence) is overridable.
- **FLI-2 (replace-branch atomicity).** Post-Phase-3, `git ls-files` MUST contain `docs/upgrading-from-symlink.md` AND MUST NOT contain `docs/upgrading-from-pre-compression.md`. Both halves of the swap are required; either alone is a defect.
- **FLI-3 (script exit-code surface).** The script's three exit codes (0, 2, 3) are the protocol-level contract Phase 2 tests against; new exit codes added by Phase 3 outside this set are scope-creep.
- **FLI-4 (no slash-command chaining).** The script MUST NOT attempt to invoke `/plugin marketplace add` or `/plugin install` itself; those are operator-bound session-restart-aware actions per Pre-mortem Scenario 2 defense (Section M.2 Step 7). Test (a) asserts stdout names them as the next manual step.
- **FLI-5 (POSIX-only).** Bash 3.2 + POSIX utilities only; no `mapfile`, `readarray`, `[[` extended pattern matching beyond Bash 3.2 surface, or GNU-only flags. macOS default shell must run the script unmodified.
- **FLI-6 (envelope discipline).** All Phase 3 writes land within the plan's `envelope:` regex list; the operator-envelope at `.claude/active-envelope.yaml` (if active) or `role_guard.py` per-phase allowlist enforces this — no scope creep into adjacent paths.
- **FLI-7 (literal-URL canonicalisation).** Every consumer-facing surface that names the marketplace install command MUST use the literal `https://github.com/firaaz/cairn` (sourced from `.claude-plugin/marketplace.json:12`) — no `<marketplace-url>` placeholder, no `<git-url>` token, no synonym. Surfaces in F3 scope: `README.md`, `CONSUMER.md`, `docs/upgrading-from-symlink.md`. Phase 4 audit check 8 enforces. The validator-stdout-literal placeholder at `CONSUMER.md:21-22` is a different placeholder class (validator stdout, not URL) and is explicitly OUT of FLI-7's scope; it remains an F1-followup.

## Explicit Scope-Out

Per plan §Out-of-scope follow-ups, Boundary, and the operator amendment:

- **Multi-consumer rollout playbook.** F3 covers `complex-rag-analysis` only; a general N-consumer migration playbook with version-skew detection is deferred (track on `docs/roadmap.md`).
- **Plugin uninstall hygiene tests.** Rollback documents `/plugin uninstall` but no clean-uninstall-test ships in F3.
- **Settings.json schema validator (typed).** A pydantic model for settings.json shape would catch drift; out of scope.
- **End-to-end CI integration test.** "Install plugin in fixture repo, dispatch trivial feature, assert clean exit" is M5.1+ work; F1's unit-level post-install validator is the F3-era ceiling.
- **Auto-detection of the cairn git URL.** Operator-supplied per the runbook; future ergonomic improvement.
- **Cairn-internal `.slice-system → .` retire.** Explicitly NOT in scope (D8 / INV-011); requires a superseding ADR.
- **CONSUMER.md migration subsection (delete-branch content).** Replace-branch keeps the runbook in `docs/upgrading-from-symlink.md`; CONSUMER.md gets ONLY the mechanical URL fix (R.4 Step 16.5), no migration subsection. CONSUMER.md stays a steady-state consumer entry doc.
- **Validator-stdout-literal placeholder fix (`CONSUMER.md:21-22`).** Tracked as a separate F1-followup per the operator amendment scope; F3's R.4 resolves only the `<marketplace-url>` placeholder. The dual-placeholder state post-F3 is intentional and called out in Phase 4 sweep-notes (Risk Surface item 7).
- **Slash-command payload (`/catchup`, `/handoff`, `/decision`, `/new-adr`).** Deferred to M5.1 per ADR D3; F3 does not ship them.
