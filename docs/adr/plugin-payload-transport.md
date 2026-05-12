---
id: plugin-payload-transport
name: Plugin payload transport — self-marketplace via dev/dist, A7 fallback
status: superseded
firmness: provisional
date: 2026-05-11
topic: architecture
invariants-touched: [INV-012]
supersedes: []
supersedes-sections: [m5-plugin-deployment-pattern/D2, m5-plugin-deployment-pattern/D7, marketplace-source-url-amend/D2-revised]
superseded-by: plugin-payload-transport-a1
---

# plugin-payload-transport: Plugin payload transport — self-marketplace via dev/dist, A7 fallback

## Status

Accepted, provisional. Probe-gated: escalates to firm after the A3a empirical probe records green on both install and update cycles in a fresh consumer session, and F3 audit check-9 transitions PENDING → PASS.

## Date

2026-05-11

## Context

Cairn ships as a Claude Code plugin via `.claude-plugin/marketplace.json`. The M5 plan committed to `source: "github"` + `repo: "firaaz/cairn"` + `ref: "release"` (m5-plugin-deployment-pattern/D2). V-3 attempt 1 (2026-05-10) falsified that shape: Claude Code's resolver force-routes `github`-source plugins through an SSH-clone path against `git@github.com:`, which fails on consumer machines without a registered SSH key. The amendment ADR `marketplace-source-url-amend` (2026-05-10) pivoted to `source: "url"` + HTTPS URL + `ref: "release"` on the hypothesis that the `url` source-type would honor the URL's HTTPS scheme.

V-3 attempt 2 (2026-05-11) ran in a fresh non-cairn Claude Code session after `/plugin marketplace remove` + clean re-add. The cached `marketplace.json` on disk carries the amended shape; marketplace-add via HTTPS succeeded (full repo present at `~/.claude/plugins/marketplaces/cairn-marketplace/`). The install failed with the identical `git@github.com: Permission denied (publickey)` stderr and the same `temp_github_<id>` cache-dir naming as attempt 1. The amendment is falsified at the install layer: the resolver's `url`-source handler, when the URL host is `github.com`, falls through to the same github-clone code path that forced SSH on attempt 1. `marketplace-source-url-amend` is now `status: falsified`.

Three upstream Claude Code issues document the resolver's host-based SSH-coercion as a known unfixed bug: `anthropics/claude-code#26588` (reverse-engineered patch lives inside `case 'github':` handler in `cli.js`), `#47088` (closed completed without code fix), `#50725` (Windows; explicitly names `source: "url"` + HTTPS URL as the failing shape and host-detection as the coercion mechanism). No upstream fix has shipped through Claude Code 2.1.138.

The cliff: M7 merge-final is blocked behind F3 audit check-9 (`m5-plugin-deployment-pattern/D9`), which is in turn blocked behind a working consumer install path. The `delivery-mechanism-friction` ADR's "zero-friction install" premise also depends on this transport question. Without a transport decision, the entire downstream deployment-ergonomics arc stalls.

Empirical research into `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json` (Anthropic's reference marketplace) surfaced three population patterns: 82 `source: "url"` plugins (all `github.com`, all sha-pinned, none ref-pinned, none tarball URLs), 49 string-relative-path plugins (`"source": "./plugins/<name>"` — self-marketplace shape), 36 `git-subdir` plugins (sha + ref). Cairn's `url + ref + no sha` shape is uniquely outlier; the self-marketplace shape is the only Anthropic-validated pattern in which the consumer install path involves no second clone (and therefore no host-based routing for the resolver to coerce).

The full decision trail — Phase 0 constraints, Phase 0.5 user-journey, Phase 1 pre-mortem, Phase 2 three-approach evaluation (A1 sha-pin, A3a self-marketplace, A6 Releases tarball), Phase 2 convergence note, Phase 3 adversarial reshape — is preserved under `.claude/skill-runs/plugin-payload-transport/`.

## Decision

**D1. Adopt self-marketplace transport (A3a).** Rewrite `.claude-plugin/marketplace.json` to:

```json
{
  "name": "cairn-marketplace",
  "owner": { "name": "firaaz" },
  "plugins": [
    {
      "name": "cairn",
      "description": "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code.",
      "source": "./dist"
    }
  ]
}
```

The string-relative-path `source` resolves filesystem-local against the consumer's marketplace cache (`~/.claude/plugins/marketplaces/cairn-marketplace/dist/`), which is populated by the marketplace-add HTTPS clone of `dev`. Plugin-install is a filesystem copy. There is no URL for the resolver to coerce; the SSH-forcing failure mode is structurally unreachable, not merely avoided by hypothesis.

**D2. `dist/` is committed-current on `dev` and is the authoritative consumer install target.** The `release` branch is retained as archaeology + tag anchor (preserves D8 of `m5-plugin-deployment-pattern`) but `marketplace.json` no longer references it; consumers do not install from `release`.

**D3. `dist-gate.yml` escalates from advisory to mandatory.** A PR that modifies source files under the `dist/` allow-list (`scripts/build_dist.py`'s mirror set) without a corresponding `dist/` rebuild commit must fail CI. Stale-`dist` is a release blocker, not a hint. The existing `dist-gate.yml` provides the rebuild + diff comparison; this decision flips its severity.

**D4. `release-publish.yml` removes any post-push marketplace.json rewrite step.** No two-step CI coupling (the rejection axis named in `m5-plugin-deployment-pattern` Phase-3 stress test). The workflow may add a fail-fast check that `git diff --quiet dist/` is empty at workflow start; otherwise unchanged. `--force-with-lease` on the `release` branch sync is preserved.

**D5. `tests/unit/test_marketplace_schema.py` is rewritten for the self-marketplace shape.** Three of the five currently-green assertions are replaced; two are retained:
- `test_marketplace_source_is_relative_dist`: assert `plugins[0]["source"] == "./dist"` (replaces `test_marketplace_source_source_is_url`).
- `test_marketplace_source_relative_path_exists`: assert the `./dist` path resolves to a directory containing `.claude-plugin/plugin.json` in the repo (replaces `test_marketplace_source_url_is_https_cairn_git`).
- `test_marketplace_plugin_entry_omits_version`: retained.
- `test_marketplace_source_omits_legacy_type_field`: retained, generalized to `isinstance(plugins[0]["source"], str)` regression check.
- `test_marketplace_source_ref_is_release`: deleted. INV-012's `ref: "release"` clause is redefined (see D7).

**D6. A3a empirical probe is the precondition for firmness escalation.** Run in this order in the impl slice:

1. Hand-edit `marketplace.json` to the D1 shape on a probe branch off `dev`; ensure `dist/` is built and committed.
2. Push the probe branch; in a fresh Claude Code session on a directory that is NOT cairn, with `~/.ssh/id_*` moved aside (or no GitHub SSH key configured), run `/plugin marketplace remove cairn-marketplace; /plugin marketplace add https://github.com/firaaz/cairn` (targeting the probe branch via fork or temporary default-branch override).
3. Run `/plugin install cairn@cairn-marketplace`. **Install pass criteria:** payload lands under `~/.claude/plugins/`; install log contains no `git@github.com:` and no `temp_github_<id>` paths; `postinstall_validate.py` self-test PASS.
4. Bump `dist/.claude-plugin/plugin.json:version` on the probe branch; rebuild + commit + push; run `/plugin update cairn@cairn-marketplace`. **Update pass criteria:** consumer-visible version reflects the bumped value; no manual `marketplace remove + add` required.

Both criteria must record green before this ADR's firmness escalates to firm. If either fails, fall to D9.

**D7. INV-012 is redefined.** Prior wording (per `ARCHITECTURE.md` and `marketplace-source-url-amend/D2-revised`): "`marketplace.json` carries `source: "url"` + HTTPS URL + `ref: "release"`; `release` branch is the authoritative payload source." New wording: "`marketplace.json` carries `source: "./dist"` (string-relative-path); `dev`-tip carrying committed-current `dist/` is the authoritative consumer install target. The `release` branch is retained as archaeology + tag anchor but is no longer the install target." The schema-lint binding (`test_marketplace_source_is_relative_dist`) replaces the prior `test_marketplace_source_ref_is_release` test as the machine-checkable invariant.

**D8. Source-tree exposure in the marketplace cache is accepted.** `/plugin marketplace add` HTTPS-clones the full cairn repo (scripts/, docs/, tests/, ADRs, `.slice-system → .` symlink, plans) into `~/.claude/plugins/marketplaces/cairn-marketplace/`. The *installed* plugin tree under `~/.claude/plugins/cache/` stays curated to `dist/` only, but the marketplace cache dir contains the full source. This matches the behavior of all 49 self-marketplace plugins in Anthropic's reference marketplace. Document in `CONSUMER.md`. Verify that Claude Code's marketplace-cache walkers do not recurse with `followlinks=True` (the `.slice-system → .` self-symlink would infinite-loop); document the hazard in `docs/operational-reference.md`.

**D9. Named v1 fallback (A7): document SSH-key prerequisite.** If D6 probe falsifies on install or update, do not chain a third ADR amendment on resolver-internals hypotheses. Instead: amend `delivery-mechanism-friction` to soft-spec the "zero-friction install" property as "conditional on Claude Code resolver fix"; add a `CONSUMER.md` note instructing consumers without GitHub SSH keys to run `git config --global url.https://github.com/.insteadOf git@github.com:` before `/plugin install`; subscribe to upstream issues #26588 / #47088 / #50725 for fix-shipped triggers a re-decision. A7's exit-ramp cost when upstream fixes the bug is one-line CONSUMER.md revert.

**D10. Rejected approaches.**
- **A1 (`source: "url"` + `sha:` pin, drop `ref:`)** — Phase 3 adversarial showed the 82/82 sha-pin population pattern in Anthropic's marketplace is non-causal under any model fitting upstream evidence. Issue #26588's reverse-engineering places the SSH-coercion inside `case 'github':` in the resolver, which fires for `source: "url"` against `github.com` regardless of pin field. A1 also reintroduces the two-step CI coupling (`release` push → capture HEAD-sha → rewrite `marketplace.json` on `dev` → push `dev`) that `m5-plugin-deployment-pattern` Phase 3 explicitly rejected as a structural anti-pattern. Demoted to backup-of-backup; accept only if D6 surfaces an unforeseen `dist/`-discipline blocker that breaks A3a but a sha-pin would not.
- **A6 (GitHub Releases tarball URL)** — Rejected without probe. Zero empirical prior (no Anthropic plugin uses a tarball URL); release-asset URL becomes a forever-public contract that brittles update cycles; release-publish ordering interacts with the existing tag step in fragile ways.

## Consequences

### Easier

- F3 audit check-9 has a structurally sound completion path: install + update probe in a fresh consumer session, no SSH key dependency. Once D6 records green, M7 merges merge-final.
- The `delivery-mechanism-friction` impl slice unblocks: its SessionStart `using-cairn` skill ships via the same `dist/` payload that D1 names.
- Falsification chain ends. `marketplace-source-url-amend` stays `status: falsified`; this ADR is the structural replacement, not another amendment on the `url`-source bet.
- No new infrastructure, no new credentials, no new third-party Action. CI surface narrows (no two-step coupling).
- Update story rides the same marketplace-cache refresh that 49 Anthropic self-marketplace plugins use — strongest available inferential evidence for a working Stage-6 mechanism.

### Harder

- `dist/` must be committed-current on `dev` at every release moment. PR-time `dist-gate.yml` escalation makes stale-`dist/` a release blocker, adding small release-time discipline. Operator-only `chore: release` commits should be the path of least friction.
- Consumer's marketplace cache contains the full cairn source tree, including ADRs, plans, scripts, and tests. Consumers grepping `~/.claude/plugins/marketplaces/cairn-marketplace/` see cairn-internal docs they should not reason from. Documented but real.
- `.slice-system → .` self-symlink survives the marketplace-add clone. Claude Code's marketplace-cache walkers must not recurse through it. Verified once at probe time; documented in `operational-reference.md` as a known hazard.
- Two of five existing `test_marketplace_schema.py` assertions go away; INV-012's defensive net thins. Replacement assertions on `./dist` shape + plugin.json existence partially compensate; net reduction is acceptable given the structural simplification.
- The dev/release semantic distinction softens. Before this ADR: `dev` is source, `release` is shipped payload. After: `dev` is both. The `release` branch keeps its archaeology role but loses install authority. The collapse is honest — `release` carried no information not derivable from `dev` + `build_dist.py` — but it's a real reduction in separation of concerns.
- Probe-falsification path (D9) concedes the "zero-friction install" premise from `delivery-mechanism-friction`. If A3a falsifies, that property becomes conditional pending upstream fix. Real cost; budgeted in D9.

## Alternatives Considered

- **A1 — `source: "url"` + `sha:` pin (drop `ref:`).** Cheapest probe (~5 min), strongest empirical prior (82/82 of Anthropic's `url`-source plugins use sha-pinning). Rejected per D10: the 82/82 pattern is non-causal under upstream issue #26588's reverse-engineering, and A1 reintroduces two-step CI coupling. Full evaluation: `.claude/skill-runs/plugin-payload-transport/phase-2-approach-A1.md`.
- **A6 — GitHub Releases tarball URL** (`https://github.com/firaaz/cairn/releases/download/v0.1.0/cairn-v0.1.0.tar.gz`). Hypothesis: `.tar.gz` URLs take an HTTP-fetch path. Rejected per D10: zero Anthropic precedent, asset-URL forever-contract, worst update story. Full evaluation: `.claude/skill-runs/plugin-payload-transport/phase-2-approach-A6.md`.
- **A2 — Self-hosted artifact (S3/R2/CDN).** Avoids github.com host entirely. Rejected on infrastructure-debt grounds (S5 from Phase 1 pre-mortem): adds a new always-on infra dep, new credentials, new failure modes; violates "first-party CI only" preference; expands the consumer prereq floor implicitly via host availability. Not enumerated in Phase 2 deep-dives.
- **A4 — Separate `cairn-marketplace` GitHub repo** (marketplace.json + bundled payload in a dedicated repo). Achieves self-marketplace effect without dev-branch source exposure. Rejected: doubles the repo maintenance surface; release-publish must push to two repos; consumer-facing URL changes (`https://github.com/firaaz/cairn-marketplace` instead of `cairn`) violate the "consumer commands UNCHANGED" lock in D2 of `m5-plugin-deployment-pattern`. A3a achieves the same SSH-bypass with strictly less surface.
- **A5 — Non-GitHub host (GitLab / Codeberg / sourcehut mirror).** Avoids `github.com` host-based routing. Rejected on operational grounds: maintain a mirror, sync drift, additional account; corporate-proxy consumers may have github.com allowlisted but not the alternative; adds a contingent dependency on a third-party host's availability.
- **A8 — File upstream Claude Code bug + wait.** Three issues already open with no fix shipped; passive waiting is not a v1-shippable decision. Subsumed into D9's trigger condition (re-decide when upstream ships a fix).

## Risk Register

- **R1. A3a probe falsifies on install.** Resolver does not resolve `"./dist"` filesystem-local; instead errors, or routes through some unexpected resolution. Mitigation: D9 fallback (A7) takes over without ADR re-amendment. Probability: low (49 Anthropic plugins use this shape successfully); consequence if realized: bounded — one operator hour to document SSH prereq + amend `delivery-mechanism-friction`.
- **R2. A3a probe passes install but falsifies on update.** Consumer's marketplace cache does not refresh `dist/` on `/plugin update`; consumers stuck at install-time version. Mitigation: D9 fallback; or document a manual `marketplace remove + add` cycle as the update path. Probability: medium (no direct empirical evidence on the update mechanism); detection at first release cycle.
- **R3. Marketplace-cache walker recurses through `.slice-system → .`.** Infinite-loop hazard in any tool walking the marketplace cache. Mitigation: D6 probe step 3 should grep the install log for symlink-recursion errors; if confirmed, the `.slice-system` symlink must be deleted on `dev`-tip — but that breaks INV-011's maintainer dogfood property, requiring a separate decision. Probability: low (Anthropic's 49 self-marketplace plugins don't appear to hit this; their repos likely lack a self-symlink); consequence if realized: blocks A3a, escalates to a `slice-system-vs-self-marketplace` decision.
- **R4. `dist/`-current-on-dev discipline fails operationally.** Operator forgets to rebuild `dist/` on a PR that touches the allow-list; CI escalation catches it, but adds release-time friction. Mitigation: a pre-commit hook on `dev` PRs that rebuilds `dist/` and stages the diff. Out of scope for this ADR; tracked as a follow-up.
- **R5. Upstream Claude Code ships the resolver fix shortly after A3a lands.** A3a's exit-ramp cost is ~1-2h (restore URL shape + assertions in `marketplace.json` + tests). Not zero, but bounded. The dev/release semantic collapse from D2/D8 is not auto-reverted; that would require an explicit follow-up ADR. Mitigation: subscribe to upstream issues; revisit at fix-release.
- **R6. Source-tree exposure leaks consumer-confusing artifacts.** Consumer encounters cairn's internal ADRs/plans/handoff under `~/.claude/plugins/marketplaces/cairn-marketplace/` and reasons from them as if they're consumer-facing. Mitigation: `CONSUMER.md` note explicitly clarifies "the marketplace cache contains cairn's full source repo; consumer-facing surface is `~/.claude/plugins/cache/`."
