---
id: plugin-payload-transport-a1
name: Plugin payload transport — url+sha pin (A1), supersedes plugin-payload-transport
status: accepted
firmness: firm
date: 2026-05-12
topic: architecture
invariants-touched: [INV-012]
supersedes: [plugin-payload-transport]
supersedes-sections: [plugin-payload-transport/D1, plugin-payload-transport/D2, plugin-payload-transport/D5, plugin-payload-transport/D7]
superseded-by: null
---

# plugin-payload-transport-a1: Plugin payload transport — url+sha pin (A1)

## Status

Accepted, firm. Empirically validated end-to-end at commit 3df4a53 (M7 F3 check 9 PASS): install, hook-load, and hook-fire all confirmed in a fresh consumer Claude Code session without GitHub SSH key. Update mechanism fragility documented in D5; see CONSUMER.md note (D6).

## Date

2026-05-12

## Context

The predecessor ADR `plugin-payload-transport` (2026-05-11) elevated **A3a (self-marketplace via `dev`/`dist`)** as load-bearing on the Phase-3 adversarial premise that **A1 (`url` + `sha:`)** would also be force-routed through the resolver's `case 'github':` SSH-clone branch — i.e., that the 82/82 sha-pinning population pattern in Anthropic's marketplace was non-causal (stylistic CI convention, not a behavioral resolver branch). That premise was empirically falsified by V-3 attempt 3 on 2026-05-12.

Sequence:
- Operator declined to pay A3a's commit-`dist/` operational cost speculatively (the operational shift A3a's D2 implies — flipping `.gitignore:39 dist/` and committing build outputs — was real but `plugin-payload-transport`'s text had under-specified it). Elected to run A1's 5-minute probe first.
- Probe commit 9f419aa swapped `marketplace.json` from `ref: "release"` → `sha: "<release-HEAD>"`. Push to `origin/dev`.
- Fresh consumer session (SSH key absent), `/plugin marketplace remove cairn-marketplace` + add + install. **Install: PASS.** No `git@github.com: Permission denied`, no `temp_github_<id>` cache path. The `url`-source handler's sha-pin path takes a fetch-by-commit branch over HTTPS that does not enter the `case 'github':` SSH-coercion branch.
- Latent M5 packaging bug surfaced at hook-load time: cairn shipped `hooks.json` flat (`{PreToolUse: [...], PostToolUse: [...]}`) but Claude Code's plugin schema requires the `{"hooks": {...}}` wrapper. Bug latent through M5/M6/M7 because every prior install attempt failed at SSH before reaching the hook loader. Fixed at commit a18bca0; release-publish workflow re-run at v0.1.0; new release HEAD `04994cc`. marketplace.json sha-pin bumped at commit 2a7e145.
- Re-tested: install + hook-load + hook-fire (V-5: `reversibility-guard.sh` blocked a recursive-delete probe with `REVERSIBILITY GUARD` stderr) all green. F3 check 9 PASS at 3df4a53.

The empirical reality: A1 works for install + hook-load + hook-fire. A3a's structural argument ("no URL → no host coercion") remains valid but is now strictly more expensive than A1 for the same outcome — A1 needs only a sha-pin field and a small release-publish step, while A3a requires un-ignoring `dist/`, escalating `dist-gate.yml` to mandatory, and accepting source-tree exposure in the marketplace cache. With install empirically green on A1, A3a's restructure is not justified.

The Phase-3 adversarial argument that drove the prior ADR's reshape is now a load-bearing **lesson**: a non-causal-pattern-dismissal can be wrong, and a 5-minute empirical probe trumps a strong structural argument when the probe-cost is low. The argument was intellectually defensible but empirically incorrect; the cheap-probe-first heuristic (operator-elected) caught it.

The decision trail is preserved at `.claude/skill-runs/plugin-payload-transport/`. This ADR re-derives the load-bearing pick on empirical grounds and supersedes the relevant decision sections of the prior ADR.

## Decision

**D1. `marketplace.json` carries `source: "url"` + HTTPS URL + `sha: <40-char commit SHA>`** (drop `ref:`):

```json
{
  "name": "cairn-marketplace",
  "owner": { "name": "firaaz" },
  "plugins": [
    {
      "name": "cairn",
      "description": "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code.",
      "source": {
        "source": "url",
        "url": "https://github.com/firaaz/cairn.git",
        "sha": "04994cc863a00afd14ac0d67c2a78f25a601a922"
      }
    }
  ]
}
```

The `sha:` field pins the consumer install to a specific `release` branch HEAD commit. Claude Code's resolver, given `url`-source + `sha:` against a `github.com` URL, takes a fetch-by-commit branch over HTTPS that does not enter the github-source clone code path — confirmed empirically by V-3 attempt 3 install. This matches the shape of all 82 `url`-source plugins in Anthropic's `claude-plugins-official` marketplace.

**D2. `release` branch remains the authoritative payload source.** Each release-publish workflow run force-with-leases the `release` branch to a new HEAD; the `marketplace.json` sha pin is bumped on `dev` to point at that new HEAD. The `release` branch's working-tree HEAD IS the curated dist payload (no `dist/` subdirectory; build output lands at branch root) — preserves the M5 layout (`m5-plugin-deployment-pattern/D1` unchanged).

**D3. The release-publish workflow gains one step: capture the new release HEAD sha and update `.claude-plugin/marketplace.json` on `dev`.** This is the two-step coupling that `plugin-payload-transport`'s Phase-3 argument cited as a structural negative against A1. The objection is acknowledged but downgraded: in practice, the second step is a single-line `sed`/`jq` rewrite of `marketplace.json`'s sha field followed by a `chore: bump A1 sha to <short-sha>` commit on `dev`, idempotent and revertible. The cost is ceremonial, not architectural; A3a's commit-`dist/` cost was strictly larger and turned out to be unnecessary. Concrete sketch:

```yaml
- name: Bump marketplace.json sha pin on dev (A1)
  if: github.event_name == 'workflow_dispatch'
  env:
    GH_TOKEN: ${{ github.token }}
  run: |
    set -euo pipefail
    RELEASE_SHA="$(git -C /tmp/release-worktree rev-parse HEAD)"
    git fetch origin dev:dev
    git switch dev
    uv run python -c "
    import json, pathlib
    p = pathlib.Path('.claude-plugin/marketplace.json')
    d = json.loads(p.read_text())
    d['plugins'][0]['source']['sha'] = '${RELEASE_SHA}'
    p.write_text(json.dumps(d, indent=2) + '\n')
    "
    git add .claude-plugin/marketplace.json
    git diff --cached --quiet || git commit -m "chore: bump marketplace sha pin to ${RELEASE_SHA:0:7}"
    git push origin dev
```

`chore:` prefix preserves INV-001. First-party CI only; no third-party Actions. `--force-with-lease` invariant preserved on the `release` branch (D6 of `m5-plugin-deployment-pattern` unchanged). Implementation is a follow-up slice; until it lands, the bump is operator-manual (as performed at commit 2a7e145).

**D4. `tests/unit/test_marketplace_schema.py` is rewritten for the A1 sha-shape:**
- `test_marketplace_source_source_is_url`: assert `plugins[0]["source"]["source"] == "url"`. Retained.
- `test_marketplace_source_url_is_https_cairn_git`: assert `plugins[0]["source"]["url"] == "https://github.com/firaaz/cairn.git"`. Retained.
- `test_marketplace_source_sha_is_40_hex`: assert `plugins[0]["source"]["sha"]` matches `^[0-9a-f]{40}$`. **NEW** (replaces `test_marketplace_source_ref_is_release`).
- `test_marketplace_source_omits_ref_field`: assert `"ref"` not in `plugins[0]["source"]`. **NEW** (defensive — prevents accidental `ref:` re-introduction which routes back to the broken github-clone path).
- `test_marketplace_plugin_entry_omits_version`: retained.
- `test_marketplace_source_omits_legacy_type_field`: retained.

Net: 4 of the original 5 retained, 1 redefined, 1 added. INV-012's defensive net is preserved.

**D5. Update mechanism fragility is documented, not fixed.** Per Phase 1 pre-mortem S4 (`.claude/skill-runs/plugin-payload-transport/phase-1-pre-mortem.md:51-63`), an A1-shaped manifest has the worst-case update story: `/plugin update cairn@cairn-marketplace` does NOT refresh the consumer's marketplace cache to pick up new sha pins on `dev`. Empirically confirmed at M7 close (sweep-notes 2026-05-12 closure block). Until Anthropic ships a fix, **the canonical update procedure for cairn consumers is**:

```
/plugin marketplace remove cairn-marketplace
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

— a manual two-step per release iteration. This is documented in `CONSUMER.md` (D6).

**D6. CONSUMER.md gains an "Updating" section.** Explicit prose: "Cairn pins consumer installs to a specific `release` branch commit SHA via `marketplace.json`. To pick up a new cairn release, run `/plugin marketplace remove cairn-marketplace` followed by `/plugin marketplace add https://github.com/firaaz/cairn` and `/plugin install cairn@cairn-marketplace`. Plain `/plugin update` does not refresh the marketplace cache; the manual remove + re-add is required until Claude Code's plugin update path is fixed (tracked at `anthropics/claude-code` issues #26588 / #50725)." Out of scope for this ADR's commit; tracked as a follow-up edit.

**D7. INV-012 wording in `docs/ARCHITECTURE.md` reverts toward the M5 + amendment shape but with `sha:` instead of `ref:`.** New wording: "`marketplace.json` carries `source: "url"` + HTTPS URL + `sha: <40-char commit SHA>` pointing at the `release` branch HEAD; the `release` branch's working-tree HEAD IS the curated dist payload." `release` branch authority preserved (reverses `plugin-payload-transport/D7`'s redefinition).

**D8. A3a, A6, A7, and the prior ADR's other rejected approaches are not re-evaluated.** The empirical signal for A1 is sufficient; re-running Phase-2 forced enumeration would be ceremony without information gain. A3a is acknowledged as structurally sound but operationally costlier than A1 for equivalent install behavior. A6 remains rejected for the reasons stated in `phase-2-approach-A6.md`. A7 (document SSH prereq) is no longer needed as a fallback since A1 is empirically alive; the related update-mechanism documentation in D6 borrows from A7's shape.

## Consequences

### Easier

- M7 merge-final reached (F3 check 9 PASS at 3df4a53). The plugin-deployment thread closes after a six-attempt arc (M5 design → V-3 attempt 1 falsified → marketplace-source-url-amend → V-3 attempt 2 falsified → plugin-payload-transport ADR → A1 probe PASS).
- Consumer install path is structurally minimal: standard `marketplace add` + `plugin install`, no SSH key, no extra prerequisites.
- No new infrastructure, no new credentials, no new third-party dependency.
- `dist/` stays gitignored. The "commit build output" anti-pattern that A3a would have introduced is avoided.
- Schema-lint test set retains 4 of 5 prior assertions; defensive coverage is broadly preserved (D4).
- The five-stage decision archaeology (`.claude/skill-runs/plugin-payload-transport/`) is fully preserved as a teachable record of "Phase-3 adversarial reshape can be wrong; cheap empirical probe trumps strong structural argument."

### Harder

- **Update mechanism is fragile (D5).** Consumers must manually `marketplace remove + re-add` per release iteration. Documented in CONSUMER.md but real friction. Tracked upstream; revisit if Anthropic ships a fix.
- **Two-step CI coupling reintroduced (D3).** The release-publish workflow gains a sha-bump step on `dev` after the `release` branch push. Acknowledged objection from the predecessor ADR; downgraded on cost grounds. Implementation is follow-up; until shipped, sha-bumps are operator-manual.
- **Sha pinning is opaque** — the manifest carries a 40-char hex string with no human-readable semantic. The previous `ref: "release"` shape was self-documenting in a way `sha:` is not. Mitigation: commit messages on sha bumps cite the short SHA; release-publish run logs link sha to version.
- **Phase-3 adversarial trust takes a credibility hit.** The structural argument was rigorous and the verdict (RESHAPE A1→A3a) was internally coherent, but the empirical reality was different. Future /decision runs need to weight cheap probes more heavily before letting adversarial argument lock in a heavier path. Captured in `docs/lessons.md` (separate commit).

## Alternatives Considered

- **A3a (self-marketplace via `dev`/`dist`).** Phase-2 deep dive at `phase-2-approach-A3.md`. Rejected on cost grounds: A3a's commit-`dist/` operational shift, dist-gate escalation, source-tree exposure in marketplace cache, and `.slice-system` symlink hazard are all real costs that A1 avoids. A3a remains structurally valid (its "no URL → no coercion" argument is correct) but the empirical confirmation that A1 works makes A3a's costs unjustified.
- **A6 (Releases tarball URL).** Rejected without probe per `plugin-payload-transport/D10`. Asset-URL forever-contract risk, worst update story, zero Anthropic precedent.
- **A7 (document SSH-key prereq).** No longer needed as primary fallback. The update-mechanism documentation in D6 is structurally similar to A7's approach but addresses the update axis, not the install axis.
- **A1 (this decision).** Initially demoted to backup-of-backup by Phase 3 adversarial; promoted to load-bearing by empirical probe.

## Risk Register

- **R1. Update fragility silently strands consumers on old SHAs.** Per D5, manual `marketplace remove + re-add` is required per release. Risk: a consumer who runs `/plugin update` and gets no error believes they're current but isn't. Mitigation: D6's CONSUMER.md "Updating" section; release notes also call out the manual update procedure. Severity: medium; consequence is stale install, not broken install. Subscribe to upstream issues #26588 / #50725 for fix-shipped trigger.
- **R2. Sha-bump step in release-publish coupling fails or races.** D3 names the workflow step; if it errors after `release` is force-pushed, `marketplace.json` on `dev` points at a stale sha while `release` advances. Detection: V-1 to V-2 cross-check (release-publish workflow asserts `plugin.json:version` equals input `version` before push; a missing sha-bump would not cross-check anything but would also leave consumers pinned to a working sha). Mitigation: the sha-bump step is idempotent (re-running captures latest); operator can run it manually if CI fails partway.
- **R3. Anthropic fixes the resolver's host-based SSH-coercion.** When that happens, `ref: "release"` becomes a viable shape again. Reverting from A1 to ref is a one-line `marketplace.json` edit + reverting the D3 workflow step + restoring `test_marketplace_source_ref_is_release`. Exit-ramp cost: ~30 minutes, one PR. The release branch tagging + force-with-lease invariants are unchanged either way.
- **R4. Sha-pin discoverability for archaeology.** A consumer reading `marketplace.json` sees a 40-char SHA with no semantic. To map sha → release version, they need to query `gh release view` against the release tag, or read commit history. Mitigation: release-publish workflow already creates a `v0.x.y` tag pointing at the release branch HEAD; sha and tag are 1:1 within a release.
- **R5. Phase-3 adversarial may be over-trusted in future /decision runs.** The credibility hit from this episode is small (one falsified reshape) but real. Mitigation: the lessons.md entry surfaces "cheap-probe-first" as a heuristic for future /decision runs; convergence-note phase should explicitly call out probe-cost vs adversarial-strength trade and recommend probe-first when the cost ratio is favorable.
