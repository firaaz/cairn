---
id: premise-guard-trial-c
name: "premise_guard.py — Trial C approval-gate premise-grounding"
envelope:
  # Union envelope (whole-feature). Per-slice envelopes are given in each slice
  # section; a cairn-tdd-feature run should be dispatched with its slice's subset.
  - ^scripts/lib/premise_match\.py$
  - ^scripts/validate_architecture\.py$
  - ^checks/premise_guard\.py$
  - ^templates/intent\.md$
  - ^\.claude/skills/cairn-tdd-feature/SKILL\.md$
  - ^docs/operational-reference\.md$
  - ^tests/unit/test_premise_match\.py$
  - ^tests/unit/test_premise_guard\.py$
  - ^tests/unit/test_premise_grounding\.py$
invariants-touched: []
---

# premise_guard.py (Trial C) Implementation Plan

> **For agentic workers:** This is a cairn feature plan-doc. Slices 1–2 are executed via the `cairn-tdd-feature` dispatch skill (Phase 1 derives intent from this doc; Phase 2 writes RED tests from that intent *alone* — so this doc specifies behavior precisely and deliberately does **not** inline test/impl code). Slice 3 is direct edits (no failing-test shape). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `premise_guard.py` as an approval-gate check that diffs an intent's verbatim source-quotes against live source and blocks Phase-2 dispatch on a stale/fabricated/missing premise — the mechanical defense against the slice-#25 wrong-premise failure, and the keystone's first live enforcement surface.

**Architecture:** A pure matcher (`scripts/lib/premise_match.py`) is shared by both the already-shipped validator assertion and a new CLI gate (`checks/premise_guard.py`), so the two cannot diverge on tolerance. The gate is run by the `cairn-tdd-feature` skill at the Phase-1→Phase-2 operator-confirmation checkpoint; the premise block is operator-authored into the per-run `intent.md` at that gate (Phase 1's derive-from-ADR-only Reader contract is untouched).

**Tech Stack:** Python (function-based, stdlib + `pyyaml`); pytest; cairn hook/validator substrate.

---

## What

Add a premise-grounding **approval gate**: an intent may declare a `## Premise Grounding` block listing `{source, quote, label}` premises; `premise_guard.py` reads each cited source, diffs the verbatim quote against it under a whitespace-and-comment-stripping tolerance, and exits non-zero (blocking Phase-2 dispatch) when a quote is absent, the source is missing, or the source is unreadable. The quote-match logic is extracted into one shared matcher that the existing `premise-grounding` validator assertion is re-pointed at.

## Why

Per `cairn-thin-substrate-direction` D7, premise-grounding is cairn's identity keystone — "the layer that keeps AI-authored intent bound to verifiable evidence." The keystone shipped in `d79d2ae` only as a validator assertion (`scripts/validate_architecture.py`) with no live call site and run by no automated surface; the session-gating `premise_guard.py` hook D6 names as "the buildable core" is still unbuilt. The `2026-05-20-cairn-thin-substrate-trials.md` §1.3 slice-#25 counterfactual proves no current mechanical layer reads source to challenge a premise. Building this is **Trial C**; it closes the partial Trial-E gate (`premise_guard.py` shipping is one of Trial E's two required gates).

## Boundary

- It does **not** convert `intent.md` to EARS / `must-satisfy` contract grammar (that is Trial D).
- It does **not** mechanically force premise *presence* (no path-detection heuristic that says "a clause naming a file requires a premise") — it checks the premises that are listed. Presence-forcing is deferred (trials §4 Q4).
- It does **not** add a `PreToolUse`/`SessionStart` hook or change `settings.json`; the gate is a CLI the dispatch skill invokes.
- It does **not** read source for *comprehension* — verbatim-quote-vs-source diff only (anti-temptation §5).
- It does **not** change the `phase-1-tdd` Reader contract; the premise block is operator-authored at the approval gate.

## Specification

### Component A — `scripts/lib/premise_match.py` (shared matcher)

Pure, no I/O beyond what callers pass in. Two functions:

- `normalize(text: str, ext: str) -> str` — `ext` is the `Path(source).suffix` form (leading dot, e.g. `.py`, `.md`).
  1. **Comment-strip by extension.** `.py`, `.sh`, `.yaml`, `.yml`: remove a `#` and everything after it when the `#` is at line start or preceded by whitespace — regex per line `r'(^|\s)#.*$' -> r'\1'` (avoids truncating `#` embedded in a token, e.g. a color literal). `.md`: remove `<!-- ... -->` spans, `re.DOTALL`. Any other / no extension: no comment-strip.
  2. **Whitespace-normalize.** Collapse every run of whitespace (including newlines) to a single space and strip ends: `' '.join(stripped_text.split())`.
  - Tolerated by this scheme: indentation changes, trailing whitespace, line-rewrapping where a space already existed, and comment edits. **Not** tolerated (by design): a change to non-whitespace tokens, or whitespace appearing/disappearing immediately adjacent to punctuation. Authors copy the quote with consistent internal spacing.

- `grounded(source_text: str, quote: str, ext: str) -> bool`
  - Returns `normalize(quote, ext) in normalize(source_text, ext)`.
  - If `normalize(quote, ext)` is empty (quote was blank / whitespace-only / comment-only) → return `False` (a premise must quote substantive content).

### Component B — `scripts/validate_architecture.py` re-alignment

`_run_premise_grounding_assertion` currently uses exact `if quote not in text`. Re-point the match through the shared matcher: import `from lib.premise_match import grounded` and replace the membership test with `if not grounded(text, quote, source_suffix)`, where `source_suffix` is the cited source's extension (e.g. `Path(source).suffix`). All existing failure-message strings and the missing/unreadable-source branches are unchanged. The five existing `tests/unit/test_premise_grounding.py` cases must stay green (they use no-comment, single-line quotes where exact and normalized agree).

### Component C — `checks/premise_guard.py` (CLI gate)

Function-based Python script. Invocation: `uv run python checks/premise_guard.py <path-to-intent.md>`.

- **Project root:** `Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())`. Premise `source` paths are repo-root-relative.
- **Importing the shared matcher:** `checks/` is not on pytest's `scripts`-pythonpath at runtime, so before importing do `sys.path.insert(0, str(project_root / "scripts"))` then `from lib.premise_match import grounded`. (Tests under `tests/` get `lib.*` from the configured pythonpath and import it directly; the CLI is best exercised via `subprocess` against the real exit codes — no mocks.)
- **Parse:** locate the `## Premise Grounding` heading in the intent markdown; take the body up to the next `## ` heading; extract the first fenced ```` ```yaml ```` … ```` ``` ```` block; `yaml.safe_load` it to `{"premises": [ {source, quote, label?}, … ]}`.
- **Check:** for each premise, resolve `project_root / source`; if absent → failure "cited source not found: <source>"; if unreadable (`OSError`/`UnicodeDecodeError`) → failure "cited source unreadable: <source>"; else if not `grounded(text, quote, Path(source).suffix)` → failure "premise no longer grounded in <source> (quoted text absent — stale or fabricated): <quote>". Collect all failures.
- **Exit codes** (mirroring `role_guard.py`): `0` = all listed premises grounded, OR no `## Premise Grounding` section / empty `premises` list; `1` = one or more failures (print each failure to stderr); `2` = intent file missing, unreadable, or the YAML block is malformed, or bad args (print diagnostic to stderr).
- **Escape hatch:** `CAIRN_PREMISE_FIX=1` → print a one-line bypass notice to stderr and exit `0` without checking (mirrors `ADR_EDITORIAL_FIX=1`).

### Component D — `templates/intent.md` schema delta

Add a new, **optional**, trailing section:

```markdown
## Premise Grounding
<!-- Optional. Operator-authored at the Phase-1→Phase-2 approval gate (NOT by
phase-1-tdd, whose Reader contract forbids reading implementation source). For
each claim this intent makes about EXISTING source behavior, quote the cited
span verbatim so premise_guard.py can diff it against live source. Omit the
section entirely if the intent makes no source-behavior claims. -->
```yaml
premises:
  - source: scripts/_root.py            # repo-root-relative path
    quote: |                            # verbatim span being relied on
      def project_root() -> Path:
    label: "one-line current-behavior claim the intent depends on"
```
```

### Component E — `.claude/skills/cairn-tdd-feature/SKILL.md` gate wiring

Insert a step between current Step 5 (verify Phase-1 commit) and Step 6 (dispatch Phase 2):

> **5a. Premise-grounding approval gate.** Surface the committed `intent.md` to the operator for confirmation. If the intent makes claims about existing source, the operator adds a `## Premise Grounding` block (see `templates/intent.md`). Run `uv run python checks/premise_guard.py .claude/skill-runs/<feature-id>/intent.md`. On exit `0`, proceed to Phase 2. On exit `1`, surface the stderr diff and **block dispatch** until the operator corrects the premise (or sets `CAIRN_PREMISE_FIX=1` for known divergence). On exit `2`, treat as a malformed-intent RAISE_ISSUE.

### Component F — `docs/operational-reference.md`

Document: `premise_guard.py` purpose + invocation + exit codes; the `## Premise Grounding` intent section and authoring convention; the `CAIRN_PREMISE_FIX` env override; the whitespace+comment-strip tolerance semantics; the shared-matcher invariant (FLI-1 below).

## Verification

- `tests/unit/test_premise_match.py` (new): `normalize`/`grounded` across `.py`/`.sh`/`.yaml`/`.md`/unknown extensions — indentation/trailing/line-wrap reflow grounds; comment add/edit grounds; a token/value change does NOT ground; empty/comment-only quote → `False`.
- `tests/unit/test_premise_grounding.py` (existing): all five cases stay green after the matcher swap; add one case proving the new tolerance (reflowed-indent quote grounds; commented-source quote grounds).
- `tests/unit/test_premise_guard.py` (new): CLI exit `0` (all grounded / absent section / empty premises / `CAIRN_PREMISE_FIX=1`), `1` (stale quote, fabricated quote, missing source, unreadable source), `2` (missing intent file, malformed YAML block, bad args); multiple premises with one stale.
- **Slice-#25 re-probe (Trial-C pass criterion)**, in `tests/unit/test_premise_guard.py`: build a synthetic source file whose body contradicts a docstring-style premise (the slice-#25 *pattern*; the literal M4-era files are gone), assert the wrong-premise intent exits `1`; assert the corrected-premise intent exits `0`.
- Full suite + validator green: `uv run pytest -q` (no new failures vs. snapshot baseline) and `uv run python scripts/validate_architecture.py`.

## Risk Surface

The failure modes that pass CI: (1) **lenient strictness** — an operator who simply omits a premise for a source-claim bypasses grounding entirely (accepted for Trial C; measured by the trial). (2) **comment-strip masking** — a meaning-bearing change confined to a stripped comment in the cited span will ground when it should not (operator-accepted tolerance call). (3) **correct-quote-misread** — a verbatim-accurate quote the author misinterprets still passes (the residual semantic class D7 admits premise-grounding cannot catch). None of these surface as a test failure; they are inherent scope limits, not defects.

## Feature-Local Invariants

- **FLI-1:** `premise_guard.py` and `validate_architecture.py`'s `premise-grounding` assertion MUST resolve quote-vs-source through the same `scripts/lib/premise_match.grounded` — they cannot diverge on tolerance. A premise that passes one MUST pass the other for identical inputs.
- **FLI-2:** The gate is fail-open on *absence* (no premise block → exit 0) but fail-closed on *malformation* (unparseable block → exit 2). A present-but-broken premise block never silently passes.

## Explicit Scope-Out

- EARS / `must-satisfy` conversion of `intent.md` (Trial D).
- Presence-detection heuristic forcing a premise per source-naming clause (trials §4 Q4).
- `PreToolUse`/`SessionStart` hook wiring or `settings.json` changes.
- Any change to `phase-1-tdd`'s Reader contract or its agent definition.
- Source comprehension beyond verbatim-quote diff.

---

## Slice breakdown

### Slice 1 — shared matcher + validator re-alignment  *(execute via `cairn-tdd-feature`)*

Envelope: `^scripts/lib/premise_match\.py$`, `^scripts/validate_architecture\.py$`, `^tests/unit/test_premise_match\.py$`, `^tests/unit/test_premise_grounding\.py$`.

- [ ] Create `scripts/lib/premise_match.py` (Component A) — RED `tests/unit/test_premise_match.py`, then GREEN.
- [ ] Re-point `_run_premise_grounding_assertion` at `grounded` (Component B); existing `test_premise_grounding.py` stays green + add the tolerance case.
- [ ] Phase 4 audit: full suite + `validate_architecture.py` green.

**Acceptance:** FLI-1 holds; reflow/comment quotes ground; token changes don't; existing validator tests green.

### Slice 2 — `premise_guard.py` CLI + slice-#25 re-probe  *(execute via `cairn-tdd-feature`)*

Envelope: `^checks/premise_guard\.py$`, `^tests/unit/test_premise_guard\.py$`.

- [ ] RED `tests/unit/test_premise_guard.py` (exit-code matrix + multi-premise + slice-#25 re-probe), then GREEN `checks/premise_guard.py` (Component C).
- [ ] Phase 4 audit: full suite green; re-probe blocks the wrong premise, passes the corrected one.

**Acceptance:** the slice-#25-pattern wrong premise exits 1; corrected exits 0; `CAIRN_PREMISE_FIX=1` bypasses; FLI-2 holds.

### Slice 3 — template + skill gate + docs  *(direct edits — no failing-test shape)*

Paths (all already in the operator envelope): `templates/intent.md`, `.claude/skills/cairn-tdd-feature/SKILL.md`, `docs/operational-reference.md`.

- [ ] Add the `## Premise Grounding` section to `templates/intent.md` (Component D).
- [ ] Insert Step 5a into `SKILL.md` (Component E).
- [ ] Document in `docs/operational-reference.md` (Component F).
- [ ] Manual end-to-end check: run `premise_guard.py` against a hand-authored intent fixture with a grounded and a stale premise; confirm 0 / 1.

**Acceptance:** the gate is encoded between Phase-1 verify and Phase-2 dispatch; the template documents operator-at-gate authoring; the env override + tolerance are documented.

---

## References

- `docs/adr/cairn-thin-substrate-direction.md` — D6/D7 (keystone, `premise_guard.py` as the gate); D2.5.
- `docs/plans/2026-05-20-cairn-thin-substrate-trials.md` — §1.3 slice-#25 counterfactual; §2 Trial-3 spec; §4 Q6 tolerance.
- `scripts/validate_architecture.py:728` — shipped `_run_premise_grounding_assertion`.
- `tests/unit/test_premise_grounding.py` — validator-parity anchor.
- `checks/role_guard.py` — exit-code + project-root convention this gate mirrors.
- `.claude/skills/cairn-tdd-feature/SKILL.md` — dispatch flow the gate wires into.
