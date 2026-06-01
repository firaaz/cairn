---
name: using-cairn
description: SessionStart carrier — on session open it emits a neutral, state-accurate pointer to the active Cairn intent (resume) or a no-intent statement, then points to the cairn-intent loop. Pointer-only, byte-budgeted, never gates, no imperative prose. If it does not fire, cairn-intent Step 1 loads or forms the intent explicitly.
---

# using-cairn

Cairn's SessionStart carrier (`delivery-mechanism-friction` D1, `intent-management-loop` D5,
`using-cairn-carrier-contract` Approach D). Fires on session open. It is a **pointer, not a
payload** — byte-budgeted (`CAIRN_CARRIER_BUDGET_BYTES`, ~2,000-token proxy) — and it **never
gates**: loading the active intent is cheap and read-only; nothing here blocks a write or holds the
operator at a boundary.

The emitter is `checks/using-cairn-carrier.sh`. This skill is its documented surface; the Codex
plugin's `using-cairn` skill is a chooser, not a SessionStart carrier (Codex has no SessionStart
hook). Both name the same workflows and skills.

## What it emits on session open

The first stdout line is always the machine marker `CAIRN_CARRIER_FIRED` (the testable
fired-signal, D2), followed by exactly one of:

1. **Active-intent pointer (resume).** If the handoff names an intent thread in the `open` state
   with an `intent.md` under `.claude/skill-runs/<feature>/`, emit the neutral pointer block —
   `cairn intent (open): <path>` and its one-line scope statement. State-aware (INV-002): a
   `deferred`/`blocked`/closed thread is not active and is not emitted. The full intent body is
   not loaded; the `cairn-intent` skill reads it when work begins.
2. **No-intent statement.** If no `open` intent exists, emit the neutral statement
   `cairn: no active intent on record`. No gate, no block, no instruction — the operator may
   proceed read-only (D8 exempts read-only / Q&A sessions).

## Neutral emission — no imperative prose (L-012)

A SessionStart hook's stdout merges into every agent's effective prompt. An imperative line
(*"run the X skill"*, *"you must"*, *"cannot proceed"*) can be read by a tier-sensitive agent as a
command or blocker and trigger a hard refusal (`docs/lessons.md` L-012, a verified incident). The
carrier therefore states **facts only** and never instructs. This skill's prose may reference the
`cairn-intent` entry point for a human reader; the carrier's **emitted** lines never do.

## Compose with superpowers, never double-load (delivery-mechanism-friction D2)

Probe for a `superpowers` SessionStart presence (a filesystem marker under the plugins dir). If
superpowers already injected methodology framing, emit only the cairn-delta (the pointer or the
no-intent statement). Otherwise emit a one-line cairn-orientation block first.

## Token budget (delivery-mechanism-friction D1, INV-004)

The emitted payload is byte-clamped (`CAIRN_CARRIER_BUDGET_BYTES`, default 8000 ≈ 2,000 tokens).
This is a pointer surface — the marker, the pointer or no-intent line, and an optional scope line.
No intent body, no command catalogue, no `.full.md` siblings inline. The byte clamp is a proxy; a
token-exact CI gate is recorded EXPOSED in the ADR (a real tokenizer is outside the standing deps).

## Fallback (intent-management-loop D5, R3)

The carrier is an **optimization, not the only path**. On a non-Claude-Code host, or any session
where SessionStart does not fire, `cairn-intent` Step 1 (`load-or-form-intent`) does the load/form
explicitly and unconditionally. The loop is correct whether or not the carrier fired; the carrier
only saves the operator the first prompt.

## Distribution (using-cairn-carrier-contract D6)

cairn-internal only. The carrier is registered in cairn's local `.claude/settings.json` and is not
in `scripts/build_dist.py`, so it dogfoods inside cairn (self-consumption) without shipping to
consumers. Consumer distribution is deferred to the firm D7 retirement ADR.

## Pointers (Tier-2, load on demand)

- Operating loop — the `cairn-intent` skill.
- Phase-isolated TDD fallback — the `cairn-tdd-feature` skill.
- Substrate, envelope, gates — `CLAUDE.md`, `docs/operational-reference.md`.
