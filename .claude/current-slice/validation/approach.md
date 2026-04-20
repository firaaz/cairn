# Phase 2 Approach — compression/slice-2-state-machine

## Strategy

Thirteen RED test files, one per intent-specified defect (B2, B3/B4, B6, B7,
B8, B9, B10, B11, B12, B13, B14, B15, B16). Each test imports the live module
(`slice_orchestrator` or `checks/role_guard.py`) as public interface;
tests monkey-patch `dispatch_phase_agent`, `Popen`, `subprocess.run`,
`time.sleep`, `_parse_structured_tail`, and module-level path constants
(`SLICE_YAML`, `DEBUG_DIR`) rather than reach into internals. `role_guard` is
exercised end-to-end by subprocess (stdin JSON, env vars, exit code).

## RED evidence

`uv run pytest` on the thirteen files: **30 failed, 4 passed**. The four
incidental passes are negative-control sanity cases bundled with the RED
sets (well-formed YAML still parses at B12; slice.yaml still parses
post-SIGTERM at B13). Every assertion tied to a B-defect target fails for
the intended reason — no `_git` helper, no `close_slice` call site, no
signal handler, `AGENT_ENVELOPE` parsed as regex not JSON, `_parse_clusters`
line-based, no FAILED classification, etc.

## Boundaries respected

Source reads limited to `slice_orchestrator.py` and `role_guard.py` public
surface — no look-ahead at Phase 3 work. Test envelope matches `intent.md`
frontmatter `envelope:` exactly. No production code, no ADR edits.

## Ambiguities resolved from intent

- B14 redispatch-commit timing: commit after persisting `current_phase:
  target` and before `phase = target; continue` — test asserts commit
  message prefix and yaml state at the moment Phase 1 re-enters.
- B8 retry count: `CAIRN_FAILED_TRANSIENT_MAX_RETRIES=3` drives three
  `sleep` calls totalling 1+4+16=21 s (tolerance 21–30 s for overhead).
- B2 log-filename shape: `{slice-slug}-phase-3-cluster-{name}-{ts}.log`
  where slug replaces `/` with `-` and ts = `YYYYMMDDTHHMMSSZ`.
- B16 implicit-cluster path: empty `clusters.yaml` OR every `files: []`
  collapses to one dispatch whose envelope is the intent envelope; empty
  intent envelope short-circuits to FAILED without any dispatch.

No unresolved ambiguity → status OK.
