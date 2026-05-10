---
slice: cairn-m7-plugin-deployment-pattern
phase: V-3 attempt 1 falsified + amendment landed; V-3 attempt 2 + V-5 operator-bound
branch: dev
as-of: 2026-05-10 8771c45
---

## State

V-3 (M7 audit check 9 attempt 1) ran and **falsified** the M7-shipped manifest shape. From a fresh non-cairn Claude Code session, `/plugin install cairn@cairn-marketplace` failed with `git@github.com: Permission denied (publickey)` — Claude Code's plugin resolver constructs SSH-protocol clones for `source: "github"` regardless of how the marketplace was added (HTTPS). The `release` branch payload is intact and HTTPS-cloneable; only the resolver's protocol choice is broken.

Three parallel research threads (Explore agents) corroborated this is a known unfixed Claude Code bug: anthropics/claude-code #26588 (OPEN), #47088 (CLOSED-without-fix 2026-04-12), #50725 (OPEN, Windows-specific intersection). Anthropic's own `claude-plugins-official` marketplace uses `git-subdir` and `url` source-types — never `github`.

Amendment ADR `marketplace-source-url-amend` landed (`85229ca`) supersedes-sections `m5-plugin-deployment-pattern/D2` + `/D7`. Manifest pivoted to `source: "url"` with explicit `https://github.com/firaaz/cairn.git` URL; `ref: "release"` unchanged. Schema-lint test, INV-012 prose, INV-012 binding description all updated. Pytest 5/5 GREEN. Validator clean (only known INV-002 baseline failure). **No `release`-branch / v0.1.0 tag changes** — `release` never carried `marketplace.json`.

Field memo `docs/operator-field-notes-2026-05-10.md` committed (`08f27bd`) — five gaps observed in operator-side use; six-item action shortlist. Envelope expanded (`96fed26`) for `^docs/operator-field-notes-.*\.md$` pattern.

Six GitHub issues filed (firaaz/cairn #27–#32): three concrete (#28 intent template tightening; #31 M7 close; #32 Node 20 deprecation) and three roadmap-shaped retitled to match `kind:design-adr` / `kind:discussion-adr` labels — #27 *"ADR: operator surface — does the materialization carve-out earn its keep?"*, #29 *"Design: adversarial review at Phase 1 (mechanism TBD)"*, #30 *"ADR: cairn-on-cairn — maintainer-carve-out boundary"*. Titles now scan as decision-shaped vs work-shaped from the issues list.

Origin/dev pushed `05b2de3..08f27bd`.

## Next

**V-3 attempt 2 (operator-bound, fresh non-cairn session against amended manifest):**

1. Fresh Claude Code session in any directory NOT inside cairn's tree.
2. ```
   /plugin marketplace add https://github.com/firaaz/cairn
   /plugin install cairn@cairn-marketplace
   ```
3. **Expected: install succeeds via HTTPS clone.** If still SSH'd: significant new finding (intersects #50725's `url`-source SSH behavior on macOS, worth filing upstream).
4. From consumer cache: `uv run python ${CLAUDE_PLUGIN_ROOT}/postinstall_validate.py` — expect clean exit + envelope-enforcement self-test PASS. (Already verified end-to-end against published `release` payload in V-4 machine-half; this is verbatim record from real cache layout.)
5. **V-5:** Trivial `cairn-tdd-feature` dispatch in fresh project. Confirm `reversibility-guard.sh` / `role_guard.py` stderr OR `.claude/envelope-grants.log` landing consumer-side.

When V-3 + V-5 return green: orchestrator amends sweep-notes check-9 closure block (PASS-with-pending → PASS); lands F3 PENDING → PASS follow-up commit; lands F1 dist/ deployment-gap closure note; optional envelope trim of M7 phase-3 expansion. Closes M5+M6 structurally. Issue #31 closes.

If V-3 attempt 2 fails: capture stderr; the `url` source-type is documented and used by Anthropic's own marketplace, so unexpected failures here are signal worth filing upstream.

## Blocked / Pending

- **V-3 attempt 2 + V-5** — operator-bound; gates merge-final per ADR D9. Tracked in #31.
- **F3 PENDING → PASS amendment + F1 deployment-gap closure note** — gated on V-3+V-5 green. Tracked in #31.
- **Operator envelope trim** — post-merge: revisit `.claude/active-envelope.yaml` M7 phase-3 expansion at commit `527f49a`; trim or keep per next session's scope. Tracked in #31.
- **Node 20 deprecation** — workflow Action versions need bump before 2026-06-02. Tracked in #32.
- **Roadmap-shaped issues** awaiting design work — #27 (operator surface), #29 (`/critique-intent`), #30 (cairn-on-cairn carve-out). Each needs `/decision` or design ADR before code.
- 2 baseline `TestSlice011AssertionCoverage` failures + INV-002 re-baseline (carry-overs, not yet filed as issues).
- 6 amendment ADRs + spec-v2 correction + pre-§9 audit (carry-overs from prior handoffs, not yet filed).
- `/handoff` skill — 8th manual refresh in a row; not yet filed as issue.

## Features

- `cairn-m5-f1-packaging`: shipped + on `origin/dev` — structural gap closure note pending V-3+V-5.
- `cairn-m5-f2-consumer-doc-surface`: closed.
- `cairn-m6-f3-migration-and-symlink-retire`: closed + merged + branch deleted; check 9 PENDING → resolves on V-3+V-5.
- `cairn-m7-plugin-deployment-pattern`: P1-P4b shipped; V-3 attempt 1 falsified; amendment landed (`marketplace-source-url-amend`); V-3 attempt 2 + V-5 operator-bound. Merge-eligible, not merge-final until V-3+V-5 close. Marketplace shape on `dev` correct (`source: "url"`); release branch on origin populated; v0.1.0 tag pushed.

## Pointers

- `docs/adr/marketplace-source-url-amend.md` — amendment ADR (V-3 attempt 1 falsification record + rejected alternatives).
- `docs/adr/m5-plugin-deployment-pattern.md` — original ADR; D2 + D7 partially superseded but text intact (append-only).
- `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/integration/sweep-notes.md` — full audit; check-9 section now carries V-3 attempt 1 falsification block + V-3 re-run runbook (lines 224–262).
- `docs/operator-field-notes-2026-05-10.md` — operator memo: five gaps + six-item action shortlist.
- `docs/ARCHITECTURE.md:99-105` — INV-012 prose + invariant-check description (now reflect amended `source: "url"` shape).
- GitHub issues: [#27](https://github.com/firaaz/cairn/issues/27), [#28](https://github.com/firaaz/cairn/issues/28), [#29](https://github.com/firaaz/cairn/issues/29), [#30](https://github.com/firaaz/cairn/issues/30), [#31](https://github.com/firaaz/cairn/issues/31), [#32](https://github.com/firaaz/cairn/issues/32).
- Release branch on origin: SHA `779b013`; v0.1.0 tag SHA `f8e2b70`; M7 release-publish workflow run https://github.com/firaaz/cairn/actions/runs/25601897616.
- Amendment commit: `85229ca`; envelope expansion: `96fed26`; field memo commit: `08f27bd`.
