# Intent Challenge Report

Registry: `cairn-intent`
Stage: `cairn-intent-challenge`
Role: `intent-challenger`
Case: `trial-e-w1-case-05`
Intent: `.claude/skill-runs/trial-e-w1-case-05/intent.md`

## Scope

This challenge used only the case intent, the source cited by its Premise
Grounding, `docs/adr/intent-management-loop.md`, and `checks/premise_guard.py`.
It did not continue into construction or close review.

## Premise-Source-Checks

### P1

- Intent premise source: `checks/atomicity_guard.py`
- Intent quote:

  ```python
  intent_path = Path(argv[1])
  ```

- Intent label: `atomicity_guard reads the intent path directly from the CLI argument`
- Mechanical grounding: pass. The quoted line is live at
  `checks/atomicity_guard.py:108`.
- Semantic support: pass. `main(argv)` validates argument presence at
  `checks/atomicity_guard.py:98-101`, assigns `intent_path = Path(argv[1])` at
  `checks/atomicity_guard.py:108`, then immediately checks and reads that same
  path at `checks/atomicity_guard.py:109-113`. There is no live rebasing through
  `CLAUDE_PROJECT_DIR`, `PROJECT_ROOT`, or the cairn root between assignment and
  the readability check.
- Related contract support: the unreadable-intent behavior is live in adjacent
  source. A non-file path prints `atomicity_guard: intent not readable:
  {intent_path}` and returns `2` at `checks/atomicity_guard.py:109-111`; an
  `OSError` while reading prints `atomicity_guard: cannot read intent: {exc}` and
  returns `2` at `checks/atomicity_guard.py:112-116`.
- Challenge note: the premise quote itself grounds direct CLI path handling. The
  unreadable-failure claim is supported by adjacent live source, not by the
  quoted single line alone; this is acceptable here because the Contract
  separately requires preserving unreadable-intent failure behavior.

## Semantic-Counterfactual-Search

- Stale-comment counterfactual attempted: `checks/atomicity_guard.py:22-23`
  mentions `CLAUDE_PROJECT_DIR (or cwd) for the intent path resolution`, but the
  executable code does not define a project-root path for the intent argument and
  does not join `argv[1]` to one. Treating that comment as license to resolve the
  intent path under `CLAUDE_PROJECT_DIR` would contradict the live behavior at
  `checks/atomicity_guard.py:108-113`.
- Wrong-model counterfactual attempted: `checks/premise_guard.py` resolves
  premise `source` paths against `PROJECT_ROOT` at
  `checks/premise_guard.py:22-23` and `checks/premise_guard.py:100`, but that is
  premise-source resolution for the approval gate, not
  `atomicity_guard.py` intent-argument resolution. Importing that model into
  `atomicity_guard.py` would contradict the cited source.
- Verbatim-grounding counterfactual attempted: a future change could preserve the
  literal line `intent_path = Path(argv[1])` while rebasing or replacing
  `intent_path` later, which would pass `premise_guard.py`'s quote-presence check
  as described by `checks/premise_guard.py:95-114` while contradicting current
  behavior. The current intent blocks that counterfactual with its
  `must-not-violate` clause forbidding project-root or cwd handling changes, and
  live source confirms the intended behavior.
- ADR alignment: the challenge stage is meant to attack premises against live
  source before construction (`docs/adr/intent-management-loop.md:61-64`) and the
  slice-#25 counterfactual is explicitly the front-challenge acceptance gate
  (`docs/adr/intent-management-loop.md:88-90`, `docs/adr/intent-management-loop.md:100-104`).

## Verdict

Pass. Challenged premise ids: `P1`.

The cited quote is live, the label faithfully describes the source, and the
source supports the Contract claims that construction must preserve direct
`Path(argv[1])` handling and unreadable-intent failure behavior. The stale-comment
and wrong-model counterfactuals are blocked as invalid interpretations, not as
defects in this intent.
