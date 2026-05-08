---
id: cairn-m5-f2-consumer-doc-surface
name: Cairn M5 F2 — Consumer-doc surface
snapshot-sha: b4eb5b74630f050ec3b6c6acd452979f443723bb
invariants-touched:
  - INV-003
---

## What

Land cairn's consumer-facing documentation surface: tag CLAUDE.md cross-cutting sections `[both]`/`[maintainer]`; author CONSUMER.md (anchor-link, not duplicate); replace README.md:31-37's unordered list with an explicit four-step reading order (README → CONSUMER.md → operational-reference.md → spec-v1.md); promote the Phase Skill Guide (operational-reference.md:141-174) to its own `docs/phase-skill-mapping.md` with a pointer left behind; author `docs/adoptable-disciplines.md` enumerating four standalone-portable pieces; extract five new templates (`feature-plan.md`, `intent.md`, `sweep-notes.md`, `adr-frontmatter.yaml`, `active-envelope.yaml`).

## Why

ADR `m5-plugin-distribution-and-symlink-retire` D6 (audience model) and D7 (template extraction) are unmet, and the 2026-04-23 portfolio-evaluation review's Findings 1–5 captured concrete first-time-consumer friction (audience ambiguity, no reading order, templates drop-off, buried Phase Skill Guide, missing adoptable-disciplines list). F1 ships the plugin payload; without F2, consumers install the plugin and immediately hit `spec-v1.md` first or have no copy-pasteable per-phase contract templates. F2 closes the consumer-doc gap so partial adoption is a first-class path, not an apology.

## Boundary

Markdown + YAML + Python pytest only. Envelope covers six doc files (CLAUDE.md, CONSUMER.md, README.md, two new docs/*.md, operational-reference.md), six templates, and three new tests under `tests/unit/`. **Out:** `scripts/validate_architecture.py` (deliberate — see Risk Surface), source code, hooks, slash-command consumer docs (deferred M5.1), F1's marketplace URL/validator stdout placeholders, F3 symlink removal, comprehensive doc-link validator.

## Specification

T1 audience model: legend line under CLAUDE.md title; append ` [both]` to Identifier scheme, Hook deps, ADRs append-only, Force-push, Operator envelope; ` [maintainer]` to `.slice-system/` rule and Symlink-recursion. Author CONSUMER.md (≤1500 words) with eleven ordered sections per plan F2.1 Step 3, anchor-linking CLAUDE.md `[both]` headings rather than duplicating prose.

T2 templates: create `templates/{feature-plan,intent,sweep-notes}.md` and `templates/{adr-frontmatter,active-envelope}.yaml` matching the schema-required keys/sections enumerated in plan F2.2 Step 1. `templates/intent.md` body MUST surface all eight schema sections (What, Why, Boundary, Specification, Verification, Risk Surface, Feature-Local Invariants, Explicit Scope-Out) so future Phase 1 dispatches cannot omit by oversight. `templates/active-envelope.yaml` defaults `mode: off` with the self-pattern shown in commented example.

T3 README: replace `README.md:31-37` with a "## Reading order" numbered list (README → CONSUMER.md → operational-reference.md → spec-v1.md), then "## Other docs" bullets covering the rest. Update "How to consume" to point at CONSUMER.md as canonical install path with symlink kept as F3-flagged fallback.

T4 promotion: lift `operational-reference.md:141-174` verbatim into new `docs/phase-skill-mapping.md` (preserving binding-surface caveat); replace original section body with ≤5-line pointer. Sequenced **before** CONSUMER.md anchors stabilise.

T5 adoptable: author `docs/adoptable-disciplines.md` with four sections (handoff-as-pointer, three hooks, architecture validator, phase-skill-mapping table), each with What/Why-portable/Integration-cost/What-to-copy.

## Verification

- `tests/unit/test_consumer_doc_surface.py`: `test_claude_md_cross_cutting_sections_carry_both_tag`; `test_consumer_md_anchors_resolve_into_claude_md` (slugify-approximation anchor resolution); `test_phase_skill_mapping_doc_exists` (four agent slugs, four role names, "Superpowers" literal); `test_operational_reference_phase_skill_guide_is_a_pointer` (≤5-line body, link literal); `test_adoptable_disciplines_lists_four_disciplines` (per-discipline heading + Integration-cost line).
- `tests/unit/test_template_extraction.py`: five sub-tests (one per template) for existence, non-empty (>200 chars), frontmatter shape, and required body sections per plan F2.2 Step 1.
- `tests/unit/test_readme_reading_order.py`: `test_readme_has_four_step_reading_order` asserts numbered list naming the four docs in order.
- `uv run pytest -q` baseline + new tests green; `uv run python scripts/validate_architecture.py` → `ALL CHECKS PASSED`; `bash scripts/smoketest_hooks.sh` → exit 0; `wc -w CONSUMER.md` ≤ 1500.

## Risk Surface

T4 relocates the Phase Skill Guide that INV-003's `validate_phase_topology` regex-extracts from (operational-reference.md:142-143 names it as binding surface). If the validator hard-codes the source path, F2.4 silently breaks the three-way phase-topology cross-reference — domain wrongness pytest greens cannot catch (validator-run is separate). `scripts/validate_architecture.py` is intentionally outside envelope; Phase 4 must RAISE_ISSUE if binding broke. Secondary: CLAUDE.md↔CONSUMER.md anchor drift (ADR Risk-4) — F2 ships narrow test only.

## Feature-Local Invariants

- **FLI-1** Every `CLAUDE.md#<anchor>` cross-reference appearing in CONSUMER.md MUST resolve to a real heading in CLAUDE.md under the slugify approximation (lowercase, spaces and `[`/`]` → `-`, strip non-alphanumeric except `-`).
- **FLI-2** `templates/intent.md` body MUST contain all eight Phase-1 schema section headings in order (`## What`, `## Why`, `## Boundary`, `## Specification`, `## Verification`, `## Risk Surface`, `## Feature-Local Invariants`, `## Explicit Scope-Out`); the schema's derive-don't-fabricate contract requires the template to surface every required section so omission-by-oversight is structurally prevented.
- **FLI-3** `docs/phase-skill-mapping.md` MUST preserve the four canonical agent slugs (`phase-1-tdd`..`phase-4-tdd`), the four role names (Reader, Skeptic, Builder, Auditor), and the literal `Superpowers` token — these are the regex anchors INV-003's `validate_phase_topology` keys on.
- **FLI-4** `operational-reference.md`'s `## Phase Skill Guide` section, after pointer replacement, MUST contain a literal link to `docs/phase-skill-mapping.md` and have body ≤5 lines.
- **FLI-5** `templates/active-envelope.yaml` MUST default to `mode: off` and include the self-pattern `^\.claude/active-envelope\.yaml$` in its commented example block — the operator-envelope `mode: operator` requires a self-matching pattern or the file becomes uneditable.
- **FLI-6** CONSUMER.md MUST be ≤1500 words; it is a navigation surface, not an alternative spec.

## Explicit Scope-Out

- **Comprehensive doc-link validator** parsing every `[text](path#anchor)` link across CLAUDE.md/CONSUMER.md/README.md/`docs/*.md` — Risk-4 motivates this; deferred to M5.1 per plan F2 "Out-of-scope follow-ups". F2 ships only the narrow CONSUMER.md→CLAUDE.md anchor-resolution contract test.
- **Slash-command consumer documentation** (`/catchup`, `/handoff`, `/decision`, `/decision.full`, `/new-adr`, `/new-adr.full`) — ADR D3 defers these to M5.1 payload bump; CONSUMER.md ships only a one-line note.
- **F1-blocked literals** — F1's marketplace git URL and post-install validator stdout are placeholders with `<!-- F1-followup -->` comments; F1 backfills.
- **F3-blocked items** — README.md "How to consume" keeps the symlink instruction with `<!-- F3-followup -->` until F3's `complex-rag-analysis` migration; symlink-instruction removal lands in F3.
- **`scripts/validate_architecture.py` source-edit for INV-003 binding** — deliberately outside F2's envelope. If F2.4's relocation invalidates the validator's regex anchor, Phase 4 must RAISE_ISSUE for envelope expansion (the dispatch triager will likely ESCALATE_TO_USER); F2 will not silently patch the validator to be permissive.
- **CLAUDE.md "New-code guidance" tagging** — left untagged (defaults to `[maintainer]`); future review may retag if consumer-relevant content surfaces.
- **Within-feature parallel dispatch in Phase 3** — permitted per CLAUDE.md but not mandated; Phase 3 may fan out F2.2/F2.4/F2.5 (independent file writes) or run sequentially at Builder's discretion. This intent does not prescribe the dispatch shape.
