---
slice: cairn-m5-f2-consumer-doc-surface
phase: complete
branch: dev
as-of: 2026-05-08 8ca229f
---

## State

F2 closed in 5 commits (P1 `4e3cb0b` → P2 `2518dd1` → P3 `2583bbe` → fixup `e3d088d` → P4 `8ca229f`). Intent-system schema (Risk Surface + Feature-Local Invariants + Explicit Scope-Out, committed at `39f5e9f` after a plan-doc alignment at `b4eb5b7`) shipped and was dogfooded by F2 itself: Risk Surface predicted the INV-003 validator-binding break exactly, Phase 3 honored Scope-Out and RAISE_ISSUE'd, triager classified ESCALATE_TO_USER, operator approved fixup-on-this-dispatch — first dogfood signal **positive (n=1)**. INV-003 reanchored to `docs/phase-skill-mapping.md`. Suite 414 passed / 2 failed (pre-existing) / 2 xfailed; validator `ALL CHECKS PASSED`. `dev` is 5 ahead of `origin/dev`.

## Next

Push `dev` → `origin/dev`, then dispatch F3 against `docs/plans/2026-05-08-cairn-m6-f3-migration-and-symlink-retire.md` (now unblocked — F1+F2 preflight green). F3 dispatch briefs MUST explicitly remind each phase agent to invoke its canonical Superpower per `docs/phase-skill-mapping.md` (P2: `test-driven-development` RED-half; P3: `test-driven-development` GREEN-half + `verification-before-completion`; P4: `verification-before-completion` + `requesting-code-review`). Main-session work invokes `superpowers:verification-before-completion` before claiming complete.

## Blocked / Pending

- `/handoff` skill — companion to `/catchup`; this refresh was manual
- `.gitignore` cleanup — `dist/` and untracked `.claude/envelope-grants.log`
- 2 baseline failures: `TestSlice011AssertionCoverage::{test_no_extra_assertion_blocks, test_invariant_count_unchanged}` → INV-002 re-baseline on `docs/handoff.md`
- 6 amendment ADRs (governance follow-up)
- spec-v2 correction → `~/.claude/plans/look-at-docs-spec-v2-md-and-rippling-wadler.md` (drop authoring-shift framing; narrow to recognition+invocation; F2 dogfood is the n=1 positive signal that informs this)
- Pre-§9 audit: 5 recent intent.mds × "cited ADR shaped impl?"; <50% yes ⇒ substrate redesign justified

## Features

- `cairn-m5-f1-packaging`: shipped (`6e25777`, squashed)
- `cairn-m5-f2-consumer-doc-surface`: closed (`8ca229f`, 5-commit slice with operator-approved fixup)
- `cairn-m6-f3-migration-and-symlink-retire`: ready to dispatch (second schema dogfood)

## Pointers

- `docs/adr/m5-plugin-distribution-and-symlink-retire.md` — governing ADR for the F1/F2/F3 program
- `docs/plans/2026-05-08-cairn-m6-f3-migration-and-symlink-retire.md` — F3 plan; M.0 preflight checks F1+F2 shipped
- `.claude/skill-runs/cairn-m5-f2-consumer-doc-surface/integration/sweep-notes.md` — F2 audit; schema dogfood evidence
- `.claude/agents/phase-1-tdd.md` — authoritative for the 8-section intent.md schema
- `templates/intent.md`, `templates/handoff.md`, `templates/feature-plan.md`, `templates/sweep-notes.md`, `templates/adr-frontmatter.yaml`, `templates/active-envelope.yaml` — F2-shipped phase-boundary contract templates
