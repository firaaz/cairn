# plugin-payload-transport — decision framing

## Question

How does cairn deliver plugin payloads to fresh Claude Code sessions without requiring consumer SSH keys, given that Claude Code's resolver forces SSH-clone for any `source` type pointing at a `github.com` host?

## What's empirically established (do not re-litigate)

- **V-3 attempt 1 (2026-05-10):** `source: "github"` + `repo: "firaaz/cairn"` + `ref: "release"` → install fails with `git@github.com: Permission denied (publickey)`. Stderr path: `~/.claude/plugins/cache/temp_github_<id>/`.
- **V-3 attempt 2 (2026-05-11):** Amended to `source: "url"` + `url: "https://github.com/firaaz/cairn.git"` + `ref: "release"`. Removed + re-added marketplace cleanly. Identical SSH-clone failure, identical `temp_github_<id>` path.
- **Marketplace-add HTTPS clone works** (full repo lands at `~/.claude/plugins/marketplaces/cairn-marketplace/` via HTTPS).
- **Cached marketplace.json carries the amended `source: "url"` shape** — install path still routes through the github-source handler. The resolver's host-based routing (github.com → github handler) overrides the declared `source` type.
- **Upstream issues** open and unfixed: `anthropics/claude-code#26588` (req: HTTPS default), `#47088` (closed completed without fix), `#50725` (Windows `url`-type also forces SSH).
- **Anthropic's own `claude-plugins-official` marketplace** uses `source: "github"` registration with a `.gcs-sha` + tarball cache shape — special-cased at the resolver, not portable.

## Approaches to enumerate (non-exhaustive seed)

1. **GitHub Releases tarball URL** — `https://github.com/.../archive/refs/heads/release.tar.gz` or release-asset URL. Bet: the `url` handler's HTTP-fetch path activates for non-`.git` URLs and bypasses the git-clone code.
2. **Self-hosted artifact** (S3/CDN/Fly/Cloudflare R2). Avoids github.com host entirely; adds infra + release-publish pipeline.
3. **`git-subdir` source-type** against github.com. Unknown if it routes through the same github-clone handler.
4. **`git-subdir` (or `url`) against a non-github host** (GitLab/Codeberg/srht mirror). Avoid host-based routing by hosting elsewhere.
5. **Document SSH-key prerequisite** in CONSUMER.md / README. Falsifies the zero-friction install premise underpinning `delivery-mechanism-friction`.
6. **File upstream + wait** for Anthropic to fix the resolver's host-based SSH-forcing.

## Supersedes (when accepted)

- `docs/adr/m5-plugin-deployment-pattern.md` — sections D2 and D7 (manifest `source` shape)
- `docs/adr/marketplace-source-url-amend.md` — already falsified

## Blocks

- M7 merge-final
- F3 check-9 PENDING → PASS
- `delivery-mechanism-friction` impl slice (SessionStart skill ships via same transport)

## Constraints to verify in Phase 0

- INV-012 binding (`tests/unit/test_marketplace_schema.py::test_marketplace_source_ref_is_release`) — does the new transport preserve a meaningful `ref: "release"` invariant, or does the invariant need redefinition?
- `release` branch + v0.1.0 tag — still authoritative payload source, or replaced?
- `release-publish.yml` workflow — what would it produce under each approach?
- `dist-gate.yml` — PR-time gating still meaningful?
- Standing dep set (pydantic, typer, pyyaml only) — does any approach pull in new deps?
- `.slice-system` symlink retire (M6 F3) — already done; should not regress.
- Operator-envelope and write-path enforcement — must continue to fire consumer-side after install.

## References

- Falsification: `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/integration/sweep-notes.md` (V-3 attempt 2 block, commit 6286da0)
- M5 plan: `docs/plans/2026-05-08-cairn-m5-f1-packaging.md`
- M7 plan: `docs/plans/2026-05-09-cairn-m7-plugin-deployment-pattern.md`
- Falsified amendment: `docs/adr/marketplace-source-url-amend.md`
- ADRs to read in Phase 0: `m5-plugin-distribution-and-symlink-retire`, `m5-plugin-deployment-pattern`, `delivery-mechanism-friction`, `cliff-failure-mode-and-v1-defenses`
