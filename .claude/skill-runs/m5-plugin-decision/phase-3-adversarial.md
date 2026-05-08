# Phase 3 — Adversarial stress-test of A-prime

Plain subagent. Stress-tests `phase-2-convergence-note.md`. Evidence: file:line citations and live `WebFetch` of `code.claude.com/docs/en/{plugins,plugins-reference,plugin-marketplaces,discover-plugins}` (2026-05-08).

## Disconfirming search

### D1 — "Curated payload" is not a manifest field

Convergence picks "curated payload, not full-minus-internals" because B's allow-list "makes the leak structurally impossible" (`phase-2-convergence-note.md:11`). Disconfirming: the plugin manifest schema (`code.claude.com/docs/en/plugins-reference` "Component path fields") supports `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`, `experimental.{themes,monitors}` — **no `include:`/`exclude:` glob field for arbitrary repo files**.

What this means concretely: a "plugin" is the directory tree the plugin lives in. Component-path fields tell Claude Code where to find *components*; they do NOT restrict what gets cloned. Claude Code "copies the plugin directory to a cache" (`code.claude.com/docs/en/plugin-marketplaces` "How plugins are installed"). So the cache contains every file the maintainer pushed. A consumer agent's `find`/`Glob` could still surface `.local/` files in the plugin cache.

Curation in cairn's case requires *physical* separation: either a `cairn-plugin/` subdirectory with `.claude-plugin/plugin.json` consumed via a `git-subdir` source, or a separate plugin-only repo/branch. Doable, but the convergence does not name this commitment. The "structural impossibility of `.local/` leakage" claim degrades to "Claude Code only invokes components from named dirs" — behaviour-by-default, not structural.

### D2 — `claude plugin install <git-url>@<tag>` does NOT exist

`phase-0-constraints.md:11` and `phase-2-approach-A.md:19` both assume this UX. The live docs (`code.claude.com/docs/en/discover-plugins` "Install plugins") show **no such syntax**. Plugins install via marketplaces only: `/plugin install <plugin-name>@<marketplace-name>` or `claude plugin install <plugin-name>@<marketplace-name> --scope <scope>`. There is **no** `claude plugin install git+https://...@sha` form.

Pinning lives in the marketplace's `marketplace.json` plugin-source: `source.ref` (branch/tag) or `source.sha` (full 40-char commit) — `code.claude.com/docs/en/plugin-marketplaces` "Plugin entries → Source types".

**Implication:** the convergence's "git-URL plugin install, consumers pin SHAs" UX (`phase-2-convergence-note.md:7`) requires cairn to ship a `marketplace.json` *alongside* `plugin.json`. Cairn becomes (a) a marketplace publishing one plugin, and (b) the plugin itself. Documented and supported, but Phase 0 and the convergence both elide it.

### D3 — `role_guard.py:28` `__file__`-anchor IS broken under plugin invocation (verified)

`checks/role_guard.py:28-29`:
```
CAIRN_ROOT = Path(__file__).resolve().parent.parent
OPERATOR_ENVELOPE_PATH = CAIRN_ROOT / ".claude" / "active-envelope.yaml"
```

When the script lives at `~/.claude/plugins/cache/<hash>/cairn/checks/role_guard.py`, `CAIRN_ROOT` resolves to `~/.claude/plugins/cache/<hash>/cairn/` and `OPERATOR_ENVELOPE_PATH` to a path that does not exist in the consumer repo. `_load_operator_envelope()` returns `None` (line 88-89), no-envelope happy path is taken (line 150-151), operator-session writes pass unchecked. Pre-mortem Scenario 1 is **mechanically real**.

Side-effect the convergence misses: `_log_grant()` (line 121) uses the same `CAIRN_ROOT` to write `envelope-grants.log`. Under plugin cache, grant logs disappear on plugin update — the audit trail silently vanishes. The fix must update both call sites.

### D4 — `cairn-tdd-feature` SKILL.md does NOT depend on deferred slash-commands

Read end-to-end. Skill dispatches via Agent tool with `subagent_type: phase-{1..4}-tdd`/`triager-tdd` (SKILL.md:56,62,66,70,76). It does NOT invoke `/catchup`, `/handoff`, `/decision`, or `/new-adr`. **Confirms** the convergence's "slash-commands deferred to M5.1" decision does not break the TDD skill.

### D5 — Constraint #14 framing is stale

Constraint #14 (Phase 0:31) says "Plugin install must reproduce this hook registration shape … in the consumer's `.claude/settings.json`." Disconfirmed: plugin hooks live in `<plugin-root>/hooks/hooks.json` (or inline in `plugin.json`); they are **not** merged into the consumer's settings.json. Claude Code loads them from the plugin cache when the plugin is enabled (`code.claude.com/docs/en/plugins-reference` "Hooks → Location"). Hook commands use `${CLAUDE_PLUGIN_ROOT}/...` substitution.

This is **good news for A-prime** — Pre-mortem Scenario 2 (settings-merge drift) is structurally less acute than the convergence's Assumption #3 implies. But it also means the convergence's "stable shim entry point" defense (`phase-2-approach-A.md:26`) is unnecessary friction — there is no consumer-visible settings.json hook string to drift. **Convergence overdesigns this defense.**

### D6 — Other constraints intact

`docs/ARCHITECTURE.md:42,118` (#25 phase-lock), `CLAUDE.md:5-7` (identifier scheme), `checks/role_guard.py:28-29` (#15), `checks/role_guard.py:90-92` (#12 lazy yaml import) all match Phase 0 verbatim. No internal inconsistencies in the 27-constraint set found.

## Assumption audit

| # | Status | Evidence |
|---|---|---|
| 1 | **REFUTED (as stated)** | Plugin manifest has no `include:`/`exclude:` patterns. Curation needs repo separation or `git-subdir` source. Convergence must restate the mechanism. (D1) |
| 2 | **REFUTED (as stated)** | `claude plugin install <git-url>@<sha>` does not exist. Pinning lives in `marketplace.json` `source.sha`/`source.ref`. Cairn must ship marketplace.json alongside plugin.json. (D2) |
| 3 | **REFUTED (gracefully)** | Hooks register from `<plugin-root>/hooks/hooks.json`, NOT merged into consumer settings.json. Validates the *concern*, disconfirms the *mechanism*. A-prime is *easier* than assumed. (D5) |
| 4 | **VERIFIED MUST-FIX** | `__file__`-anchor breakage confirmed at `checks/role_guard.py:28-29`. Replacement with `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))` is mechanically sound (stdlib only, no new dep). Also fix `_log_grant()` at line 121. (D3) |
| 5 | **BELIEVED** | Path B (cairn keeps self-symlink) is the convergence's stated choice; nothing in the docs disconfirms it but I did not test end-to-end. To close: dogfood by editing `role_guard.py` while maintainer hooks reference the canonical checkout, verify next tool call uses the new code. |
| 6 | **BELIEVED** | No quiescence requirement in current SKILL.md. Skill-run state lives entirely in `.claude/skill-runs/<id>/` (consumer-owned). Single-atomic-commit migration is plausible but session-restart is non-negotiable (`SKILL.md:26`, `phase-0.5-journey.md:33`). To close: write the migration script and dry-run it against a fixture skill-run. |
| 7 | **MOOT under actual schema** | `.claude/settings.json:7` sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. No hits on `teammateMode` anywhere in cairn. Plugin-shipped `settings.json` only supports `agent` and `subagentStatusLine` keys (`code.claude.com/docs/en/plugins` "Ship default settings"). The plugin **cannot** ship `teammateMode`/`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` even if it tried. To close: CI test asserting plugin payload's `settings.json` (if present) contains only allowed keys. |

**Summary.** Three of seven (#1, #2, #3) are REFUTED-AS-STATED — convergence's *direction* is right, but its *mechanism* names features the plugin system doesn't have. One (#4) is VERIFIED MUST-FIX. One (#7) is moot. Two (#5, #6) need dogfood validation. **No assumption is fatal.**

## Runner-up steel-man

Convergence rejects B's audience-tagged-single-CLAUDE.md citing "drift risk as sections evolve" (`phase-2-convergence-note.md:15`). The portfolio reviewer's literal text (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:66`):

> "split `CLAUDE.md` into two files, **or** add an explicit 'Audience' block at top distinguishing `cairn-maintainer` rules from `cairn-consumer` rules. At minimum the `.slice-system/` stripping caveat … should be tagged as maintainer-only."

The reviewer offered a disjunction with an "at minimum" floor for tagging. Approach B's framing that tagging is "the reviewer's literal suggestion" (`phase-2-approach-B.md:43,75-77`) is half-right — tagging is one of two endorsed options.

**For tagging.** (1) **One canonical location per rule** — a rule like `CLAUDE.md:11` cannot exist in two files at once. File-split's risk: rule lives only in CLAUDE.md, consumer doesn't see it; or it's duplicated in CONSUMER.md and the copies drift. (2) **Discoverability** — a consumer who lands on CLAUDE.md first doesn't bounce; they skip `[maintainer]` blocks. File-split requires the README reading-order fix to land *first*; constraint #22 (README reading order) is currently SOFT/unfixed. (3) **The "at minimum" floor still applies under file-split** — CONSUMER.md inevitably needs to reference maintainer concepts, so tagging discipline pays for itself either way.

**For file-split (convergence's choice).** (1) **Bisection at glance** — read CONSUMER.md, ignore CLAUDE.md, no mental filtering. (2) **Tooling-friendly** — `grep <thing> CONSUMER.md` is trivial; `grep '\[consumer\]' CLAUDE.md` is fragile to tag-syntax drift. (3) **Lower cognitive surface for first-time consumers** — no tag vocabulary to learn.

**Verdict: medium-strong, not strong enough to overturn.** Tagging wins on drift-resistance and reviewer's-actual-words. File-split wins on consumer cognitive surface. The convergence's stated objection ("drift risk as sections evolve") is *partly inverted*: tagging actually has *lower* drift risk because there's one source. The real argument for file-split is consumer onboarding, not drift.

**Recommendation: keep file split, but apply audience tags in CLAUDE.md for cross-cutting rules** per the reviewer's "at minimum" floor. Identifier scheme (`CLAUDE.md:5-7`) applies to both audiences — tag, don't duplicate. CONSUMER.md remains the onboarding surface; tagged CLAUDE.md is maintainer + cross-cutting. Costs almost nothing; answers the reviewer's exact suggestion.

## Verdict

passes with these caveats: (1) restate Assumption #1's curated-payload mechanism — no manifest `include`/`exclude`; curation needs a separate plugin root via subdir or repo (D1); (2) restate Assumption #2's pin UX — `claude plugin install <git-url>@<sha>` does not exist; pinning lives in `marketplace.json` `source.sha`/`source.ref`, cairn ships marketplace.json alongside plugin.json (D2); (3) drop the "stable shim entry point" defense for Pre-mortem Scenario 2 — plugin hooks register from `<plugin-root>/hooks/hooks.json`, no consumer settings-string to drift (D5); (4) confirm Assumption #4's `__file__`→`CLAUDE_PROJECT_DIR` rewrite as MUST-FIX, and extend the fix to `_log_grant()` at `role_guard.py:121` (D3); (5) keep file split for CLAUDE.md/CONSUMER.md but apply audience tags in CLAUDE.md for cross-cutting rules per the reviewer's "at minimum" floor. None of these is fatal; all are mechanism-restatements or scope-additions, not direction changes. A-prime survives.
