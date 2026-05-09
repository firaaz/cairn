---
decision: plugin-deployment-pattern
parent-adr: m5-plugin-distribution-and-symlink-retire
parent-decisions-touched: [D1, D3]
operator-prompt-date: 2026-05-09
mode: teamed (Phase 0/0.5 parallel; Phase 2 A/B/C parallel)
---

# Brief — plugin deployment pattern

## The decision question

How does cairn's `dist/` plugin payload reach consumers' `/plugin install` resolution? F3 closed (M5+M6 milestone shipped on `origin/dev` at `6a6f430`), but F1's `.claude-plugin/marketplace.json:13` declares `source.path: "dist/"` against a `dist/` directory that **was never committed to any pushed ref**. `.github/workflows/dist-gate.yml` only validates the build (lines 23–24 build to `/tmp/dist-ci`); no step publishes. Today, `/plugin install cairn@cairn-marketplace` resolves the manifest's `path:` against the cloned default branch and finds no `dist/`. F3's audit check 9 (manual end-to-end real install) is **PENDING on this gap**.

## Operator-named approaches (the seed set)

The operator surfaced three documented options at handoff (`bfef6e5`). Each agent must verify viability against `code.claude.com/docs/en/plugins-reference` (the same source the M5 ADR's mechanism evidence relied on) — do not assume the option is structurally permitted by the marketplace schema.

- **Approach A — Release branch with `dist/` committed + sync CI.** Keep `marketplace.json` as `type: git, path: "dist/"`. CI builds `dist/` on tag/release and commits it to a release branch (or a tagged commit) that consumers point `source.ref` at. The default branch (`dev`/`main`) keeps `dist/` git-ignored.
- **Approach B — npm publish (`source.source: "npm"`).** Change `marketplace.json` `source.type` from `git` to whatever schema designation maps to npm-registry-fetch (verify the field name and schema). CI runs `npm publish` of the `dist/` payload on release.
- **Approach C — GitHub release + git-subdir.** Use a release-archive download mechanism (verify the marketplace.json shape supports it) so consumers fetch a release artifact (tarball or zip extracted to a subdir) at install time.

**Phase 2 is allowed to propose a fourth approach** if the constraint envelope or pre-mortem surfaces a hybrid the operator didn't enumerate. That is the protocol's `forced-enumeration` requirement; do not reduce to A/B/C if a stronger fourth exists.

## Why this is decision-weight (not bug-fix)

The M5 ADR's D3 commits to "CI populates `dist/` at release from a curated allow-list" but is silent on **how the payload gets to a ref consumers can resolve**. That silence is the gap. Each approach has different:

- **Versioning semantics** — does `source.ref` pin a tag, a branch, or a release artifact? D2's "explicit semver-via-tags" (pre-v1 `0.x.y` with manual bumps) constrains this.
- **Stability stance** — D2 says consumers pin SHAs/tags; A and C honor this directly. B introduces npm semver-range semantics that might collide.
- **Marketplace.json schema** — A is the M5 ADR's literal posture. B and C require schema changes.
- **Maintainer load** — A is `git push` to a release branch. B is npm-org credentialing + publish. C is GitHub release artifact attachment.
- **Vision impact** — D26's "agent-portable substrate, Windsurf as second runtime" must survive whichever distribution channel we lock in.

Decision-weight per operator memory `feedback_designs_through_decision.md` (architectural distribution change ⇒ /decision, not brainstorming → writing-plans).

## Workspace contract (for parallel agents)

Each agent writes to its own file, never to another phase's file. Phases are sequenced; cross-phase reads are explicit:

| Phase | Output file | Reads (other than this brief) | Owner |
|---|---|---|---|
| 0 | `phase-0-constraints.md` | ARCHITECTURE.md, lessons.md, m5-plugin-distribution-and-symlink-retire ADR, identifier-scheme ADR, build_dist.py, dist-gate.yml, marketplace.json, postinstall_validate.py | Subagent (general-purpose) |
| 0.5 | `phase-0.5-journey.md` | F3 sweep-notes (`.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md`), CONSUMER.md, README.md, `code.claude.com/docs/en/plugins-reference` (`/plugin install` resolution), m5 phase-0.5-journey.md (prior precedent) | Subagent (general-purpose) |
| 1 | `phase-1-pre-mortem.md` | Phase 0 + 0.5 outputs | Lead session (sequential) |
| 2A | `phase-2-approach-A.md` | Phase 0/0.5/1, m5 phase-2-approach-A.md (precedent format), Anthropic plugins-reference | Subagent (Plan) |
| 2B | `phase-2-approach-B.md` | same | Subagent (Plan) |
| 2C | `phase-2-approach-C.md` | same | Subagent (Plan) |
| 3 | `phase-3-adversarial.md` | All Phase 2 + steelman runner-up + disconfirming search | Lead session |
| 4 | new ADR (or amendment to m5-plugin-distribution-and-symlink-retire) via `/new-adr` | Phase 3 | Lead session |
| 5 | `phase-5-independent-verification.md` (only if firm) | Decision question + Phase 0 + ARCHITECTURE.md + relevant ADRs ONLY (no Lead reasoning) | Fresh subagent |

## Citation rules

- Evidence from files (`file:line`) or docs (`adr-id` per identifier-scheme), never from memory.
- External mechanism claims (Anthropic plugins-reference) cite `code.claude.com/docs/en/plugins-reference:<line>` — fetch and verify, don't trust the M5 ADR's prior fetch.
- Cross-ADR citations use `<adr-id>/<decision-slug>` form (e.g., `m5-plugin-distribution-and-symlink-retire/D3`).

## Adversarial discipline (per operator memory `feedback_attack_before_synthesis.md`)

In Phase 3, the lead must mount adversarial attacks on every load-bearing claim:

- The handoff's claim that `dist/` was never committed (verify against full ref history, not just `dev`/`main` HEAD).
- The handoff's claim that `/plugin install` resolves `path:` "statically against the cloned default branch" (re-verify against current Anthropic docs).
- The premise that A/B/C are exhaustive (search for hybrids: e.g., release-branch with auto-sync GitHub Action; or git-subtree push).
- The premise that this needs a new ADR vs an amendment to m5-plugin-distribution-and-symlink-retire (the M5 ADR is firmness: firm; an amendment is a Section 3 patch with frontmatter `amends-section: D3`).

Default-to-acceptance is the named failure mode. Phase 3 is where the lead earns the synthesis.

## Pointers (curated)

- `docs/adr/m5-plugin-distribution-and-symlink-retire.md` — governing ADR; D1 (own marketplace), D2 (semver-via-tags pre-v1), D3 (allow-list = contract; physical separation), D9 (M5+M6 atomic) are the load-bearing prior commitments.
- `.claude-plugin/marketplace.json` — the manifest carrying `source.path: "dist/"`.
- `scripts/build_dist.py` + `.github/workflows/dist-gate.yml` — current build pipeline; CI validates but doesn't publish.
- `.claude/skill-runs/m5-plugin-decision/` — prior `/decision` workspace; structural template + mechanism citations.
- `.claude/skill-runs/cairn-m6-f3-migration-and-symlink-retire/integration/sweep-notes.md` — F3 audit, check 9 PENDING.
- `docs/adr/identifier-scheme.md` — citation form rules (D2 of identifier-scheme).
