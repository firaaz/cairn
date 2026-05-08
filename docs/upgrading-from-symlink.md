# Upgrading from `.slice-system` symlink to `/plugin install cairn`

This runbook is for downstream consumers currently consuming cairn via a
`.slice-system → /path/to/cairn` symlink. Cairn's M5 milestone shipped a
plugin payload (`cairn@cairn-marketplace`); this doc takes you from the
legacy symlink to plugin install.

> **Cairn-the-repo itself is exempt** from this migration. Cairn's own
> `.slice-system → .` self-symlink is the maintainer bootstrap exception
> (INV-011, `docs/ARCHITECTURE.md:91`). The migration helper
> `scripts/migrate_from_symlink.sh` exits 3 if it detects a self-symlink
> target of `.`. Do not run this runbook against cairn-the-repo.

## 1. Quiescence preflight

Before migrating, complete in-flight `cairn-tdd-feature` runs to Phase 4
close. Migration mid-dispatch will orphan
`.claude/skill-runs/<feature-id>/intent.md` and the per-phase artefacts
under that directory. The dispatch skill's read paths reference
`.slice-system/...`; once the symlink is gone, in-flight phases can no
longer locate their canonical inputs.

**Pre-mortem Scenario 6** is the named risk. The migration helper checks
that every `.claude/skill-runs/<id>/` directory contains
`integration/sweep-notes.md` (the Phase 4 commit artefact). If any
in-flight run lacks that file, the helper exits 2 with the offending
path on stderr.

If you understand the orphan-state risk and need to migrate anyway, set
`CAIRN_MIGRATE_FORCE=1`. The helper will print a loud stderr warning
naming Pre-mortem Scenario 6 and the orphaned skill-runs, then proceed.

## 2. Atomic swap

Run the four mechanical steps below from your consumer-project root.

1. **Unlink the `.slice-system` symlink.**

   ```bash
   unlink .slice-system
   ```

   Use `unlink`, NOT `rm -rf` — the latter follows the symlink and
   deletes the cairn checkout it points to.

2. **Add the cairn marketplace.**

   ```
   /plugin marketplace add https://github.com/firaaz/cairn
   ```

   This is a Claude Code slash command, run from a Claude Code session
   in your consumer project. The literal URL above is canonical
   (sourced from cairn's `.claude-plugin/marketplace.json`).

3. **Install the plugin.**

   ```
   /plugin install cairn@cairn-marketplace
   ```

4. **Filter stale `.claude/settings.json` hook entries.**

   The legacy symlink-based wiring registered hooks at
   `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`. After plugin install
   the hooks live at the plugin-cache path; the old entries 404 silently.
   The helper script `scripts/migrate_from_symlink.sh` (in the cairn
   repo, available via your symlink prior to step 1 — copy it out
   before unlinking) bundles steps 1 and 4 into a single `jq` filter
   pass with atomic write.

## 3. Session restart

After `/plugin install` lands, **restart your Claude Code session**.
Agent and hook registries are populated at session start; a freshly
installed plugin's agents and hooks do not become active until the
next session.

## 4. State preservation

The following state survives the migration unchanged:

- `.claude/handoff.md`
- `.claude/active-envelope.yaml`
- `.claude/skill-runs/*` (per-feature dispatch artefacts)
- `.claude/learning.md`
- `.claude/adr-editorial-fixes.log`
- `docs/plans/*`
- `docs/adr/*`
- `docs/ARCHITECTURE.md`

The following goes away:

- The `.slice-system` symlink itself.
- Hook entries in `.claude/settings.json` whose `command` field
  references `$CLAUDE_PROJECT_DIR/.slice-system/...` (filtered by
  step 2.4).

## 5. Rollback

If the migration goes wrong **before you quit the session**, recover
in-place:

```bash
ln -s /absolute/path/to/cairn .slice-system
git checkout HEAD -- .claude/settings.json
```

Then `/plugin uninstall cairn@cairn-marketplace` and relaunch. Quitting
the session before rolling back makes recovery harder (the agent
registry will have already been refreshed against the plugin); roll
back before quitting if at all possible.

## 6. Smoke test

After the session restart:

1. Re-run F1's post-install validator
   (`uv run python scripts/validate_plugin_install.py` once the cairn
   plugin is installed — the script lives under the plugin path; cairn
   ships it at `scripts/postinstall_validate.py`). Confirm clean exit.
2. Dispatch a trivial `cairn-tdd-feature` run end-to-end. Watch for
   four commits (intent, validation, implementation, integration sweep
   notes).
3. Confirm `.claude/envelope-grants.log` lands consumer-side per ADR D5
   of `m5-plugin-distribution-and-symlink-retire`.

If any of the three smoke checks fail, see the rollback path above and
file an issue against cairn with the smoke-check output.
