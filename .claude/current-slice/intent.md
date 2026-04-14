---
slice: feature-slice-model
date: 2026-04-14
phase: 1-intent
invariants-touched: [INV-006, INV-007]
adrs-referenced: [ADR-006, ADR-008]
envelope:
  - "commands/claude-code/start-slice.md"
  - "commands/claude-code/start-slice.full.md"
  - "commands/claude-code/handoff.md"
  - "commands/claude-code/handoff.full.md"
  - "commands/claude-code/catchup.md"
  - "commands/claude-code/catchup.full.md"
  - "checks/scope-guard.sh"
  - "templates/handoff.md"
  - ".claude/features/*.yaml"
  - "tests/unit/test_feature_*.py"
out-of-scope:
  - "Parked-state protocol (ADR-006 D6) — separate slice"
  - "Mid-work discovery protocol (ADR-006 D7) — separate slice"
  - "Status derivation logic (ADR-006 D4 is a convention, not validator code)"
  - "Feature auto-close or lifecycle management"
  - "Retroactive migration of completed slices SLICE-001 through SLICE-008"
  - "validate_architecture.py changes"
---

### What and Why

Cairn currently has no structured decomposition artifact. Multi-slice work decomposes in the operator's head; slice-to-slice ordering lives in handoff prose; and `handoff.md` carries both cross-session pointers (its ADR-002 Layer 1 role) and implicit decomposition state. ADR-006 and ADR-008 defined the feature-slice information model and its context-tier integration. This slice implements the core model: feature file creation, skill integration at trigger points, scope-guard allowlisting, and the cross-feature index in `handoff.md`.

### Specification Detail

**Feature file schema** (ADR-006 D1, D2):
- Path: `.claude/features/<id>.yaml` where `<id>` is a semantic kebab-case identifier (ADR-005).
- Required fields:
  - `id`: string, matches the filename stem
  - `intent`: string, one-sentence description of the feature's purpose
  - `created`: date in YYYY-MM-DD format
- Optional field:
  - `slices`: list of slice entries, each with:
    - `id`: string (required) — the slice's semantic kebab-case ID
    - `after`: list of slice IDs this slice depends on (optional, default empty)
    - `added`: date in YYYY-MM-DD (required on every entry)
    - `status`: only legal value is `dropped` (optional; absence = not dropped)
    - `reason`: string (optional; only meaningful when `status: dropped`)
- No narrative prose in feature files — structured plan only.
- Dropped slices stay in the file with `status: dropped`; they are never deleted (append-only spirit).

**Always-create policy** (ADR-006 D3):
- Every new slice gets a feature file, even single-slice features. `/start-slice` must create a feature file if one does not already exist for the current feature.
- Eliminates the routing question "is this big enough for a feature file?"

**Trigger-based updates** (ADR-006 D5):
- No background sync. Each event updates a bounded set of files (max 2 per event).
- `/start-slice` (new slice): creates or updates the feature file + creates `slice.yaml`. If a feature file already exists for the feature, adds a new slice entry to it.
- `/handoff`: updates `handoff.md` with cross-feature index. If decomposition changed during the session, prompts operator to update the feature file.
- `/catchup` Tier 1: reads cross-feature index from `handoff.md`. Does NOT load feature files at Tier 1.

**Cross-feature index in handoff.md** (ADR-008 D0, D1):
- `handoff.md` gains a `## Features` section containing one line per active feature: `- <feature-id>: <status-summary>` (e.g., `- feature-slice-model: SLICE-009 active, phase intent`).
- Each line is ~15–25 tokens. At v1 scale (2–5 features), the index adds 30–125 tokens — within ADR-002's 150–400 token budget.
- The handoff template (`templates/handoff.md`) is updated with the `## Features` section.

**Feature file as Tier 2 on-demand read** (ADR-008 D0):
- `/catchup` loads feature files only under existing Tier 2 admission criteria — when entering a feature's work or verifying decomposition state before acting.
- Feature files are never loaded in Tier 1 regardless of how many features are active.

**scope-guard update:**
- `.claude/features/*.yaml` is added to the always-allowed write paths (same category as `.claude/current-slice/`, `.claude/handoff.md`, `.claude/sweep.yaml`).

### Boundary

- **D6 (parked state):** Not implemented. Slice entries can carry `after` fields but the park/resume workflow is a separate slice.
- **D7 (mid-work discovery):** Not implemented. The three discovery scenarios are protocol guidance, not code — they will be added to skill prose in a separate slice.
- **D4 (status derivation):** This is a design convention (status derived from git state, not stored). No validator or tool changes needed in this slice. The one stored exception (`status: dropped`) is part of the feature file schema above.
- **No feature lifecycle management:** Features don't auto-close. Manual close is the v1 policy.
- **No retroactive migration:** Slices SLICE-001 through SLICE-008 are not retroactively assigned to features.

### Verification

1. **Feature file creation:** After running `/start-slice` for a new slice, `.claude/features/<id>.yaml` exists with all required fields (`id`, `intent`, `created`) and a `slices` list containing at least one entry with `id` and `added` fields.
2. **Always-create:** Even a single-slice feature produces a feature file — no conditional "too small to need one" path.
3. **Existing feature update:** Running `/start-slice` for a second slice within the same feature adds a new entry to the existing feature file's `slices` list without destroying existing entries.
4. **Cross-feature index:** After running `/handoff`, `handoff.md` contains a `## Features` section with one line per active feature. The section is absent or empty when no features are active.
5. **Tier 2 gating:** `/catchup` Tier 1 reports active features from the handoff index. Feature file detail is NOT loaded in Tier 1 — only in Tier 2 under admission criteria.
6. **scope-guard:** Writes to `.claude/features/*.yaml` are allowed by `checks/scope-guard.sh` regardless of slice phase.
7. **Dropped slices:** A slice entry with `status: dropped` and `reason` field is preserved in the feature file; subsequent reads/updates do not remove it.
8. **Trigger discipline:** Feature file updates happen only at the events listed in D5 (start-slice, handoff, decomposition change). No polling, no background sync.
9. **Token budget:** The cross-feature index with 5 features stays under 125 tokens, keeping `handoff.md` within the 400-token ceiling.
