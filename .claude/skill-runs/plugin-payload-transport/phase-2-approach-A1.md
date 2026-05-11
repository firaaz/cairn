# Phase 2 — Approach A1: `source: "url"` + `sha: <commit-sha>` (drop `ref:`)

Scope: A1 only. Hypothesis: Claude Code's resolver routes `url`-source-types differently when pinned by `sha:` versus `ref:` — sha-pinning takes an HTTP-fetch-by-commit path that honours the URL's scheme; ref-pinning falls back to a github-host-aware clone path that forces SSH (research-anthropic-marketplace.md:38-44).

## 1. Shape

### marketplace.json — before (`.claude-plugin/marketplace.json:8-12`)
```json
"source": {
  "source": "url",
  "url": "https://github.com/firaaz/cairn.git",
  "ref": "release"
}
```

### marketplace.json — after
```json
"source": {
  "source": "url",
  "url": "https://github.com/firaaz/cairn.git",
  "sha": "<40-char commit sha of release-branch HEAD>"
}
```

`ref:` removed; `sha:` added. The literal HTTPS URL stays (binds INV-012's HTTPS-protocol-forcing leg, ARCHITECTURE.md:99).

### release-publish.yml diff sketch
After the `Sync release branch (force-with-lease)` step (release-publish.yml:67-110) push completes, append a **third step** that runs on the source ref (`dev`), captures the freshly-pushed release-branch SHA, rewrites `.claude-plugin/marketplace.json` on `dev`, and pushes:

```
- name: Update marketplace.json sha pin on dev (A1)
  if: github.event_name == 'workflow_dispatch'
  run: |
    set -euo pipefail
    RELEASE_SHA="$(git -C /tmp/release-worktree rev-parse HEAD)"
    uv run python -c "
    import json, pathlib
    p = pathlib.Path('.claude-plugin/marketplace.json')
    d = json.loads(p.read_text())
    d['plugins'][0]['source']['sha'] = '${RELEASE_SHA}'
    d['plugins'][0]['source'].pop('ref', None)
    p.write_text(json.dumps(d, indent=2) + '\n')
    "
    git add .claude-plugin/marketplace.json
    git diff --cached --quiet || git commit -m "chore: pin marketplace sha to ${RELEASE_SHA:0:7}"
    git push origin HEAD:dev
```

`chore:` prefix preserves INV-001 (ARCHITECTURE.md:13-20). No third-party Action introduced. Two-step coupling (release push, then dev rewrite) is the explicit cost — see §5.

## 2. How A1 bypasses SSH

The hypothesis (research-anthropic-marketplace.md:38-44): 82/82 of Anthropic's `claude-plugins-official` `url`-source plugins pin by `sha:` and zero use `ref:`; cairn's `url + ref` shape is uniquely outlier. The simplest model that explains both the empirical population pattern and V-3's SSH-forcing failure (sweep-notes §V-3 attempt 2, framing.md:10): sha-pinning enables an HTTP fetch-by-commit (e.g. `git fetch <https-url> <sha>` or a tarball-by-SHA endpoint) that does not pass through the github-host SSH-coercion branch; ref-pinning invokes the `temp_github_<id>` clone handler that forces SSH against `github.com` regardless of declared scheme. Upstream issues #26588 / #47088 / #50725 (framing.md:13) document the host-coerces-to-SSH bug for the ref path but say nothing about sha — consistent with the sha path being a separate code branch.

This is **BELIEVED, not verified.** §4 is the falsifier.

## 3. Phase-2 pre-mortem checklist (10 items)

1. **Empirical probe plan** — §4 below. BELIEVED → empirical probe needed.
2. **Consumer prerequisite delta** — Zero. No new tool, no SSH key, no new credential. Consumer floor stays `{jq, ruff, python3}` (phase-0-constraints.md:32). VERIFIED (no consumer-side code path changes).
3. **Platform support claim** — If the hypothesis holds on darwin, it should hold on Linux (same resolver binary path). Windows (#50725) remains BELIEVED — needs the same scratch-branch probe on Windows; if it fails, A1 covers macOS+Linux only, which matches cairn's current de-facto floor.
4. **INV/ADR amendment list** — Amends: m5-plugin-deployment-pattern D2 + D7 (ref→sha pin field); marketplace-source-url-amend D2-revised + D7-revised (same); INV-012 wording (ARCHITECTURE.md:99) — "explicit `ref: 'release'`" becomes "explicit `sha:` resolved from release-branch HEAD." Stays intact: INV-001 (chore: prefix), INV-011 (.slice-system), D1 (release-branch authoritative), D3 (no marketplace `version`), D5 (workflow_dispatch + version cross-check), D6 (force-with-lease), D8 (v-tag).
5. **test_marketplace_schema.py impact** — `test_marketplace_source_ref_is_release` (lines 61-69) is rewritten to `test_marketplace_source_sha_is_40_hex`. Other 4 assertions unchanged (source=="url", url==https-cairn-git, no version, no type). Net: 4 preserved, 1 redefined. VERIFIED via reading test file.
6. **release-publish.yml diff sketch** — §1 above. Preserves `--force-with-lease` (line 110), preserves first-party-CI-only (no new Actions), preserves `chore:` commit prefix. The new step writes to `dev`, not `release`, so the release-branch tree stays canonical. VERIFIED at workflow shape level.
7. **Update path** — v0.1.1 reaches an installed v0.1.0 consumer **only if the consumer's marketplace cache refreshes marketplace.json from `dev`** (Stage 6, journey:88-96). This is the load-bearing unknown for A1: if `/plugin update` re-clones the marketplace, the new sha propagates; if it caches forever, consumers are sha-locked until they manually `marketplace remove + add`. BELIEVED — empirical probe in §4 must cover update, not just install.
8. **New-infra delta** — Zero. No new service, no new credential, no new repo. VERIFIED.
9. **Exit-ramp cost** — If Anthropic fixes #26588 next month: revert the marketplace.json edit (one line: drop sha, restore ref) and revert the release-publish.yml step. One PR, <30 minutes. VERIFIED structurally.
10. **F3 audit check 9 plan** — In a fresh consumer project with no GitHub SSH key configured: (a) `/plugin marketplace add https://github.com/firaaz/cairn`; (b) `/plugin install cairn@cairn-marketplace`; (c) confirm install completes without `git@github.com: Permission denied`; (d) confirm `~/.claude/plugins/cache/` path is NOT `temp_github_<id>`; (e) ship v0.1.1 via release-publish; (f) `/plugin update cairn@cairn-marketplace`; (g) confirm consumer sees v0.1.1's `plugin.json:version`. BELIEVED until run.

## 4. Empirical probe (scratch-branch, pre-impl)

Branch: `probe/a1-sha-pin` off `dev`. Steps:

1. Hand-edit `.claude-plugin/marketplace.json` to add `sha: "<current release HEAD sha>"` and remove `ref:`. Push to GitHub.
2. In a fresh consumer dir on a machine with NO GitHub SSH key (or temporarily `mv ~/.ssh/id_* /tmp/`), run `/plugin marketplace remove cairn-marketplace || true` then `/plugin marketplace add https://github.com/firaaz/<repo>@probe/a1-sha-pin` (or amend default-branch if marketplace-add doesn't take a ref).
3. Run `/plugin install cairn@cairn-marketplace` with `CLAUDE_CODE_DEBUG=1` (or whatever verbose flag is available) capturing stderr.
4. **Expected pass:** install completes; cache path is NOT `temp_github_<id>`; stderr shows HTTPS fetch, no `git@github.com` string anywhere.
5. **Falsifiers:** (a) same `Permission denied (publickey)` as V-3 attempts 1+2 → A1 dead; (b) `sha not reachable / unable to resolve commit` → A1 needs a tag instead of bare sha; (c) silent partial install (Pre-mortem S1) → check `dist/.claude-plugin/plugin.json` exists in installed payload.
6. **Update probe:** bump release-branch HEAD on a second probe push, rewrite marketplace.json sha on `dev`, run `/plugin update`. Expected: consumer sees new sha. Falsifier for §3-item-7: consumer stays at old sha → A1 install-works-update-doesnt failure mode.

## 5. Risks specific to A1

- **R-A1-a: Two-step CI coupling.** release-publish must push `release` first, then rewrite `marketplace.json` on `dev`. Phase 3 stress-test of m5-plugin-deployment-pattern (constraints.md:45) rejected Approach D for exactly this shape. The mitigation here is that step 2 is idempotent (re-run captures latest release SHA) and a failure between steps leaves a marketplace.json pinned to the previous release — degraded but not broken.
- **R-A1-b: Sha-pinning UX for consumers on update.** Pre-mortem S4 (lines 51-63) — if `/plugin update` doesn't re-pull marketplace.json from `dev`, consumers are silently stuck on the install-time sha. Worse than ref-pinning because the pin is opaque (no "release" string in the manifest, just a hex). Detection is delayed to second release.
- **R-A1-c: INV-012 wording erosion.** Once the invariant says "sha resolved from release-branch HEAD," the literal-`ref: "release"` defence (S7, marketplace-source-url-amend D2-revised) is replaced by a derived assertion. If the release-publish rewrite step ever races or fails silently, the manifest could point at an older sha while the release branch advances, and no schema test would catch it.

## 6. Adversarial steelman against A1

The strongest case A1 fails:

- **"Anthropic's resolver resolves `ref:` to a sha internally, so sha vs ref shouldn't matter."** If true, V-3's SSH failure is not caused by the pin field but by the github.com host detection (the same `temp_github_<id>` path runs either way). The 82/82 sha-only pattern in `claude-plugins-official` would then be a stylistic Anthropic convention, not a resolver branch — a non-causal correlation. Test in §4 step 4 is the discriminator: if sha-pinned install still hits `temp_github_<id>` and SSH, this steelman is confirmed and A1 dies. The hypothesis (research:38-44) is "strongly suggested" — that's confidence about the population pattern, not about causation.
- **Sha may reach the same buggy code path via a different door.** Even if there's a separate sha branch, it might also detect `github.com` in the URL and route to the SSH clone (issue #50725 suggests host-detection is pervasive, not pin-field-conditional).
- **A1 trades a binding `ref: "release"` invariant — which has been the load-bearing "deterministic release pointer" since M5 (ARCHITECTURE.md:99) — for an opaque sha that drifts per release.** If the hypothesis is wrong, we have already burned ADR amendment #2 (after marketplace-source-url-amend #1, framing.md:27) and the next falsification would be the third amendment in the chain — the operator's plan-credibility budget is exhausted.

Net: **A1 must not advance to the impl slice without the §4 probe passing.** A negative probe result reroutes to A2/A3/A6 (out of A1's lane; for synthesis).
