# Phase 2 — Approach A (steel-man)

**Approach A.** Cairn ships as a Claude Code plugin via **git-URL install** (`claude plugin install <git-url>`), pre-v1, consumers pin SHAs and accept drift. Payload is **full-repo-minus-internals** (excludes `tests/`, `docs/adr/`, `docs/plans/`, `commands/claude-code/.local/`). `CLAUDE.md` stays maintainer-only; new `CONSUMER.md` is the consumer entry doc. **M5+M6 ship together**; the symlink retires in the same milestone. **Post-install hook validates** `jq`/`ruff` and the operator-envelope round-trip. **Comprehensive template extraction** — every phase-boundary contract gets a worked example.

Author: Phase-2 teammate, plain subagent (no team-spawn affordance available; this file stands as the deliverable).

---

## 1. Boundary coverage

For each cross-role boundary in `phase-0.5-journey.md:64-78`, the specific Approach-A handling. Grouped by category.

### Distribution mechanics

- **Hook-script delivery + invocation path** (`phase-0.5-journey.md:66`). Plugin manifest places `checks/reversibility-guard.sh`, `checks/reality-check.sh`, `checks/role_guard.py` under `${CLAUDE_PLUGIN_ROOT}/checks/`. CONSUMER.md install instructions show consumers the merged `.claude/settings.json` snippet (matcher + command strings). The settings.json hook commands swap `$CLAUDE_PROJECT_DIR/.slice-system/checks/...` for `${CLAUDE_PLUGIN_ROOT}/checks/...` (constraint #14, `.claude/settings.json:30,39,50`). One template (`templates/settings.hooks.json`) ships the canonical merge shape.
- **Agent-registry resolution** (`phase-0.5-journey.md:67`). Plugin payload includes `.claude/agents/{phase-{1..4}-tdd,triager-tdd}.md` and `role-topology.yaml`; Claude Code resolves them at session start from the plugin cache. The "full-payload-minus-internals" choice is what makes this trivial — we don't curate, we ship the whole `.claude/agents/` directory.
- **Slash-command discovery** (`phase-0.5-journey.md:68`). `commands/claude-code/{catchup,decision,decision.full,new-adr,new-adr.full}.md` ship via the plugin payload. The `.local/` exclusion (constraint #24) is enforced by an explicit deny-list in the build manifest plus a CI test that asserts `.local/` paths are absent from the tarball — direct response to pre-mortem Scenario 5.
- **Skill discovery** (`phase-0.5-journey.md:69`). `.claude/skills/cairn-tdd-feature/SKILL.md` ships in the plugin; Claude Code's Skill tool finds it the same way it finds `superpowers:*` skills today (settings.json `enabledPlugins`, `.claude/settings.json:2`).
- **Versioning + pinning boundary** (`phase-0.5-journey.md:78`). Pre-v1 SHA-pin is the explicit policy (Brainstorm decision #3). Consumers run `claude plugin install <git-url>@<sha>`; cairn maintains a CHANGELOG with breaking-change callouts per SHA. The README's "post-v1, the symlink converts to a git submodule pinned at a tagged version" promise is replaced cleanly: SHA-pin pre-v1, semver-tag post-v1. No middle ground.

### Consumer state and contracts

- **Consumer-owned `.claude/` state** (`phase-0.5-journey.md:72`). `handoff.md`, `active-envelope.yaml`, `skill-runs/<id>/`, `learning.md`, `adr-editorial-fixes.log` live in the consumer repo, untouched by plugin install. Approach A's full-payload-minus-internals never writes into consumer-owned `.claude/` runtime state — only the plugin cache. CONSUMER.md documents this boundary explicitly (which files are consumer-owned vs plugin-supplied) so the rollback path (`phase-0.5-journey.md:35`) stays viable.
- **Plan-doc + envelope contract** (`phase-0.5-journey.md:73`). The "comprehensive templates" decision (Brainstorm #6) lands `templates/plan.md`, `templates/intent.md`, `templates/active-envelope.yaml`, `templates/adr.md`, plus Phase-2 RED-test scaffold and Phase-4 audit shape. Each ships with a *worked example* (pre-mortem Scenario 4 defense), not just blank frontmatter — closes Finding 3 from the portfolio review (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:82-85`).
- **Identifier-scheme contract** (`phase-0.5-journey.md:74`). The `id:`/`name:` rule (`CLAUDE.md:5-7`) is documented in CONSUMER.md as a consumer-facing rule (today it sits in maintainer CLAUDE.md and the audience is ambiguous — Finding 1, `docs/reviews/2026-04-23-from-portfolio-evaluation.md:60-66`). Templates carry the `id:` scheme baked in.
- **Settings.json hook-string boundary** (`phase-0.5-journey.md:75`). Versioned-string contract is acknowledged. CONSUMER.md ships the canonical hook-merge snippet; `claude plugin install` performs first-install merge. Approach A pairs this with **a stable shim entry point** to absorb pre-mortem Scenario 2's drift: hook commands reference `${CLAUDE_PLUGIN_ROOT}/cairn-hook <name>` (single stable string per consumer), and internal restructuring within the plugin doesn't change settings.json strings. Pre-v1 SHA drift remains *behavioural* not *enforcement-disabled*.

### Runtime and deps

- **Python-runtime boundary** (`phase-0.5-journey.md:70`). `role_guard.py` continues to run via `uv run python` from the consumer's project root. CONSUMER.md prerequisites add `uv` to the install checklist next to `jq`/`ruff`. The lazy-yaml import (`checks/role_guard.py:90-92`) preserves the stdlib-only happy path so consumers without pyyaml don't hit ImportError on every Write call (constraint #12 HARD).
- **System-dep contract** (`phase-0.5-journey.md:71`). The post-install hook (Brainstorm decision #8) is the affirmative answer: `claude plugin install <cairn>` runs a validator that probes `jq -V`, `ruff --version`, and `uv --version`, prints a structured report, and warns loudly on missing deps. Critically — **the validator also exercises envelope enforcement positively** (write a tmp `active-envelope.yaml`, attempt a denied write, assert exit 1, clean up). This is the Scenario-1 defense: catches the silent-no-op failure mode CLAUDE.md:13-16 already calls out, but at install time rather than runtime-after-damage.

### Stability and migration

- **Symlink-stripping logic** (`phase-0.5-journey.md:76`). Approach A retires the `.slice-system` prefix entirely (Brainstorm decision #7). `reversibility-guard.sh:48,76` symlink-stripping branch is removed in M5; CLAUDE.md:11's "edit canonical paths only" rule becomes obsolete and is deleted. One scheme, one path discipline.
- **Cairn self-consumption circularity** (`phase-0.5-journey.md:77`). Approach A defaults to **Path B** (cairn-the-repo keeps an in-repo registration; only consumers use plugin) for M5 — explicitly resolves the open question at `brainstorm-decisions.md:25` rather than punting. Rationale: pre-mortem Scenario 3 (severity: blocks ship). The maintainer continues to invoke hooks against canonical `checks/...` (no symlink — the `.slice-system → .` self-loop retires) via a thin in-repo registration mechanism (e.g., a top-level `.claude/settings.json` referencing `checks/...` directly without `$CLAUDE_PROJECT_DIR/.slice-system/` prefix). Plugin consumers go through `${CLAUDE_PLUGIN_ROOT}/`. The hook scripts must accept either anchor — handled by `role_guard.py` switching from `__file__`-anchored to `$CLAUDE_PROJECT_DIR`-anchored CAIRN_ROOT (pre-mortem Scenario 1 defense; `checks/role_guard.py:28`).

---

## 2. Pre-mortem responses

| Scenario | Approach A defense |
|---|---|
| **1 — Silent envelope bypass** (blocks ship) | Replace `__file__`-anchored `CAIRN_ROOT` (`checks/role_guard.py:28`) with `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))`. Post-install validator includes a positive enforcement round-trip (write tmp envelope, attempt denied write, assert exit 1). Unit test under `tests/unit/` runs `role_guard.py` from a `/tmp` copy and asserts it still finds the consumer envelope. Three-layer defense — exactly what the pre-mortem prescribed. |
| **2 — Settings-merge drift** (ongoing pain) | Stable shim entry point `${CLAUDE_PLUGIN_ROOT}/cairn-hook <name>`; one settings.json string per hook regardless of internal restructuring. F3 ships a `cairn doctor` command that diffs consumer hook entries against the manifest. CI smoke test installs v_n over v_{n-1} and asserts single-hook registration. |
| **3 — Self-consumption circularity** (blocks ship) | Approach A explicitly picks **Path B** for M5 (cairn maintainer keeps in-repo registration, not plugin-installs-self). Rationale documented in the M5 design doc and a co-landed ADR per constraint #18. Pre-commit hook exercises hook scripts against the *staged* tree, surfacing regressions before publish. Bootstrap-exception applicability (constraint #27) is documented for the M5 self-consumption transition. |
| **4 — Audience confusion despite CONSUMER.md split** (ongoing pain) | F2 deliverable explicitly includes README reading-order rewrite (constraint #22; portfolio review `:68-79` is the spec). Templates ship *worked examples*. CONSUMER.md elevates the "minimum-viable-cairn" graduated-adoption path (constraint #9) — try the hooks first, adopt the skill later. The split is *not* a literal bisection of the existing docs; it's a re-targeting. |
| **5 — `.local/` payload leakage** (blocks ship) | Build manifest carries an explicit deny-list (`commands/claude-code/.local/**`, `tests/**`, `docs/adr/**`, `docs/plans/**`, `docs/reviews/**`, `.claude/skill-runs/**`). CI test builds the tarball and asserts none of those paths appear and consumer-facing paths all do. The `.local/` convention is elevated from folklore (constraint #24) to a documented exclusion rule in `docs/ARCHITECTURE.md`. |
| **6 — Migration-orphan in flight** (ongoing pain) | F3 ships a `cairn migrate --dry-run` that refuses to proceed if `.claude/skill-runs/` contains any feature directory not at Phase-4-complete state. CONSUMER.md migration section says "finish or abandon, then migrate" — no live-migration claim. Post-install validator re-dispatches a known-good fixture skill-run end-to-end. |

**No scenario is left unaddressed.** The two ongoing-pain scenarios (2, 6) admit residual risk: SHA-pin drift may still bite consumers who upgrade infrequently, and a determined consumer could still attempt mid-feature migration despite the dry-run gate. Both are surfaceable, not silent — Approach A's overall posture.

---

## 3. Why this beats the alternatives

Three axes where Approach A is structurally superior:

**(a) Honors the agent-portable substrate vision (constraint #26 HARD; `docs/operational-reference.md:409`).** Git-URL install is runtime-agnostic by construction — any agent harness that can `git clone` and parse a manifest can adopt cairn. A marketplace-first approach (rejected) couples cairn's distribution to one vendor's plugin registry, foreclosing Windsurf as a second runtime (constraint #4 SOFT, `docs/plans/2026-05-06-cairn-shrink-design.md:125,160,294`). Approach A's git-URL channel keeps `.claude/skills/` portable for free; the manifest is a thin plugin-only adaptor.

**(b) Honors the pre-v1 stability stance (constraint #7 SOFT; `docs/reviews/2026-04-23-from-portfolio-evaluation.md:32,52,111`).** The portfolio evaluator explicitly rejected symlink-adoption citing "coupling a consumer's tooling to a moving upstream creates drift risk." SHA-pin (Brainstorm decision #3) is the consumer-controlled answer: consumers choose when to absorb upstream churn. A v1-first or tag-only approach would force cairn to freeze its six open amendment ADRs prematurely; SHA-pin lets cairn iterate without breaking pinned consumers.

**(c) Honors M5+M6 atomicity (constraint #21 SOFT, brainstorm-confirmed).** Combining M5+M6 with symlink retirement in the same milestone gives one cutover event, one CHANGELOG entry, one migration doc. Splitting them (rejected) would force the maintainer to maintain dual-mode hook-path resolution (`$CLAUDE_PROJECT_DIR/.slice-system/...` AND `${CLAUDE_PLUGIN_ROOT}/...`) for an indefinite intermediate period — a permanent tax on hook-script edits and a new failure surface (`phase-0.5-journey.md:54` Path B-like state, but worse: not a maintainer choice, a forced transition mode).

---

## 4. Honest weaknesses

**(a) Pre-v1 SHA-pin is a hack, not a feature.** SHA-pin works because `claude plugin install <git-url>@<sha>` is an immutable reference, but consumer UX is poor: there's no `cairn upgrade` discoverability, no security advisories channel, no semver signal. Consumers who don't follow cairn's CHANGELOG will discover breakage by hook-deny. **Concession:** this is genuinely worse than a marketplace + semver tag combo for consumer UX. **Defense:** it's the price of pre-v1 honesty (constraint #7); a marketplace listing pre-v1 advertises stability we don't have.

**(b) Full-payload-minus-internals over-ships.** The `.local/` deny-list (Scenario 5 defense) is a static exclusion; new internals added by maintainers default to *shipped* unless someone remembers to update the deny-list. An allow-list-first approach (rejected) would be safer per-leak but more brittle to consumer-facing additions. **Concession:** Approach A trades safety-against-leak for velocity-of-consumer-feature-shipping. The CI gate is the mitigation, not the elimination.

**(c) Path B for self-consumption is the conservative choice, not the elegant one.** A plugin-installs-self design (Path A) would dogfood the consumer experience natively — every maintainer iteration would be a real installation. Path B preserves a maintainer/consumer asymmetry that cairn's vision (`docs/why-cairn.md:107-108` "meta-dogfoodable from feature #1") would prefer to eliminate. **Concession:** Approach A defers Path A to a future milestone; the M5 design doc must call this out so it doesn't become folklore.

---

## Synthesis

Approach A is **strongest** on vision-fit (agent-portable substrate, pre-v1 honesty, M5+M6 atomicity) and pre-mortem coverage — every blocking scenario has a named, layered defense. It is **weakest** on consumer UX (SHA-pin discoverability), payload-leak resilience (deny-list is one CI-gate away from regression), and dogfooding fidelity (Path B preserves a maintainer/consumer asymmetry the vision would rather collapse). **One specific test that would falsify Approach A:** if dogfooding the post-install validator reveals that the envelope round-trip cannot be exercised positively without writing into consumer-owned `.claude/` paths (i.e., the validator can't be both safe and informative), the silent-no-op failure mode (Scenario 1) is structurally unaddressable at install time and a different distribution shape — likely a packaged single-binary entry point with embedded enforcement self-test — becomes preferable.
