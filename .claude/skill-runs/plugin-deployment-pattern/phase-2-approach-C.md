# Phase 2 — Approach C: git-subdir against tag (with optional release-branch anchoring)

Author: Phase-2 sub-agent C (Plan), 2026-05-09. Persisted by lead.

## Synopsis

**Recommended configuration: Approach D — `git-subdir` source pinned to `source.ref: "v0.x.y"`, with the tagged commit anchored on a long-lived `release` branch.** The naming "Approach D" is deliberate: the operator-named "GitHub release + git-subdir" was mechanism-ambiguous (Phase-0 conflict C2; Phase-0.5 §1.C′; Phase-0 constraint 17 — no release-archive `source.source` value exists). Re-grounding "Approach C" onto the closest documented mechanism — `git-subdir` against a tag — produces two configurations:

- **C-detached.** Tagged commit reachable only by tag; no branch carries it. Bears S6 (detached-commit ergonomics).
- **C-anchored ≡ Approach D.** Tag points at HEAD of a long-lived `release` branch; both exist; branch keeps commit reachable; tag is what consumers pin. Dissolves S6.

I recommend **Approach D** because (a) S6 is unforced loss under C-detached for no compensating gain, (b) D dominates A on S2 (default-branch trap) because `git-subdir` source decouples plugin-source resolution from marketplace's clone ref, and (c) D dominates A on S7 footgun-readability (`ref: "v0.x.y"` reads as a pin; `ref: "release"` reads as a moving target).

## Concrete shape

### marketplace.json (lives on `dev`, default branch unchanged)

```json
{
  "name": "cairn-marketplace",
  "owner": { "name": "firaaz" },
  "plugins": [
    {
      "name": "cairn",
      "description": "TDD-by-construction dispatch skill, hooks, and protocols for Claude Code.",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/firaaz/cairn.git",
        "path": "dist",
        "ref": "v0.1.0"
      }
    }
  ]
}
```

Decisive shape elements vs today's manifest:
- Discriminator field renamed `type` → `source` (constraint 12; Phase-0.5 Evidence 1).
- Discriminator value `"git"` → `"git-subdir"` (constraint 12, 14).
- `path: "dist/"` → `path: "dist"` (no trailing slash; documented form per Evidence 2).
- New required field `ref: "v0.1.0"` — explicit tag pin per D2 and S7 mitigation.
- No `sha` — tag is the readable pin.

### dist/.claude-plugin/plugin.json (lives on tagged commit, on `release` branch)

Plugin.json's `version` field MUST equal the tag's `v` prefix-stripped form. Per Phase-0.5 Evidence 9, plugin.json wins silently over marketplace.json plugin entry. So marketplace entry need NOT carry `version` — `source.ref` is consumer's pin handle; `dist/.claude-plugin/plugin.json:version` is the cache key.

`scripts/build_dist.py:30` copies `plugin-template.json` → `dist/.claude-plugin/plugin.json` verbatim. CI bumps the template before building.

### CI workflow `.github/workflows/release.yml` (NEW)

```yaml
name: release

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 0.1.0)'
        required: true
        type: string

concurrency:
  group: release
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: true

      - name: Install uv
        uses: astral-sh/setup-uv@v3
      - name: Sync project venv
        run: uv sync

      - name: Resolve version
        id: ver
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "version=${{ inputs.version }}" >> "$GITHUB_OUTPUT"
            echo "tag=v${{ inputs.version }}" >> "$GITHUB_OUTPUT"
          else
            ref="${GITHUB_REF#refs/tags/}"
            echo "tag=$ref" >> "$GITHUB_OUTPUT"
            echo "version=${ref#v}" >> "$GITHUB_OUTPUT"
          fi

      - name: Bump plugin-template version
        run: |
          uv run python scripts/bump_plugin_version.py \
            --template .claude-plugin/plugin-template.json \
            --version "${{ steps.ver.outputs.version }}"

      - name: Build dist payload (into worktree dist/)
        run: uv run python scripts/build_dist.py --repo-root . --dist-root ./dist

      - name: Run dist-gate equivalents
        env:
          CLAUDE_PLUGIN_ROOT: ./dist
        run: |
          uv run pytest tests/unit/test_build_dist.py -q
          uv run python scripts/postinstall_validate.py

      - name: Configure git identity
        run: |
          git config user.name "cairn-release-bot"
          git config user.email "release@cairn.invalid"

      - name: Materialize release branch + commit dist payload
        run: |
          set -euo pipefail
          if git ls-remote --heads origin release | grep -q release; then
            git fetch origin release:release
            git checkout release
            git merge --no-ff --no-edit "$GITHUB_SHA"
          else
            git checkout -b release
          fi
          git add dist/ .claude-plugin/plugin-template.json
          git commit -m "chore: release ${{ steps.ver.outputs.tag }} dist payload from ${GITHUB_SHA::7}" \
            -m "Bumps dist/.claude-plugin/plugin.json to ${{ steps.ver.outputs.version }}." \
            -m "Auto-generated by release.yml; tag: ${{ steps.ver.outputs.tag }}."

      - name: Tag the release commit (idempotent)
        run: |
          if git rev-parse "${{ steps.ver.outputs.tag }}" >/dev/null 2>&1; then
            test "$(git rev-parse '${{ steps.ver.outputs.tag }}')" = "$(git rev-parse HEAD)"
          else
            git tag -a "${{ steps.ver.outputs.tag }}" -m "Release ${{ steps.ver.outputs.tag }}"
          fi

      - name: Push release branch and tag
        run: |
          git push origin release
          git push origin "${{ steps.ver.outputs.tag }}"

      - name: Open PR to bump marketplace.json source.ref on dev
        uses: peter-evans/create-pull-request@v6
        with:
          base: dev
          branch: release-bot/bump-marketplace-${{ steps.ver.outputs.tag }}
          title: "chore: bump marketplace.json source.ref to ${{ steps.ver.outputs.tag }}"
          commit-message: |
            chore: bump marketplace.json source.ref to ${{ steps.ver.outputs.tag }}
          body: |
            Auto-generated by release.yml after publishing tag ${{ steps.ver.outputs.tag }}.
            Bumps `.claude-plugin/marketplace.json` `plugins[0].source.ref` to the new release tag.
          add-paths: .claude-plugin/marketplace.json
```

The bump-marketplace-PR step closes S4 two-step coupling: same release run that pushes the tag also opens the PR bumping `dev`'s marketplace.json. New helper `scripts/bump_plugin_version.py` (~20 lines, stdlib + typer).

**Decision point: does the tag move?** Two implementation choices:
- **Choice 3a — manual workflow_dispatch (RECOMMENDED).** Tag stays where maintainer pushed it. CI runs only on dispatch, after maintainer tags. Honors tag-immutability hygiene.
- **Choice 3b — auto tag-trigger.** CI re-points tag onto release-branch HEAD on tag-push. Tag-mutation, violates immutability hygiene.

I recommend **Choice 3a**.

### Maintainer-side release flow (literal)

1. On `dev`: confirm dist-gate green.
2. Create and push tag: `git tag -a v0.1.0 -m "Release v0.1.0" && git push origin v0.1.0`.
3. Run workflow_dispatch with `version: 0.1.0`. CI builds, commits to `release`, tags, pushes.
4. CI opens auto-PR to `dev` bumping `marketplace.json:source.ref`.
5. Maintainer reviews and merges PR.
6. Update CHANGELOG.md / handoff.md.

### Consumer-side install flow (literal)

```
/plugin marketplace add https://github.com/firaaz/cairn
/plugin install cairn@cairn-marketplace
```

**Same literal commands as today's `README.md:19` and `CONSUMER.md:14`.** No `@ref` qualifier; default branch (`dev`) carries marketplace.json which points at `git-subdir` ref `v0.x.y`. Plugin source resolution decoupled from marketplace clone ref (key D win vs A).

## Constraint fit

- **Phase-0 constraint 7 (D2 explicit semver-via-tags).** **Most natural fit of any approach.** D2 reads "tags follow `v0.x.y`; consumers pin via `marketplace.json` `source.ref` (tag) or `source.sha` (commit)." D's `source.ref: "v0.x.y"` is verbatim instantiation.
- **Constraint 12 (git-subdir documented schema).** Verbatim per Phase-0.5 Evidence 1.
- **Constraint 14 (sparse-clone bandwidth).** Phase-0.5 Evidence 2: "minimizing bandwidth for large monorepos."
- **Constraint 17 (no release-archive source-type).** Accepted re-grounding.
- **D2/D3/D8/D9 binding.**
  - **D2 (semver-via-tags):** verbatim instantiation.
  - **D3 (curation by physical separation):** `dist/` is same allow-list; lives on `release`'s tagged commit.
  - **D8 (cairn-self stays Path B):** unaffected — default branch stays `dev`. **Decisive win over Approach A's most-direct S2 fix.**
  - **D9 (M5+M6 atomic):** F3 check 9 unblocks.

## Pre-mortem scenario defense

### S1 — Schema-parse failure (CRITICAL, baseline)
**Defense.** marketplace.json rewrite to `source.source: "git-subdir"`. Same cost as A and B; structural prerequisite.

### S4 — Two-step release coupling (HIGH) — **Borne by C/D**
**Defense:**
1. **Same-CI-run coupling.** `release.yml` does both: pushes tag + `release` AND opens auto-PR bumping marketplace.json. Maintainer merges one PR — one click.
2. **Release-checklist gate.** CI job firing on PR-merge to `dev` from release-bot branch asserts `marketplace.json:source.ref` matches most-recent tag (`git describe --tags --abbrev=0`). Fails if diverge >1 commit.
3. **Optional aggressive variant** — CI commits marketplace.json bump directly to `dev` (not via PR). Eliminates human-merge but conflicts with force-push hygiene. Recommend PR approach.

C/D's coupling is **2-way** (tag + marketplace.json), one position better than B's **3-way**. `dist/.claude-plugin/plugin.json:version` is bumped in same commit as tag (lives on release's tagged commit) — no separate alignment.

### S5 — INV-001 commit-prefix binding (HIGH, all)
**Defense.** Commit message in "Materialize release branch" step starts with `chore:`. Verified `chore:` in `_FALLBACK_REGISTRY` (`validate_architecture.py:279`). Marketplace-bump commit also `chore:`-prefixed.

### S6 — Detached-commit ergonomics (MEDIUM, C-detached only)
**Decisive scenario for C-detached vs D ranking.**

- **C-detached:** `git branch --contains v0.1.0` returns empty. Future maintainer doing `git log dev` doesn't see release commits. `git gc --prune` could prune orphan if tag deleted (very unlikely accident, but footgun). Network-shallow-clone consumers may fetch defaults that don't include tag.
- **D:** `release` branch keeps tagged commit reachable via `git fetch` defaults. `git log release` shows full release history. Future-maintainer archaeology trivial.

Cost of D over C-detached: one long-lived branch named `release`. Refs surface gains one entry. Tiny tax for meaningful ergonomics win. **Recommendation: D dissolves S6.**

### S7 — D2 stability stance violated by ref-omission (HIGH)
**Defense.** marketplace.json **always** carries `source.ref: "v0.x.y"`. Three layers:
1. **Schema lint.** New `tests/unit/test_marketplace_schema.py` asserts `plugins[0].source.ref` non-empty and matches `r"^v\d+\.\d+\.\d+$"`. dist-gate.yml runs every PR.
2. **Documented prominently.** CONSUMER.md callout warning open-source-fork case.
3. **Release CI sets the ref.** Auto-PR generates new marketplace.json with new tag — no human-typed-ref path.

### S8 — Schema breaking change upstream (MEDIUM)
**Defense.** Same as A/B: monitor changelog. C/D's schema surface (`source.source: "git-subdir"` + 4 fields) is small.

### S10 — Engagement with synthesis question

Phase 1 S10: "test whether C-without-release-branch is workable. If not, propose Approach D."

**Honest answer:**
- **C-detached IS workable.** `git fetch --depth=1 origin tag v0.1.0` retrieves tag-only commits. **Not empirically verified against Claude Code's actual `git-subdir` resolver** — Phase 3 should verify.
- **C-detached has no unique advantage.** Only "one fewer branch" — cosmetic gain at S6 cost.
- **D is NOT structurally identical to A.** A pins to *branch HEAD* (moves with each release-branch advance); D pins to *specific tag* (immutable until marketplace.json bumped). Artifact-side overlap (release branch + tagged commits + curated `dist/`) is real; consumer-side semantics distinct: **D honors D2 ("consumers pin via tags") more directly than A.**

**Therefore: Approach D dominates A and C-detached.** Bears S4 + S5 (same as B and C); dissolves S2, S6, S9. Vs A wins on S2 and S7. Vs B wins on S3 and version-alignment surface (2-way vs 3-way).

### Defended-vs-residual summary

| Scenario | C-detached | D (C-anchored) | Notes |
|---|---|---|---|
| S1 (schema-parse) | defended | defended | structural prereq, paid identically |
| S2 (default-branch trap) | defended | defended | git-subdir decouples |
| S3 (npm prereq) | n/a | n/a | no npm |
| S4 (two-step coupling) | defended (auto-PR + checklist) | defended (same) | residual: human merge |
| S5 (INV-001 prefix) | defended | defended | verified |
| S6 (detached-commit) | borne | dissolved | the C-detached vs D split |
| S7 (D2 ref-omission) | defended | defended | three-layer |
| S8 (upstream schema) | residual | residual | small surface |
| S9 (cairn dogfood) | defended | defended | dev unchanged; D8 unaffected |
| S10 (synthesis) | offers nothing unique | recommended | propose D |

## Downstream impact

### CONSUMER.md / README

**Literal consumer commands DO NOT change.** Major win over A. Phase-0.5 boundary B1 scoring "clean."

What changes:
- CONSUMER.md callout: "cairn ships pinned to `v0.x.y` tags."
- CONSUMER.md prerequisites stay at jq + ruff. **No npm vs B; no submodule literacy vs A heavier variants. Smallest consumer-prereq footprint.**
- New `docs/release-process.md` (maintainer-only).

### Tag-discovery ergonomics

`git tag -l 'v*'` lists releases. `git log release` shows chronological history. `git log v0.1.0..v0.1.1 -- dist/` shows what changed in payload between releases.

### F3 audit check 9

Unblocks. Same fresh-consumer flow.

### Vision #1 — Windsurf portability

**Honest finding: `git-subdir` is Anthropic-specific.** But artifact (directory tree at tag) is consumable by any tool. Roughly tied with A on portability; better than B on cairn-identity preservation.

## Honest negative consequences

- **Tag-creation discipline.** Every release is manual tag-push. Mitigation: "needs release tag" CI label.
- **Release-CI complexity.** ~120 lines YAML + ~20 lines Python. Tested once; runs without intervention. Roughly equivalent to A's release-CI; tag-creation choreography pays for tag-pin advantage.
- **Detached-commit-or-release-branch decision.** Resolved by recommending D. Mitigation if abandoned: branch protection on `release`.
- **Two-place version discipline.** `plugin.json:version` AND tag name (`v0.x.y`) must match. CI ensures via shared source. Add CI assertion comparing on every `release.yml` run.
- **`marketplace.json:source.ref` is consumer-visible state on `dev`.** Every release produces commit on `dev` bumping this. "Noise" vs hypothetical world where marketplace lives on `release`. Trade-off: noise in exchange for D8 preservation + no `@ref` qualifier requirement.
- **Tag-mutation hazard if Choice 3b chosen.** Recommend Choice 3a.

## Cross-approach comparison hooks

| Axis | A | B | C-detached | D |
|---|---|---|---|---|
| Default-branch friction | awkward (S2) | clean | clean | clean |
| Release-CI complexity | medium | medium | medium | medium-high (~10% more YAML than A) |
| Consumer prereqs | jq, ruff, git | jq, ruff, **npm**, network to npm | jq, ruff, git | jq, ruff, git |
| D2 fit | indirect (branch HEAD pin) | indirect (npm version) | **direct** (tag pin) | **direct** (tag pin) |
| S6 (detached commits) | n/a | n/a | bears | dissolves |
| S9 (cairn dogfood) | bears | clean | clean | clean |
| Schema-rewrite work | yes | yes | yes | yes |
| F3 check 9 unblock | yes | yes | yes | yes |
| Windsurf portability | medium | medium | medium | medium |

**D is strongest candidate.** Tied or better than A on every axis; dominates B on consumer-prereqs and version-alignment; dominates C-detached on S6.

## What this approach proposes Phase 0/0.5/1 didn't anticipate

Phase-0.5 Gap 11 surfaced "Cross-cutting Approach D: combination/hybrid not enumerated." Phase 1 S10 explicitly invited proposal.

**This plan formally proposes Approach D** with one specific mechanism choice Gap-11 did NOT specify: **marketplace.json `source.source` is `git-subdir`, not `github`.** The Gap-11 framing was "marketplace.json points at `release` branch HEAD"; this plan refines to "marketplace.json points at a specific tag via `git-subdir`." Distinction matters: Gap-11's framing inherits A's "consumer pin moves with release-branch advance"; this plan keeps consumer pin immutable until marketplace.json bumped.

**Two further refinements:**
1. **Manual-dispatch-after-tag (Choice 3a)** vs auto-tag-trigger. Recommend 3a for tag-immutability hygiene.
2. **CI auto-PR for marketplace.json bump** as S4 mitigation. Phase 1 S4 said "single CI workflow OR checklist gate." This plan picks **both** — same-CI-run auto-PR (closing gap to one merge click) AND checklist-gate validator (catching divergence if PR sits unmerged).

End of Phase 2C / Approach D proposal.
