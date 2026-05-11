# Research — Anthropic's `claude-plugins-official` marketplace shape

Inspected `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json` (cached locally, lastUpdated 2026-05-11).

## Source-type frequency

| Source type | Count | Notes |
|---|---|---|
| `url` | 82 | All `https://github.com/.../.git` URLs |
| STRING-RELATIVE-PATH (e.g. `"./plugins/foo"`) | 49 | Self-marketplace-relative; payload lives inside the marketplace repo |
| `git-subdir` | 36 | URL + path subselection |
| `github` | 2 | Outlier |

## Critical pattern — pinning style by source-type

| Source-type | `ref:` populated | `sha:` populated | Both |
|---|---|---|---|
| `url` (n=82) | **0** | **82** | 0 |
| `git-subdir` (n=36) | 35 | 36 | 35 |

**Every `source: "url"` plugin pins by `sha:`. NONE use `ref:`.**
**Every `git-subdir` plugin pins by `sha:` + (mostly) `ref:`.**

## What cairn currently does (the outlier)

`.claude-plugin/marketplace.json`:
```json
"source": {
  "source": "url",
  "url": "https://github.com/firaaz/cairn.git",
  "ref": "release"
}
```

`source: "url"` + `ref:` + no `sha:` — **no Anthropic-marketplace plugin uses this shape.**

## Working hypothesis

Claude Code's plugin resolver routes `source: "url"` differently based on pinning style:

- **`sha:` set, no `ref:`** → direct git-fetch by commit SHA over HTTPS (the URL's protocol is honored). This is what Anthropic uses for all 82 of their `url`-type plugins.
- **`ref:` set, no `sha:`** → falls back to "resolve ref" which invokes the github-clone code path that prefers SSH against github.com hosts. This is cairn's shape, and it falsified at V-3 attempts 1 + 2.

This hypothesis is **strongly suggested but not empirically verified**. The signal is the population pattern (82/82 use sha; cairn's ref-only shape is uniquely outlier). It would explain why Anthropic's marketplace works for users without SSH keys.

## Additional finding — self-marketplace shape

49 of Anthropic's plugins use `"source": "./plugins/<name>"` (a string relative path). This means the marketplace repo itself bundles the payload as subdirectories. Marketplace-add HTTPS-clones the marketplace repo, and plugin-install is a filesystem copy from the cached marketplace dir — **no second clone needed, no SSH path at all**.

Cairn could adopt this pattern by either:
1. Making `release` branch the marketplace home (marketplace.json + payload all at root), and accepting that the default-branch resolution would change, OR
2. Adopting a separate `cairn-marketplace` GitHub repo that bundles the dist payload, and a release-publish workflow that pushes both.

## Implications for Phase 2

The approach space expands meaningfully:

- **A1.** `source: "url"` + `sha:` + drop `ref:` (cheapest; tests the hypothesis directly).
- **A2.** `source: "git-subdir"` + `sha:` + `ref:` (Anthropic's other common shape).
- **A3.** Self-marketplace via `release` branch carrying `marketplace.json` + payload at root with `"source": "."` (radical restructure).
- **A4.** Self-marketplace via separate `cairn-marketplace` repo.
- **A5.** Non-github host (GitLab/Codeberg) with current shape.
- **A6.** GitHub Releases tarball URL (HTTP fetch, no git resolver involvement).
- **A7.** Document SSH-key prerequisite (counter to delivery-mechanism-friction).
- **A8.** File upstream + wait.

A1 is the dominant candidate on cost grounds: a tiny `sha:` field addition to marketplace.json + a release-publish workflow tweak to auto-populate it.
