# Phase 0.5 — User-Journey Trace

Decision: "How does cairn ship as a consumer-installable methodology, replacing the `.slice-system → .` symlink consumption pattern?"

Source: `general-purpose` agent run, 2026-05-08.

## Role 1 — First-time consumer

1. Lands on `README.md:11` which warns "Solo development, pre-v1. Not yet ready for adoption" — first boundary they cross is deciding to proceed.
2. Follows README's "How to consume cairn" block (`README.md:23-31`) and learns the only documented mechanism is `ln -s ~/.../cairn .slice-system` plus `.gitignore` — workstation-local absolute path, not a published artifact.
3. Installs system deps `brew install jq && uv tool install ruff` (`CLAUDE.md:13-15`); without these the three hooks silently no-op.
4. Runs `uv sync` inside the cairn checkout (`docs/operational-reference.md:11`) which materialises `.venv` and pins `uv.lock`. Consumer repo also needs a venv if it wants to invoke `uv run python role_guard.py` from its own settings.
5. M5 substitutes `claude plugin install cairn` for the symlink. Plugin must drop `.claude/skills/cairn-tdd-feature/`, `.claude/agents/phase-{1..4}-tdd.md`+`triager-tdd.md`+`role-topology.yaml`, slash commands under `commands/claude-code/`, and three hook scripts in `checks/`. Must also rewrite the `.claude/settings.json:21-51` hook entries from hardcoded `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` to a plugin-resolved path.
6. Hand-authors first plan doc at `docs/plans/<date>-<feature-id>.md` with `id:`/`envelope:` frontmatter (`docs/operational-reference.md:39-46`); cairn ships no template (Finding 3). Instantiates `.claude/handoff.md` from `templates/handoff.md`; optionally writes `.claude/active-envelope.yaml`.
7. Invokes `cairn-tdd-feature` with the plan path. Skill writes per-feature artifacts under `.claude/skill-runs/<feature-id>/` in *their* repo (`SKILL.md:40-44`); four phase agents commit to *their* git history; Phase-3 writes are gated by `role_guard.py` reading their plan doc's envelope.

**Boundaries:**
- Plugin install boundary: artifacts move from cairn's release artefact into `~/.claude/plugins/.../cairn/`; settings.json hook entries register from plugin → consumer settings.
- System-dep boundary: `jq`/`ruff` cross from system PATH into hook subprocesses.
- Hook-invocation boundary: Claude Code passes tool-input JSON via stdin to a script path resolved from consumer's CWD.
- Consumer-state boundary: per-feature plan docs, `.claude/skill-runs/<id>/`, `.claude/handoff.md`, `.claude/active-envelope.yaml` all live in the consumer repo, NOT in plugin cache.
- Python-runtime boundary: `role_guard.py` is invoked via `uv run python` — consumer needs uv + a venv reachable from `$CLAUDE_PROJECT_DIR`.
- Identifier-scheme boundary: cairn's `id:` convention crosses into consumer's filenames and frontmatter.

**Failure modes:** missing `jq`/`ruff` → silent no-op + false sense of safety; uv-not-installed → role_guard never runs and all writes pass; plugin-cache path differs from `$CLAUDE_PROJECT_DIR/.slice-system/...` literal in shipped settings.json → hooks 404; plan-doc `envelope:` mis-shaped → Phase-3 denies all writes; `.claude/skill-runs/` collides with consumer's existing `.claude/`.

## Role 2 — Existing symlink consumer (complex-rag-analysis)

1. Today their repo has `.slice-system → /abs/path/to/cairn` (per `README.md:25-26`); their `.claude/settings.json` carries the same three hook entries referencing `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`.
2. Resolutions through symlink: `.slice-system/.claude/skills/cairn-tdd-feature/SKILL.md`, `.slice-system/.claude/agents/phase-*-tdd.md`, `.slice-system/commands/claude-code/*.md`, `.slice-system/checks/*.sh`, `.slice-system/checks/role_guard.py`, `.slice-system/scripts/_root.py`, `.slice-system/templates/handoff.md`. The `.slice-system → .` self-loop means each is also reachable as `.slice-system/.slice-system/...` — `project_root()` deliberately avoids `__file__`-anchored lookups for this reason (`docs/operational-reference.md:286-292`, "L-017").
3. Their own `.claude/` carries: `handoff.md`, `active-envelope.yaml`, `skill-runs/<feature-id>/` (in-flight Phase artifacts), `learning.md`, plus plan docs at `docs/plans/`. Consumer-local state, not symlinked from cairn.
4. Migration sequence: pause in-flight `cairn-tdd-feature` dispatch; phase verification (`SKILL.md:60,64,68,71` Steps 5/7/9/11) reads `git show <commit>` and re-dispatches in fresh agent — surviving migration requires the agent registry continuing to expose the same `subagent_type` slugs.
5. Swap: remove `.slice-system` symlink, run `claude plugin install cairn`, edit `.claude/settings.json` to replace `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` with plugin-resolved path. Agent-registry bootstrap (`SKILL.md:24`) means operator MUST start a fresh Claude Code session after the swap.
6. State that must survive migration: `.claude/handoff.md`, `.claude/active-envelope.yaml`, `.claude/skill-runs/*`, `.claude/learning.md`, `.claude/adr-editorial-fixes.log`, all `docs/plans/*`, all `docs/adr/*`, `docs/ARCHITECTURE.md`. State that goes away: the symlink itself; `.slice-system/.claude/agents/*`.
7. Rollback: re-create the `.slice-system` symlink and revert settings.json hooks. Works only if plugin install did not write into `.claude/` paths the consumer also owns.
8. After migration: `.claude/skill-runs/<id>/` artifacts still consumer-side; phase-3 envelope still drives from the plan doc; `.claude/active-envelope.yaml` enforcement still anchored at consumer root.

**Boundaries:**
- Symlink-resolution boundary: tool-input paths via `.slice-system/...` (today), gone post-migration.
- Plugin-cache vs consumer-root boundary: hook scripts and skill markdowns in plugin cache; plan docs / handoff / skill-runs in consumer root.
- Settings.json edit boundary: hook command strings change from `$CLAUDE_PROJECT_DIR/.slice-system/...` to plugin path; one-shot edit must happen *atomically* with symlink removal.
- Agent-registry boundary: five `subagent_type` slugs must still be discoverable post-migration.
- Session boundary: existing session's loaded agent registry references old `.slice-system/.claude/agents/...` source; fresh session must be started after migration.

**Failure modes:** in-flight `.claude/skill-runs/<id>/intent.md` orphaned if Phase 2 cannot find agent definition under new path; `uv run python role_guard.py` fails if plugin-cache copy isn't part of consumer's uv project; if operator forgot to `unlink .slice-system` then BOTH old script and new plugin script fire on same tool call.

## Role 3 — Cairn maintainer (today, dogfooding)

1. Cairn consumes itself via `.slice-system → .` (self-symlink); its `.claude/settings.json:27,36,47` references hooks via `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` — maintainer is, today, indistinguishable from a consumer that happens to have the symlink point at the same directory.
2. Maintainer session loads agents from `.claude/agents/*.md` (canonical), invokes skill from `.claude/skills/cairn-tdd-feature/SKILL.md` (canonical), runs hooks resolved through symlink, writes plan docs to `docs/plans/` and skill-runs to `.claude/skill-runs/`.
3. Hooks register at cairn-repo root. Symlink-stripping in `reversibility-guard.sh:48,76` is the safety mechanism that lets a path written as `.slice-system/checks/foo.sh` get checked as `checks/foo.sh`. `role_guard.py` does not strip — `CLAUDE.md:11` rule "edit canonical paths only" exists exactly because maintainer would otherwise hit a deny when editing through symlinked tool-input path.
4. **Post-M5 question**: does cairn-the-repo install cairn-the-plugin into its own `.claude/`? Two paths exist (this trace must enumerate, not pick):
   - **Path A**: drop the self-symlink, install via plugin like any consumer. Boundary: bootstrap circularity — modifying `checks/role_guard.py` requires editing the canonical source while the *running* hook is the plugin-cached copy. Re-publish + reinstall + restart-session per iteration on the hook itself.
   - **Path B**: cairn-the-repo keeps the self-symlink (or moral equivalent in-repo registration); only consumers use plugin. Boundary: cairn's settings.json continues `.slice-system/checks/...` while consumers use `${CLAUDE_PLUGIN_ROOT}/...`; hook scripts' path-stripping must support both anchorings simultaneously.

**Boundaries:**
- Self-consumption boundary: cairn-the-repo's hooks point at scripts under `.slice-system/...` (today); post-M5 may point at canonical `checks/...`, plugin cache, or stay symlinked.
- Plugin payload boundary: `commands/claude-code/.local/`, `.claude/skill-runs/`, `tests/`, `docs/plans/`, `docs/reviews/` should NOT ship; `commands/claude-code/{catchup,decision,decision.full,new-adr,new-adr.full}.md`, `.claude/skills/cairn-tdd-feature/`, `.claude/agents/{phase-{1..4}-tdd,triager-tdd}.md`+`role-topology.yaml`, `checks/{reversibility-guard.sh,reality-check.sh,role_guard.py}`, `scripts/_root.py`+`scripts/lib/`, `templates/handoff.md` should ship.
- Hook self-edit boundary: editing `checks/role_guard.py` mid-session changes the file but the loaded hook updates next call (Python is invoked fresh per call); editing `reversibility-guard.sh` likewise (bash-fork-per-call); `.claude/settings.json` edits use new settings without session restart.
- Versioning boundary: maintainer is editing the *next* version of cairn while running the *current* version of cairn — every change to a hook/skill/agent is potentially observable in the same session.

**Failure modes:** maintainer drops self-symlink without updating settings.json → hooks 404 next tool call → enforcement silently disabled until session restart; plugin install overwrites canonical `.claude/agents/*.md` with plugin-cached copies → maintainer's edits-in-progress get clobbered; plugin payload wrongly includes `.local/` dev aids → consumers see `/dev-mode` they were never meant to invoke; Path-A circularity hits when in-progress edit to `role_guard.py` is gated by previous-version `role_guard.py` from plugin cache.

## Cross-role boundaries (must-cover for any candidate solution)

- **Hook-script delivery + invocation path** (all three roles): three `checks/*.sh|*.py` scripts must resolve to runnable absolute path from `$CLAUDE_PROJECT_DIR`; `.claude/settings.json` hook entries must reference whatever path scheme. Today: `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`.
- **Agent-registry resolution** (all three roles): `.claude/agents/{phase-{1..4}-tdd,triager-tdd}.md` and `role-topology.yaml` must be discoverable as `subagent_type` at session start.
- **Slash-command discovery** (all three roles): `commands/claude-code/{catchup,decision,decision.full,new-adr,new-adr.full}.md`.
- **Skill discovery** (all three roles): `.claude/skills/cairn-tdd-feature/SKILL.md` invokable via Skill tool.
- **Python-runtime boundary** (Roles 1+2+3): `role_guard.py` invoked as `uv run python <path>` — every consumer needs uv project at `$CLAUDE_PROJECT_DIR` or alternate Python runtime contract.
- **System-dep contract** (all three roles): `jq` (all hooks) and `ruff` (`reality-check.sh`) on PATH; today `brew install` instruction in `CLAUDE.md:13-15` with no install-time check.
- **Consumer-owned `.claude/` state** (Roles 1+2): `handoff.md`, `active-envelope.yaml`, `skill-runs/<id>/`, `learning.md`, `adr-editorial-fixes.log` written into consumer root and must not be clobbered or owned by plugin.
- **Plan-doc + envelope contract** (Roles 1+2): `docs/plans/<id>.md` frontmatter (`id:`+`envelope:`) is the consumer-supplied input feeding `AGENT_ENVELOPE` to Phase 3; plugin neither owns nor templates this today (Finding 3).
- **Identifier-scheme contract** (all three roles): `id:` vs `name:` rule (`CLAUDE.md:5-7`) authoritative across consumer files.
- **Settings.json hook-string boundary** (Roles 1+2+3): three hook commands inside `.claude/settings.json:27,36,47` are versioned-string contracts — any path-scheme change is coordinated edit across cairn's own settings.json AND every consumer's settings.json.
- **Symlink-stripping logic** (Roles 2+3): `reversibility-guard.sh:48,76` and *absence* in `role_guard.py` — plugin-install path either keeps both behaviors viable or explicitly retires the symlink-stripping branch and updates `CLAUDE.md:11`.
- **Cairn self-consumption circularity** (Role 3, sometimes 2): editing cairn's own hooks while cairn's hooks gate the edits — gate's source-of-truth path must be specified.
- **Versioning + pinning boundary** (Roles 1+2): consumers need a way to pin a cairn version; `README.md:33` says "post-v1, the symlink converts to a git submodule pinned at a tagged version" — plugin install replaces this commitment, so pin-mechanism is a boundary.
