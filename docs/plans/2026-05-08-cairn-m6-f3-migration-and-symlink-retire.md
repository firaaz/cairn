---
id: cairn-m6-f3-migration-and-symlink-retire
name: Cairn M6 F3 — Migration + Symlink Retire
firmness: provisional
status: spec — for cairn-tdd-feature dispatch
date: 2026-05-08
scope: complex-rag-analysis cutover from `.slice-system → cairn` to plugin install; retire downstream-consumer symlink docs in cairn-the-repo (cairn-the-repo's own self-symlink stays per INV-011/D8).
invariants-touched:
  - INV-011
inputs:
  - docs/adr/m5-plugin-distribution-and-symlink-retire.md
  - docs/ARCHITECTURE.md
  - docs/plans/2026-05-08-cairn-m5-f1-packaging.md
  - docs/plans/2026-05-08-cairn-m5-f2-consumer-doc-surface.md
  - .claude/skill-runs/m5-plugin-decision/phase-0.5-journey.md
  - .claude/skill-runs/m5-plugin-decision/phase-1-pre-mortem.md
envelope:
  - '^docs/plans/2026-05-08-cairn-m6-f3-migration-and-symlink-retire\.md$'
  - '^docs/upgrading-from-symlink\.md$'
  - '^docs/upgrading-from-pre-compression\.md$'
  - '^CONSUMER\.md$'
  - '^docs/ARCHITECTURE\.md$'
  - '^README\.md$'
  - '^scripts/migrate_from_symlink\.sh$'
  - '^tests/unit/test_migrate_from_symlink\.py$'
---

# Cairn M6 F3 — Migration + Symlink Retire

> **For agentic workers:** REQUIRED SUB-SKILL: `cairn-tdd-feature` is the dispatch shell; this plan is its input. Sequenced after F1 (packaging) and F2 (consumer-doc surface) — DO NOT start F3 dispatch until F1's `marketplace.json` + `dist/.claude-plugin/plugin.json` + `dist/hooks/hooks.json` and F2's `CONSUMER.md` are landed and merged. Within-feature parallel subagents are permitted per CLAUDE.md "Within-slice parallel subagents are allowed" — Section M (migration script) and Section R (retire-docs) are independent and may run in parallel agents during Phase 3.

**Goal:** Land the M6 half of the M5+M6 milestone: ship a runbook + thin migration helper that takes the only existing `.slice-system → cairn` consumer (`complex-rag-analysis`) off the symlink and onto `/plugin install cairn@cairn-marketplace`, and retire the symlink-era upgrade documentation in cairn-the-repo so future downstream consumers reach for plugin install only. INV-011 is preserved verbatim: cairn-the-repo's own `.slice-system → .` self-symlink stays exactly as it is — F3 touches only downstream-consumer documentation and consumer-side migration mechanics.

**Architecture:** Three threads. **Thread M (migration runbook + script)** authors the consumer-side cutover: a documented sequence (quiescence → atomic swap → session restart → smoke test) plus a thin `scripts/migrate_from_symlink.sh` helper that performs the mechanical steps and refuses to run if the consumer's `.claude/skill-runs/` contains a non-quiesced feature dir (Pre-mortem Scenario 6 defense). **Thread R (retire docs)** sweeps cairn-the-repo's symlink-era guidance: replaces `docs/upgrading-from-pre-compression.md` with a thin `docs/upgrading-from-symlink.md` (or deletes and folds into `CONSUMER.md` at repo root — Phase 1 picks based on F2's CONSUMER.md final shape), updates `README.md`'s "How to consume cairn" block to point at plugin install for downstream consumers while explicitly preserving the INV-011 self-symlink note for cairn-the-repo maintainers. **Thread P (preservation guard)** is a single targeted edit to `docs/ARCHITECTURE.md`'s INV-011 prose to add F3 as an explicit cite — making the self-symlink-stays commitment grep-discoverable for future migrations.

**Tech Stack:** Bash 3.2+ (script must run on macOS default shell — no bash 4 features). Markdown for all documentation surfaces. Python 3.11 + pytest for the test (`tests/unit/test_migrate_from_symlink.py` runs the script in a fixture repo via `subprocess.run`). No new dependencies; the script uses only POSIX utilities (`unlink`, `test`, `cat`, `git`, `printf`) and assumes the consumer already has `claude` CLI on PATH (per F1's plugin install precondition).

---

## Self-review summary

This plan was self-reviewed at authoring against the M5 ADR's D-commitments that fall in F3 scope:

- **D8 — Cairn self-consumption stays on Path B.** Section P (Thread P) explicitly preserves cairn-the-repo's `.slice-system → .` self-symlink. The migration script (Section M) refuses to run if it detects the self-symlink target is `.` (i.e., it's running inside cairn-the-repo). The retire-docs sweep (Section R) explicitly carves out the cairn-maintainer case and points to INV-011.
- **D9 — F3 covers `complex-rag-analysis` migration + symlink retire for downstream consumers.** Section M is the migration runbook; Section R is the retire sweep. Cairn-the-repo's exemption is restated three times (this self-review, Section M's preflight check, Section R's retire-docs prose) — INV-011 is the load-bearing reference.
- **Pre-mortem Scenario 6 defense (Risk Register row 6).** Section M Phase 1 ships the quiescence preflight check before any swap step.
- **Pre-mortem Scenario 1 carry-through.** F1 ships the `role_guard.py` `CLAUDE_PROJECT_DIR` fix + post-install validator; F3's smoke test (Section M Phase 6) re-invokes that validator and additionally dispatches a trivial `cairn-tdd-feature` to confirm the agent registry reloaded correctly.
- **F1 dependency.** Several steps in Section M reference artifacts that F1 must land first: `.claude-plugin/marketplace.json`, `dist/.claude-plugin/plugin.json`, `dist/hooks/hooks.json`, the post-install validator, and the `role_guard.py:28,121` anchoring fix. If any of those are missing at F3 dispatch time, **abort and surface to operator** — F3 is structurally blocked on F1.
- **F2 dependency.** Section R Phase 2 (delete vs. replace `upgrading-from-pre-compression.md`) is gated on F2's final `CONSUMER.md` shape: if F2 ships a "migration from symlink" subsection, F3 deletes the old upgrade doc; if F2 keeps `CONSUMER.md` install-only, F3 replaces it with `upgrading-from-symlink.md`.

Coverage gaps deliberately deferred to **Out-of-scope follow-ups** at the bottom — review them before Phase 1.

---

## Section M — Consumer migration runbook + helper script

This is the consumer-side cutover sequence. The runbook is canonical (lives in `CONSUMER.md`'s migration section at repo root per F2, OR in `docs/upgrading-from-symlink.md` per Section R Phase 2 — Phase 1 of F3 must read F2's landed `CONSUMER.md` and decide the home). The helper script in `scripts/migrate_from_symlink.sh` is a thin wrapper: it does NOT replace operator judgment; it enforces the preflight checks and prints the next manual step, refusing to chain operations that need a fresh Claude Code session (e.g., the agent-registry reload after swap).

### M.0 Preflight: F1 + F2 landed?

- [ ] **Step 1: Verify F1 deliverables exist on cairn's `dev` branch.**

F1's actual contract is that cairn ships *templates* and a *build script* — the `dist/` tree is synthesized on demand by `scripts/build_dist.py`, NOT committed (per ADR D3 + `scripts/build_dist.py` ALLOW_LIST). Verify the templates, the build script, the post-install validator, and the CI gate — plus a smoke build to confirm `build_dist.py` can produce a usable plugin payload:

```bash
# In cairn-the-repo:
test -f .claude-plugin/marketplace.json &&
test -f .claude-plugin/plugin-template.json &&
test -f .claude-plugin/hooks-template.json &&
test -f scripts/build_dist.py &&
test -f scripts/postinstall_validate.py &&
test -f .github/workflows/dist-gate.yml &&
git log --oneline --grep="role_guard.*CLAUDE_PROJECT_DIR\|m5-f1\|F1" -- checks/role_guard.py | head &&
# Smoke-build dist into a tmp tree and confirm it materialises plugin.json + hooks.json:
uv run python scripts/build_dist.py --dist-root /tmp/cairn-f3-preflight-dist &&
test -f /tmp/cairn-f3-preflight-dist/.claude-plugin/plugin.json &&
test -f /tmp/cairn-f3-preflight-dist/hooks/hooks.json &&
rm -rf /tmp/cairn-f3-preflight-dist
```

Expected: all six artefacts present, at least one commit touching `checks/role_guard.py` to anchor `CAIRN_ROOT` via `CLAUDE_PROJECT_DIR` (D5), and the smoke-build produces a valid `dist/` tree. If any check fails, **abort this dispatch** and re-queue F3 after F1 lands or is repaired.

- [ ] **Step 2: Verify F2 deliverables exist on cairn's `dev` branch.**

F2 shipped `CONSUMER.md` at the **repo root** (not `docs/CONSUMER.md`) — verify the actual landed path:

```bash
test -f CONSUMER.md &&
grep -q "Reading order\|reading order\|Where to next" README.md
```

Expected: `CONSUMER.md` present at root, README has a reading-order block (in F2's shipped form this section is titled "Where to next"). If missing, abort and re-queue F3 after F2 lands.

- [ ] **Step 3: Decide where the migration runbook lives.**

Read F2's landed `CONSUMER.md` (at repo root). If it includes a "Migrating from `.slice-system` symlink" subsection, F3's runbook content is authored there directly (Section R Phase 2 deletes `upgrading-from-pre-compression.md`). Otherwise, F3 ships `docs/upgrading-from-symlink.md` (Section R Phase 2 replaces). Phase 1 captures the decision in `intent.md`. (Preflight evidence at F3 dispatch time: `CONSUMER.md` does NOT have a migration subsection — the **replace** branch is expected.)

**Decision-context amendment (2026-05-08, post-initial-Phase-1):** F3 now ALSO fixes CONSUMER.md's F1-followup placeholder (line 14: `<marketplace-url>` → `https://github.com/firaaz/cairn`) regardless of replace-vs-delete branch — see Section R.4 below. Because CONSUMER.md is mutated either way, the replace/delete decision is freshly contested at Phase 1: now that CONSUMER.md is being touched, does it also gain the migration subsection (delete branch), or does the URL fix stay mechanical-only and the runbook live in `docs/upgrading-from-symlink.md` (replace branch)? Phase 1 picks with this expanded scope in mind.

### M.1 Pre-migration quiescence (Pre-mortem Scenario 6)

- [ ] **Step 4: Document the quiescence requirement in the runbook.**

The runbook must state, verbatim near the top: "Before migrating, complete in-flight `cairn-tdd-feature` runs to Phase 4 close. Migration mid-dispatch will orphan `.claude/skill-runs/<feature-id>/intent.md` because the live session's agent registry references the pre-migration `.slice-system/.claude/agents/*` paths and Phase 2/3 re-dispatch will fail to discover the `subagent_type` slugs." Reference Pre-mortem Scenario 6 by name.

- [ ] **Step 5: Implement quiescence preflight in `scripts/migrate_from_symlink.sh`.**

The helper script's first action is a quiescence check:

```bash
# Pseudo-code; Phase 3 implements
for d in .claude/skill-runs/*/; do
  feat="$(basename "$d")"
  if [ -d "$d" ] && [ ! -f "$d/integration/sweep-notes.md" ]; then
    echo "ABORT: in-flight skill-run at $d (no Phase-4 sweep-notes.md)" >&2
    echo "  Finish or abandon this dispatch before migrating." >&2
    exit 2
  fi
done
```

Operator can override with `CAIRN_MIGRATE_FORCE=1` (env-var override discipline per CLAUDE.md "no hardcoded ... in consumer-facing scripts"). Force-mode prints a loud stderr warning naming Pre-mortem Scenario 6 and the exact orphan-state risk.

### M.2 Atomic swap

- [ ] **Step 6: Document the swap sequence in the runbook.**

The four mechanical steps, in order, with exact commands:

1. **Remove the symlink:** `unlink .slice-system` (NOT `rm -rf .slice-system` — that follows the symlink and would delete cairn).
2. **Add cairn marketplace:** `/plugin marketplace add https://github.com/firaaz/cairn` (the literal URL from `.claude-plugin/marketplace.json:12`; F1 left the `<marketplace-url>` placeholder unresolved in CONSUMER.md and README.md, and F3's R.1 + R.4 resolve it).
3. **Install cairn:** `/plugin install cairn@cairn-marketplace`. Per F1/D4, this drops hook registrations into the plugin's internal `hooks/hooks.json`, NOT the consumer's `.claude/settings.json` — but legacy symlink-anchored entries already in `.claude/settings.json` will still fire and 404 silently if not removed (Pre-mortem Scenario 2 collapse).
4. **Edit `.claude/settings.json` to remove stale symlink-anchored hook entries.** Specifically: any `"command"` field containing `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`. The runbook ships a `jq` snippet that filters these out:

```bash
jq '
  .hooks |= with_entries(
    .value |= map(
      select(
        (.hooks // [] | map(.command // "" | contains("$CLAUDE_PROJECT_DIR/.slice-system/")) | any) | not
      )
    )
  )
' .claude/settings.json > .claude/settings.json.new && mv .claude/settings.json.new .claude/settings.json
```

(Phase 3 verifies the exact `jq` shape against the consumer's settings.json structure; the snippet above is illustrative.)

- [ ] **Step 7: Implement the swap in `scripts/migrate_from_symlink.sh`.**

The script automates steps 1 and 4 (mechanical: unlink + jq edit). Steps 2 and 3 (`/plugin marketplace add`, `/plugin install`) are slash commands inside Claude Code — the script CANNOT execute them; it prints them as the operator's next action and exits with code 0 + a "next step" banner. This boundary is deliberate: Pre-mortem Scenario 2's defense relies on operator awareness; chaining the swap in a single script call would hide the session-restart requirement.

- [ ] **Step 8: Cairn-the-repo exemption check (D8/INV-011 preservation).**

The script's preflight detects whether it's running inside cairn-the-repo and aborts:

```bash
if [ -L .slice-system ] && [ "$(readlink .slice-system)" = "." ]; then
  echo "ABORT: this is cairn-the-repo (self-symlink target = '.')." >&2
  echo "  INV-011 (docs/ARCHITECTURE.md:91) preserves cairn's self-symlink." >&2
  echo "  Migration is for downstream consumers only." >&2
  exit 3
fi
```

This is the structural enforcement of D8. The script literally cannot run in cairn-the-repo.

### M.3 Session restart

- [ ] **Step 9: Document the session-restart requirement.**

Per Phase 0.5 Role 2 trace (lines 33, 43): the agent registry loads at session start; agent definitions added mid-session aren't `subagent_type`-discoverable. After the swap, the operator MUST quit and re-launch Claude Code before the next `cairn-tdd-feature` dispatch. The runbook states this in a callout block, not buried in prose. The migration script's exit banner reiterates: "Next: quit Claude Code, re-launch, then run the smoke test below."

### M.4 State preservation

- [ ] **Step 10: Document state that survives migration.**

The runbook enumerates explicitly. **State that survives** (lives in consumer root, untouched by migration):

- `.claude/handoff.md`
- `.claude/active-envelope.yaml`
- `.claude/skill-runs/*` (all per-feature workspaces)
- `.claude/learning.md`
- `.claude/adr-editorial-fixes.log`
- All `docs/plans/*`
- All `docs/adr/*`
- `docs/ARCHITECTURE.md`

**State that goes away:**

- The `.slice-system → cairn` symlink itself.
- The stale hook entries in `.claude/settings.json` referencing `$CLAUDE_PROJECT_DIR/.slice-system/...`.

The list is verbatim from Phase 0.5 Role 2 §6 — no invention.

### M.5 Rollback

- [ ] **Step 11: Document the rollback path.**

If the post-migration smoke test fails or the operator decides to revert:

1. Re-create the symlink: `ln -s <abs-path-to-cairn-checkout> .slice-system`.
2. Restore the original `.claude/settings.json` from git: `git checkout HEAD -- .claude/settings.json`.
3. Quit and relaunch Claude Code.
4. Optionally: `/plugin uninstall cairn@cairn-marketplace` and `/plugin marketplace remove <git-url>` (cleanup; not strictly required since the plugin install does not modify the consumer's symlink-era state).

The runbook states the rollback must happen BEFORE quitting the migration session if at all possible — settings.json edits after a fresh-session restart with the new agent registry require coordinating two source-of-truth states. Phase 1 may refine this based on operator-tested behavior.

### M.6 Post-migration smoke test

- [ ] **Step 12: Document the smoke test.**

After the session restart:

1. Re-run F1's post-install validator (per D5: writes a sample envelope, attempts a denied write, confirms exit 1). The validator's exact invocation is whatever F1 ships — Phase 1 reads F1's plan-doc to capture it.
2. Dispatch a trivial `cairn-tdd-feature` to confirm hooks fire and the agent registry resolved. The runbook ships a "hello-world" plan-doc fixture (or points at an existing trivial plan in cairn — Phase 1 picks; one option is to point at `docs/plans/2026-05-08-hook-bare-python3-smoketest.md`-style minimal plan).
3. Confirm `.claude/envelope-grants.log` lands in the consumer's `.claude/` (not the plugin cache) — direct verification of D5's anchoring fix.

If any step fails, follow Section M.5 rollback.

### M.7 Test the migration script

- [ ] **Step 13: Phase 2 RED tests for `scripts/migrate_from_symlink.sh`.**

`tests/unit/test_migrate_from_symlink.py`:

1. Sets up a fixture consumer repo in `tmp_path` with a `.slice-system` symlink, a fake `.claude/settings.json` carrying a symlink-anchored hook entry, and an empty `.claude/skill-runs/`. Runs the script. Asserts: symlink unlinked, settings.json no longer contains `.slice-system/`, exit 0, stdout names the next manual step (`/plugin marketplace add`).
2. Sets up a fixture with a non-quiesced skill-run dir (no `integration/sweep-notes.md`). Asserts: exit 2, stderr names "in-flight skill-run", symlink and settings.json untouched.
3. Sets up a fixture mimicking cairn-the-repo (self-symlink target `.`). Asserts: exit 3, stderr names INV-011, no state change.
4. Force-mode test: non-quiesced skill-run + `CAIRN_MIGRATE_FORCE=1`. Asserts: exit 0, stderr contains the Pre-mortem Scenario 6 warning.

- [ ] **Step 14: Phase 3 implements `scripts/migrate_from_symlink.sh`.**

Bash 3.2-compatible. No bash-isms beyond what macOS default shell supports. Phase 3 makes Phase 2's tests green.

---

## Section R — Retire symlink-era docs in cairn-the-repo

### R.1 Update README's consumption block

- [ ] **Step 15: Rewrite README's "How to consume cairn" section.**

Today the section instructs `ln -s ~/.../cairn .slice-system`. After F3 lands, the canonical path is plugin install. Replace the section with:

1. A first-time-consumer block: "Run `/plugin marketplace add https://github.com/firaaz/cairn` then `/plugin install cairn@cairn-marketplace`. See `CONSUMER.md` for the full quickstart." (Note: literal URL inline — supersedes the F1-followup `<marketplace-url>` placeholder at the current README.md:21.)
2. A migration block (one paragraph): "If you currently consume cairn via `.slice-system → cairn` symlink, see the migration runbook at <link to wherever Phase 1 picked: `CONSUMER.md#migrating-from-symlink` or `docs/upgrading-from-symlink.md`>."
3. A maintainer carve-out (verbatim): "Cairn-the-repo itself retains a `.slice-system → .` self-symlink for maintainer dogfooding (INV-011, `docs/ARCHITECTURE.md`). This is a one-repo exemption — downstream consumers must NOT recreate it."
4. **Drop the "fallback while plugin marketplace stabilises" framing.** The current README.md:23 reads `Symlink-based consumption is kept as a fallback while the plugin marketplace stabilises:` — this prose is the F1-era hedge. Plugin install is now the primary path; the symlink is retired for downstream consumers. The R.1 rewrite removes this line and any prose that follows it framing symlink as a current-default; the maintainer carve-out (item 3 above) is the only surviving symlink mention in the consumption block.

The carve-out preserves D8/INV-011 in plain sight at the README level so future re-readers don't accidentally extend the symlink-retire to cairn-the-repo.

### R.2 Replace or delete `upgrading-from-pre-compression.md`

- [ ] **Step 16: Decide based on F2's CONSUMER.md.**

Per Section M.0 Step 3 decision:

- **If F2's CONSUMER.md has a migration subsection:** delete `docs/upgrading-from-pre-compression.md` outright. Add a note in `CONSUMER.md`'s migration section: "This supersedes the pre-compression upgrade doc retired in M6/F3." No further breadcrumb needed; git history preserves the old doc.
- **If F2's CONSUMER.md is install-only:** replace `docs/upgrading-from-pre-compression.md` with a thin `docs/upgrading-from-symlink.md` (≤200 words, in the same shape: deltas, Verify snippet per delta). Old file is git-rm'd; new file lives at the new path.

Phase 3 enacts whichever branch Phase 1 picked. Phase 4 audit confirms only one of the two doc-states is on disk post-merge (no lingering dual-doc state).

### R.4 Resolve F1-followup placeholders in CONSUMER.md

- [ ] **Step 16.5: Replace the `<marketplace-url>` placeholder in CONSUMER.md.**

F1 shipped CONSUMER.md with two unresolved F1-followup comments at lines 11–22 (the install + post-install validator quickstart blocks). F3 resolves these regardless of the R.2 replace/delete branch decision — both branches mutate CONSUMER.md. The fix:

- Replace the `# F1-followup: marketplace git URL literal lands in F1's PR.` comment + the `claude plugin install <marketplace-url>/cairn` line with the canonical two-step install:

```bash
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

- The post-install validator block (`# F1-followup: validator stdout literal lands in F1's PR.` + `uv run python scripts/validate_plugin_install.py`) is a separate F1-followup tracking a different deliverable (the validator's stdout literal). F3's scope per the operator amendment is the marketplace URL placeholder only — the validator stdout literal stays as a documented F1-followup unless Phase 1 picks the delete-branch in R.2 (in which case the surrounding migration content provides the escape valve to author the literal verification at the same edit). Phase 1 records the decision.

If Phase 1 picks the **delete branch** in R.2 (CONSUMER.md gains the migration subsection), Step 16.5 happens as part of the same CONSUMER.md edit. If Phase 1 picks the **replace branch**, Step 16.5 is a standalone CONSUMER.md edit and the migration runbook still lives in `docs/upgrading-from-symlink.md`.

### R.3 Sweep stale `.slice-system/` references in cairn docs

- [ ] **Step 17: Grep and review.**

```bash
grep -rn "\.slice-system" docs/ README.md CLAUDE.md | grep -v "INV-011\|self-symlink\|self-consumption\|bootstrap"
```

Expected: every remaining `.slice-system` mention in docs is in the context of (a) cairn-the-repo's own self-symlink (INV-011, the bootstrap exception), or (b) historical references in ADRs / spec / plans that document past state. Any prose that suggests a *new downstream consumer* should set up `.slice-system` is stale and gets rewritten to point at plugin install. Phase 4 audit re-runs the grep.

ADR text is append-only (`reversibility-guard.sh`) and is exempt from this sweep — past ADRs that mention `.slice-system` describe the state-of-the-world at their date and stay verbatim.

---

## Section P — INV-011 explicit cite of F3 (preservation breadcrumb)

### P.1 ARCHITECTURE.md INV-011 prose update

- [ ] **Step 18: Add F3 to INV-011's defense citation.**

Today `docs/ARCHITECTURE.md:91` cites `m5-plugin-distribution-and-symlink-retire` as the bootstrap-exception. Append (at the end of the existing prose, before the closing cite parenthesis):

"M6/F3 explicitly excludes cairn-the-repo from the downstream-consumer migration: the `scripts/migrate_from_symlink.sh` helper aborts with exit 3 if it detects a self-symlink target of `.`, and the retire-docs sweep preserves cairn-the-repo's self-symlink documentation."

This is a frontmatter-adjacent prose edit; `reversibility-guard.sh` allows Edits whose `old_string` first-line begins with frontmatter keys, but INV-011 is body prose, NOT frontmatter — verify the hook permits the edit. If denied, F3 must surface to operator (the edit is small enough that operator can author it manually outside the dispatch envelope; note this in Phase 4 sweep-notes).

The new cite makes future migrations grep-discoverable: anyone running `grep -n "F3\|INV-011" docs/ARCHITECTURE.md` finds the preservation guarantee.

---

## Verification (Phase 4 audit)

Phase 4 confirms:

1. `scripts/migrate_from_symlink.sh` exists, is executable, passes the four `test_migrate_from_symlink.py` cases.
2. `README.md`'s consumption block has been rewritten; the maintainer carve-out paragraph is present and references INV-011.
3. Exactly one of `{docs/upgrading-from-pre-compression.md, docs/upgrading-from-symlink.md}` exists post-merge (per the Section R.2 decision); the other is gone from `git ls-files`.
4. `docs/ARCHITECTURE.md` INV-011 prose cites F3 explicitly.
5. `grep -rn "\.slice-system" docs/ README.md CLAUDE.md` returns only INV-011 / self-symlink / bootstrap context lines (or ADR/spec/plan historical references).
6. Cairn-the-repo's `.slice-system → .` self-symlink is unchanged: `readlink .slice-system` returns `.`. (Direct INV-011 verification; INV-011's existing `invariant-check` block in `docs/ARCHITECTURE.md` continues to validate.)
7. The full pytest suite remains green relative to the F2-landed baseline (the new test adds; nothing else regresses).

---

## Out-of-scope follow-ups

These are deliberate exclusions; track them on `docs/roadmap.md` if they become relevant.

- **Multi-consumer rollout playbook.** F3 covers `complex-rag-analysis` only because it's the only existing symlink consumer. A general-purpose multi-consumer migration playbook (with consumer-version pinning across N consumers, version-skew detection, etc.) is deferred — Pre-mortem Scenario 2's full defense (`cairn upgrade` doctor command) is a separate feature.
- **Plugin uninstall hygiene.** F3's rollback path documents `/plugin uninstall` but doesn't ship tests for clean uninstall (e.g., does the plugin leave residual state in `.claude/`?). Defer to a hardening pass after first real-consumer migration data.
- **Settings.json schema validator.** F3's `jq` snippet for stripping stale hook entries assumes a specific settings.json shape. A typed validator (pydantic model for settings.json) would catch shape drift but isn't shipping in F3.
- **CI gate that builds + smoke-tests the plugin install end-to-end.** F1 should ship a unit-level post-install validator; an integration-level "install plugin in fixture repo, dispatch trivial feature, assert clean exit" CI test is follow-up M5.1+ work.
- **Auto-detection of the cairn git URL.** The runbook's `<git-url>` is operator-supplied. Future ergonomic improvement: `scripts/migrate_from_symlink.sh` reads the symlink target's `git remote get-url origin` and prints the install command pre-filled. Defer; correctness over convenience for a one-time migration.
- **Cairn-internal `.slice-system → .` retire.** Explicitly NOT in scope per D8/INV-011. Any future retire would require a superseding ADR.

---

## Plan-doc updates (2026-05-08, F3 dispatch preflight)

Operator-approved corrections at F3 dispatch time, before Phase 1 fired. The plan was authored against expected F1/F2 contracts; F1 and F2 landed with adjacent-but-different shapes, and the literal preflight in M.0 would have falsely triggered an abort. Changes:

- **`CONSUMER.md` path:** F2 shipped `CONSUMER.md` at the repo root, not at `docs/CONSUMER.md`. The envelope (`^docs/CONSUMER\.md$` → `^CONSUMER\.md$`), M.0 Step 2 path check, and all body references were corrected.
- **F1 deliverable shape:** F1 ships `.claude-plugin/{marketplace,plugin-template,hooks-template}.json` + `scripts/build_dist.py` + `scripts/postinstall_validate.py` + `.github/workflows/dist-gate.yml`. The `dist/` tree is *built on demand* by `build_dist.py` (per ADR D3 + the script's ALLOW_LIST), not committed. M.0 Step 1 was rewritten to verify the templates + build script + validator + CI gate, plus a smoke-build into `/tmp/cairn-f3-preflight-dist` that confirms `plugin.json` and `hooks/hooks.json` materialise.
- **CONSUMER.md migration-subsection state:** F2's landed `CONSUMER.md` does NOT contain a "Migrating from `.slice-system` symlink" subsection at F3 dispatch time, so Section R.2's **replace** branch is expected (ship `docs/upgrading-from-symlink.md`, delete `docs/upgrading-from-pre-compression.md`). Phase 1 confirms.

No changes to threads M/R/P content, deliverable inventory, or invariant scope. The Phase 4 audit checklist is unchanged.

### Plan-doc updates 2 (post-initial-Phase-1, F1-followup placeholder absorption)

After the initial Phase 1 (`d640ac6`) shipped its intent.md, the operator's interview-style review flagged that F1 left literal `<marketplace-url>` placeholders unresolved in CONSUMER.md (line 14) and README.md (line 21), plus a "fallback while plugin marketplace stabilises" framing at README.md:23 that contradicts F3's primary-path repositioning. The intent did not acknowledge these. F3 absorbs the fixes (operator decision: amend intent + RE_DISPATCH Phase 1):

- **M.2 Step 6 (atomic swap):** literal `https://github.com/firaaz/cairn` URL inline; F1-followup placeholder reference added; cite to `.claude-plugin/marketplace.json:12` as source of truth.
- **R.1 Step 15 (README rewrite):** literal URL in the first-time-consumer block; new bullet 4 explicitly drops the "fallback while plugin marketplace stabilises" framing so plugin install is the primary path post-F3.
- **New R.4 Step 16.5 (CONSUMER.md placeholder fix):** F3 resolves CONSUMER.md's `<marketplace-url>` placeholder regardless of the R.2 replace/delete branch decision, since both branches mutate CONSUMER.md. The validator-stdout-literal placeholder stays as a separate F1-followup unless the delete branch is picked.
- **M.0 Step 3 amendment:** the replace/delete decision is freshly contested at Phase 1 — now that CONSUMER.md is touched regardless, the decision tree adds a new variable (does CONSUMER.md gain the migration subsection in addition to the URL fix, or stay install-only?). Phase 1 picks with this expanded scope.

The envelope is unchanged (CONSUMER.md was already permitted; no new paths). The Phase 4 audit checklist gains an implicit eighth check: CONSUMER.md and README.md no longer contain `<marketplace-url>` placeholder strings.
