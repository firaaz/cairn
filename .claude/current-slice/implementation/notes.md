---
slice: compression/infrastructure
phase: 3-implementation
date: 2026-04-19
---

## Decisions and deviations

### D1 — Slash-command file convention forced legacy/start-slice composition

intent.md §4 specified `commands/claude-code/start-slice-legacy.md` as "archive of the current `start-slice.md` + `start-slice.full.md` content". Two test contracts blocked literal compliance:

- `test_progressive_disclosure.py::test_s1_lite_files_within_token_budget` — every non-`.full.md` file in `commands/claude-code/` ≤ 500 tokens. A full prose archive cannot fit.
- `test_progressive_disclosure.py::test_s3_load_full_predicates_resolve` — every lite file's `## Load full` section must reference an existing `.full.md` sibling (or say "no full form").

Resolution: `start-slice-legacy.md` became a thin (≤500 tokens) pointer file whose `## Load full` section delegates to the existing `start-slice.full.md` — the canonical pre-refactor prose protocol already lives there, no duplication needed. The "archive" requirement is materialised through reuse, not a second copy. Phase 4 V10 evidence reads against this composition (start-slice.md references `--legacy` + `CAIRN_LEGACY_START_SLICE`; start-slice-legacy.md exists; both point at the same prose protocol).

### D2 — `commands/claude-code/settings.json` is a methodology template, not a wiring file

The actual Claude Code settings path that fires hooks is `.claude/settings.json` (consumer-local). Slice A's envelope explicitly authorised `commands/claude-code/settings.json`, so the hook registration shipped there as a methodology-tier template. Consumers (and cairn's own `.claude/settings.json`) compose this template with their own preferences. Per intent's "AGENT_ROLE is unset during Slice A's own phases", role_guard.py is a no-op on Slice A regardless — Slice B's first compressed dispatch is the empirical activation check.

### D3 — Agent file bodies are loaded into session-start context

Empirical: stripping `.claude/agents/issue-triager.md` from 1827 to 157 chars dropped turn-1 tokens by ~150. So agent bodies (not just `description:` frontmatter) participate in the cached prompt. Each of the five agents was therefore tuned to be the tightest viable system-prompt — role identity, allow/deny lines, structured-return contract, no narrative — to keep INV-004's 30k turn-1 ceiling within reach.

### D4 — INV-004 turn-1 budget is borderline, with prompt-cache-driven variance

After the trim pass, `test_inv004_turn1_token_budget` measures 29,800–30,050 tokens depending on which Anthropic edge cache the session lands on (`cache_creation_input_tokens` vs `cache_read_input_tokens`). The 30,000 hard budget is sometimes a passing margin and sometimes a 25-token miss. Root cause: shipping five agent definitions plus a new slash command inherently grows the auto-loaded context surface.

This is a real, slice-attributable cost — not pre-existing — but the agent definitions are mandatory infrastructure the intent commits to. Two non-mutually-exclusive paths forward (Auditor's call):

- Treat the variance as acceptable noise around a budget that the slice deliberately approaches. Document the new floor in `architecture/INV-004` provenance as part of a future re-baselining ADR.
- Tighten further by removing one of the five agents (collapsing `issue-triager` into orchestrator code) or by trimming the agent bodies to ~300 chars each.

Either path is out-of-scope for Slice A under the "no ADR amendments" constraint and the spec-locked agent count. Logged here for Phase 4.

### D5 — `_current_phase` is module-replaceable

`run_phase_loop` reads the current phase via the module-level `_current_phase()` function rather than inlining the lookup. Tests rely on this seam (`monkeypatch.setattr(so, "_current_phase", lambda: 1, raising=False)`). Same pattern for `_slice_id` and `_dispatch_for_phase`.

### D6 — `target_phase` validation is strict per intent amendment B3

Per the handoff's noted spec amendment, `intent.md:90` "floor clamp" was superseded by strict `{1..max_phase}` validation. `run_phase_loop`'s RAISE_ISSUE → RE_DISPATCH branch refuses both `target_phase < 1` and `target_phase > max_phase`, returning non-zero in both cases. Tests `test_a6_target_phase_zero_returns_nonzero` and `test_a6_target_phase_out_of_bounds_returns_nonzero` cover the two ends.

### D7 — Bootstrap-safe coupling-clusters parser

`_parse_clusters` is a deliberately small line-parser, not a YAML import. CLAUDE.md mandates stdlib-only; the format expected by tests (one `- name:` per cluster with inline `files: [...]`) is well-defined enough that a 20-line parser suffices. Future Slice B may migrate to PyYAML if cluster schemas grow.

## Pre-existing failures (not slice scope)

Confirmed unchanged from `01ae938` baseline; called out in handoff:

- `tests/unit/test_adr_rename_sweep.py` — 2 tests
- `tests/unit/test_hook_relpath_bypass.py` — 3 tests
- `tests/unit/test_hook_tolerance.py` — 3 tests

Slice-attributable status: see D4.
