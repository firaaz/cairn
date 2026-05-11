---
id: marketplace-source-url-amend
status: falsified
firmness: firm
supersedes: []
supersedes-sections: [m5-plugin-deployment-pattern/D2, m5-plugin-deployment-pattern/D7]
superseded-by: null
topic: architecture
invariants-touched: [INV-012]
date: 2026-05-10
---

# marketplace-source-url-amend: Amendment — pivot marketplace plugin source from `github` to `url`

## Status

Accepted (post-V-3 empirical falsification of `m5-plugin-deployment-pattern/D2`, 2026-05-10; operator-approved after parallel research confirmed `source: "github"` forces SSH-clone in Claude Code's resolver).

## Date

2026-05-10

## Context

`m5-plugin-deployment-pattern/D2` (firm, 2026-05-09) prescribed the marketplace.json plugin source as:

```json
{ "source": "github", "repo": "firaaz/cairn", "ref": "release" }
```

That ADR (line 151) explicitly flagged the residual: "`source.source: "github"` is documented to clone at `ref: "release"` separately from the marketplace's clone. This decoupling is supported by the docs but **never empirically verified against Claude Code's actual resolver**. F3 audit check 9, run against this ADR's manifest before merge per D9, is the empirical verification."

V-3 of the M7 implementation feature ran that empirical verification on 2026-05-10 and **falsified the load-bearing assumption — but on a different axis than the ADR predicted.** The schema parses; the resolver follows `ref: "release"` correctly; the failure is in transport-protocol selection.

### Empirical evidence

Running `/plugin install cairn@cairn-marketplace` from a fresh non-cairn Claude Code session produced:

```
Failed to install: Failed to clone repository: Cloning into
  '/Users/firaazfarook/.claude/plugins/cache/temp_github_<id>'...
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

Claude Code's plugin resolver, given `source.source: "github"`, constructs an SSH clone URL (`git@github.com:firaaz/cairn`) regardless of what protocol was used to add the marketplace. This fails on any consumer without an authorized GitHub SSH key — including the operator's machine, which uses HTTPS for `git push` and has no SSH key registered. Manual HTTPS clone of the same `release` branch succeeds (verified: `git clone --branch release https://github.com/firaaz/cairn` produces an intact tree).

### Corroboration

Three parallel research threads (2026-05-10) confirmed this is a known, widely-reported, unfixed Claude Code bug:

- **anthropics/claude-code#26588** (OPEN) — feature request: "Marketplace plugin cloning should default to HTTPS instead of SSH" — explicit, unshipped.
- **anthropics/claude-code#47088** (CLOSED COMPLETED 2026-04-12) — "claude plugin install for source: github plugins requires SSH, undocumented" — same failure mode, macOS, identical stderr. Closed without code-fix.
- **anthropics/claude-code#50725** (OPEN) — Windows-specific; reports SSH-clone behavior on `url`-typed sources too. Risk caveat for Windows consumers, not the macOS/Linux common case.
- **Anthropic's own `claude-plugins-official` marketplace uses `git-subdir` and `url` source types**, never `github`. Community survey of 7 public marketplaces found zero using `source: github` for cross-repo plugin sources.

The four documented `source.source` values are `{github, url, git-subdir, npm}` (`code.claude.com/docs/en/plugin-marketplaces`). Only the `url` and `git-subdir` types accept an explicit URL field; the `url` field's documentation reads: *"Full git repository URL (`https://` or `git@`)"* — protocol is consumer-controlled. `git-subdir` requires a `path:` field for a subdirectory, which conflicts with cairn's branch-root payload layout (`m5-plugin-deployment-pattern/D1`). `url` is the structurally-forced choice.

## Decision

### D2-revised — `marketplace.json` uses `source.source: "url"` with explicit HTTPS URL and `ref: "release"`

The manifest is rewritten from the M7-shipped shape:

```json
{ "source": "github", "repo": "firaaz/cairn", "ref": "release" }
```

to:

```json
{
  "source": "url",
  "url": "https://github.com/firaaz/cairn.git",
  "ref": "release"
}
```

The `url` field's explicit HTTPS value forces HTTPS-protocol clone; the `.git` suffix is documented as optional but included for clarity. `ref: "release"` is unchanged — the decoupling from marketplace's clone ref still holds (`url` source documents `ref?` identically to `github`). The `release` branch payload on origin (`779b013`, v0.1.0 tag `f8e2b70`) is unchanged; **no re-release / re-tag is required** — `release` branch never carried `marketplace.json` (only `.claude-plugin/plugin.json`).

The literal consumer commands at `README.md:19`, `CONSUMER.md:14`, and `docs/upgrading-from-symlink.md:49` remain UNCHANGED. Zero docs churn for consumer-facing copy.

### D7-revised — schema-shape lint assertions updated

`tests/unit/test_marketplace_schema.py` assertions become:

- `plugins[0].source.source == "url"` (was `"github"`).
- `plugins[0].source.url == "https://github.com/firaaz/cairn.git"` (replacing `repo == "firaaz/cairn"`).
- `plugins[0].source.ref == "release"` (unchanged).
- `"version" not in plugins[0]` (unchanged, FLI-6).
- `"type" not in plugins[0].source` (unchanged regression-guard).

D7's enumeration of valid `source.source` values (`{github, url, git-subdir, npm}`) is unchanged — the set is the same; the assertion now picks the `url` member.

INV-012's `invariant-check` test-ref binding (`docs/ARCHITECTURE.md:99-105`, pointed at `test_marketplace_source_ref_is_release`) is unchanged — that test asserts `ref: "release"`, which is preserved.

## Consequences

### Easier (positive)

- **V-3 unblocks.** A fresh consumer running the literal README commands resolves the manifest at `dev`-tip, follows `source: "url"` + explicit HTTPS URL + `ref: "release"` to the `release` branch via HTTPS, and gets a working install. The original D9 acceptance criterion is satisfiable.
- **Zero release/payload churn.** `release` branch HEAD is unchanged; v0.1.0 tag is unchanged. Only `dev`-tip's marketplace.json + the schema-lint test change.
- **Aligns with Anthropic's own usage.** `claude-plugins-official` marketplace uses `url` and `git-subdir` source types. Cairn now matches the de-facto community pattern.
- **Surfaces a less-obscure schema.** `url` source-type carries the URL as a first-class field; future readers see `https://github.com/firaaz/cairn.git` on the page rather than inferring transport protocol from `repo: "firaaz/cairn"`.

### Harder (negative)

- **Windows consumers may still hit `#50725`.** Issue #50725 (OPEN) reports SSH-clone behavior even for `url`-typed sources on Windows. Risk applies to Windows consumers only; macOS/Linux consumers (the operator's class) are unaffected per the issue's scope. If a Windows consumer reports the same failure, the next escalation is filing a new issue or providing the documented `git config insteadOf` workaround.
- **Two ADRs to read.** Future maintainers reading `m5-plugin-deployment-pattern/D2` see the rejected `github`-source shape and must follow the `superseded-by`-style cross-link here. Mitigated by `supersedes-sections:` frontmatter on this ADR (mechanical link) and by leaving D2's prose intact (append-only invariant).
- **Loss of the `repo: "firaaz/cairn"` self-documentation.** The `github` source-type's `repo` field clearly stated which repository the plugin lived in. The `url` field requires reading the full HTTPS URL to extract the same fact. Trivial cost.

## Alternatives Considered

### `source: "git-subdir"` with `url: https://...` + `path: "."`

Rejected. The `git-subdir` source-type requires a `path:` field documenting "Subdirectory path within the repo containing the plugin." Cairn's `release` branch carries the plugin payload at branch ROOT, not in a subdirectory (`m5-plugin-deployment-pattern/D1`: "No `dist/` subdirectory on `release`; the build output's contents land at branch root"). Whether `path: "."` or `path: ""` is accepted is undocumented. Forcing a non-empty `path:` value would require restructuring the `release` branch — invalidating D1, the v0.1.0 tag SHA, and the published payload. Higher cost than `url` for no compensating benefit.

### Force HTTPS on `source: "github"` via `git config --global url."https://github.com/".insteadOf "git@github.com:"`

Rejected. The `git config insteadOf` workaround is the documented community fix per anthropics/claude-code#26588's discussion, but it requires a per-consumer setup step that contradicts the M5 ADR's "literal consumer commands, zero prerequisite" claim (`m5-plugin-deployment-pattern.md:78`). It also doesn't fix the issue for plugin SUBINSTALL (per #50725); it only patches marketplace-add. Switching schemas is the correct fix; consumer-side workarounds are scaffolding around an upstream bug we have no control over.

### Wait for anthropics/claude-code#26588 to ship

Rejected. #26588 has been open since at least early 2026; #47088 was filed and closed without code-fix. The empirical signal is "Anthropic team has not prioritized this." Cairn has a working alternative (`url` source-type) that is documented and used by Anthropic's own official marketplace; waiting indefinitely while V-3 stays red is not an option.

## Notes on the M5/M7 line

This amendment does NOT close M7. M7's machine-half work (`release` branch, release-publish workflow, dist-gate, schema-lint test infrastructure) all stand. M7's V-thread V-3 is what surfaced this falsification — that's the design loop firing as intended (D9). M7 V-3 + V-5 must re-run against the amended manifest before M7 records merge-final and F3 sweep-notes flips PENDING → PASS.

Sweep-notes recording protocol: `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/integration/sweep-notes.md` check-9 section gains a "V-3 falsification + amendment" block; VERDICT remains PASS-with-pending-manual-round-trip until V-3 (re-run on amended manifest) records green.
