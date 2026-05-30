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
