# Phase 5 — Independent Verification

**Verifier:** fresh agent, blinded to lead/Phase-2-teammate outputs.
**Inputs read:** `phase-0-constraints.md`, `phase-0.5-journey.md`, `brainstorm-decisions.md`, plus spot-reads of `.claude/settings.json`, `checks/role_guard.py`, repo `ls`, and WebFetches of `code.claude.com/docs/en/plugins`, `/plugins-reference`, `/plugin-marketplaces`.
**Files NOT read:** `phase-1-pre-mortem.md`, `phase-2-approach-{A,B,C}.md`, `phase-2-convergence-note.md`, `phase-3-adversarial.md`, `phase-3-corrections-applied.md`. Confirmed by directory listing only — none opened.

## My top-3 failure scenarios

### 1. The marketplace-vs-direct-install UX gap (severity: HIGH)

The brainstorm-decisions table assumes consumers run `claude plugin install <git-url>` (a direct git-URL install). The actual Claude Code mechanism is two-step: users `/plugin marketplace add <git-url>` then `/plugin install cairn@<marketplace-name>` (`plugin-marketplaces` doc lines around marketplace add + install). If we ship cairn as a plugin without a `.claude-plugin/marketplace.json` describing it, consumers literally cannot install it from a git URL — they'll get "marketplace not found." Failure mode: M5 lands, `claude plugin install <our-git-url>` fails, complex-rag-analysis migration in M6 stalls because the operator-confirmed UX commitment doesn't match the actual platform contract. Recovery is cheap (add a `marketplace.json` co-located in the repo or a sibling marketplace repo) but only if we catch it pre-ship.

### 2. Hook path resolution + uv-runtime double-binding (severity: HIGH)

`.claude/settings.json:39` invokes `uv run python $CLAUDE_PROJECT_DIR/.slice-system/checks/role_guard.py` — `uv run` resolves the venv at `$CLAUDE_PROJECT_DIR`, but the script lives in plugin cache. Post-plugin, the command must become `uv run --project ${CLAUDE_PLUGIN_ROOT} python ${CLAUDE_PLUGIN_ROOT}/checks/role_guard.py` (or equivalent), AND `role_guard.py:28` resolves `CAIRN_ROOT` via `Path(__file__).resolve().parent.parent` — that now points into the plugin cache, NOT the consumer repo. The script then reads `.claude/active-envelope.yaml` from the plugin cache (always absent), so operator-envelope enforcement silently fails open. Severity is high because the failure mode is *silent enforcement disable*, exactly what `CLAUDE.md:13-15` warns about for missing system deps. Must fix `CAIRN_ROOT` to anchor on `$CLAUDE_PROJECT_DIR` (envvar set by Claude Code), not `__file__`.

### 3. Self-consumption circularity bricks the maintainer (severity: MEDIUM-HIGH)

Phase-0.5 Role-3 enumerates Path A (cairn-installs-itself-as-plugin) vs Path B (cairn keeps `.slice-system → .` self-symlink). Brainstorm-decision #7 says "symlink retired; plugin install becomes the only path" — that pushes us toward Path A. But Path A means: edit `checks/role_guard.py` in canonical repo → the *running* hook is the plugin-cached previous version, which gates the edit using stale logic. Worse, every iteration on a hook requires re-publish + `/plugin update` + session restart. If we ship M5 with Path A enforced and the maintainer hits a hook regression, they cannot fix it without bypassing their own enforcement. Severity is bounded because `bootstrap-exception.md` already provides an escape hatch, but the workflow tax is real.

## My ≥3 viable approaches

### Approach Alpha — Marketplace-paired plugin, full-payload, dual-mode (cairn keeps self-symlink for maintainer)

Ship one git repo containing both `.claude-plugin/marketplace.json` (catalog with one entry) AND the plugin payload at repo root. Consumers `/plugin marketplace add <our-git-url>@<sha>` then `/plugin install cairn@cairn`. Hook commands rewritten to use `${CLAUDE_PLUGIN_ROOT}` substitution. Cairn-the-repo retains `.slice-system → .` self-symlink and existing `$CLAUDE_PROJECT_DIR/.slice-system/...` settings.json — Path B from Role-3. Favored by HARD #14, #15 (path resolution), HARD #25-26 (no single-runtime lock-in), SOFT #4 (Windsurf compat preserved because skill prose ports), and avoids failure scenario #3.

### Approach Beta — Marketplace-paired plugin, full-payload, eat-our-own-dogfood (cairn migrates to plugin-installs-itself)

Same as Alpha but cairn-the-repo deletes `.slice-system` symlink and installs itself as a plugin. Hook scripts MUST move all path resolution to `$CLAUDE_PROJECT_DIR` envvar (no `__file__` anchoring) so a plugin-cached `role_guard.py` can still find consumer's `.claude/active-envelope.yaml`. Forces the bootstrap-circularity tax onto the maintainer. Favored by SOFT #3 (maintainer == consumer maximises dogfooding), HARD #15 (forces the path-resolution fix that Alpha could skip), and the cleanliness argument that two install paths == two test surfaces.

### Approach Gamma — Two-tier split: minimum-viable-cairn plugin + maintainer remains in-repo

Ship a *subset* plugin (skill + 5 agents + 3 hooks + slash commands + handoff template) per portfolio-evaluator's "most-portable atomic pieces" finding (CONTEXT #9). Cairn's full repo (ADRs, plans, dispatch dev aids) stays out of the plugin payload. CONSUMER.md explicitly enumerates the shipped surface; CLAUDE.md stays maintainer-only. Maintainer keeps self-symlink. Favored by HARD #6 (audience-split is a real cliff per portfolio-evaluator), SOFT #7 (one prospective consumer already chose copy-adoption over symlink), CONTEXT #9 (named atomic pieces), and CONTEXT #24 (`.local/` precedent for maintainer-only surfaces).

## My converged pick

**Approach Alpha with Gamma's payload-curation discipline** — i.e., marketplace-paired plugin, payload curated to "full repo minus internals" (matching brainstorm-decision #4), with cairn-the-repo keeping its `.slice-system → .` self-symlink (Path B).

### Distribution mechanism

- Ship a `.claude-plugin/marketplace.json` at the cairn repo root pointing at a single plugin entry whose `source` is the same repo (`source: "."` or `source: { source: "github", repo: "firaaz/cairn" }`). This makes one repo = one marketplace = one plugin, preserving the operator's "git-URL install" intent (brainstorm #2).
- Consumers run `/plugin marketplace add firaaz/cairn` then `/plugin install cairn@cairn`. Pinning is via `sha:` in marketplace source (`plugins-reference:1004-1005`, `plugin-marketplaces` source-spec lines around 282-295). README's "How to consume cairn" block updates to this two-command UX.
- Mechanism evidence: `${CLAUDE_PLUGIN_ROOT}` substitution in hook commands is documented at `plugins-reference:542` ("the absolute path to your plugin's installation directory"). Marketplace source supports both `ref` (branch/tag) and `sha` (40-char commit) per `plugin-marketplaces` source-spec.

### Payload curation (brainstorm #4 + audit pass)

Ships: `.claude/skills/cairn-tdd-feature/`, `.claude/agents/{phase-{1..4}-tdd,triager-tdd}.md` + `role-topology.yaml`, `commands/claude-code/{catchup,decision,decision.full,new-adr,new-adr.full}.md`, `checks/{reversibility-guard.sh,reality-check.sh,role_guard.py}`, `scripts/_root.py` + `scripts/lib/`, `templates/` (expanded per brainstorm #6 — intent.md, plan-doc, ADR frontmatter, active-envelope.yaml templates), `CONSUMER.md`.

Excludes: `tests/`, `docs/plans/`, `docs/adr/` (cairn's own decisions), `docs/reviews/`, `commands/claude-code/.local/`, `.claude/skill-runs/`, `mcp_servers/`, `efficiency_program/`, `.worktrees/`. CONTEXT #24's `.local/` precedent already shows the project knows how to fence maintainer-only surfaces.

### Hook registration

`hooks/hooks.json` at plugin root mirrors `.claude/settings.json:23-55` schema (per `plugins.md` migration-steps section: "Copy the `hooks` object from your `.claude/settings.json`"). Three commands rewritten:

- `${CLAUDE_PLUGIN_ROOT}/checks/reversibility-guard.sh`
- `uv run --project "$CLAUDE_PROJECT_DIR" python "${CLAUDE_PLUGIN_ROOT}/checks/role_guard.py"` — keeps consumer's venv as the runtime but loads the plugin-cached script
- `${CLAUDE_PLUGIN_ROOT}/checks/reality-check.sh`

**Mechanism unknown I must flag:** I can't verify from the docs whether hooks declared in `hooks/hooks.json` auto-register on plugin enable, or whether consumers must merge a snippet into their `.claude/settings.json`. The migration-steps section implies auto-registration ("Hooks in `hooks/hooks.json`" replaces "Hooks in `settings.json`"), but I'd want to test on a throwaway plugin before committing the M5 design to that. If auto-registration is real, brainstorm #2's UX promise holds; if not, CONSUMER.md must include a settings.json merge step.

**Required code change for path resolution (HARD #12, #15):** `role_guard.py:28` must change from `Path(__file__).resolve().parent.parent` to `Path(os.environ["CLAUDE_PROJECT_DIR"])` (or the existing `scripts/_root.py:project_root()` which deliberately avoids `__file__` anchoring per `operational-reference.md:286-292` "L-017"). This is the single most load-bearing edit in M5 — without it, operator-envelope enforcement reads from plugin cache (always absent) and silently fails open.

### Audience model

Split per brainstorm #5: maintainer `CLAUDE.md` stays maintainer-only and is NOT in the plugin payload. New `CONSUMER.md` ships in the plugin and is the consumer's first-read entrypoint. `README.md` gets a 4-line reading-order block (CONSUMER.md → operational-reference.md → spec-v1.md → architecture) per SOFT #22.

### Migration path (M5 + M6 combined per brainstorm #7)

1. Land M5 plugin payload + marketplace.json + CONSUMER.md + post-install dep-validator hook (a small SessionStart or first-PreToolUse hook that warns on missing `jq`/`ruff`/`uv`, satisfying brainstorm #8) — single ADR supersedes the symlink commitment in `README.md:33` and `docs/why-cairn.md:74`.
2. In complex-rag-analysis (M6 step): pause in-flight skill-runs, `unlink .slice-system`, edit settings.json to remove three hook entries (now auto-registered by plugin), `/plugin marketplace add firaaz/cairn`, `/plugin install cairn@cairn --pin <sha>`, restart session.
3. Cairn-the-repo keeps `.slice-system → .` and its existing settings.json (Path B). The cost is two test surfaces (consumer-via-plugin and maintainer-via-symlink); the benefit is avoiding bootstrap-circularity in the maintainer loop.

### Versioning

Pre-v1 stance (brainstorm #3) → omit `version` from `plugin.json`, let commit-SHA drive (`plugins-reference:1005`). Consumers pin via marketplace `sha:` field. When v1 lands, switch to explicit `version` + semver tags.

## My falsifying test

I'd pick differently if any of the following turn up:

1. **Hooks in `hooks/hooks.json` do NOT auto-register** — they require a consumer-side settings.json merge. Then the UX promise of "one-shot install" collapses, CONSUMER.md balloons, and Approach Gamma (smaller payload, more honest doc burden) becomes more attractive than Alpha.
2. **`${CLAUDE_PLUGIN_ROOT}` is NOT exported as an actual env var inside the hook subprocess** (only substituted in the command-string before exec). Then `role_guard.py` cannot use it for fallback path resolution, and the path-anchoring fix gets harder (must rely solely on `$CLAUDE_PROJECT_DIR`, which is fine for finding the consumer's `.claude/` but not for finding sibling scripts in the plugin payload).
3. **Marketplace-add from a private git URL requires SSH-key plumbing the consumer can't realistically set up** — then "git-URL install" is effectively gated on going public, which contradicts brainstorm #2's "private or public" framing and would push toward making cairn public earlier than the pre-v1 stance comfortably supports.
4. **The `reversibility-guard.sh:48,76` `.slice-system/` prefix-stripping turns out to also fire in plugin-mode tool inputs** (Claude Code passing some path under plugin cache the script doesn't recognise) — then the post-shrink retire-the-stripping commitment in HARD #3 is premature and we need to keep the dual-anchoring branch.

A 30-minute throwaway-plugin smoke test (one trivial skill + one trivial PreToolUse hook, installed from a local git URL via marketplace) would falsify or confirm #1 and #2 cheaply, and I'd run that before locking the M5 design.

---

**Final agent message:** My converged pick is a marketplace-paired single-repo plugin (`.claude-plugin/marketplace.json` co-located with the plugin payload at cairn repo root), full-repo-minus-internals payload curation, hooks declared in `hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}` for script paths, audience-split via new CONSUMER.md, and cairn-the-repo retaining its `.slice-system → .` self-symlink (Path B from Role-3) to avoid bootstrap-circularity in the maintainer loop. The single most load-bearing mechanism claim that the lead's prior synthesis must also have, for our verifications to align, is: **`role_guard.py:28` must stop anchoring `CAIRN_ROOT` on `Path(__file__).resolve().parent.parent` and instead resolve from `$CLAUDE_PROJECT_DIR` (the env var Claude Code sets to the consumer's project root) — without this edit, the operator-envelope file lookup silently fails open in plugin-cache mode, breaking HARD constraint #15 and #17 simultaneously.**
