# Phase 5 — Reconciliation Note

Phase 5 (independent verification, fresh-context blind agent) ran 2026-05-08 and converged on a direction. This note compares Phase 5's pick to the post-Phase-3 corrections-applied direction.

## Matches

- **Marketplace-paired single-repo plugin.** Both Phase 5 and the convergence land on cairn shipping `.claude-plugin/marketplace.json` co-located with the plugin payload in the cairn repo. ✓
- **`hooks/hooks.json`** as the hook registration mechanism, using `${CLAUDE_PLUGIN_ROOT}` substitution. ✓
- **CONSUMER.md** for the audience split. ✓
- **Path B for cairn-the-repo self-consumption** — `.slice-system → .` self-symlink retained. Phase 5 reached this via Pre-mortem #3 (bootstrap circularity tax under Path A); convergence reached it via the same Path-A risk. ✓
- **`role_guard.py:28` fix** — anchor `CAIRN_ROOT` on `$CLAUDE_PROJECT_DIR` instead of `__file__`. Phase 5 named this as the single most load-bearing claim that the lead's synthesis must also contain. ✓ Convergence has it.

## Divergence: payload curation

| Direction | Phase 5 (independent) | Post-Phase-3 convergence |
|---|---|---|
| Curation | Full-repo-minus-internals (per brainstorm #4) | Curated `dist/` subdir built by CI from allow-list |
| Mechanism | Phase 5 did not verify whether plugin manifest supports include/exclude fields | Phase 3 verified it does NOT (`code.claude.com/docs/en/plugins-reference`) |

**Reconciliation:** Phase 5 used the brainstorm's looser specification because they didn't run the Phase 3 mechanism check. The actual plugin system has no manifest-level filter, so curation requires physical separation. The corrected curated-`dist/` direction stands; Phase 5 would agree with it given the mechanism evidence.

## Phase 5's honestly-flagged unknowns — resolved

### Unknown 1: hooks/hooks.json auto-register vs consumer settings.json merge

**Resolved.** Direct WebFetch of `code.claude.com/docs/en/plugins-reference` confirms:
- Line 85: "Location: `hooks/hooks.json` in plugin root, or inline in plugin.json"
- Line 671: plugin layout shows `hooks/hooks.json` at plugin root
- No mention of consumer settings.json merge for plugin hooks

Hooks load directly from the plugin's `hooks/hooks.json` once the plugin is enabled. NO consumer settings.json edits required.

Phase 5's recommendation of a "30-min throwaway-plugin smoke test before locking design" is still sound — F1 should include this as a smoke-test gate before announcing M5 ships.

### Unknown 2: `${CLAUDE_PLUGIN_ROOT}` runtime env var vs string substitution

**Resolved.** WebFetch line 542: "`${CLAUDE_PLUGIN_ROOT}`: the absolute path to your plugin's installation directory. Use this to reference scripts, binaries, and config files bundled with the plugin."

It's a substitution variable (resolved before exec) — same pattern as `${CLAUDE_PLUGIN_DATA}`, `${user_config.*}`, and `${ENV_VAR}` (line 320). Hook command strings substitute it at registration; the running script doesn't see it as a runtime env var.

## Phase 5's notable divergence-risk flag

> "I did NOT pick Path A (cairn-installs-itself-as-plugin). If the lead converged on Path A, that's a real disagreement."

The convergence agrees: cairn-the-repo stays on Path B per assumption #5. No disagreement.

## Verdict

**Convergence is verified.** Both lead and independent-verification routes reach the same direction on every load-bearing axis. The single divergence (curation) reduces to a mechanism finding Phase 5 didn't run — when shown the evidence, Phase 5's direction collapses onto Phase 3's correction. The ADR can proceed with high confidence.
