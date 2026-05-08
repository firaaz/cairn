---
id: cairn-m5-f2-consumer-doc-surface
name: Cairn M5 F2 — Consumer-doc surface
firmness: provisional
status: draft
date: 2026-05-08
scope: Consumer-doc surface — D6 audience model, D7 template extraction, README reading order, phase-skill-mapping promotion, adoptable-disciplines list
inputs:
  - docs/adr/m5-plugin-distribution-and-symlink-retire.md
  - docs/reviews/2026-04-23-from-portfolio-evaluation.md
  - .claude/skill-runs/m5-feature-plans/brief.md
  - docs/operational-reference.md
  - CLAUDE.md
  - README.md
  - templates/handoff.md
envelope:
  - ^docs/plans/2026-05-08-cairn-m5-f2-consumer-doc-surface\.md$
  - ^CLAUDE\.md$
  - ^CONSUMER\.md$
  - ^README\.md$
  - ^docs/phase-skill-mapping\.md$
  - ^docs/adoptable-disciplines\.md$
  - ^docs/operational-reference\.md$
  - ^templates/feature-plan\.md$
  - ^templates/intent\.md$
  - ^templates/sweep-notes\.md$
  - ^templates/adr-frontmatter\.yaml$
  - ^templates/active-envelope\.yaml$
  - ^templates/handoff\.md$
  - ^tests/unit/test_consumer_doc_surface\.py$
  - ^tests/unit/test_template_extraction\.py$
  - ^tests/unit/test_readme_reading_order\.py$
---

# Cairn M5 F2 — Consumer-doc surface

> **For agentic workers:** REQUIRED SUB-SKILL: this plan is the input to the `cairn-tdd-feature` dispatch skill (the four-phase pipeline). Within-feature parallelism via `superpowers:dispatching-parallel-agents` is permitted per CLAUDE.md "Within-slice parallel subagents are allowed" — Sections F2.2 (template extraction), F2.4 (phase-skill-mapping promotion), and F2.5 (adoptable-disciplines) are independent file-write tasks that can fan out in Phase 3. Sections F2.1 (CLAUDE.md `[both]` tags + CONSUMER.md authoring) and F2.3 (README reading order) have ordering constraints — see Architecture below.

**Goal:** Land cairn's consumer-facing documentation surface so a first-time external consumer can install the plugin (per F1's manifests), follow a reading order that does not dump them into `spec-v1.md` first, copy phase-boundary contract templates verbatim, and identify which standalone disciplines (handoff-as-pointer, the three hooks, the architecture validator, the phase-skill-mapping table) are portable without committing to the full four-phase methodology. Closes ADR `m5-plugin-distribution-and-symlink-retire` D6, D7, and portfolio-review Findings 1–5 (`docs/reviews/2026-04-23-from-portfolio-evaluation.md`).

**Architecture:** Five threads. **T1 — audience model (D6):** add `[both]`/`[maintainer]` tags to cross-cutting CLAUDE.md sections; author CONSUMER.md whose body cross-references CLAUDE.md `[both]` sections by anchor link rather than duplicating. **T2 — template extraction (D7):** add five new files under `templates/` covering every phase-boundary contract surface. **T3 — README reading order (Finding 2):** replace `README.md:31-37` unordered list with an explicit four-step order (README → CONSUMER.md → operational-reference.md → spec-v1.md). **T4 — phase-skill-mapping promotion (Finding 4):** lift `docs/operational-reference.md:141-174` to its own `docs/phase-skill-mapping.md`; leave a pointer behind. **T5 — adoptable-disciplines list (Finding 5):** author `docs/adoptable-disciplines.md` enumerating the four standalone-portable pieces. Sequencing: T4 lands **before** CONSUMER.md anchors stabilise (CONSUMER.md links it); T3 lands **after** CONSUMER.md exists (the reading order names it). T2 and T5 are independent.

**Tech Stack:** Markdown only (CLAUDE.md, README.md, CONSUMER.md, docs/*.md, templates/*.md). YAML for `templates/adr-frontmatter.yaml` and `templates/active-envelope.yaml`. Python 3.11 for the validation tests under `tests/unit/` (pyyaml + pathlib). No source code; no new hook; no Bash. uv-managed venv (`uv run pytest`).

## Self-review summary

Coverage map against ADR D6 + D7 and Findings 1–5 of `docs/reviews/2026-04-23-from-portfolio-evaluation.md`:

- **D6** → Sections F2.1 + F2.3 + F2.4 (file split + audience tags + reading order + cross-references).
- **D7** → Section F2.2.
- **Finding 1** (audience ambiguity) → F2.1 (the file-split + tag hybrid the finding's "at minimum" floor endorsed).
- **Finding 2** (no reading order) → F2.3.
- **Finding 3** (templates drop-off) → F2.2.
- **Finding 4** (phase-skill-mapping buried) → F2.4. Brief leaves own-doc vs. CONSUMER.md-section to this plan; chooses **own-doc** (`docs/phase-skill-mapping.md`) so the table is independently cherry-pickable by Superpowers-users without coupling to CONSUMER.md. CONSUMER.md cross-references it.
- **Finding 5** (adoptable-disciplines missing) → F2.5.

Gap surfaced during self-review (deferred to "Out-of-scope follow-ups"): a comprehensive doc-link validator. Risk-4 in the ADR's risk register names CLAUDE.md ↔ CONSUMER.md drift as residual; F2.6 ships a narrow anchor-resolution contract test, full validator deferred to M5.1.

---

## Section F2.1 — Audience model: `[both]` tags + CONSUMER.md (D6)

**Files touched:**
- Modify: `CLAUDE.md`
- Create: `CONSUMER.md`

**Why:** Per D6 and Finding 1, CLAUDE.md is currently maintainer-primary with no markers telling a first-time consumer which rules apply to them. The portfolio review's "at minimum" floor (`docs/reviews/2026-04-23-from-portfolio-evaluation.md:66`) endorses tagging cross-cutting rules; D6's "Easier" consequence notes the hybrid (split + tags) is strictly better than either alone.

### Tasks

- [ ] **Step 1 (Phase 2 — RED): contract test for `[both]` tag presence.** Author `tests/unit/test_consumer_doc_surface.py` with a test `test_claude_md_cross_cutting_sections_carry_both_tag()` that reads `CLAUDE.md` and asserts the lines naming the four cross-cutting sections — `## Identifier scheme`, `**Edit canonical paths only` (the safety-critical lead), `**Hook dependencies.**`, `**ADRs are append-only.**`, `**Force-push policy.**`, `**Operator envelope**` — each have a literal `[both]` token on the same line or the line directly above. Run; expect FAIL.

- [ ] **Step 2 (Phase 3 — GREEN): edit CLAUDE.md to add `[both]` tags.** For each cross-cutting heading/lead in CLAUDE.md, append ` [both]` (literal, bracketed). Specifically:
  - `## Identifier scheme` (CLAUDE.md:5) → `## Identifier scheme [both]`
  - `**Edit canonical paths only, never via .slice-system/.**` (CLAUDE.md:11) — note this rule is **maintainer-only** in spirit (the `.slice-system/` symlink is a maintainer-internal hazard); tag as `[maintainer]` per Finding 1's specific suggestion that `.slice-system` stripping be tagged maintainer-only. The contract test must accept either `[both]` or `[maintainer]` for this specific line.
  - `**Hook dependencies.**` (CLAUDE.md:13) → tag `[both]` (consumers also need `jq` + `ruff` per F1's post-install validator).
  - `**Symlink recursion hazard.**` (CLAUDE.md:18) → `[maintainer]` (consumers don't have `.slice-system → .` after F3).
  - `**ADRs are append-only.**` (CLAUDE.md:20) → `[both]` (consumers writing their own ADRs follow the same protocol).
  - `**Force-push policy.**` (CLAUDE.md:22) → `[both]`.
  - `**Operator envelope**` (CLAUDE.md:24) → `[both]`.
  - The remaining "New-code guidance" section (CLAUDE.md:26-32) stays untagged (defaults to maintainer-only — only relevant to writing new cairn code, not to consuming cairn). Add a one-line legend at the top of CLAUDE.md right under the title: `> Audience tags: [both] = consumers + maintainers; [maintainer] = cairn-internal. Untagged sections default to [maintainer].`
  - Run the Step 1 contract test; expect PASS.

- [ ] **Step 3 (Phase 3 — GREEN): author CONSUMER.md.** Create `CONSUMER.md` (repo root) with these sections, in order:
  1. **Title + tagline** — "Cairn — consumer entry doc."
  2. **What you get** — one paragraph naming what the plugin installs (skills, agents, hooks, templates) and what it doesn't (slash commands deferred to M5.1 per ADR D3).
  3. **Install (quickstart)** — the two-line install flow from D1; note that F1's post-install validator exits non-zero if `jq`/`ruff` missing; cross-link `CLAUDE.md#hook-dependencies-both`.
  4. **First dispatch in 10 minutes** — walk-through: copy `templates/feature-plan.md` → `docs/plans/<feature>.md`, set `.claude/active-envelope.yaml` from `templates/active-envelope.yaml`, invoke `cairn-tdd-feature` via Skill tool, observe four commits.
  5. **The four phases** — one-paragraph summary; pointer to `docs/operational-reference.md` "The Four Phases".
  6. **The Phase Skill Guide** — two lines + pointer to `docs/phase-skill-mapping.md` (F2.4).
  7. **Cross-cutting rules consumers must follow** — bullet list of anchor links into CLAUDE.md `[both]` sections (identifier scheme, ADR append-only, envelope contract, force-push, hook deps). One line each, no duplicated prose.
  8. **Templates** — one-line bullet per `templates/*` file.
  9. **Troubleshooting** — minimum five entries: hooks silently no-op (deps); writes denied unexpectedly (envelope mode); Phase 3 can't find tests (Phase 2 commit not visible); ADR edit blocked (frontmatter-only); post-install validator fails (F1 cross-ref).
  10. **Where to next** — mirrors F2.3 reading order so the consumer can navigate forward.
  11. **Adoptable disciplines (no plugin install)** — pointer paragraph to `docs/adoptable-disciplines.md`.

  Word budget ≤ 1500; CONSUMER.md is a navigation doc, not an alternative spec.

- [ ] **Step 4 (Phase 2 — RED): cross-reference contract test.** Extend `tests/unit/test_consumer_doc_surface.py` with `test_consumer_md_anchors_resolve_into_claude_md()`: for every `CLAUDE.md#<anchor>` link in CONSUMER.md, assert the anchor exists in CLAUDE.md (use a slugify approximation: lowercase, replace spaces and `[`/`]` with `-`, strip non-alphanumeric except `-`). Run; expect FAIL until Step 3's anchors are stable.

- [ ] **Step 5 (Phase 3 — GREEN): make all anchor cross-refs resolve.** Iterate Step 3's CONSUMER.md or Step 2's CLAUDE.md tag forms until every anchor link in CONSUMER.md resolves to a real heading in CLAUDE.md. Run Step 4's test; expect PASS.

---

## Section F2.2 — Comprehensive template extraction (D7)

**Files touched:**
- Create: `templates/feature-plan.md`
- Create: `templates/intent.md`
- Create: `templates/sweep-notes.md`
- Create: `templates/adr-frontmatter.yaml`
- Create: `templates/active-envelope.yaml`
- Modify: `templates/handoff.md` (only if necessary to add a header pointing to the new sibling templates — per "no premature abstraction," only edit if the sibling-pointer materially improves discoverability; otherwise leave untouched).

**Why:** Per D7 and Finding 3, `templates/` currently holds only `handoff.md`. The portfolio review names templates as "exactly the part most valuable to copy." Each new file maps 1:1 to a phase-boundary contract surface in the dispatch skill.

### Tasks

- [ ] **Step 1 (Phase 2 — RED): existence + shape contract test.** Author `tests/unit/test_template_extraction.py` with one test per template, asserting:
  - File exists, non-empty (>200 chars).
  - `*.md` templates begin with a YAML frontmatter block; YAML templates parse cleanly.
  - `templates/feature-plan.md` frontmatter contains keys `id`, `envelope`, `firmness`, `status`, `date` (per operational-reference.md:39-46).
  - `templates/intent.md` body contains the four-zone literals "Zone 1", "Zone 2", "Zone 3", "Zone 4" (per Phase 1 rules).
  - `templates/sweep-notes.md` body contains `## Test results`, `## Validator results`, `## Invariant verification`, `## Adjacent code regression check` (per Phase 4 rules).
  - `templates/adr-frontmatter.yaml` contains keys `id`, `name`, `status`, `firmness`, `date`, `topic`, `invariants-touched`, `supersedes`, `superseded-by` (mirrors working ADR frontmatter).
  - `templates/active-envelope.yaml` has `mode: off` default, a `# paths:` commented-block example including the self-pattern `^\.claude/active-envelope\.yaml$`.
  Run; expect FAIL on all five.

- [ ] **Step 2 (Phase 3 — GREEN): author `templates/feature-plan.md`.** Skeleton with full frontmatter (`id`, `name`, `firmness: provisional`, `status: draft`, `date`, `scope`, `inputs:`, `envelope:` regex array with placeholder examples) + body sections **What/Why**, **Boundary**, **Specification**, **Verification** per operational-reference.md:39-46. Top HTML comment cross-references "Per-feature plan-doc shape" in operational-reference.md.

- [ ] **Step 3 (Phase 3 — GREEN): author `templates/intent.md`.** Frontmatter slot (`feature-id`, `as-of`, `phase: 1-intent`). Body has four zone headings (`## Zone 1: YAML envelope`, `## Zone 2: What / Why / Boundary`, `## Zone 3: Specification detail`, `## Zone 4: Verification`) each with a `<!-- -->` instruction comment. Top pointer to operational-reference.md Phase 1 rules.

- [ ] **Step 4 (Phase 3 — GREEN): author `templates/sweep-notes.md`.** Frontmatter slot (`feature-id`, `as-of`, `phase: 4-integration`, `verdict`). Body sections `## Test results`, `## Validator results`, `## Invariant verification` (one row per invariant with `file:line` citation evidence per Phase 4 rules), `## Adjacent code regression check`, `## Handoff append (optional)`.

- [ ] **Step 5 (Phase 3 — GREEN): author `templates/adr-frontmatter.yaml`.** Pure YAML matching the live shape at `docs/adr/m5-plugin-distribution-and-symlink-retire.md:1-11`. Comment lines name allowed values for each field (`status`, `firmness`, `topic`, `invariants-touched`).

- [ ] **Step 6 (Phase 3 — GREEN): author `templates/active-envelope.yaml`.** Default `mode: off` per D7. Commented-out example block shows `mode: operator` + `paths:` regex array including the self-pattern `^\.claude/active-envelope\.yaml$`. Top comment points to operational-reference.md "Operator envelope".

- [ ] **Step 7 (Phase 4 — verify): run Step 1's tests.** All five pass. Run `uv run pytest tests/unit/test_template_extraction.py -v`. Expect 5 PASSED.

---

## Section F2.3 — README reading order (Finding 2, D6)

**Files touched:**
- Modify: `README.md` (specifically lines 31-37, the "Documentation" section).

**Why:** Per Finding 2 and D6's reading-order bullet, the current `README.md:31-37` lists four docs without an order. The fix names CONSUMER.md as step 2 (must exist before this lands — sequencing constraint with F2.1).

### Tasks

- [ ] **Step 1 (Phase 2 — RED): reading-order contract test.** Author `tests/unit/test_readme_reading_order.py` with `test_readme_has_four_step_reading_order()`: read `README.md`, assert it contains a numbered list with at least four entries naming, in order, `README.md` (or "you are here"), `CONSUMER.md`, `docs/operational-reference.md`, `docs/spec-v1.md`. Run; expect FAIL.

- [ ] **Step 2 (Phase 3 — GREEN): rewrite `README.md` "Documentation" section.** Replace the current bulleted `docs/...` list with a "Reading order" block matching Finding 2:

  ```
  ## Reading order

  1. README.md (you are here) — what cairn is, at a glance
  2. CONSUMER.md — install, dispatch, troubleshooting (start here if consuming cairn)
  3. docs/operational-reference.md — how cairn works (Layer 1)
  4. docs/spec-v1.md — why cairn is shaped this way (Layer 2; pull in deliberately)

  ## Other docs

  - docs/why-cairn.md, docs/vision.md, docs/roadmap.md
  - docs/adoptable-disciplines.md — partial adoption menu
  - docs/phase-skill-mapping.md — phase → Superpowers skill map
  ```

  Update "How to consume cairn from another project" (`README.md:17-29`) to point at CONSUMER.md as the canonical install path post-F1. Keep the existing symlink instruction as a fallback with a one-line caveat; flag with `<!-- F1-followup: remove symlink path once plugin marketplace is stable; F3-followup: full removal after consumer migration. -->`

- [ ] **Step 3 (Phase 4 — verify): run Step 1's test.** Expect PASS.

---

## Section F2.4 — Phase-skill-mapping promotion (Finding 4, D6)

**Files touched:**
- Create: `docs/phase-skill-mapping.md`
- Modify: `docs/operational-reference.md` (replace `:141-174` "Phase Skill Guide" section with a 2–3 sentence pointer to the new file).

**Why:** Per Finding 4, the Phase Skill Guide is "the most portable idea and the hardest to find." This plan chooses **own-doc promotion** over CONSUMER.md-section promotion (see Self-review summary): a standalone `docs/phase-skill-mapping.md` is independently cherry-pickable by Superpowers users who want only this artefact and not the rest of cairn.

### Tasks

- [ ] **Step 1 (Phase 2 — RED): test for new file + operational-reference pointer.** Add to `tests/unit/test_consumer_doc_surface.py`:
  - `test_phase_skill_mapping_doc_exists()`: `docs/phase-skill-mapping.md` exists, contains the four canonical agent slugs (`phase-1-tdd`..`phase-4-tdd`), the four role names (Reader, Skeptic, Builder, Auditor), and the literal "Superpowers".
  - `test_operational_reference_phase_skill_guide_is_a_pointer()`: locate `## Phase Skill Guide` in operational-reference.md; assert section body ≤ 5 lines and contains link literal `docs/phase-skill-mapping.md`.
  Run; expect FAIL.

- [ ] **Step 2 (Phase 3 — GREEN): create `docs/phase-skill-mapping.md`.** Lift content from `docs/operational-reference.md:141-174` verbatim — role/anti-behavior table, phase-to-skill mapping, explicit-exclusions block. Top paragraph frames the doc as consumable standalone by Superpowers users without full cairn adoption (Finding 4 benefit). Preserve the operational-reference.md:142-143 binding-surface caveat: this section is the surface INV-003's `validate_phase_topology` regex-extracts from. **Risk flag (see Out-of-scope):** if `validate_architecture.py` hard-codes the source path, relocation needs a source-file edit not in this section's envelope — RAISE_ISSUE in Phase 1 intent if Phase 4 audit reveals it.

- [ ] **Step 3 (Phase 3 — GREEN): replace operational-reference.md `## Phase Skill Guide` body with a pointer.** 2–3 sentences naming the new file, the binding-surface preservation, and that mapping updates remain ordinary doc edits per phase-lock-and-role-declaration.

- [ ] **Step 4 (Phase 4 — verify): validator + binding.** `uv run python scripts/validate_architecture.py` → `ALL CHECKS PASSED`. If `validate_phase_topology` fails on a moved anchor, see "Out-of-scope follow-ups" envelope-expansion risk.

---

## Section F2.5 — Adoptable-disciplines list (Finding 5)

**Files touched:**
- Create: `docs/adoptable-disciplines.md`

**Why:** Per Finding 5 and the portfolio-review's "what the portfolio plans to port" table, four pieces of cairn stand alone without the four-phase discipline: handoff-as-pointer, the three hooks (`reversibility-guard.sh`, `role_guard.py`, `reality-check.sh`), the architecture validator (`scripts/validate_architecture.py`), and the phase-skill-mapping table (now `docs/phase-skill-mapping.md` per F2.4). A consumer-facing list of these makes partial adoption a first-class path rather than an apology.

### Tasks

- [ ] **Step 1 (Phase 2 — RED): contract test.** Add to `tests/unit/test_consumer_doc_surface.py`: `test_adoptable_disciplines_lists_four_disciplines()` — file exists, contains a section per discipline with a literal heading naming each, plus an "Integration cost" line per entry (matches the portfolio review's table column). Run; expect FAIL.

- [ ] **Step 2 (Phase 3 — GREEN): author `docs/adoptable-disciplines.md`.** Top paragraph frames the doc as cairn's "menu of standalone disciplines" — cairn's full pipeline is calibrated for safety-critical / long-horizon work per `docs/spec-v1.md` §1; these four pieces are useful even when the consumer has decided against the full pipeline. Cross-link `docs/reviews/2026-04-23-from-portfolio-evaluation.md` as prior-art evidence. Then four sections, each with **What it is**, **Why it's portable**, **Integration cost**, **What to copy**:
  1. **Handoff-as-pointer** — `templates/handoff.md` + four-section format + 150–400 token cap; cite operational-reference.md "Layer 1". Cost: low.
  2. **The three hooks** — `checks/reversibility-guard.sh`, `checks/role_guard.py`, `checks/reality-check.sh`. Cost: minutes with `jq` + `ruff` present. Note the F1 plugin-install path supersedes copy; copy is for non-plugin consumers.
  3. **The architecture validator** — `scripts/validate_architecture.py`. Cost: low; depends on consumer's ADR + ARCHITECTURE.md split.
  4. **The phase-skill-mapping table** — `docs/phase-skill-mapping.md`. Cost: trivial; requires Superpowers.

- [ ] **Step 3 (Phase 4 — verify): run Step 1's test.** Expect PASS.

---

## Section F2.6 — Cross-cutting verification

**Files touched:** none (test-only).

- [ ] **Step 1: full pytest run.** `uv run pytest -q`. Expect baseline + the three new test files green. Capture full FAILED list per operational-reference.md "Baseline capture" precondition.

- [ ] **Step 2: architecture validator run.** `uv run python scripts/validate_architecture.py`. Expect `ALL CHECKS PASSED`. If the F2.4 phase-skill-mapping relocation invalidates an INV-003 binding regex anchor, fix the anchor before declaring green (do **not** patch the validator to be permissive — the binding is load-bearing).

- [ ] **Step 3: smoketest hooks.** `bash scripts/smoketest_hooks.sh`. Expect `PASS role_guard.py` and exit 0. (No hook source changes in F2; this is a regression-safety run.)

- [ ] **Step 4: anchor sanity sweep.** Manually open CONSUMER.md and click-through each `CLAUDE.md#<anchor>` and `docs/<file>.md` link in a markdown previewer; confirm no broken anchors. (The Step F2.1 contract test approximates this mechanically; this manual step is the human-eyes verification per Auditor anti-behavior "evidence-backed assertions" — operational-reference.md Phase 4.)

- [ ] **Step 5: word-count check on CONSUMER.md.** `wc -w CONSUMER.md`. Expect ≤ 1500 words. If over, ruthlessly cut duplication; the doc is a navigation surface, not an alternative spec.

---

## Out-of-scope follow-ups

Deferred to M5.1 or a later feature:

- **Mechanical doc-link validator.** A pytest-side test that parses every `[text](path#anchor)` link in CLAUDE.md, CONSUMER.md, README.md, and `docs/*.md` and verifies the target resolves. Risk-4 in the ADR risk register motivates this. F2 ships a narrow contract test (anchors from CONSUMER.md into CLAUDE.md only); comprehensive validator deferred. Track in `docs/roadmap.md`.
- **Slash-command consumer documentation.** ADR D3 defers `/catchup`, `/handoff`, `/decision`, `/decision.full`, `/new-adr`, `/new-adr.full` to M5.1. CONSUMER.md ships a one-line note that slash commands arrive in a follow-up payload bump.
- **F1-blocked items.** CONSUMER.md "Install" section references F1's marketplace URL and post-install validator output. F2 authors placeholder text with `<!-- F1-followup -->` comments; F1 backfills the literal git URL and validator stdout in its PR.
- **F3-blocked items.** README.md "How to consume" keeps the symlink instruction with an `<!-- F3-followup -->` flag until F3's `complex-rag-analysis` migration lands and the D8 self-symlink-only stance is publicly stable. Symlink-instruction removal lands in F3.
- **Validator binding for `phase-skill-mapping.md`.** If `validate_architecture.py` regex-extracts from a hard-coded `docs/operational-reference.md` anchor (operational-reference.md:142-143 hints at this), F2.4's relocation may need a source-file change. `scripts/validate_architecture.py` is **not** in F2's envelope; flag in Phase 1 intent and RAISE_ISSUE if Phase 4 audit reveals the binding broke. The dispatch-skill triager will likely ESCALATE_TO_USER for envelope expansion.
- **Tagged-section migration of "New-code guidance."** F2 leaves CLAUDE.md's "New-code guidance" untagged (defaults maintainer-only). If a future review surfaces consumer-relevant content there, retag in a follow-up edit.
