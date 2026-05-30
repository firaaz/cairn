---
id: cairn-trial-d-scope-split
name: "Trial D — scope-split rule + four atomicity exception classes"
firmness: provisional
status: draft
date: 2026-05-30
scope: Build Trial D's prerequisite — the scope-split (atomicity) check on intent must-satisfy clauses, with the four named exception classes — by cloning the shipped Trial-C premise-grounding keystone. Build + tests only; the 3-intent measurement is a separate follow-on.
inputs:
  - docs/adr/cairn-thin-substrate-direction.md
  - docs/plans/2026-05-20-cairn-thin-substrate-trials.md
  - checks/premise_guard.py
  - scripts/lib/premise_match.py
  - scripts/validate_architecture.py
  - templates/intent.md
envelope:
  - "^scripts/lib/atomicity\\.py$"
  - "^checks/atomicity_guard\\.py$"
  - "^scripts/validate_architecture\\.py$"
  - "^templates/intent\\.md$"
  - "^tests/unit/test_atomicity\\.py$"
  - "^tests/unit/test_atomicity_guard\\.py$"
  - "^tests/unit/test_template_extraction\\.py$"
  - "^\\.claude/agents/phase-1-tdd\\.md$"
  - "^\\.claude/skills/cairn-tdd-feature/SKILL\\.md$"
  - "^docs/operational-reference\\.md$"
  - "^docs/plans/2026-05-30-cairn-trial-d-scope-split\\.md$"
---

# Trial D — scope-split rule + four atomicity exception classes

## What / Why

Trial D (`docs/plans/2026-05-20-cairn-thin-substrate-trials.md` §2 "Trial 2") is gated on a hard prerequisite: the four atomicity exception classes (`universal-set`, `regression-meta`, `operator-bound`, `trivial-existence`) "must be specified in the intent template **and** accepted by the scope-split rule." Two independent grep sweeps confirm the scope-split / atomicity rule **does not exist in code** — `atomic`, `scope-split`, and the four tag names appear only in ADR + plan prose. This is greenfield, not an extension.

`cairn-thin-substrate-direction` (status: accepted) specifies it: D2.1 (six-clause contract grammar, EARS internal to `must-satisfy`), D2.3 ("Scope-split rule. Atomic-primitive check on `must-satisfy`. Authoring-time hook. Atomicity exceptions named in D3"), D3 (the four classes verbatim with required declarations; atomicity = "verifiable by a single tool call or single file check"; "clauses without a tag must pass atomicity"). This is **execution of the accepted spec**, not a new decision.

The de-risked path is to mirror the keystone that already shipped green — Trial C premise-grounding (`checks/premise_guard.py` + `_run_premise_grounding_assertion` in `scripts/validate_architecture.py` + shared `scripts/lib/premise_match.py`, 36 tests). The scope-split rule ships as the same **dual surface behind one shared lib**: a CLI authoring-time gate (mirrors `premise_guard.py`, runs at the Phase-1→Phase-2 boundary where rubber-stamping happens) plus a `scope-split` validator assertion, both calling one `scripts/lib/atomicity.py`. The four-tag declaration check (deterministic, zero false-positive) is the primary enforcement; the atomicity heuristic is deliberately **shy** (biased to pass), and the exception tag is always a one-line escape from a false flag — that is the structural lever holding Trial D's <10% false-positive bound.

## Boundary

This feature deliberately does NOT:

- **Run the 3-intent measurement.** Session scope is build + tests only. The heuristic is frozen at close; the measurement (LIGHT `m2-dogfood-extract-invariant-ids`, MEDIUM `cairn-m7-plugin-deployment-pattern`, HEAVY `cairn-m5-f1-packaging`) runs as a distinct follow-on so the false-positive rate is not tuned to its own test set.
- **Make the `## Contract` block mandatory.** It stays optional + fail-open per ADR D6 trial-gating, so the six existing prose intents do not break. Absence prints a **visible stderr notice** (the skip is auditable, never silent); `CAIRN_CONTRACT_REQUIRED=1` is an opt-in lever that flips absence to a hard block. Making it mandatory by default would alter the migration posture D6 gates and would itself require a `/decision`.
- **Syntactically enforce EARS.** The ADR records the named failure mode (universal-quantification-over-implicit-domain) has "no syntactic hook to catch it," so EARS phrasing is template guidance only; the mechanical surface is atomicity-nudge + tag-validity.
- **Become a source-comprehension / execution layer.** Atomicity is a syntactic nudge plus tag-presence/declaration-presence checking — nothing parses or runs the cited tooling. Anything more is a new `/decision`.
- **Verify tag *correctness* or declaration *truth*.** The gate checks a tag is from the known set and its required declaration is non-empty; semantic mis-tagging stays operator-review-bound (same honest limit as premise grounding).
- **Replace the eight prose section headings.** The `## Contract` block is ADD-not-REPLACE; the existing `test_template_extraction.py` eight-heading-in-order assertion stays green.

## Specification

**`scripts/lib/atomicity.py`** (shared evaluator; pure functions, stdlib `re` only; no decorators/metaprogramming; FLI-1 single-source-of-truth like `premise_match.py`):
- `EXCEPTION_TAGS = frozenset({"universal-set", "regression-meta", "operator-bound", "trivial-existence"})`
- `TAGS_REQUIRING_DECLARATION = EXCEPTION_TAGS - {"trivial-existence"}`
- `is_atomic(clause: str) -> bool` — shy 3-signal heuristic; biased to return True. Signals: universal/plural quantifier tokens at word boundaries (`every|all|each|any|none of|exactly the following`) + negative-universal (`no `); conjunction of two distinct **verb-like** phrases (` and `/` & `/`;`) where both sides are verb-like (so adjectival "exists and parses" stays atomic); regression meta-phrases (`unchanged|behaves identically|no regression`).
- `parse_exception(item) -> tuple[str | None, str]` — from a `{clause, except: "<tag>: <declaration>"}` mapping, return `(tag, declaration)`; bare strings → `(None, "")`.
- `check_clauses(must_satisfy: list) -> list[str]` — returns offence strings (`[]` == pass). An item passes iff: bare string AND `is_atomic`, OR mapping with `tag in EXCEPTION_TAGS` AND (`tag == "trivial-existence"` OR declaration non-empty). Offences: bare non-atomic clause; unknown tag; tag in `TAGS_REQUIRING_DECLARATION` with empty declaration.

**`## Contract` block in `templates/intent.md`** (optional; added AFTER the existing `## Premise Grounding` block; fenced YAML):
- Six clause-lists: `must-satisfy`, `must-not-violate`, `wrong-if`, `escalate-when`, `evidence`, `execution-scope`.
- Each `must-satisfy` item is either a bare EARS string (atomicity-checked) or a mapping `{clause: "<EARS>", except: "<tag>: <declaration>"}` (atomicity-waived, declaration required unless `trivial-existence`).
- HTML-comment derive-instruction documents the five EARS shapes + the atomicity one-liner (D3) + the four tags and their required declarations, with one worked example.

**`checks/atomicity_guard.py`** (CLI gate, cloned from `premise_guard.py`):
- Invocation: `uv run python checks/atomicity_guard.py <path-to-intent.md>`.
- `CAIRN_ATOMICITY_FIX=1` → bypass (exit 0, stderr notice). `CAIRN_CONTRACT_REQUIRED=1` → absent `## Contract` block becomes exit 1.
- Extracts the `## Contract` YAML via the same fence-state-machine as `premise_guard.py`; dual-root `sys.path` (`CLAUDE_PROJECT_DIR|cwd` for the intent; cairn root for `from lib.atomicity import ...`).
- Exit codes (mirror `premise_guard.py`): **0** = no `## Contract` block (fail-open; prints `atomicity unchecked — no contract block` to stderr unless `CAIRN_CONTRACT_REQUIRED`), or all clauses atomic-or-validly-tagged; **1** = one+ offences from `check_clauses` (bare clause flagged / unknown tag / missing declaration), or absence under `CAIRN_CONTRACT_REQUIRED`; **2** = intent unreadable, malformed YAML, or `## Contract` heading present but no parseable block (fail-closed backstop via `_section_has_contract`). Collects and prints all offences (like `_check_premises`).

**`scripts/validate_architecture.py`**: add `_run_scope_split_assertion(project_root, inv_id, assertion) -> str | None` beside `_run_premise_grounding_assertion`, importing the SAME `from lib.atomicity import check_clauses`; register one branch `if atype == "scope-split": return _run_scope_split_assertion(...)` in the `_run_assertion` if-chain before the final `return None`.

**Env knobs** (registered in `docs/operational-reference.md`): `CAIRN_ATOMICITY_FIX`, `CAIRN_CONTRACT_REQUIRED`.

**Skill wiring**: in `.claude/skills/cairn-tdd-feature/SKILL.md`, add the atomicity gate as a sibling of the premise gate at the Phase-1→Phase-2 boundary (exit 0 → proceed; 1 → surface stderr, block until tagged-or-split or `CAIRN_ATOMICITY_FIX=1`; 2 → RAISE_ISSUE → triager). `.claude/agents/phase-1-tdd.md` gains a note that the optional `## Contract` block exists and tagging is the cheap escape from a flagged clause. Regenerate the `dist/` mirror via `scripts/build_dist.py` (not hand-edited).

## Verification

Phase 4 runs and records as evidence (CI `dist-gate.yml` runs NONE of these — green CI does not imply green Trial D):

- `uv run pytest tests/unit/test_atomicity.py -q` — shared evaluator, table-driven over the real corpus: all 8 `m2-dogfood-extract-invariant-ids` behaviors pass `is_atomic` **untagged** (the false-positive denominator); `m5-f1` A3/A4/A6 (universal) + A8 (regression) and `m7` FLI-4/FLI-7 **flag when bare** and **pass when carrying the correct tag+declaration**; unknown tag fails; required-declaration tag with empty declaration fails; `trivial-existence` needs no declaration. Assertion cases route through the public `_run_assertion(tmp, "INV-TEST", {"type": "scope-split", "must-satisfy": [...]})` to pin type-wiring.
- `uv run pytest tests/unit/test_atomicity_guard.py -q` — subprocess integration (mirror `test_premise_guard.py`): exit 0 (absent block → fail-open + notice; all-atomic/validly-tagged; `CAIRN_ATOMICITY_FIX`), exit 1 (untagged clause flagged; unknown tag; empty declaration; absent block under `CAIRN_CONTRACT_REQUIRED`), exit 2 (missing intent; malformed YAML; `## Contract` heading present but unparseable). Each fail-open hazard (flush-left heading inside fence; fenced code inside a clause scalar; non-yaml fence before yaml; stray bare fence) gets a paired passes-0 / non-atomic-fails-1 test proving no silent bypass.
- `uv run pytest tests/unit/test_template_extraction.py -q` — eight-heading-in-order assertion still green PLUS new `## Contract` heading-present + yaml-parses assertion.
- `uv run pytest -q` — full suite, prior count + new tests, 0 fail.
- `uv run python scripts/validate_architecture.py` — `ALL CHECKS PASSED`, no regression.
- `bash scripts/smoketest_hooks.sh` — `PASS atomicity_guard.py` (clean import under bare `python3`).
- Drift audit: the tag set documented in `templates/intent.md` equals `scripts/lib/atomicity.EXCEPTION_TAGS`.
- Wiring check: grep confirms the atomicity gate step is present in `.claude/skills/cairn-tdd-feature/SKILL.md` and its `dist/` mirror; `docs/operational-reference.md` env-var table lists `CAIRN_ATOMICITY_FIX` and `CAIRN_CONTRACT_REQUIRED`.

## Status (as of 2026-05-30, HEAD 496e1e7)

Mechanism **SHIPPED** through cairn-tdd-feature phases 1-4 (`233096e` intent · `8dec48e` RED · `c1ae50c`+`644f3db` GREEN+wiring · `25a734e` close · `61a3ad8`+`496e1e7` handoff-contract fix). 58 new tests green; validator + smoketest pass; 8 pre-existing baseline failures, zero new. Adversarial verification (26 gate-bypass inputs): no real defects; escape-hatch design holds.

Trial D's **pass criteria are NOT yet met** — only the prerequisite (the four exception classes accepted by a scope-split check) is built. The three pass numbers from §2 Trial 2 of the trials plan are unmeasured. This section is the next-session brief.

## Next session — fix F1, then the 3-intent measurement

### Step 1 — fix F1 (`\bno\s` over-block) FIRST, via cairn-tdd-feature or a focused TDD pass

The adversarial probe ran the **frozen** `is_atomic` over real corpus clauses and measured **~22% false-positive rate, every miss from the `\bno\s` alternative** in `_UNIVERSAL` (`scripts/lib/atomicity.py:19-22`). Confirmed FP clauses: m2 b2 "…returns no INV-NNN patterns", m2 b8 "…carries no word boundaries", m5-f1 A4 "no path under…", m5-f1 A6 "No hook command contains…", m7 FLI-4 "No third-party Actions…", m7 FLI-7 "No merge to dev…". All are genuinely atomic single checks. `\bno\s` carries no multiplicity semantics — it fires on any "no <noun>". This makes the supposedly *shy/biased-to-pass* heuristic non-shy; measuring #3 against it just re-derives "22%, fix `\bno\s`".

- **Verified-stable signals — DO NOT touch:** `each`/`every` (m5-f1 A3 = true positive), the verb-conjunction path (m5-f1 A1 = true positive), `_REGRESSION` (fired on nothing — zero false positives). `do NOT`/`does NOT` correctly pass (`NOT` ≠ `no\s`).
- **OPEN DESIGN QUESTION (settle before editing):** should `is_atomic` flag universal-NEGATION at all, or drop `\bno\s` entirely and leave negation to the `universal-set` tag — so the bare heuristic only catches `each`/`every`/`exactly the following` + verb-conjunctions + regression phrases? Leaning: drop `\bno\s` (the tag is the escape; a shy heuristic should under-fire). A narrower middle option: only fire on "no <plural-noun>" / "none of", not "no <singular>".
- **TDD shape:** add the 6 confirmed FP clauses as a RED regression test in `tests/unit/test_atomicity.py` (assert `is_atomic` True), plus keep a true-positive guard (A1/A3 still flag), then narrow the regex GREEN. Re-pin the synthetic test rows to these VERBATIM corpus strings while here (the Phase-2 synthetic-corpus gap, F2).

### Step 2 — the 3-intent measurement (operator-author / assistant-instrument)

**This cannot be run headless.** #1 and #2 below measure the OPERATOR's authoring experience; if the assistant authors the Contract blocks the numbers are void. Protocol: the operator authors each intent's `## Contract` block in EARS shape with tags available, gate running at the Phase-1→2 boundary; the assistant instruments.

Candidate intents (span the size range): LIGHT `.claude/skill-runs/m2-dogfood-extract-invariant-ids/intent.md` (8 behaviors, the false-positive denominator — should be ~all atomic); MEDIUM `.claude/skill-runs/cairn-m7-plugin-deployment-pattern/intent.md` (FLI-1..7); HEAVY `.claude/skill-runs/cairn-m5-f1-packaging/intent.md` (A1..A12).

| # | Metric | Target (§2 Trial 2) | How |
|---|--------|--------------------|-----|
| 1 | Authoring-time delta | ≤30% | operator stopwatches EARS+tag authoring vs felt prose baseline; small-N self-report (no recorded baseline exists — same shape as Probe A's +25-33%) |
| 2 | Rubber-stamp reduction | ≥2 of 3 intents | binary per intent: did the gate surface a split/tag decision the operator would otherwise have waved through? |
| 3 | Atomicity false-positive rate | <10% | of clauses the gate flags, the fraction the operator judges genuinely atomic; assistant runs the gate + proposes labels, operator adjudicates; denominator anchored on m2's 8 atomic behaviors |

**Pass → Trial E unblocks.** Fail (#3 still >10% after the fix, or #1 breaches 30% on the HEAVY intent) is itself a real Trial-D finding — the surcharge/precision is too high — not a bug to paper over; record it and decide whether to narrow further or accept the heuristic as advisory-only.

### Carried findings (from `integration/sweep-notes.md`)

- **F3 foot-guns** (low severity, defer): `_extract_contract_block` first-yaml-fence-wins (a 2nd `## Contract` block is unchecked); near-miss heading `##  Contract` (wrong spacing/casing) fails-open. Candidates for a hardening slice only if the gate becomes a hard enforcement wall rather than an advisory shy check.
- **F4 residual semantic hole** (by design): a non-atomic clause mis-tagged `trivial-existence`, or a junk declaration on a required tag, passes — operator-review-bound, the same honest limit as premise-grounding. A judge-agent is the post-Trial-E closer.
- **Close-sequence bug → file on `gh#4` (close-sequence-hardening):** Phase 4 runs its audit BEFORE it appends the handoff pointer, so a handoff line that violates `test_handoff_contract` (>120 chars, or a non-`docs/`/`gh:`/`sha` pointer) ships green-on-phase-4 and only fails the next full suite. The fix: the handoff-append step must run `test_handoff_contract` after writing, or construct the pointer line through the contract's shape.

### Envelope note

`.claude/active-envelope.yaml` is `mode: operator` and already grants every path the next session needs (`scripts/lib/.*`, `tests/.*`, `.claude/skill-runs/.*`, this plan doc, `templates/intent.md`). It is left modified-uncommitted (worktree-scoped, operator-owned).
