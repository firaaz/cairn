# Phase 0.5 Journey — Consumer Payload Delivery End-to-End

## Stage 1: Discovery — Consumer hears about Cairn

**First action:** Consumer reads `README.md` or project documentation directing them to cairn. They encounter:
- **Artifact**: `https://github.com/firaaz/cairn` (homepage in `README.md:5`).
- **What they need**: The repository URL and knowledge that installation happens via Claude Code's plugin system.
- **Boundary crossed**: GitHub discovery → local machine (consumer's Claude Code session).

## Stage 2: Marketplace add — Discovery to registration

**Command**: `/plugin marketplace add https://github.com/firaaz/cairn`

**On-disk effect** (empirically verified in sweep-notes.md §V-3 attempt 2):
- Anthropic's resolver clones the repository via HTTPS to `~/.claude/plugins/marketplaces/cairn-marketplace/`.
- Resolves `marketplace.json` at `.claude-plugin/marketplace.json` in the cloned tree.
- Registers the marketplace entry in `~/.claude/plugins/known_marketplaces.json`.

**Boundary crossed**: GitHub → local plugin cache (HTTPS clone). **Transport: works today (empirically confirmed, sweep-notes:271).**

**Manifest shape** (`.claude-plugin/marketplace.json:8-12`):
- `source: "url"` (amended from `"github"` in sweep-notes §V-3 attempt 1 falsification)
- `url: "https://github.com/firaaz/cairn.git"`
- `ref: "release"` (immutable payload reference; INV-012 binding)

## Stage 3: Plugin install — Payload resolver and transport protocol selection

**Command**: `/plugin install cairn@cairn-marketplace`

**Resolver behavior** (OPEN-QUESTION with empirical signal):

The manifest declares `source: "url"` + `url: "https://github.com/firaaz/cairn.git"`. Anthropic's resolver **observes the host is github.com** and routes to the github-source clone handler, which forces SSH-protocol clone (sweep-notes:276–277). **Transport failure documented in sweep-notes §V-3 attempt 2 falsification (lines 260–289):**
- Operator machine has no GitHub SSH key.
- Manual `git clone --branch release https://github.com/firaaz/cairn` succeeds (confirms HTTPS works, repo intact).
- Install fails: `git@github.com: Permission denied (publickey)`.

**What's empirically known vs. unknown:**

| Source Type | Host | Transport | Verified? | Evidence |
|---|---|---|---|---|
| `source: "url"` | `github.com` | SSH (forced by host-based routing) | YES | sweep-notes:260–289; issues #26588, #47088 (upstream unfixed) |
| `source: "url"` | non-github (S3/CDN/etc) | HTTP-fetch (hypothetical) | OPEN | Anthropic's marketplace has no examples; empirical test needed |
| `source: "git-subdir"` | `github.com` | ??? | OPEN | Anthropic's marketplace uses `git-subdir` against github.com + githubusercontent.com (sweep-notes:244; examples at `.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`); SSH vs. HTTPS unknown |
| `source: "git-subdir"` | non-github | ??? | OPEN | Same resolver behavior as above; unknown |

**Manifest on release branch:** Payload lands at `~/.claude/plugins/cache/temp_github_<id>/` (failed install) or `~/.claude/plugins/cache/<resolver-path>/` (successful install, hypothetically; not yet observed live). The manifest's `.claude-plugin/plugin.json` declares version `"0.1.0"` (sweep-notes.md §V-4, Check 2).

**Boundary crossed**: Local plugin cache → payload filesystem (resolver + git/HTTP transport). **Transport: BLOCKED for github.com SSH; unknown for alternatives.**

## Stage 4: Hooks register — Enforcement substrate activation

**Plugin installation success** (precondition: Stage 3 succeeds):

Resolver copies payload to the consumer's `.claude/plugins/` installation tree and registers hooks.

**Hooks shape** (`.claude-plugin/hooks-template.json`):
- `PreToolUse` on `Bash|Edit|Write` → `checks/reversibility-guard.sh` (destructive-op guard, ADR-append enforcement, env-file block).
- `PreToolUse` on `Write|Edit|MultiEdit|NotebookEdit` → `checks/role_guard.py` (role-based write-path enforcement, operator-envelope gate).
- `PostToolUse` on `Edit|Write` → `checks/reality-check.sh` (linting: ruff, jq validation).

**Enforcement activation:**
- Reversibility guard fires on first `Bash|Edit|Write` (role_guard.py checks happen in PreToolUse; postinstall_validate.py confirms this self-tests to green, sweep-notes.md:V-4, line 202).
- Operator envelope fires if `.claude/active-envelope.yaml` exists with `mode: operator` (checked in role_guard.py:82–100).

**Boundary crossed**: Consumer's hook filesystem → Claude Code session event stream. **Mechanism: plugin-registered hooks (Anthropic's hook system).**

## Stage 5: First slice run — Operator envelope and phase-based write-gating

**Consumer action**: `/plugin dispatch cairn-tdd-feature docs/plans/YYYY-MM-DD-<feature-id>.md`

**Dispatch invocation** (hypothetical — operator-envelope already fire-tested in postinstall_validate.py:57–109):
1. Phase 1 (phase-1-tdd, AGENT_ROLE="phase-1-tdd") → allowed writes to `.claude/skill-runs/<id>/intent.md` (role_guard.py:32–34).
2. Phase 2 (phase-2-tdd, AGENT_ROLE="phase-2-tdd") → allowed writes to `tests/`, `.claude/skill-runs/<id>/validation/` (role_guard.py:36–38).
3. Phase 3 (phase-3-tdd, AGENT_ROLE unset, envelope-driven) → allowed writes to paths matching `active-envelope.yaml:paths` regex list (role_guard.py:82–140; envelope shape at templates/active-envelope.yaml).
4. Phase 4 (phase-4-tdd, AGENT_ROLE="phase-4-tdd") → allowed writes to `.claude/skill-runs/<id>/integration/`, `.claude/handoff.md` (role_guard.py:39–41).

**Artifacts in consumer's `.claude/`:**
- `.claude/active-envelope.yaml` (consumer-created, operator-envelope gate; template: templates/active-envelope.yaml).
- `.claude/skill-runs/<feature-id>/` (phase outputs: intent.md, RED tests, source edits, sweep-notes.md).
- `.claude/envelope-grants.log` (optional; logged by role_guard.py when envelope permits a write, if CLAUDE_CODE_DEBUG or similar set — sweep-notes.md:V-5).

**Boundary crossed**: Dispatcher session → consumer session (artifact persistence, hook enforcement). **Mechanism: plugin-installed role_guard.py + active-envelope.yaml write-gate.**

## Stage 6: Update — Payload refresh

**Consumer action**: `/plugin update cairn@cairn-marketplace` (or equivalent refresh mechanism)

**Unknown behavior (OPEN-QUESTION):**
- Does the resolver re-clone from `release` (full fetch), or git-pull-rebase, or tarball-download?
- Does it preserve the consumer's `.claude/active-envelope.yaml`, `.claude/skill-runs/`, `.claude/handoff.md`?
- What if the consumer has modified cairn's source (e.g., local hook edits)? Conflict detection?

**Hypothesis (from plugin semantics):**
- Marketplace-add HTTPS clone worked (sweep-notes.md:271). If marketplace-add re-clones on update, and uses HTTPS for marketplace operations, then plugin-update likely clones fresh to `~/.claude/plugins/cache/<new-id>/` and swaps-in the new payload without colliding with consumer's `.claude/` dotfiles.

**Boundary crossed**: Local installed version → upstream release branch. **Transport: unknown; depends on update mechanism.**

---

## Boundary and Mechanism Summary

| Stage | Boundary | Mechanism | Status |
|---|---|---|---|
| 1 | Discovery (web) → GitHub URL | None (doc link) | Known |
| 2 | GitHub → local marketplace cache | HTTPS clone (Anthropic resolver) | PASS |
| 3 | Marketplace → payload install | Host-based routing + git-clone transport | **BLOCKED (github.com SSH) / UNKNOWN (other hosts, git-subdir)** |
| 4 | Payload → hook registration | Plugin hook-system registration (Anthropic's harness) | PASS (assumed; empirically self-tested in V-4) |
| 5 | Dispatch → consumer enforcement | AGENT_ROLE + operator-envelope write-gating | PASS |
| 6 | Consumer version → upstream version | Plugin update mechanism (unknown protocol) | **UNKNOWN** |

---

## Phase 2 Decision Axes

Each approach must have an explicit story for:

1. **Stage 3 resolution** — What transport bypasses the SSH-forcing behavior or avoids it entirely?
   - GitHub Releases tarball (`.tar.gz` URL): HTTP-fetch, no git clone needed?
   - Self-hosted artifact (S3/R2/CDN): No github.com host-based routing?
   - `git-subdir` source-type: Unknown resolver behavior; empirical test required?
   - SSH-key prerequisite: Falsifies zero-friction premise.
   - Upstream bug fix: Out-of-band, not portable.

2. **Stage 4 invariance** — Must hooks.json remain in `.claude-plugin/` at root, or can postinstall relocate/install them elsewhere?

3. **Stage 5 envelope portability** — Active-envelope enforcement shape is locked into role_guard.py:82–140 (YAML, pyyaml-parsing, `paths` key). Any source-type change must not break consumer-facing `.claude/active-envelope.yaml` shape.

4. **Stage 6 update stability** — Consumer's `.claude/skill-runs/`, `.claude/handoff.md`, and local modifications must survive update. Any payload transport must preserve consumer's `.claude/` dotfiles.

5. **INV-012 binding** — Tests in `tests/unit/test_marketplace_schema.py` (5 assertions, all currently GREEN) assert `ref: "release"` immutability. New transport must not break this invariant or redefine `ref:` semantics.

6. **Release-publish workflow** — `.github/workflows/release-publish.yml` pushes to `release` branch with force-with-lease, produces v0.1.0 tag. Update approach must maintain tag/branch authority.
