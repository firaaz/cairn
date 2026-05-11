# Phase 2 — Approach A6: GitHub Releases Tarball URL

## 1. Tarball-URL variant pick

**Pick: release-asset URL** — `https://github.com/firaaz/cairn/releases/download/v0.1.0/cairn-v0.1.0.tar.gz`.

Rationale vs. auto-archive (`archive/refs/tags/v0.1.0.tar.gz`):

- Auto-archive is **a git-tree snapshot of the tagged ref** — it contains the full source tree at the tag, not the curated `dist/` payload. To use auto-archive against `v0.1.0` (which points at `dev`-HEAD per release-publish.yml:124), the tarball would carry scripts/, docs/, tests/, .slice-system symlink — violating phase-0-constraints:38 ("Payload curation via physical separation"). An auto-archive against `release` branch tip (`archive/refs/heads/release.tar.gz`) does carry just the curated payload, but the URL has **no version segment** — every release overwrites the same URL, killing sha-pinning as a defense and making the URL useless for archaeology.
- Release-asset gives us a versioned, immutable URL pointing at a tarball we control the contents of (we upload exactly `/tmp/dist-out` packaged). We can tar the curated payload directly without round-tripping through the `release` branch.

Tradeoff accepted: release-asset adds a `gh release create` + asset-upload step (S5 cost line); auto-archive needs zero workflow changes but loses curation control or versioning.

## 2. Shape

**`.claude-plugin/marketplace.json` diff**:
```json
"source": {
  "source": "url",
  "url": "https://github.com/firaaz/cairn/releases/download/v0.1.0/cairn-v0.1.0.tar.gz"
}
```
`ref:` field dropped (no git ref applies to a tarball). **This breaks `test_marketplace_schema.py::test_marketplace_source_ref_is_release`** (constraints:21).

**`.github/workflows/release-publish.yml` diff** — adds a step after the existing release-branch sync (line 110) and before the tag step (line 112):

```yaml
- name: Package dist payload as release asset
  if: github.event_name == 'workflow_dispatch'
  env:
    INPUT_VERSION: ${{ github.event.inputs.version }}
  run: |
    set -euo pipefail
    tar -C /tmp/dist-out -czf "/tmp/cairn-v${INPUT_VERSION}.tar.gz" .

- name: Create GitHub Release with asset
  if: github.event_name == 'workflow_dispatch'
  env:
    GH_TOKEN: ${{ github.token }}
    INPUT_VERSION: ${{ github.event.inputs.version }}
  run: |
    gh release create "v${INPUT_VERSION}" \
      "/tmp/cairn-v${INPUT_VERSION}.tar.gz" \
      --title "cairn v${INPUT_VERSION}" \
      --target release
```

**Ordering hazard:** the existing tag step (release-publish.yml:112-125) creates `v${VERSION}` *after* the release-branch push. `gh release create v...` will create the tag itself if absent. Must consolidate: either (a) `gh release create` becomes the tag-creator and the old step deletes, or (b) tag step runs first, then `gh release create v... --notes ... <asset>` against the existing tag. (b) preserves D8 semantics.

**Tag/branch invariant impact:** `release` branch still pushed (force-with-lease) — preserved for archaeology and as the `--target` for the release. But **marketplace.json no longer references it**. INV-012 binding "`marketplace.json` points to `release` branch" is broken; the release branch becomes a CI artifact with no live consumer dependency.

## 3. How it bypasses SSH — hypothesis (UNVERIFIED)

The premise: the resolver, when given `source: "url"`, may branch on URL shape:
- URL ends in `.git` or resolves to a git host → invoke git-clone code path (which has the host-based SSH-forcing bug).
- URL ends in `.tar.gz` (or HEAD returns `application/gzip` / `application/x-gtar`) → invoke an HTTP-fetch path that downloads + extracts, no git involved.

**This is unverified.** research-anthropic-marketplace.md shows zero of 82 `url`-type plugins use tarball URLs — every single one is `https://github.com/.../.git` with sha-pinning. We **cannot piggyback on Anthropic's empirical evidence** the way A1 can (82/82 examples). The hypothesis is purely structural: it would be unusual for a resolver named "url-source-type" to *not* honor URL-shape routing, but Claude Code's resolver has already demonstrated it does the unusual thing once (host-based override of declared scheme, sweep-notes:276-277). It could equally route ALL `url` source-types through git-clone regardless of suffix.

## 4. Phase-2 ten-item checklist

1. **Empirical probe plan** — Scratch branch `probe/a6-tarball`. Build dist locally, `tar -czf /tmp/cairn-probe.tar.gz -C dist .`, manually upload to a personal release (or temporarily host via `gh release create v0.0.0-probe`). Hand-edit marketplace.json to point at the asset URL on `dev`-tip. Fresh consumer dir: `claude /plugin marketplace remove cairn-marketplace; /plugin marketplace add https://github.com/firaaz/cairn; /plugin install cairn@cairn-marketplace`. Pass = payload extracted to `~/.claude/plugins/cache/...` with `.claude-plugin/plugin.json:version == "0.1.0"`, hooks registered, no SSH error in stderr. Fail = any `git@github.com` invocation, or "unsupported source" error.
2. **Consumer prereq delta** — Zero. Tarball extraction is in-resolver (Node.js stdlib `tar` package presumably). No `tar` on consumer PATH needed (asserted, not verified; probe must check Windows). Floor `{jq, ruff, python3}` unchanged.
3. **Platform support** — macOS/Linux: expected pass. Windows: **unverified**; tarball extraction on Windows depends on resolver's tar implementation, not OS. Corporate proxy: `objects.githubusercontent.com` (GitHub release-asset host) typically allowlisted alongside github.com. No-git-on-PATH: A6's selling point — install path doesn't invoke git.
4. **INV/ADR amendment list** — Amends: m5-plugin-deployment-pattern D2 (URL shape), D7 (schema assertions), D8 (tag step folded into gh release create), marketplace-source-url-amend D2-revised (superseded entirely — URL no longer `.git`). INV-012 redefined: `release` branch authority replaced by `v0.x.y` release-asset authority; `ref: "release"` invariant deleted. Intact: D1 shape, D3 version signal (plugin.json), D5 workflow-dispatch trigger, D6 force-with-lease (release branch still pushed), D9 F3 check 9.
5. **test_marketplace_schema.py impact** — Rewrite. Drop `test_marketplace_source_ref_is_release` and the URL=`https://github.com/firaaz/cairn.git` assertion. Add: `source.source == "url"`, `source.url` matches `^https://github\.com/firaaz/cairn/releases/download/v\d+\.\d+\.\d+/cairn-v\d+\.\d+\.\d+\.tar\.gz$`, no `ref`, no `sha`, no `version` on entry.
6. **release-publish.yml diff sketch** — See §2 above. Preserves force-with-lease (release branch still synced). First-party CI only (`gh` CLI is GitHub-native). New permission requirement: `permissions: contents: write` already present (line 27) — covers release creation.
7. **Update path** — **Worst case of all approaches.** marketplace.json on `dev` carries the version-pinned URL. Consumer's marketplace cache (`~/.claude/plugins/marketplaces/cairn-marketplace/`) holds a snapshot of marketplace.json. For v0.1.1 to reach a consumer: (a) marketplace cache must refresh (manual `/plugin marketplace update`?), (b) which then sees the new URL, (c) which pulls a new tarball. If `/plugin update` doesn't refresh the marketplace itself, consumer is locked. **Empirical probe required:** install v0.1.0-probe, publish v0.1.1-probe with updated marketplace.json URL, run `/plugin update`, observe. This is the S4 failure mode (pre-mortem:51-63) materialized.
8. **New-infra delta** — Zero new services, zero new credentials (uses `github.token`, already in workflow), zero new repos. GitHub Releases is "free, already-trusted, no new credential" — the best-case shape for S5 (pre-mortem:77).
9. **Exit-ramp cost** — Medium. If Anthropic fixes the resolver: revert marketplace.json to `{source:url, url:...git, ref:release}`, revert workflow (delete release-asset step), restore the dropped test assertions. ~2 PRs. The release-asset URL becomes orphaned but doesn't break anything — old consumers' marketplace caches still point at it until they `/plugin marketplace update`. Bigger drag: the published v0.1.0 release asset URL is forever-public; deleting it would brick any consumer who installed via A6 and hasn't refreshed.
10. **F3 audit check 9 plan** — Two-cycle manual test in fresh consumer dir: (1) install v0.1.0 via marketplace add + plugin install, verify hooks fire on a sample Bash/Edit, verify role_guard.py with active-envelope.yaml. (2) publish v0.1.1 release-asset + update marketplace.json on dev, run `/plugin marketplace update` + `/plugin update cairn`, verify `dist/.claude-plugin/plugin.json:version == "0.1.1"` in consumer cache.

## 5. Empirical probe — elevated importance

A1 has 82/82 confirming examples in Anthropic's marketplace. A6 has **zero**. The probe is the single load-bearing evidence for A6's viability — without it, A6 is pure conjecture about resolver internals. Probe outcome should gate any ADR amendment; do not write the impl slice before the probe returns green.

The probe is also cheap: ~30 minutes (build dist, tar, gh release create on a throwaway tag, hand-edit marketplace.json on scratch branch, install in fresh consumer). Cheap enough that A6 should not be ranked against A1/A2 in synthesis *until* the probe runs.

## 6. Risks specific to A6

- **R-A6-1 — Hypothesis-falsification risk (highest).** Resolver may route all `source: "url"` through git-clone regardless of URL suffix, ignoring `.tar.gz`. Probe falsifies in ~30 minutes; consequence is A6 is dead, no second amendment to ADR chain because A6 never landed.
- **R-A6-2 — Update mechanism coupling.** Tarball lacks `.git` metadata; consumer cannot `git pull` for updates. Update is forced through "marketplace.json URL rotation + marketplace cache refresh" — a fragile, undocumented path (S4 pre-mortem). Even if install works, updates may silently never reach consumers.
- **R-A6-3 — Release-publish ordering complexity.** `gh release create` interacts with the existing D8 tag step (release-publish.yml:112-125). Must consolidate without breaking the FLI-2 cross-check or the idempotent-retag invariant. New failure mode: release-asset upload fails after release-branch push succeeds, leaving v0.1.0 tag pointing at release but no asset at the URL marketplace.json names → broken install URL.
- **R-A6-4 — Asset URL immutability lockout.** Once `cairn-v0.1.0.tar.gz` is published and consumers' marketplace caches point at it, the URL is a forever-contract. Any need to rebuild v0.1.0 (e.g., postinstall_validate.py bugfix backported) requires either a new version bump or deleting+re-uploading the asset (which GitHub allows but breaks reproducibility). Sha-pinned git refs (A1) have no equivalent rebuild hazard — the sha *is* the content.
- **R-A6-5 — `release` branch becomes vestigial.** marketplace.json no longer references `release`. The branch still ships for archaeology, but its semantic meaning ("authoritative payload source") evaporates. INV-012 becomes an archive-only invariant, weakening the deterministic-release story.

## 7. Adversarial steelman against A6

**"If it worked, Anthropic would already do it."** This is the strongest case against A6 and deserves direct engagement.

Anthropic ships 82 plugins via `source: "url"` + sha-pinning. They have first-party knowledge of the resolver. If a tarball URL bypassed the SSH-forcing cleanly, it would be the **strictly easier** distribution shape: no sha to capture post-push, no two-step ceremony, no force-with-lease coordination — just upload a tarball, point marketplace.json at it. They don't do it. Three explanations, in decreasing order of damage to A6:

1. **The resolver doesn't support tarball URLs at all.** `source: "url"` means "git URL." Tarball is unsupported, and the resolver will either reject the manifest or git-clone the tarball URL (which fails). This is the lethal case for A6 and is consistent with the "no Anthropic plugin uses this" data point.
2. **Tarball works but loses update semantics.** Anthropic's plugins update via sha-bumps in marketplace.json + git-fetch. Tarball updates require URL rotation + cache refresh — UX-worse. They picked the better shape. A6 still works for install but is strategically inferior; would need a follow-up update-mechanism slice.
3. **It works fine, Anthropic just picked sha-pinning first and never revisited.** Plausible but weak — Anthropic's plugin team is small but careful, and tarball-URL is the obvious "just use HTTP" shape that would emerge in any design review.

(1) is the dominant prior. A6 should be probed cheaply and **rejected fast if the probe shows resolver rejects the manifest or git-clones the .tar.gz URL**. Do not invest in A6 beyond the probe without empirical green.

The steelman also weakens A6 even when probe passes: even a successful install leaves the update story (§4 item 7) as a documented unknown — and if Anthropic's reason for avoiding tarball-URL is update-UX rather than install-impossibility, we inherit that UX cost without their justification.
