# D1.2 — Superpowers SessionStart Hook Override: Deferred

**Date:** 2026-04-11
**Status:** Deferred — no working per-project override in Claude Code 2.1.101
**Related:** `docs/plans/2026-04-11-context-discipline-design.md` D1.2; `docs/plans/2026-04-11-d1-floor-cuts-plan.md` Task 5

## Problem

The `superpowers` plugin's `SessionStart` hook (`~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.7/hooks/session-start`) injects the full `using-superpowers` SKILL.md into every session's context wrapped in an `<EXTREMELY_IMPORTANT>` block. Measured at ~1,140 tokens per session. The content is redundant — the skill is already listed in the `Skill` tool metadata.

## Investigation

Searched the Claude Code 2.1.101 binary (`/Users/mohammed.farook/.local/share/claude/versions/2.1.101`, 201 MB Mach-O arm64) for known settings keys that would support disabling a plugin-defined hook from user or project settings:

- `disabledHooks` — 0 hits
- `disableHooks` — 0 hits
- `disablePlugins` — 0 hits
- `pluginHookOverrides` — 0 hits
- `suppressHooks` — 0 hits

The plugin hook is defined in `hooks/hooks.json` inside the plugin cache and runs whenever the plugin is enabled. There is no user-space mechanism to disable the hook while keeping the plugin's skills available.

## Options considered

1. **Disable the `superpowers` plugin entirely in cairn** — rejected. Cairn needs the superpowers skills (brainstorming, TDD, systematic-debugging, executing-plans, subagent-driven-development) for the protocol work in Slice #2 and beyond. Losing all skills to save 1,100 tokens is a bad trade.

2. **Fork the plugin with a no-op SessionStart hook** — rejected for D1. Maintenance burden, and the fork needs to be re-synced on every upstream update. Not appropriate for a reversible floor-cut change.

3. **Replace `hooks/session-start` in the plugin cache with a no-op** — rejected. Direct edits to plugin cache files are reverted on plugin update and leave no breadcrumb when they break. Fragile.

4. **Upstream request** — pending. File an issue/PR on the superpowers repository asking for either (a) a "minimal SessionStart" mode that outputs only a one-line "superpowers skills available via Skill tool" reminder, or (b) a plugin-config opt-out. This is the correct long-term path.

5. **Accept the ~1,100 tokens as unfixable until upstream supports it** — chosen. Document the trade, measure without the cut, and revisit when upstream or Claude Code exposes a mechanism.

## Decision

D1.2 is deferred. The D1 ship-set (Tasks 1–4 in the implementation plan) proceeds without it. Expected D1 savings are revised downward from ~2,700–3,400 tokens to **~1,600–2,300 tokens** (CLAUDE.md trim + global plugin relocation, minus D1.2).

## Revisit criteria

Revisit this deferral when any of the following is true:

- Claude Code exposes a settings key that lets a user or project disable a specific plugin hook.
- The superpowers upstream repo exposes a plugin-config opt-out or a minimal-mode SessionStart.
- The measured cost of the injection rises materially (e.g., the `using-superpowers` SKILL.md grows past 2,000 tokens).
- Cairn ships its own protocol work that conflicts with the injection (unlikely, but possible).
