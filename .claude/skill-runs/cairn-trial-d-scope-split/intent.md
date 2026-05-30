---
id: cairn-trial-d-scope-split
name: "Trial D — scope-split rule + four atomicity exception classes"
snapshot-sha: c2e93f9c8ec6956e984e9ea3739558f36b18e297
invariants-touched: []
---

<!--
Phase 1 (Reader) intent. Authoritative shape source: .claude/agents/phase-1-tdd.md.
Eight prose section headings in order + an optional ## Premise Grounding block.
The ## Contract template block referenced in the Specification does NOT yet exist
in templates/intent.md — this feature creates it; do not require it here.
-->

## What

Build the scope-split (atomicity) check on intent `must-satisfy` clauses, with the four named exception classes (`universal-set`, `regression-meta`, `operator-bound`, `trivial-existence`), by cloning the shipped Trial-C premise-grounding keystone. The rule ships as a dual surface behind one shared lib: a CLI authoring-time gate (`checks/atomicity_guard.py`, mirroring `premise_guard.py` at the Phase-1→Phase-2 boundary) plus a `scope-split` validator assertion, both calling one `scripts/lib/atomicity.py`. A new optional `## Contract` block is added to `templates/intent.md`. Build + tests only.

## Why

`cairn-thin-substrate-direction` (accepted) specifies it: D2.3 ("Scope-split rule. Atomic-primitive check on `must-satisfy`. Authoring-time hook. Atomicity exceptions named in D3") and D3 (the four classes verbatim; atomicity = "verifiable by a single tool call or single file check"; "Clauses without a tag must pass atomicity"). Trial 2/D is gated on these classes being "specified in the intent template **and** accepted by the scope-split rule." Two grep sweeps confirm none exists in code — this is execution of accepted spec, not a new decision. The four-tag declaration check (deterministic, zero false-positive) is primary enforcement; the atomicity heuristic is deliberately shy (biased to pass), and the tag is a one-line escape — the lever holding Trial D's <10% false-positive bound.

## Boundary

This feature deliberately does NOT: run the 3-intent measurement (build + tests only; heuristic frozen at close); make the `## Contract` block mandatory (stays optional + fail-open per ADR D6, visible stderr notice on absence, `CAIRN_CONTRACT_REQUIRED=1` opt-in lever — mandatory-by-default would need a `/decision`); syntactically enforce EARS (template guidance only — the named failure mode "has no syntactic hook to catch it"); become a source-comprehension / execution layer (nothing parses or runs cited tooling); verify tag *correctness* or declaration *truth* (checks tag-in-set + declaration-non-empty only; mis-tagging stays operator-review-bound); replace the eight prose section headings (`## Contract` is ADD-not-REPLACE; `test_template_extraction.py` eight-heading-in-order assertion stays green).

## Specification

**`scripts/lib/atomicity.py`** (shared evaluator; pure functions, stdlib `re` only; no decorators/metaprogramming; single-source-of-truth like `premise_match.py`):
- `EXCEPTION_TAGS = frozenset({"universal-set", "regression-meta", "operator-bound", "trivial-existence"})`.
- `TAGS_REQUIRING_DECLARATION = EXCEPTION_TAGS - {"trivial-existence"}` (i.e. `{universal-set, regression-meta, operator-bound}`).
- `is_atomic(clause: str) -> bool` — shy 3-signal heuristic, biased to return True. Signals: universal/plural quantifier tokens at word boundaries (`every|all|each|any|none of|exactly the following`) + negative-universal (`no `); conjunction of two distinct **verb-like** phrases (` and `/` & `/`;`) where both sides are verb-like (so adjectival "exists and parses" stays atomic); regression meta-phrases (`unchanged|behaves identically|no regression`).
- `parse_exception(item) -> tuple[str | None, str]` — from a `{clause, except: "<tag>: <declaration>"}` mapping return `(tag, declaration)`; a bare string returns `(None, "")`.
- `check_clauses(must_satisfy: list) -> list[str]` — returns offence strings (`[]` == pass). An item passes iff: bare string AND `is_atomic`, OR mapping with `tag in EXCEPTION_TAGS` AND (`tag == "trivial-existence"` OR declaration non-empty). Offences: bare non-atomic clause; unknown tag; tag in `TAGS_REQUIRING_DECLARATION` with empty declaration.

**`## Contract` block in `templates/intent.md`** (optional; added AFTER the existing `## Premise Grounding` block; fenced YAML):
- Six clause-lists: `must-satisfy`, `must-not-violate`, `wrong-if`, `escalate-when`, `evidence`, `execution-scope`.
- Each `must-satisfy` item is a bare EARS string (atomicity-checked) or a mapping `{clause: "<EARS>", except: "<tag>: <declaration>"}` (atomicity-waived; declaration required unless `trivial-existence`).
- HTML-comment derive-instruction documents the five EARS shapes + the atomicity one-liner (D3) + the four tags and their required declarations, with one worked example.
- ADD-not-REPLACE: the eight existing prose headings remain, in order.

**`checks/atomicity_guard.py`** (CLI gate, cloned from `premise_guard.py`):
- Invocation: `uv run python checks/atomicity_guard.py <path-to-intent.md>`.
- `CAIRN_ATOMICITY_FIX=1` → bypass (exit 0, stderr notice), mirroring `premise_guard`'s `CAIRN_PREMISE_FIX=1` early-return. `CAIRN_CONTRACT_REQUIRED=1` → absent `## Contract` block becomes exit 1.
- Extracts the `## Contract` YAML via the same fence-state-machine as `premise_guard._extract_premise_block` (a fence closes only on a bare ``` at its open indent). Dual-root `sys.path`: `CLAUDE_PROJECT_DIR|cwd` for the intent; cairn root for `from lib.atomicity import ...`.
- Exit codes (mirror `premise_guard.py`): **0** = no `## Contract` block (fail-open; prints a visible `atomicity unchecked — no contract block` notice to stderr unless `CAIRN_CONTRACT_REQUIRED`), or all clauses atomic-or-validly-tagged; **1** = one+ offences from `check_clauses`, or absence under `CAIRN_CONTRACT_REQUIRED`; **2** = intent unreadable, malformed YAML, or `## Contract` heading present but no parseable block (fail-closed backstop via `_section_has_contract`, mirroring `_section_has_premises`). Collects and prints all offences (like `_check_premises`).

**`scripts/validate_architecture.py`**: add `_run_scope_split_assertion(project_root, inv_id, assertion) -> str | None` beside `_run_premise_grounding_assertion`, importing the SAME `from lib.atomicity import check_clauses`; register one branch `if atype == "scope-split": return _run_scope_split_assertion(...)` in the `_run_assertion` if-chain before the final `return None`.

**Env knobs** registered in `docs/operational-reference.md`: `CAIRN_ATOMICITY_FIX`, `CAIRN_CONTRACT_REQUIRED`.

**Skill wiring**: in `.claude/skills/cairn-tdd-feature/SKILL.md`, add the atomicity gate as a sibling of the premise gate at the Phase-1→Phase-2 boundary (0 → proceed; 1 → surface stderr, block until tagged-or-split or `CAIRN_ATOMICITY_FIX=1`; 2 → RAISE_ISSUE → triager). `.claude/agents/phase-1-tdd.md` gains a note that the optional `## Contract` block exists and tagging is the cheap escape from a flagged clause. Regenerate the `dist/` mirror via `scripts/build_dist.py` (not hand-edited).

**Envelope (source files Phase 3 may write), verbatim from the plan-doc frontmatter:**
- `^scripts/lib/atomicity\.py$`
- `^checks/atomicity_guard\.py$`
- `^scripts/validate_architecture\.py$`
- `^templates/intent\.md$`
- `^tests/unit/test_atomicity\.py$`
- `^tests/unit/test_atomicity_guard\.py$`
- `^tests/unit/test_template_extraction\.py$`
- `^\.claude/agents/phase-1-tdd\.md$`
- `^\.claude/skills/cairn-tdd-feature/SKILL\.md$`
- `^docs/operational-reference\.md$`
- `^docs/plans/2026-05-30-cairn-trial-d-scope-split\.md$`

## Verification

Phase 4 runs and records (CI `dist-gate.yml` runs NONE of these — green CI ≠ green Trial D):
- `uv run pytest tests/unit/test_atomicity.py -q` — shared evaluator, table-driven over the real corpus: all 8 `m2-dogfood-extract-invariant-ids` behaviors pass `is_atomic` **untagged** (the false-positive denominator); `m5-f1` A3/A4/A6 (universal) + A8 (regression) and `m7` FLI-4/FLI-7 **flag when bare** and **pass when carrying the correct tag+declaration**; unknown tag fails; required-declaration tag with empty declaration fails; `trivial-existence` needs no declaration. Assertion cases route through `_run_assertion(tmp, "INV-TEST", {"type": "scope-split", "must-satisfy": [...]})` to pin type-wiring.
- `uv run pytest tests/unit/test_atomicity_guard.py -q` — subprocess integration (mirror `test_premise_guard.py`): exit 0 (absent block → fail-open + notice; all-atomic/validly-tagged; `CAIRN_ATOMICITY_FIX`), exit 1 (untagged clause flagged; unknown tag; empty declaration; absent block under `CAIRN_CONTRACT_REQUIRED`), exit 2 (missing intent; malformed YAML; `## Contract` heading present but unparseable). Each fail-open hazard (flush-left heading inside fence; fenced code inside a clause scalar; non-yaml fence before yaml; stray bare fence) gets a paired passes-0 / non-atomic-fails-1 test proving no silent bypass.
- `uv run pytest tests/unit/test_template_extraction.py -q` — eight-heading-in-order assertion still green PLUS new `## Contract` heading-present + yaml-parses assertion.
- `uv run pytest -q` — full suite, prior count + new tests, 0 fail.
- `uv run python scripts/validate_architecture.py` — `ALL CHECKS PASSED`, no regression.
- `bash scripts/smoketest_hooks.sh` — `PASS atomicity_guard.py` (clean import under bare `python3`).
- Drift audit: the tag set documented in `templates/intent.md` equals `scripts/lib/atomicity.EXCEPTION_TAGS`.
- Wiring check: grep confirms the atomicity gate step is present in `.claude/skills/cairn-tdd-feature/SKILL.md` and its `dist/` mirror; `docs/operational-reference.md` env-var table lists `CAIRN_ATOMICITY_FIX` and `CAIRN_CONTRACT_REQUIRED`.

## Risk Surface

The shy heuristic plus the always-available tag escape can degrade into a rubber stamp: operators learn to tag everything `trivial-existence` (no declaration) and every clause passes — the gate is green while atomicity is unenforced. Equally, a too-eager `is_atomic` (false positives above 10%) trains operators to game it, the failure D3 names. Neither shows as a test failure: the suite asserts the heuristic's encoded behavior, not whether real-world clauses are genuinely atomic. The drift audit catches tag-set divergence but not heuristic mis-calibration; that needs the deferred 3-intent measurement.

## Feature-Local Invariants

- **FLI-1 (single source of truth):** `scripts/lib/atomicity.py` is the only definition of `EXCEPTION_TAGS`, `is_atomic`, and `check_clauses`; both the CLI gate and the validator assertion import it — they cannot diverge on the tag set or pass/fail logic (mirrors `premise_match.grounded` shared by `premise_guard` and the validator).
- **FLI-2 (fail-open on absence, fail-closed on malformation):** absent `## Contract` block → exit 0 with a visible stderr notice (never silent); a `## Contract` heading present but yielding no parseable block → exit 2. Absence under `CAIRN_CONTRACT_REQUIRED=1` is the one configured exception (→ exit 1).
- **FLI-3 (tag is a one-line escape, never a hard wall):** every clause `is_atomic` flags can pass by carrying a valid tag + (where required) a non-empty declaration; the gate never blocks a clause that cannot be tagged-or-split.
- **FLI-4 (declaration semantics):** `trivial-existence` needs no declaration; the other three tags require a non-empty declaration; an unknown tag always fails.
- **FLI-5 (ADD-not-REPLACE template):** the eight prose section headings remain present and in order after the `## Contract` block is added.
- **FLI-6 (template↔code tag parity):** the four tags documented in `templates/intent.md` equal `scripts/lib/atomicity.EXCEPTION_TAGS` exactly.

## Explicit Scope-Out

- No 3-intent false-positive measurement this session (build + tests only; heuristic frozen at close).
- The `## Contract` block stays OPTIONAL and fail-open-with-visible-notice; mandatory-by-default is out of scope (would require a `/decision` per ADR D6 migration gating).
- No syntactic EARS enforcement — EARS phrasing is template guidance only (the named failure mode "has no syntactic hook to catch it," ADR §Context/D7).
- No source-comprehension / execution layer — nothing parses or runs cited tooling; only tag-presence + declaration-presence are checked.
- No verification of tag *correctness* or declaration *truth* — semantic mis-tagging stays operator-review-bound (the same honest limit ADR D7 records for premise-grounding: it "does not catch a correct quote the author misreads").
- No replacement of the eight prose headings — `## Contract` is purely additive.
- No new orchestrator, MCP, daemon, or state layer (ADR "Out of scope": M4 retired the substrate; this does not re-add it).

## Premise Grounding

<!--
Each premise pins a verbatim quote from live source the intent depends on.
premise_guard.py diffs these against disk at the Phase-1→Phase-2 boundary.
-->

```yaml
premises:
  - source: docs/adr/cairn-thin-substrate-direction.md
    quote: |
      3. **Scope-split rule.** Atomic-primitive check on `must-satisfy`. Authoring-time hook. Atomicity exceptions named in D3.
    label: "ADR D2.3 mandates the scope-split rule this feature builds."
  - source: docs/adr/cairn-thin-substrate-direction.md
    quote: |
      The scope-split rule checks atomicity: a clause is atomic iff verifiable by a single tool call or single file check.
    label: "ADR D3 defines atomicity — the contract the heuristic encodes."
  - source: docs/adr/cairn-thin-substrate-direction.md
    quote: |
      Clauses without a tag must pass atomicity.
    label: "ADR D3: untagged clauses are atomicity-checked — the check_clauses bare-string rule."
  - source: docs/adr/cairn-thin-substrate-direction.md
    quote: |
      Four named exception classes do not have to be atomic but must be tagged:
    label: "ADR D3 names the four exception classes — EXCEPTION_TAGS."
  - source: docs/adr/cairn-thin-substrate-direction.md
    quote: |
      authors can write grammatically-correct EARS that should fail atomicity, with no syntactic hook to catch it.
    label: "ADR §Context: no syntactic EARS hook — grounds the no-EARS-enforcement scope-out."
  - source: docs/adr/cairn-thin-substrate-direction.md
    quote: |
      it does *not* catch a correct quote the author misreads.
    label: "ADR D7 honest-limit on premise-grounding — mirrored by the no-tag-correctness scope-out."
  - source: checks/premise_guard.py
    quote: |
      if os.environ.get("CAIRN_PREMISE_FIX") == "1":
    label: "premise_guard bypass-env early-return — atomicity_guard mirrors it with CAIRN_ATOMICITY_FIX."
  - source: checks/premise_guard.py
    quote: |
      def _extract_premise_block(text: str) -> str | None:
    label: "Fence-state-machine extractor cloned for ## Contract extraction."
  - source: checks/premise_guard.py
    quote: |
      def _section_has_premises(text: str) -> bool:
    label: "Fail-closed backstop cloned as _section_has_contract for the exit-2 path."
  - source: checks/premise_guard.py
    quote: |
      Exit codes (mirror role_guard.py): 0 = all premises grounded, or no section /
    label: "premise_guard exit-code structure (0/1/2) that atomicity_guard mirrors."
  - source: scripts/validate_architecture.py
    quote: |
      def _run_premise_grounding_assertion(
    label: "Sibling assertion fn _run_scope_split_assertion is added beside this one."
  - source: scripts/validate_architecture.py
    quote: |
      if atype == "premise-grounding":
        return _run_premise_grounding_assertion(project_root, inv_id, assertion)
      return None
    label: "_run_assertion if-chain tail — the scope-split branch is registered before the final return None."
  - source: scripts/lib/premise_match.py
    quote: |
      The validator's premise-grounding assertion and the premise_guard CLI gate both
      route their match test through `grounded`, so they cannot diverge on tolerance.
    label: "Shared-lib single-source pattern (FLI-1) that scripts/lib/atomicity.py mirrors."
  - source: templates/intent.md
    quote: |
      ## Premise Grounding
    label: "The new ## Contract block is added AFTER this existing block in templates/intent.md."
  - source: docs/plans/2026-05-30-cairn-trial-d-scope-split.md
    quote: |
      eight-heading-in-order assertion still green PLUS new `## Contract` heading-present + yaml-parses assertion.
    label: "Plan-doc Verification: test_template_extraction.py eight-heading assertion stays green (ADD-not-REPLACE)."
```
