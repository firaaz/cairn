# Phase 1 — Pre-Mortem

Decision: "How does cairn ship as a consumer-installable methodology, replacing the `.slice-system → .` symlink consumption pattern?"

Author: `pre-mortem` teammate. No team-spawn affordance was available in this session, so this file stands as the deliverable for the lead to read directly.

Frame: imagine M5+M6 has shipped per `brainstorm-decisions.md` (git-URL plugin install, full-repo-minus-internals payload, CONSUMER.md split, comprehensive templates, post-install dep-validator, symlink retired, complex-rag-analysis migrated). It is now somewhere between July and November 2026 and the rollout has visibly failed. Each scenario walks back from the failure to what was missed.

---

## Scenario 1 — Silent enforcement bypass: `role_guard.py` finds no envelope after plugin relocation

**Pre-mortem narrative.** It's August 2026. A consumer reports that an agent freely overwrote files outside the operator envelope; on inspection, `role_guard.py` had been silently allowing every Write for weeks. Walking back: when the plugin install relocated `checks/role_guard.py` into `~/.claude/plugins/<hash>/cairn/checks/`, the script's `CAIRN_ROOT = Path(__file__).resolve().parent.parent` (role_guard.py:28) now resolves to the plugin cache, not `$CLAUDE_PROJECT_DIR`. `OPERATOR_ENVELOPE_PATH` therefore points at a path that never exists in the consumer repo, so `_load_operator_envelope()` returns `None` (the no-envelope happy path) and AGENT_ROLE-unset writes pass unchecked. We missed it because the same script "worked" under the symlink — `__file__` resolved through `.slice-system → .` back into the consumer/cairn root — and no one re-tested envelope enforcement after the path-anchor changed. Constraint #15 (HARD) called this out and the F1 design checked the box on "settings.json hook entries get rewritten" without re-checking the script's own anchor logic.

**Defenses.**
- Replace the `__file__`-anchored constant in `checks/role_guard.py:28` with a CWD-or-env-anchored resolution: `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))`. Add a unit test under `tests/unit/` that runs the script from a copy in `/tmp` and asserts it still finds an envelope at the project root.
- Add a fail-loud diagnostic when `OPERATOR_ENVELOPE_PATH` is computed against a path containing `/plugins/` or that does not contain `.claude/`; print to stderr at minimum.
- Post-install validator (per Brainstorm decision #8) must include a positive assertion: write a temporary `.claude/active-envelope.yaml` with `mode: operator` and a self-only pattern, attempt a denied write, confirm exit 1, then clean up. A green dep-check that doesn't exercise enforcement is theatre.

**Severity: blocks ship.** This is the load-bearing operator-session safety mechanism (constraint #17, HARD); silent failure is exactly the failure mode CLAUDE.md:13-16 already calls out for `jq`/`ruff`. Shipping this would burn cairn's credibility on the one invariant it sells hardest.

---

## Scenario 2 — Settings-merge drift: hook entries diverge across N consumers

**Pre-mortem narrative.** It's October 2026. Cairn has eight or nine consumers; a v0.4 → v0.5 release moves the `role_guard.py` invocation from `uv run python` to a packaged entry point, and three consumers' hooks 404 silently while five work. Walking back: the F1 plugin manifest declares hook registrations, but Claude Code's plugin install merges them into the consumer's existing `.claude/settings.json` only on first install — subsequent upgrades don't touch the file (or worse, re-merge and produce duplicate entries that fire the *old* path on every Write). Consumers had hand-edited their settings to integrate cairn alongside their own hooks, so cairn's release-time string change couldn't be applied automatically without clobbering. We missed it because in dogfooding (Role 3) the maintainer always restarts a fresh session and re-runs install on the cairn repo itself; the cross-consumer-version drift only appears at N≥3 when consumers upgrade asynchronously. Constraint #14 (HARD) and the cross-role "Settings.json hook-string boundary" both flagged this as a versioned-string contract.

**Defenses.**
- Make the hook commands version-stable across cairn releases by introducing a thin shim: ship a single stable entry point (e.g. `${CLAUDE_PLUGIN_ROOT}/cairn-hook reversibility|role-guard|reality-check`) that is *the* hook command in `settings.json`; internal restructuring within the plugin never changes the consumer's settings.json. This isolates the versioned-string contract behind one indirection.
- F3 migration must include a `cairn upgrade` doctor command that diffs the consumer's hook entries against the manifest's expected ones and prints the exact `jq` patch to apply, rather than relying on plugin re-install merge semantics.
- Add a smoke-test in F1 that installs plugin v_n over v_{n-1} in a fixture repo and asserts only one hook of each type registers and points at v_n's path.

**Severity: causes ongoing pain.** Won't block first ship — only manifests as consumer count grows and as cairn iterates pre-v1 (constraint #3 SOFT, "consumers pin SHAs and accept drift"). But "drift" was meant to mean *behavioural* drift, not *enforcement-disabled* drift; this collapses the distinction.

---

## Scenario 3 — Self-consumption circularity: maintainer can't iterate on hooks

**Pre-mortem narrative.** It's July 2026, four weeks after M5+M6 ships. A maintainer needs to fix a bug in `checks/role_guard.py`; the brainstorm picked Path A (cairn-installs-itself), so the *running* hook gating the edit is the plugin-cached copy of the previous version. Each iteration — edit canonical, republish, reinstall, restart session, retry — costs minutes; worse, an in-progress edit that introduces a regression in role_guard.py is gated by the *previous* version, so the regression isn't caught until the next install. Within two weeks the maintainer has either reverted to ad-hoc `.slice-system → .` symlink locally (orphan state, untested in CI) or set `mode: off` on the operator envelope (constraint #17) to escape friction, defeating cairn's own dogfooding invariant (constraint #26 vision commitment #1). We missed it because Phase 0.5 Role 3 explicitly flagged Path A vs Path B as an open question, and the brainstorm decisions list still has it open (`brainstorm-decisions.md:25`); F1 shipped without resolving it.

**Defenses.**
- Resolve the Path A / Path B question *inside* the M5 design doc, not as a follow-up. If Path B (cairn keeps self-symlink): document the dual-mode hook-path resolution in `CLAUDE.md` and add a second test fixture exercising `.slice-system/...` resolution. If Path A: ship a `cairn dev` mode in F1 that points hook commands at the canonical checkout instead of the plugin cache, gated by an env var so prod consumers can't trip it.
- Either way, add a pre-commit/CI check that exercises the hook scripts against the *staged* tree (canonical checkout), independent of plugin install state, so regressions surface before publish.
- Document the bootstrap-exception's applicability (constraint #27) to the M5 self-consumption transition explicitly — folklore won't survive a hostile reviewer.

**Severity: blocks ship.** If the maintainer can't dogfood, vision commitment #1 (constraint #26 HARD) is dead and amendment-velocity for the six open ADRs collapses.

---

## Scenario 4 — Adoption death by audience confusion: CONSUMER.md ships, consumers still bounce

**Pre-mortem narrative.** It's September 2026. Two of the three pilot consumers have stopped using cairn; the third never finished onboarding. Their feedback echoes the portfolio-evaluator review verbatim: docs talk past them, the spec reads like a manifesto, the templates assume context they don't have. Walking back: the F2 split (CONSUMER.md vs maintainer CLAUDE.md) was implemented as a literal bisection — the consumer file describes plugin install and the templates surface, while the *why* lives in `docs/spec-v1.md` (Layer 2) and the *how* of phase mechanics lives in `docs/operational-reference.md` (Layer 3, today maintainer-shaped). README still has no reading order (constraint #22 SOFT, unfixed), and a first-time consumer who reads CONSUMER.md → tries to run the skill → hits a Phase-3 envelope denial has no on-ramp into operational-reference.md to debug it. We missed it because we treated audience-split as a documentation-organisation problem when the portfolio review (constraint #6 HARD, #22 SOFT) had already diagnosed it as a *reading-order* problem.

**Defenses.**
- F2 must rewrite `README.md` with an explicit reading order ("if you are a first-time consumer, read X then Y; if you are evaluating cairn, read Z"), not just add CONSUMER.md alongside the existing surface. The portfolio review (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:68-79`) is the spec.
- Templates (Brainstorm decision #6, "every phase-boundary contract surface") must include *worked examples*, not just blank frontmatter. A consumer who can't fill out `envelope:` correctly hits constraint #12 / role_guard denial and quits.
- Promote the "minimum-viable-cairn" subset (constraint #9 CONTEXT — handoff-as-pointer, three hooks, validator, Phase Skill Guide) into CONSUMER.md as a graduated-adoption path: try the hooks first, adopt the skill later.

**Severity: causes ongoing pain.** Doesn't block ship technically, but every quarter of low adoption is a quarter where cairn's empirical signal (constraint #8) doesn't accumulate, and v1 stabilisation gets pushed.

---

## Scenario 5 — `.local/` leakage in the plugin payload

**Pre-mortem narrative.** It's August 2026. A consumer files an issue: their agent invoked `/dev-mode` (which disables the operator envelope, constraint #17) "to get past a hook deny" because the slash command appeared in their command list. Walking back: the F1 audit pass for "internals vs consumer-facing" (Brainstorm decision #4, plus the open question at `brainstorm-decisions.md:30`) was done by allow-listing top-level paths — `tests/`, `docs/adr/`, `docs/plans/`, `commands/claude-code/.local/` — but the plugin packaging step globbed `commands/claude-code/*.md` rather than excluding `.local/` explicitly, and the `.local/` convention (constraint #24 CONTEXT) is a directory-name pattern, not a manifest field. The release tarball shipped `.local/dev-mode.md` and three other maintainer-only commands. We missed it because the audit checklist was a one-shot pre-ship pass, not an automated test, and no CI gate caught the regression when a maintainer added a new `.local/` command in week three.

**Defenses.**
- F1 ships an explicit deny-list in the plugin manifest (or the equivalent build script): `commands/claude-code/.local/**`, `tests/**`, `docs/adr/**`, `docs/plans/**`, `docs/reviews/**`, `.claude/skill-runs/**`, `efficiency_program/**`. Inverse-allowlist is too brittle for a repo where new internals get added regularly.
- Add a CI test that builds the plugin tarball and asserts none of those paths appear; assert the *consumer-facing* paths (per Phase 0.5 §6 trace) all do.
- The `.local/` convention should be elevated from a directory-name folklore (constraint #24) into a documented exclusion rule in `docs/ARCHITECTURE.md` plus a referenced ADR if not already; otherwise the next maintainer recreates the leak.

**Severity: blocks ship.** Shipping `/dev-mode` to consumers gives them a documented escape hatch from the operator envelope — direct contradiction of constraint #17.

---

## Scenario 6 — Migration-orphan in flight: complex-rag-analysis loses Phase-3 work

**Pre-mortem narrative.** It's July 2026, mid-M6 cutover. The complex-rag-analysis maintainer kicks off the migration mid-feature: a `cairn-tdd-feature` dispatch is in Phase 3 with `.claude/skill-runs/<id>/intent.md` and RED tests committed. They `unlink .slice-system`, `claude plugin install <git-url>@<sha>`, edit settings.json. Next tool call, Phase 3 fails because the agent registry in the live session still references the old `.slice-system/.claude/agents/phase-3-tdd.md`; they restart the session, re-dispatch via `git show`-replay (per Phase 0.5 Role 2 §4), but the replay-dispatch hits a `role_guard.py` deny on the envelope path because the plan-doc `envelope:` regex was authored against canonical paths and the consumer's CWD-resolution shifted slightly post-install. They abandon the in-flight feature and lose ~6 hours. Walking back: F3 documented the migration sequence linearly but didn't gate on "no in-flight skill-run"; constraint #21 (SOFT) folded M6 into M5 without a quiescence check.

**Defenses.**
- F3 ships a pre-migration check (`cairn migrate --dry-run` or similar) that refuses to proceed if `.claude/skill-runs/` contains any feature directory whose `handoff.md` is not at Phase-4-complete state.
- Document an explicit "finish or abandon, then migrate" workflow in CONSUMER.md migration section; do not advertise "live migration" as supported.
- The post-install validator (Brainstorm decision #8) should include re-dispatching a known-good fixture skill-run end-to-end before declaring install successful, catching path-resolution and registry-discovery regressions in one pass.

**Severity: causes ongoing pain.** One-time hit per consumer migrating; survivable but exactly the kind of friction that turns a Role-2 consumer into a former consumer. Not blocking, but the bad first impression is permanent.

---

## Severity tally

- **Blocks ship:** Scenarios 1, 3, 5.
- **Causes ongoing pain:** Scenarios 2, 4, 6.
- **Minor:** none.

The most severe is **Scenario 1** (silent envelope-enforcement bypass): it crosses a HARD constraint (#15), reproduces cairn's own most-criticised failure mode (silent no-op), and is invisible until the consumer audits writes after damage is done. The top defense is replacing `role_guard.py:28`'s `__file__`-anchored `CAIRN_ROOT` with `$CLAUDE_PROJECT_DIR`-anchored resolution and adding a positive end-to-end enforcement test in the post-install validator.
