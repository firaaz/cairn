# Phase 2 Approach — triager-superseded-test-heuristic

Skeptic charter: drive `detect_superseded_test_signal` and `dispatch_triager`
into existence via failing tests that encode the intent contract exactly.
Production code is assumed absent; all tests RED at Phase 2.

## Test surface

One new file `tests/unit/test_triager_superseded_heuristic.py`, two layers:

**Pure-function layer (S1).** `detect_superseded_test_signal(summary, intent)`
is stateless string-in / dict-or-None-out. The suite pins: the three
trigger classes (`supersede|superseded` literal with word boundaries;
`\bINV-\d{3}\b`; `\bDC-\d+\b` AND-gated by the same token appearing in
`intent`), case insensitivity, word-boundary semantics (`supersedes` and
`undersuperseded` do NOT fire — the regex is `\bsuperseded?\b`), empty
inputs, and evidence-list contract (list of matched tokens, deduped, in
first-match order).

**Call-site layer (S2).** `dispatch_triager` must thread the hint into the
JSON payload handed to the triager child process. Tests monkeypatch
`so._git` (fakes `git log -1 --format=%B <hash>`) and
`so._run_with_live_stderr` (captures the built `cmd` — last argv is
`json.dumps(inputs)` — returns a well-formed triager tail). A tmp
`.claude/current-slice/intent.md` carries the DC-code so the AND-gate
passes.

Three call-site cases: (a) signal fires → payload carries
`supersession_hint.hint == "likely_superseded"`; (b) no signal → key
absent; (c) `_git` raises → key absent, no crash (fail-open).

## Non-goals in RED

The RED suite does not assert triager LLM behavior (prompt amendment is
advisory, out of unit-test reach) nor re-verify `VALID_TRIAGER_ACTIONS`
membership (owned by `test_dispatch_contract_separation.py`). The
orchestrator's non-override contract ("action round-trips unchanged") is
already covered by the existing dispatch-contract suite, so not duplicated.

## Why this shape

Pure-function split keeps the regex contract human-auditable and
reversible: false-positive tuning is a one-line regex edit with no
dispatch-layer churn. Call-site tests pin the injection point (input dict,
not a side channel) so a future triager-transport refactor cannot silently
drop the hint.
