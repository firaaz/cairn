# close-review (intent-review, fresh context) — using-cairn carrier + cairn-intent skill (Approach D)

Reviewed: live diff against ADR `docs/adr/using-cairn-carrier-contract.md` (D1–D7). No constructor
claims relied upon — every clause verified against the live files, run output, and empirical carrier
invocation. Date 2026-06-01.

## Verdict: PASS (with one ADR-text discrepancy recorded as residual risk, not a block)

## 1. contract-clause-check

**D1 — Realization (SessionStart command emitter, honest-minimal).** SATISFIED.
`checks/using-cairn-carrier.sh:1-62` is a bash `type: command` emitter; `.claude/settings.json:24-32`
registers it under `hooks.SessionStart` as `type: command`. No Python module introduced (verified:
`git status --porcelain | grep .py` → only the three `tests/unit/` files; no module under
`scripts/`/`checks/`). Not a fourth enforcement guard — it always `exit 0` (line 61), never denies.

**D2 — Fired definition (marker + dynamic pointer / no-intent; render-tested).** SATISFIED.
First emitted line is the literal `CAIRN_CARRIER_FIRED` (`carrier:38`). Resume path resolves the
pointer from `.claude/handoff.md` (`carrier:44-52`); empty/missing handoff emits
`cairn: no active intent on record` (`carrier:57`). Render-tested in
`test_using_cairn_carrier.py` (first-line marker `:79-80`, no-intent `:91-92`, pointer-on-open
`:95-100`), all via subprocess against a fixture `CLAUDE_PROJECT_DIR`. rc==0 asserted in
`_run_carrier:57`. Host-injection correctly NOT unit-tested (Trial-E scope — stated `:12-14` of the
test docstring and ADR D2).

**D3 — Budget (byte-clamp, env-overridable).** SATISFIED. `BUDGET_BYTES="${CAIRN_CARRIER_BUDGET_BYTES:-8000}"`
(`carrier:26`); `emit() { head -c "$BUDGET_BYTES"; }` (`carrier:35`) clamps the whole emission block
(`carrier:59`). Tested: `CAIRN_CARRIER_BUDGET_BYTES=32` clamps to ≤32 bytes (`test:138-142`); default
≤8000 (`test:145-146`). No hardcoded size — env override present, documented in the file header
(`carrier:24-25`).

**D4 — Fallback (Step 1 unconditional, never branches on carrier).** SATISFIED.
`cairn-intent/SKILL.md:49` (Step 1): "This step is the carrier's fallback: if the SessionStart carrier
did not fire, load/form here explicitly — the carrier is an optimization, not the only path (D5)."
No conditional on carrier state. The workflow node `load-or-form-intent`
(`workflows/cairn-intent.yaml:16-65`) has `executor: conversation` and `allowed_inputs` that include
`.claude/handoff.md` + `intent.md` but NOT a carrier signal — empirically confirmed
(`test_cairn_intent_load_or_form_node.py:34-37` asserts `"carrier" not in inputs`; passes).

**D5 — Neutral, state-accurate emission (L-012 / INV-002).** SATISFIED for neutrality + state-awareness;
ADR sub-claim on read-only is overstated (see residual risk).
- Neutral: grep of the emission block (`carrier:37-59`) for `run the|you must|do not proceed|cannot|
  /start|please|should` → NONE. Tests assert the banned-imperative list absent on BOTH no-intent
  (`test:117-122`) and resume (`test:125-132`) paths.
- State-aware: the resume grep requires the thread token `open` (`carrier:45` regex
  `intent\.md[[:space:]]+open([[:space:]]|$)`). Empirically verified: a `deferred` thread → no-intent;
  an `open` thread → pointer+scope; a `blocked` thread → no-intent. Test `:106-111` pins the deferred
  case. INV-002 `{open, blocked, deferred}` honored: only `open` is treated as active.

**D6 — Distribution (cairn-internal only).** SATISFIED.
`scripts/build_dist.py` — `grep using-cairn` → NONE. `.claude-plugin/hooks-template.json` —
`grep using-cairn|SessionStart` → NONE. Registered ONLY in local `.claude/settings.json` (parses:
`json.load` OK). The settings command uses `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`, matching
the three existing guards — cairn self-consumes via its own `.slice-system → .` symlink (INV-011),
which is the canonical internal-dogfood wiring, not a consumer leak. Test `:168-174` asserts the
carrier absent from `build_dist.py`; `:152-165` asserts the SessionStart registration. Both pass.

**D7 — Acceptance coverage.** SATISFIED. Tests cover fired-detection (D2), the unconditional
load-or-form fallback + the previously-uncovered load-or-form node (D4 — the gap the deferred-carrier
close-review flagged, now closed by `test_cairn_intent_load_or_form_node.py`), neutral + state-aware
emission (D5), and the budget clamp (D3).

**using-cairn frontmatter YAML fix (the F1 unquoted-colon-space bug).** SATISFIED.
`using-cairn/SKILL.md` frontmatter parses under `yaml.safe_load` (verified directly); the `description`
value contains no bare `: ` (rewritten to avoid it). Regression guard:
`test_cairn_intent_skill_conformance.py:33-36`.

## 2. evidence-adequacy-check

Tests prove the clauses for this diff size (one ~60-line bash emitter, two SKILL docs, one settings
block, three test files). Render-vs-host boundary is honestly drawn and documented in-test. Coverage
is proportionate, not thin.

Claimed-but-untested (all honestly disclosed in ADR/skills, not silent gaps):
- **Host injection ("fired on host")** — Trial-E integration observation, dep-honest to leave at unit
  (ADR D2/R5, test docstring `:12-14`). Accepted.
- **Read-only "bare-marker" suppression (D5 line 85)** — NOT implemented and NOT unit-tested; see
  residual risk. The ADR's "Unit-tested" on this specific sub-clause is inaccurate.
- **≤2k-token budget** — only a byte proxy is enforced; token-exact CI gate is dep-forbidden and
  recorded EXPOSED (ADR D3). Accepted.

## 3. scope-check

In-scope writes, all present and correct:
`checks/using-cairn-carrier.sh`, `.claude/skills/cairn-intent/SKILL.md`,
`.claude/skills/using-cairn/SKILL.md`, `.claude/settings.json` (SessionStart only), and the three
`tests/unit/` files. No canonical edit leaked into `build_dist.py` or `hooks-template.json` (greps
clean). No new Python module (honest-minimal holds). No edit through `.slice-system/`.

One untracked file outside the seven-file contract: `.claude/skill-runs/cairn-intent-loop-build/
build-workflow.js` — a 22k orchestration scratch driver for the loop's own three-increment build,
living inside the skill-run workspace. It is an ambient loop artifact, not a canonical-source write
and not part of this increment's surface; no scope violation.

## Test evidence (run live)

- `uv run pytest tests/unit/test_using_cairn_carrier.py test_cairn_intent_skill_conformance.py
  test_cairn_intent_load_or_form_node.py -q` → **19 passed**.
- `uv run pytest -q` (full suite) → **638 passed, 2 skipped, 2 xfailed** — no regressions.

## Residual risk

ADR D5 line 85 states the carrier "on a read-only / no-write session emits at most the bare marker.
Unit-tested." This is not implemented — a SessionStart hook fires before any tool use and has no
read-only signal in its stdin payload, so it CANNOT detect read-only; the carrier has no such branch
and no test exercises one. The implementation instead achieves **neutrality** (no-intent → marker +
neutral fact line), which is the actual L-012 defense and is sound. The defect is in the ADR's claim,
not the code. Recommend a one-line ADR correction (D5: replace the read-only-suppression sub-clause
with "achieves neutrality on every path; read-only detection is infeasible at SessionStart") so the
contract text stops asserting an untestable, unimplemented behavior. Non-blocking: the code is correct
and honest; only the ADR prose overreaches.
