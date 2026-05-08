# Phase 2 — Convergence Note (lead synthesis)

After reading `phase-2-approach-A.md`, `phase-2-approach-B.md`, `phase-2-approach-C.md`, the lead synthesizes a converged direction. Phase 3 stress-tests it.

## Converged direction: **A-prime**

**Foundation: Approach A** — git-URL plugin install (`claude plugin install <git-url>`), M5+M6 combined, `CLAUDE.md`/`CONSUMER.md` split, comprehensive template extraction, post-install hook validates system deps + warns. Pre-v1; consumers pin SHAs.

**Modifications absorbing Approach B's strongest pillars:**

1. **Curated payload, not "full-minus-internals".** B's curated-payload model beats A's deny-list on Pre-mortem Scenario 5 (`.local/` leakage) — an explicit allow-list makes the leak structurally impossible, while A's deny-list is "one CI-regression away from leaking new `.local/` additions" (A's own conceded weakness). M5 initial payload is methodology core only: `.claude/skills/cairn-tdd-feature/`, `.claude/agents/{phase-{1..4}-tdd, triager-tdd, role-topology.yaml}`, `checks/{reversibility-guard.sh, reality-check.sh, role_guard.py}`, `templates/`. **Slash-commands** (`/catchup`, `/handoff`, `/decision`, `/new-adr`, plus `.full` variants) **deferred to a follow-up payload bump** (call it M5.1 or "command surface"); revisit when the audit confirms what's stable.

2. **Semver-via-tags on top of git-URL pinning.** Consumers can pin a tag (`v0.x.0`) instead of just a SHA. Addresses A's conceded "no discoverability or semver signal" UX weakness without committing to a public marketplace. Pre-v1 status is preserved — major version stays at `0`.

3. **Audience model stays as the file split** (CLAUDE.md maintainer + CONSUMER.md consumer) per brainstorm decision #5, NOT B's audience-tagged-single-CLAUDE.md. Reasoning: file split is unambiguous at glance; audience-tagging adds drift risk as sections evolve. *Phase 3 should specifically stress-test this — B argued tagged-single-file is the reviewer's literal suggestion.*

**Why this beats pure A:** A's payload-leak weakness is fragile by A's own admission. B's curated-payload eliminates it structurally. Marginal cost (slash-commands deferred) is recoverable in M5.1.

**Why this beats pure B:** B's v1-first gate ties M5+M6 to closing 6 open amendment ADRs (`cost-per-slice-budget`, `parallelism-v1`, `phase-pipeline-evaluation`, `feature-slice-model`, `context-tiers-integration`, `identifier-scheme`) — uncertain timeline; blocks complex-rag-analysis migration indefinitely. Pre-v1 SHA-pin + tag-pin is honest about upstream state without blocking ship.

**Why this beats C:** A's pillars hold (vision-fit constraint #26, M5+M6 atomicity #21, complex-rag-analysis migration actually happens). C's risk-avoidance is real but M6-deferred-indefinitely is unacceptable — complex-rag-analysis stays on a deprecated symlink with no end-state.

## Assumptions Phase 3 must audit (verified vs believed)

| # | Assumption | Why load-bearing |
|---|---|---|
| 1 | Plugin manifest format supports a curated allow-list of files (or equivalent: explicit `include:`/`exclude:` patterns). | Without this, A-prime's curated-payload defense degrades to a deny-list (back to A's Scenario 5 risk). |
| 2 | `claude plugin install <git-url>` syntax accepts `@<tag>` or `@<sha>` suffix (or equivalent pin mechanism). | Without this, semver-via-tags has no install-time signal — UX gain disappears. |
| 3 | Plugin install registers hooks automatically into consumer's `.claude/settings.json` (vs requiring consumer to manually merge a snippet). | Determines whether F1's "post-install validator" runs at all — if hooks must be manually registered, the validator is useless until consumer copies the entry, defeating Scenario 1's defense. |
| 4 | `role_guard.py:28` `__file__`-anchored CAIRN_ROOT can be replaced with `Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))` and still work under `uv run python` invocation in both maintainer-self-consumption and plugin-cache contexts. | Pre-mortem Scenario 1's fix; if this doesn't work mechanically, the most severe scenario is unfixed. |
| 5 | Cairn's self-consumption stays on Path B (self-symlink retained for cairn-the-repo). Path A's bootstrap circularity (Scenario 3) is acceptable if and only if it stays isolated to maintainer workflow. | Determines whether maintainer can iterate on hooks; Path A failure blocks every cairn development cycle. |
| 6 | complex-rag-analysis can migrate in a single atomic commit — no skill-run quiescence requirement (Pre-mortem Scenario 6). | If quiescence is required, M6 needs an explicit handoff protocol — adds work to F3. |
| 7 | Setting `teammateMode` and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` in plugin's settings.json snippet WON'T conflict with consumer's own setting (e.g., consumer has `teammateMode: in-process`). | Cross-cutting; if plugin tries to override consumer settings on install, breaks consumer expectations. |

## Runner-up to steel-man

**Approach B's audience-tagged-single-CLAUDE.md vector.** The hybrid absorbs B's curated-payload but rejects B's audience-tagging in favor of file split. Phase 3 should explicitly steel-man tagged-single-file: portfolio reviewer's *literal* suggestion was tagging, not file-split (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:60-66`); if Phase 3 finds tagging genuinely superior, the convergence revises to **A-prime + tagged-CLAUDE.md**.

## Falsifying tests inherited from Phase 2

Phase 3 should also examine whether any of these tests can be exercised IN M5 itself (so we'd find out before shipping):

- **From A's analysis:** dogfooding the post-install validator's envelope round-trip without writing into consumer-owned `.claude/` state. If unreachable → packaged single-binary entry point with embedded enforcement self-test becomes preferable.
- **From B's analysis:** dispatch a fresh prospective consumer at curated payload + tagged CLAUDE.md and ask them to onboard end-to-end without `/decision`/`/new-adr`. If they can't recover from a Phase-3 envelope denial in 30 minutes from CONSUMER.md alone → curated payload is wrong, full payload is right.
- **From C's analysis:** ship F2 (CONSUMER.md + reading order + templates + adoptable-disciplines) standalone first; have a fresh reader follow README → CONSUMER.md → templates → first dispatch. If "talk past me" verdict echoes the portfolio review verbatim → Scenario 4 isn't defused, doc surface alone insufficient.
