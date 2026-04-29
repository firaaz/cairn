# Cairn Bug-Finding Audit — 2026-04-29

**Status:** In progress — Pass 0 stub; expansion passes A-K running. 47 seed findings indexed, full evidence to be folded in as agent reports return.
**Plan:** `/Users/mohammed.farook/.claude/plans/yes-log-the-patterns-temporal-cray.md`
**Mandate:** Find, don't fix. No production code outside `docs/`, `docs/lessons.md`, and the project board is changed by this audit.

## Scope

- Cairn methodology repo at `/Users/mohammed.farook/Developer/lab/cairn`.
- Consumer-bridge surface (cairn-knowledge MCP server, `cairn_query` extractors, slash commands and hooks as consumed by downstream projects via the `.slice-system → /path/to/cairn` symlink).
- Live reproduction in `complex-rag-analysis` (Pass K).

## Methodology

**Pre-audit (complete):** 5-probe cross-layer drift sweep + 3 deep-dive code reads (lifecycle/dispatch/resume; role-guard/agent prompts; consumer-bridge MCP/extractors). Yielded 47 seed findings with file:line citations.

**Expansion (in progress):**
- Pass A — Pattern logging in `docs/lessons.md` for C1-C10 (especially C8).
- Pass B — Drift sweep on the un-probed slash commands (handoff, integration-sweep, refresh-architecture, decision, catchup, status, new-adr).
- Pass C — Verdict-OK adversarial deep-dive (Phase 4 blind spots).
- Pass D — Test-coverage × cluster matrix.
- Pass E — Symlink-recursion grep.
- Pass F — Hook silent-no-op audit.
- Pass G — Instruction-only enforcement audit (extends pre-audit catalog).
- Pass H — Cost discipline + telemetry truthfulness.
- Pass I — MCP server boundary (kuzu unavail / oversized result / malformed JSON-RPC / missing snapshot).
- Pass J — Cross-validate findings against existing tests.
- Pass K — Consumer-bridge live reproduction in complex-rag-analysis + extension.

## Severity rubric

- **S1 — Pipeline integrity / silent correctness.** Verdict-OK-with-bugs, idempotency breakage, context-isolation breach, role_guard bypass, symlink-recursion hazard. Always issue + doc.
- **S2 — Cross-repo blast radius.** Consumer-affecting: orchestrator outputs wrong path, schema field consumers depend on disappears, MCP returns malformed JSON. Always issue + doc.
- **S3 — Cross-layer drift, no current user impact.** Documented mechanism absent in code but no live wrong-output yet. Doc only, tagged "rot".
- **S4 — Doc/cosmetic.** Stale prose, dead reference, comment lies. Doc only.
- **Promote rule:** if a finding could reach S1 under a plausible adjacent change (Cluster C10 precedent), promote one level.

## Cluster index

- **C1** Empty & uncommitted handoffs
- **C2** Schema drift between layers
- **C3** Staging surface gaps & stale artifacts
- **C4** Inherited-threshold misfire
- **C5** Re-dispatch scope creep
- **C6** Silent behavioral divergence under prompt pressure
- **C7** Protocol-prose drift & doc desync
- **C8** Verdict-OK-but-bugs-present
- **C9** Code-level premises not verified at Phase 0
- **C10** Test inversion under enforcement-set widening
- **C11+** Reserved for new clusters from expansion passes

## Findings index (135 total)

**Severity counts (approximate):** S1: ~58 · S2: ~58 · S3: ~19 · S4: 0. **Bug-ceiling stop condition was hit** at finding 75; continued because yield stayed high through batch 2 (~12/pass) and consumer-bridge live reproduction (Pass K) had unique cross-repo blast-radius signal. Pass K-3 yield dropped to ~4 findings; that triggered the natural stop.

Number ranges by source:
- F-001 — F-050: pre-audit deep-dive (drift + lifecycle + dispatch + resume + role-guard + consumer-bridge + Pass E symlink scan)
- F-051 — F-071: Pass B (drift on remaining slash commands) + Pass F (hook silent-no-op)
- F-100 — F-108: Pass C (verdict-OK blind-spot taxonomy)
- F-200 — F-224: Pass G (instruction-only enforcement audit on slash-command full.md docs)
- F-301 — F-309: Pass H (cost discipline + telemetry truthfulness)
- F-400 — F-407: Pass I (MCP server boundary)
- F-500 — F-504: Pass K-1 (consumer-bridge live reproduction in complex-rag-analysis)
- F-510 — F-515: Pass K-2 (slash-command cross-repo)
- F-530 — F-533: Pass K-3 (hooks + fleet + upgrade-doc gaps)

| F-ID | Sev | Cluster | Component | One-line | Evidence anchor |
|---|---|---|---|---|---|
| F-001 | S3 | C7 | start-slice gate | D3 ADR-slug gate documented but absent from orchestrator code | `start-slice.full.md:33` vs `scripts/slice_orchestrator/*` (no impl) |
| F-002 | S2 | C7 | close-sequence | Wipe-prose claims slice.yaml-only survives; code stages sweep.yaml + handoff.md too | `start-slice.full.md:250-252` vs `lifecycle.py:526` |
| F-003 | S1 | C6 | phase-1-writer | "No source reads" rule has no code-level enforcement | `phase-1-writer.md:7` vs `role_guard.py` (no read-class deny) |
| F-004 | S2 | C3 | lifecycle commit | intent.md re-staged on every phase commit | `lifecycle.py:202-204` |
| F-005 | S1 | C3 | close_slice | sweep-results mkdir OSError uncaught — close crashes mid-sequence | `lifecycle.py:127` |
| F-006 | S1 | C3 | close_slice | Partial-wipe recovery missing; `git add -u` stages partial deletions | `lifecycle.py:513-522` |
| F-007 | S1 | C3 | close idempotency | `_is_slice_already_closed` Signal 3 trips false on heartbeat `.heartbeat` | `lifecycle.py:168` vs `telemetry.py:381` |
| F-008 | S1 | C3 | init_new_slice | Commit failure swallowed; state returned as if committed | `lifecycle.py:427-431` |
| F-009 | S1 | C3 | Phase 4 → close | Killed mid-transition re-dispatches Phase 4 on resume; non-idempotent | `lifecycle.py:276-283` |
| F-010 | S2 | C3 | _abort_slice | Commit failure swallowed; resume reconcile refuses on missing commit | `lifecycle.py:394-398` |
| F-011 | S3 | C2 | state-machine | Orphan states: `status: integration` written only by resume; `current_phase: 5` never written | `lifecycle.py` + `resume.py` |
| F-012 | S2 | C4 | retry math | Transient classification mutation across retries breaks B8 backoff sequence | `dispatch.py:358-370` |
| F-013 | S3 | C2 | telemetry | Timeout mid-retry leaves stale classification in state/telemetry | `dispatch.py:368-370` |
| F-014 | S2 | C4 | retry budget | Second-failure dispatch after FAILED bypasses B8 reclassification | `lifecycle.py:286-297` |
| F-015 | S1 | C3 | Phase-3 fan-out | ThreadPool `result()` raises on first failed worker; orphans the rest | `dispatch.py:506` |
| F-016 | S2 | C3 | Phase-3 envelope | `json.dumps(cluster["files"])` no try/except; malformed clusters kill entire phase | `dispatch.py:490` |
| F-017 | S1 | C4 | redispatch cap | Counter incremented after persist; persist-failure path skips it (B15 violation) | `lifecycle.py:340-353` |
| F-018 | S2 | C2 | triager fallback | Malformed-output ESCALATE suppresses original parse error | `dispatch.py:421-436` |
| F-019 | S2 | C2 | resume corruption | Corrupt slice.yaml + corrupt result.json → generic refuse, not corruption refuse | `resume.py:165, 173-180` |
| F-020 | S3 | C2 | resume DEGRADED | DEGRADED → IN_PROGRESS conversion drops `final_commit` for Row 7 | `resume.py:204, 246-252` |
| F-021 | S3 | C2 | resume Row 10 | Doesn't distinguish missing slice.yaml from in-progress; falls to default refuse | `resume.py:269-270` |
| F-022 | S2 | C2 | resume defaults | Both-None `rj_phase`/`slice_phase` silently defaulted to phase 1 | `resume.py:208-209` |
| F-023 | S3 | C2 | resume regex | Int cast at `_HANDOFF_RX` group(1) assumes regex airtight; ValueError if loosened | `resume.py:213` |
| F-024 | S1 | C3 | concurrency | Phase-3 ThreadPool workers mutate module-level `_state` without sync; cost/token totals corruptible | `telemetry.py` `_state` + `dispatch.py:487-506` |
| F-025 | S2 | C3 | heartbeat race | `.heartbeat` write vs atexit `_persist_state` race; partial rename leaves inconsistent file | `telemetry.py:381 & 437` |
| F-026 | S2 | C3 | _active_child race | Mutated by main thread + signal handler without lock | `dispatch.py:65`, `lifecycle.py:226` |
| F-027 | S2 | C3 | heartbeat death | New daemon started; old hung daemon never stopped | `telemetry.py:415` |
| F-028 | S1 | C3 | SIGTERM | Status=SIGNALED set in _state but not immediately persisted; SIGKILL loses record | `lifecycle.py:242` |
| F-029 | S1 | C6 | enforcement bypass | **Bash-heredoc completely bypasses envelope + role_guard for ALL phases — primary enforcement gap** | `role_guard.py:22-24`, `scope-guard.sh:48` |
| F-030 | S1 | C6 | DC-4 | Phase-4 "never `git commit`" has no code enforcement | `phase-4-integrator.md:27` |
| F-031 | S1 | C2 | snapshot pinning | AGENT_ENVELOPE not synthesized for Phases 2/3/4 → MCP queries unpinned HEAD | `dispatch.py:181-184` |
| F-032 | S2 | C6 | triager preference | "Test-amendment recommended" supersession-hint route is instruction-only | `issue-triager.md:11` |
| F-033 | S1 | C2 | regex anchoring | `^tests/` used with `re.search`; matches `.claude/tests/x.py`, `old_tests/x.py` | `role_guard.py:55` |
| F-034 | S2 | C6 | Bash write-class | Phase-2-skeptic `cp`/`dd`/`tee` unblocked by role_guard (Bash not in WRITE_TOOLS) | `role_guard.py:22-24` |
| F-035 | S2 | C2 | triager ABORT | Target_phase validation absent on ABORT branch | `lifecycle.py:333` |
| F-036 | S2 | C5 | redispatch loop | Same RAISE_ISSUE on retry → triager not called again, orchestrator aborts (no re-eval chance) | `lifecycle.py:306, 313-318` |
| F-037 | S3 | C7 | triager amendment | `amendment` field documented in prompt; orchestrator never reads it | `issue-triager.md` + `lifecycle.py` |
| F-038 | S2 | C3 | redispatch cost | Cost dict not reset on redispatch; ghost double-count if atexit fires between | `telemetry.py:103` |
| F-039 | S1 | C7 | MCP tenancy | Extractors CWD-relative; in consumer context they scan consumer's docs, not cairn's | `scripts/cairn_query/__init__.py:63-68` |
| F-040 | S1 | C2 | DB collision | Default kuzu DB path CWD-relative; consumer + cairn write to separate stores | `scripts/cairn_query/__init__.py:24` |
| F-041 | S1 | C7 | slice extractor | `_run_git("log", ...)` no explicit `cwd`; indexes consumer's slice history in consumer context | `scripts/cairn_query/extractors/slice.py:72-76` |
| F-042 | S1 | C7 | feature extractor | `Path(".claude/features")` CWD-relative; cairn's features missing in consumer queries | `scripts/cairn_query/extractors/feature.py:16, 68` |
| F-043 | S1 | — | tenancy design | **No consumer-tenancy model.** Consumer ADRs/lessons/features cannot be merged or queried alongside cairn's. Design gap → follow-up ADR | `mcp_servers/cairn_knowledge/server.py` (no tenancy code) |
| F-044 | S2 | C6 | MCP fallback | Phase-1-writer mandates MCP queries; no documented fallback when consumer's MCP not wired | `phase-1-writer.md:9-13` |
| F-045 | S2 | C7 | upgrade-doc path | Wrong hook path: `scripts/role-cheatsheet.sh` vs actual `checks/role-cheatsheet.sh` | `docs/upgrading-from-pre-compression.md:30` |
| F-046 | S2 | C7 | upgrade-doc CWD | MCP-setup section omits CWD fix; `PYTHONPATH` alone insufficient because of F-039 | `docs/upgrading-from-pre-compression.md:71-81` |
| F-047 | S2 | — | ADR cross-repo | `/new-adr` writes consumer-side, but consumer's MCP (typically pointed at cairn) doesn't see it | `commands/claude-code/new-adr.md` + F-043 |
| F-048 | S1 | C7 | orchestrator CWD coupling | All ~20+ `Path(".claude/...")` constants in `slice_orchestrator/{core,lifecycle,dispatch,telemetry}.py` rely on `Path.cwd()` resolving to the consumer project root; no env-var-based root resolution. Combined with cwd-trap, all writes route to whatever cwd the orchestrator is invoked from. | `scripts/slice_orchestrator/core.py:68-71`, `lifecycle.py:55,75,126`, `telemetry.py:142`, `dispatch.py:384` |
| F-049 | S2 | C7 | root-resolution drift | `validate_architecture.py:_repo_root` uses `CLAUDE_PROJECT_DIR` env var + `git rev-parse --show-toplevel` fallback (and L41-46 docstring explicitly forbids `__file__`-based resolution because of `.slice-system` symlink canonicalization); `cairn_query/__init__.py`, `slice_orchestrator/*`, and `snapshot_diff.py` use bare `Path()` constants. Pattern-drift across the codebase. | `validate_architecture.py:30-55` (correct) vs `snapshot_diff.py:37-39`, `cairn_query/__init__.py:24,63-68`, all `slice_orchestrator/*` |
| F-050 | S3 | C7 | snapshot_diff CWD | `snapshot_diff.py:_resolve_root` uses `Path.cwd()` (per L37-39 docstring "A4"); not env-var based; could silently snapshot consumer's tree thinking it's cairn's | `scripts/snapshot_diff.py:37-39` |
| F-051 | S2 | C7 | refresh-architecture path | Prose says `.slice-system/scripts/validate_architecture.py` (works only in consumer); cairn's own invocations use `scripts/`; operational-reference uses `scripts/` too | `refresh-architecture.md:16` + `refresh-architecture.full.md:60` vs `docs/operational-reference.md:64` |
| F-052 | S3 | C7 | integration-sweep short-form | Skill prose omits `snapshot_diff.py` exit-code-2 (no-prior-snapshot creates baseline); full ref correctly documents it | `integration-sweep.md:12` vs `snapshot_diff.py:12-15,129-134` and `integration-sweep.full.md:60` |
| F-053 | S2 | C9 | Phase-4 sweep.yaml ownership | Phase-4-integrator prompt declares write to `.claude/sweep.yaml` (a control file, not artifact); L-009 documents the regression where Phase 4 clobbered `last-sweep-at-slice-id`; ownership boundary unclear | `phase-4-integrator.md:21` vs `lifecycle.py:526` + `docs/lessons.md:152-176` (L-009) |
| F-054 | S3 | C7 | handoff verifier invocation | Prose says verifier runs as final step of `/handoff`; passive voice doesn't clarify whether skill code or operator invokes; no shell call visible | `handoff.md:17` + `handoff.full.md:106-107` (UNCLEAR — needs runtime test) |
| F-055 | S3 | C7 | /status line count | Skill prose says 6-line dashboard with Cost line; `render_status.sh` emits 5 lines, no Cost; comment at L10 says "five-line" | `status.md:3,9-15` vs `scripts/render_status.sh:1-145` |
| F-056 | S2 | C7 | /status Cost source unimplemented | Skill says read `tokens_total`/`cost_total_usd` from `<slug>-result.json`; script reads zero JSON files (only YAML/MD); INV-009 promise unfulfilled | `status.md:24` vs `scripts/render_status.sh` (no JSON reads) |
| F-057 | S3 | C7 | catchup Mode A surfacing | Mode A prose says "read operational-reference.md § Phase Skill Guide and surface role/skill row" — instruction-only, no code or hook enforcement | `catchup.full.md:120` (UNCLEAR for code-binding) |
| F-058 | S2 | C2 | new-adr superseded-by format | Prose says `superseded-by: ADR-<NNN>`; identifier-scheme D9 mandates flat slug (`superseded-by: identifier-scheme`); validators match by `id:`, not numeric. New ADRs following prose break round-trip | `new-adr.full.md:82` vs `decision.py:81` + `semantic-identity.md` |
| F-059 | S3 | C7 | ADR_EDITORIAL_FIX additive loophole | Prose restricts to "typos and formatting"; hook check is `[[ "$NEW" == *"$OLD"* ]]` — any addition that preserves OLD passes; could append entire new sections | `new-adr.full.md:100-102` vs `reversibility-guard.sh:95-100` |
| F-060 | S2 | C6 | frontmatter-only check first-line-only | Hook checks only `head -1` of `old_string` for frontmatter prefix; multiline `old_string` with frontmatter line first + body changes after passes; comment in hook acknowledges the risk but prose doesn't | `reversibility-guard.sh:85` (and L83-84 comment) vs `new-adr.full.md:82-83` |
| F-061 | S2 | C2 | ADR status lifecycle + D3 gate | Prose mentions "Accepted (or Proposed)" but doesn't define transitions; D3 gate validates ADR file existence but NOT status; slice can reference `proposed`/`draft` ADR (violates spec-v1 §6 immutability) | `new-adr.full.md:56` + `decision.py:56-63` + `start-slice.full.md:33` (D3 missing status check) |
| F-062 | S3 | C7 | new-adr filename template post-migration | Step 3 template shows `docs/adr/<NNN>-<slug>.md`; identifier-scheme D7 Phase 2 completed flat-slug rename; `test_adr_rename_sweep.py` enforces `^[a-z][a-z0-9-]*\.md$` | `new-adr.full.md:30` vs `identifier-scheme.md` D7 + tests |
| F-063 | S1 | C6 | reality-check.sh jq missing | jq missing → `exit 0` silently; Python edits bypass ruff format+lint; CLAUDE.md flags this hazard explicitly | `reality-check.sh:8-10` |
| F-064 | S1 | C6 | reality-check.sh ruff missing | ruff missing → `exit 0` silently; Python files written unformatted/unchecked | `reality-check.sh:26-28` |
| F-065 | S1 | C6 | scope-guard.sh jq missing | jq missing → `exit 0` silently; envelope enforcement disabled completely; phase-3 implementer can edit anywhere | `scope-guard.sh:8-10` |
| F-066 | S1 | C6 | reversibility-guard.sh jq missing | jq missing → `exit 0` silently; ALL destructive-op blocks disabled (`git push --force`, `rm -rf`, ADR append-only) | `reversibility-guard.sh:8-10` |
| F-067 | S2 | C6 | reversibility-guard root-resolution fallback | `PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null \|\| pwd)}"` — silent fallback to `pwd` on env+git failure; ADR path canonicalization wrong | `reversibility-guard.sh:43` |
| F-068 | S2 | C6 | scope-guard root + EXPAND_ENVELOPE inconsistency | Same root fallback + EXPAND_ENVELOPE log writes to `.claude/current-slice/envelope-expansions.log` at fallback `pwd`; next phase reads from correct root, doesn't see log | `scope-guard.sh:14` + `scope-guard.sh:117-121` |
| F-069 | S2 | C6 | role-cheatsheet git checkout swallowed | `git checkout HEAD -- "$rel_path" \|\| return 0` swallows merge conflict, lock, perms; measurements artifact refresh skipped silently | `role-cheatsheet.sh:28-30` |
| F-070 | S2 | C6 | role-cheatsheet sed/awk silent parses | Malformed `slice.yaml` → sed/awk return empty; emit_generic falls through to "No active slice" message — masks corruption | `role-cheatsheet.sh:57-59` |
| F-071 | S1 | C6 | ADR_EDITORIAL_FIX trust boundary | Hook trusts env var; substring-containment check passes for any addition that preserves OLD; no diff/reason/context in `.claude/adr-editorial-fixes.log` | `reversibility-guard.sh:95-101` |
| F-100 | S1 | C8 | Intent-codification gap | Phase 2 codifies intent.md literally; broader user-held intent → manual testing finds gaps. **Definitionally unreachable by Phase 4.** | `lessons.md:307-310` (L-016) — today's live trigger |
| F-101 | S1 | C8 | Stale invariant statement passes | validate_architecture.py Check D matches grep pattern; if Statement amended but pattern not, stale evidence still passes | `validate_architecture.py:180-206,428-448` |
| F-102 | S1 | C8 | Sweep-notes phantom evidence | Phase 4 verdict only checks sweep-notes.md exists, never validates cited file:line still contains the claimed code | `phase-4-integrator.md:33` (no content-validation code) |
| F-103 | S1 | C8 | MCP mock returns stale Statement | Phase 4 cites Statement from MCP query; if MCP serves stale corpus (F-402), sweep-notes cite phantom truth | `phase-4-integrator.md:9-18,19-20` |
| F-104 | S1 | C8 | OK emitted without sweep-notes | Phase 4 emits stdout OK; killed before sweep-notes write; close_slice doesn't precondition on sweep-notes existence | `lifecycle.py:483-530` (no sweep-notes assertion) |
| F-105 | S1 | C8 | Envelope expansions unverified | Phase 3 EXPAND_ENVELOPE additions never re-validated against Phase 2 intent boundary; verdict OK ignores breaches | `scope-guard.sh:117-121` + no Phase-4 expansion audit |
| F-106 | S1 | C8 | Snapshot-diff blind to heredoc writes | snapshot_diff SCAN_RULES limited to 5 dirs; Bash-heredoc writes outside scan paths invisible to Phase 4 | `snapshot_diff.py:28-34` + L-018 |
| F-107 | S1 | C8 | Phase-2 amendments ignored | Phase 2 amendment recommendations are instruction-only; Phase 3 doesn't load handoff reasoning; Phase 4 verdict against old invariants. **Definitionally unreachable by Phase 4.** | `start-slice.full.md:60-62` + F-032/F-037 |
| F-108 | S1 | C8 | result.json vs slice.yaml drift | No run_id UUID correlating result.json + slice.yaml; resume can route to OK against inconsistent triple | `resume.py:243-253,260-270` |
| F-200 | S1 | C6 | Phase-artifact-committed gate | "Each phase's artifact must be committed before advancing" — no automated check; D3 gate documented but operator-only | `start-slice.full.md:29` |
| F-201 | S1 | C6 | D3 plural-message commitment | "MUST name every missing ADR slug" — D3 gate not implemented at all (cf. F-001); plural-message rule has no enforcement | `start-slice.full.md:39` |
| F-202 | S2 | C6 | Gate-failure blocking unenforced | "Do not proceed — this gate is what makes the whole system work" — no code blocks the transition | `start-slice.full.md:41` |
| F-203 | S1 | C6 | Tier-2 subagent file-list bound | "Read only the files listed. Do not expand" — instruction-only; no return-path audit logs files actually loaded | `catchup.full.md:77-80` |
| F-204 | S2 | C7 | Greenfield/modification read scope | "Do not read source code" / "public interfaces only" — no role_guard rule for `src/`; semantic-judgment-only | `start-slice.full.md:175-176` + `catchup.full.md:106` |
| F-205 | S1 | C6 | Phase-2 forced-enumeration | "Only then design the validation suite" — no gate verifies approach.md exists with enumeration before tests | `start-slice.full.md:49-52` |
| F-206 | S2 | C6 | Phase 3 must not load approach.md | role_guard.py doesn't deny phase-3-implementer Read on `validation/approach.md`; instruction-only | `start-slice.full.md:62` |
| F-207 | S1 | C6 | Completion wipe enforcement | "This is not optional" — no post-commit hook checks `.claude/current-slice/` is empty after `slice: complete` | `start-slice.full.md:210` |
| F-208 | S1 | C6 | D1 completion-gate unimplemented | "Slice MUST NOT transition to complete" on validator failure — no code calls validate_architecture.py during completion | `start-slice.full.md:219` |
| F-209 | S1 | C6 | D3 completion-gates unimplemented | "If either D3 gate fails, slice MUST NOT transition" — integration_gate.py + snapshot_diff.py exist but no completion-time call | `start-slice.full.md:240` |
| F-210 | S2 | C6 | Handoff prose-vs-pointer rule | "Tells next session where to look, not what to think" — no linter; verify_handoff.sh checks prefix only | `handoff.full.md:11` |
| F-211 | S2 | C7 | Handoff "no urge to explain" rule | Anti-pattern guidance; no detection mechanism (no first-person pronoun lint, no apology marker check) | `handoff.full.md:52` |
| F-212 | S1 | C6 | Handoff template structure | "Strictly follow templates/handoff.md" — no schema validator; agent can invent sections undetected | `handoff.full.md:15` |
| F-213 | S2 | C6 | Handoff byte-count telemetry | "One piece of telemetry worth printing is the byte count" — not actually printed/checked | `handoff.full.md:104` |
| F-214 | S1 | C6 | Completed-slice immutability | "Do not retroactively edit completed slices" — scope-guard.sh permits writes to `.claude/completed-slices/` | `integration-sweep.full.md:103` + `scope-guard.sh:60` |
| F-215 | S2 | C6 | ADR parse-robustness contract | refresh-architecture spec says "warn and skip malformed frontmatter" — no test asserts this; validator may fail cryptically | `refresh-architecture.full.md:13` |
| F-216 | S1 | C6 | Vague-invariant detection | "Each must be specific, testable; vague invariants worse than none" — no lint for "should/generally/probably" | `refresh-architecture.full.md:49` |
| F-217 | S2 | C6 | EDITORIAL_FIX semantic-change check | "Do not use for substantive content changes" — no semantic-change detector; substring containment passes (cf. F-059, F-071) | `new-adr.full.md:102` |
| F-218 | S1 | C6 | Firm ADR independent verification | "Run independent verification for firm decisions" — no commit-time gate; firm ADRs can ship without Phase 5 | `decision.full.md:96-113` |
| F-219 | S2 | C7 | Handoff voice rules | "No first person, no hedging, no maybe" — no prose-style linter | `handoff.full.md:19` |
| F-220 | S1 | C6 | Feature-file sync on decomposition change | "Prompt operator to update feature file" — no detector; orphaned slices invisible | `handoff.full.md:69` |
| F-221 | S1 | C6 | Read-before-Write contract | "CC 2.1.110+ requires Read before Write" — Cairn-level: no guard; relies on CC harness | `start-slice.full.md:93` + `handoff.full.md:31` |
| F-222 | S2 | C6 | D3 plural-message test | No test asserts D3 failure with 2+ missing ADRs names both | `start-slice.full.md:39-40` |
| F-223 | S2 | C6 | Constraint envelope production | `/decision` Phase 0 "produce constraint envelope" — no test verifies envelope was written or constraints cited | `decision.full.md:22` |
| F-224 | S1 | C6 | Constraint conflict surfacing | "Stop and surface conflict before proceeding" — no detector; agent can ignore conflicts | `decision.full.md:24` |
| F-301 | S1 | C2 | INV-009 advisory-only | Threshold check emits UserWarning + event; never raises or exits; thresholds default `None` (inert) | `core.py:507-533` + `dispatch.py:269-278` (catches all) |
| F-302 | S2 | C2 | Cost dict not bounded to slice | If same process runs multiple slices, cost dict accumulates; recompute uses entire dict | `telemetry.py:91-120,116-119` |
| F-303 | S2 | C3 | model_by_phase double-overwrite | Envelope-derived vs resolved-model written in succession; comment claims "honesty" but overwrites silently | `dispatch.py:264-282` |
| F-304 | S1 | C2 | Phase-3 cluster cost race | ThreadPool workers all key on `phase=3`; last-write-wins overwrites cluster costs (extends F-024) | `dispatch.py:486-518` + `telemetry.py:103-114` |
| F-305 | S2 | C2 | Redispatch cost-attr stale | Cost dict not reset across redispatches; aborted-attempt entries persist (extends F-038) | `lifecycle.py:332-355` |
| F-306 | S3 | C4 | Heartbeat death-chain zombies | Restart attempts spawn new daemons without reaping old; on chain failure, zombie threads accumulate (extends F-027) | `telemetry.py:410-431` |
| F-307 | S2 | C2 | Close partial-state window | Multi-step close_slice sequence; if interrupted between slice.yaml write and result.json write, second invocation exits early via `_is_slice_already_closed` | `lifecycle.py:435-571,442` |
| F-308 | S3 | C3 | Envelope parse fail → wrong cost attribution | If envelope unparseable, tokens=0 (cost=$0) but model_by_phase set to resolved model; result.md shows model with $0 | `dispatch.py:264-282` + `core.py:255,355` |
| F-309 | S1 | C2 | INV-009 breach not wired to abort | Breach event recorded; orchestrator continues normally; status=OK on overspend (compounds F-301) | `dispatch.py:269-278` (catch-all) |
| F-400 | S1 | C7 | Unknown entity_type → KeyError | `_ENTITY_MAP[entity_type]` unhandled on typo; may crash stdio or return opaque -32603 | `scripts/cairn_query/storage.py:121,210,223` |
| F-401 | S1 | C7 | search() unbounded result | No pagination, no max-size; large corpus → JSON-RPC overflow | `scripts/cairn_query/storage.py:221-239` |
| F-402 | S2 | C8 | rebuild_from_sources silent stale | On extraction failure, server continues with stale DB; lazy fallback uses CWD-relative `_DEFAULT_DB_PATH`; no in-band error | `mcp_servers/cairn_knowledge/server.py:131-136` |
| F-403 | S1 | C7 | snapshot_id no validation | Server accepts any string as snapshot_id; no SHA format check, no ref-existence check | `mcp_servers/cairn_knowledge/server.py:48-55,112-113` |
| F-404 | S2 | C2 | KuzuStorage lazy-init race | Concurrent tool calls hit `if _STORAGE is None` without lock; double-init contends on kuzu exclusive lock | `mcp_servers/cairn_knowledge/tools.py:28-36` |
| F-405 | S1 | C7 | Pydantic validation defaults silently | Missing fields default to `""`/`None`; agent receives malformed entity without error signal | `scripts/cairn_query/storage.py:119-170` |
| F-406 | S2 | C7 | Cypher escapes structural lockdown | `cypher()` accepts arbitrary queries; bypasses ROLE_DENY_READ on `docs/adr/**`; phase-1-writer can enumerate Decisions | `mcp_servers/cairn_knowledge/server.py:89-92` + `tools.py:65-67` |
| F-407 | S1 | C8 | AGENT_ENVELOPE silent JSON degrade | Malformed JSON → `{}`; server runs against default snapshot ("HEAD"), not intended; no warning | `mcp_servers/cairn_knowledge/server.py:36-45` |
| F-500 | S2 | C7 | .slice-system symlink unvalidated | No code verifies `.slice-system` symlink target is a valid cairn repo (right files present, right git remote, etc.); silent misconfiguration possible | live-reproduced in complex-rag-analysis |
| F-501 | S3 | C7 | per-session kuzu DB ephemeral | Server uses temp DB per session (`server.py` comment intentional); but undocumented for operators trying to inspect the DB | `mcp_servers/cairn_knowledge/server.py:118` |
| F-502 | S2 | C2 | lessons corpus divergence | Consumer's `docs/lessons.md` (365 lines) and cairn's (357 lines) have diverged independently — consumer is unaware their lessons aren't queryable to cairn-knowledge | live-reproduced |
| F-503 | S2 | C7 | --directory fix is fragile | Consumer's correct `.mcp.json` with `--directory .slice-system` masks F-039/F-040 in operation, but underlying CWD-relative paths remain a structural weakness; one mis-config and the entire bug class re-surfaces | `complex-rag-analysis/.mcp.json:9` (correct) + `cairn_query/__init__.py:63-68` (fragile) |
| F-504 | S3 | C7 | SliceExtractor subprocess race | `subprocess.run(["git", *args])` no explicit `cwd=` parameter; minor race if cwd changes mid-extraction | `scripts/cairn_query/extractors/slice.py:21-27` |
| F-510 | S1 | C7 | /start-slice + /handoff hardcoded `.claude/` paths | Both commands use CWD-relative paths throughout; the cwd-trap incident (4 misrouted commits today) is the live proof | `lifecycle.py:55-66`, `handoff.full.md:31-76` |
| F-511 | S1 | C7 | /new-adr + /decision no CLAUDE_PROJECT_DIR | Both commands write to `docs/adr/` relative to CWD; phantom ADRs in cairn invisible to consumer; intent.md references unwritten ADRs | `new-adr.full.md:30-96`, `decision.full.md:85-94` |
| F-512 | S2 | C7 | snapshot_diff.py Path.cwd() | Baseline `.claude/structural-snapshot.json` writes to wherever CWD is, not consumer-root | `snapshot_diff.py:39,65` (D3 backstop) |
| F-513 | S2 | C7 | integration-sweep mixed env-var | integration_gate.py gets CLAUDE_PROJECT_DIR; snapshot_diff.py invoked bare; inconsistent within same sweep | `integration_gate.py:56-57` vs `integration-sweep.full.md:55-62` |
| F-514 | S3 | C7 | refresh-architecture implicit fallback | validate_architecture.py works via git-toplevel fallback when invoked from subdir; correct by accident, not by design | `validate_architecture.py:29-76` |
| F-515 | S2 | C7 | Zero documented env-var contract | No consumer-facing doc names CLAUDE_PROJECT_DIR contract; status.md mentions in passing as impl detail; operators cannot consciously work around CWD-trap | none — gap in all command docs |
| F-530 | S2 | C7 | upgrade-doc ADR slug collision | No warning that flat ADR slugs collide silently across cairn ↔ consumer corpora; consumer creating same slug shadows cairn's | `docs/upgrading-from-pre-compression.md` (Delta 5, missing) |
| F-531 | S2 | C6 | no hook installation verifier | One-line jq snippet for role_guard only; no automated verifier for all hooks present + paths resolve | `docs/upgrading-from-pre-compression.md` (Delta 1, partial) |
| F-532 | S2 | C7 | upgrade-doc PYTHONPATH ambiguity | Delta 2 says "set PYTHONPATH" without showing exact `.mcp.json` syntax or path-ordering; non-symlink consumers can hit import failures | `docs/upgrading-from-pre-compression.md` (Delta 2) |
| F-533 | S3 | C7 | upgrade-doc agent symlink incomplete | Delta 4 mentions per-file symlinks but doesn't enumerate which files; no verification step | `docs/upgrading-from-pre-compression.md` (Delta 4) |

## Findings (full evidence) — TBD

To be filled in as expansion passes return. Each finding will be expanded to:
- Verbatim quote(s) from cited file(s)
- Failure mode (1-3 sentences, observable behavior)
- Reproduction note (how to trigger, if not obvious from quote)
- Suggested fix-class (1-3 words; do not write the fix)
- Test-gap annotation (Pass J output)
- Cross-references to related findings

## Expansion-pass results — TBD

Per-pass section will be added below as each pass completes:
- Pass A: COMPLETE — L-016 (verdict-OK-but-bugs-present, the live C8 capture), L-017 (project-root resolution drift, C7+CWD-coupling), L-018 (universal escape hatches as silent enforcement bypass, C6 Bash-heredoc).
- Pass B: COMPLETE — 12 findings (F-051 through F-062). Drift on: refresh-architecture invocation path; integration-sweep short-form omits snapshot_diff exit-code-2; Phase-4 sweep.yaml ownership ambiguous (re-confirms L-009 regression); /handoff verifier invocation UNCLEAR; /status emits 5 lines not 6 (Cost line entirely unimplemented); /catchup Mode A surfacing instruction-only; /new-adr superseded-by format wrong + filename template stale post-migration + status lifecycle undocumented + frontmatter-only first-line-only bypass + ADR_EDITORIAL_FIX additive loophole.
- Pass C: COMPLETE — 9 verdict-blind-spot classes (F-100 to F-108), all S1, all C8 cluster. Two are **definitionally unreachable by Phase 4** (F-100 intent codification gap, F-107 Phase-2 amendments ignored) and require Phase-1/2 widening to detect at all. Other 7 are addressable in Phase 4 via cross-validation, sweep-notes content audit, envelope-expansion re-validation, snapshot-diff scope extension, or run_id correlation between result.json + slice.yaml.
- Pass D: COMPLETE — 9/10 clusters have defending tests; **C8 (verdict-OK-but-bugs) has ZERO COVERAGE**. High-priority bug classes nominally covered but test surfaces shallow: F-029 (Bash-heredoc) only Phase-1 restoration tested; F-031 (envelope synthesis Phases 2-4) lacks parametric assertion; F-015 (ThreadPool worker failure) test mocks return-dict, doesn't inject true exception; F-019/F-021 (resume rows) is well-covered. **CWD-coupling (F-039 to F-042, F-048-F-050) has zero coverage** — no test invokes orchestrator from non-cairn-root cwd. 5 missing test surfaces named: `test_bash_heredoc_role_guard_bypass.py`, `test_agent_envelope_phases_234_synthesis.py`, `test_phase_3_threadpool_worker_failure_isolation.py`, `test_verdict_ok_with_broken_invariant.py`, `test_cwd_coupling_orchestrator_root_resolution.py`.
- Pass E: COMPLETE — no symlink-recursion hazard found (no `os.walk`, `find -follow`, `copytree`, or `--recurse-submodules`); 3 `Path.rglob` hits all bounded scope (`snapshot_diff.py:49` SCAN_RULES limited; `lifecycle.py:80,165` `.claude/current-slice/`-bounded). Main outcome: F-048/049/050 — orchestrator + cairn_query + snapshot_diff are all CWD-coupled, while `validate_architecture.py` uses the *correct* env-var + git-toplevel pattern. Pattern drift across the codebase.
- Pass F: COMPLETE — 9 findings (F-063 through F-071). Resolved F-003 UNCLEAR: phase-1-writer "no source reads" is **instruction-only** — `role_guard.py` enforces only canonical-knowledge denials, not source-file scope. Resolved Bash matcher: NO hook inspects Bash for write-class operators (`>`, `>>`, `cat > X <<HEREDOC`, `tee`, `cp`, `mv`); reversibility-guard matches Bash but only checks destructive patterns. Resolved ADR_EDITORIAL_FIX: substring-containment validation only, no audit-trail context. Per-hook fail-mode summary: jq-missing breaks reality-check + scope-guard + reversibility-guard (all `exit 0` silently); ruff-missing breaks reality-check; git-rev-parse fallback to `pwd` in scope-guard + reversibility-guard breaks path canonicalization in consumer/detached-HEAD contexts; role-cheatsheet swallows git-checkout failures and slice.yaml parse failures.
- Pass G: COMPLETE — 24 new instruction-only findings (F-200 to F-224). Summary table: across 8 slash-command full.md docs, **24 of 30 MUST/SHALL/Never rules are instruction-only** (no code, hook, or test enforcement). Only 3 rules are code-enforced (scope-guard envelope, validate_architecture, integration-sweep scripts existence) and 3 are hook-enforced (verify_handoff prefix check). Highest-impact gaps: F-208 (D1 completion-gate documented but never implemented), F-209 (D3 completion-gates same), F-218 (firm-ADR Phase 5 verification not commit-time-gated), F-200 (phase-artifact committedness gate operator-only), F-207 (slice-completion wipe not enforced).
- Pass H: COMPLETE — 9 new findings (F-301 to F-309). Truthfulness summary: per-phase tokens, per-phase cost, total tokens, total cost, model attribution, INV-009 enforcement, close-time state consistency, heartbeat liveness — **all eight properties either non-truthful or advisory-only**. INV-009 is advisory-only and never escalates to abort (F-301, F-309); cost dict accumulates across slices and redispatches (F-302, F-305); Phase-3 cluster fan-out under-aggregates cost via ThreadPool race (F-304); model attribution is double-overwritten (F-303); envelope-parse failure produces $0 cost with attributed model (F-308); heartbeat death-chain spawns zombie threads (F-306); close partial-state can block re-close (F-307).
- Pass I: COMPLETE — 8 new findings (F-400 to F-407). MCP boundary properties: unknown entity_type (typos) raise KeyError unhandled; search() is unbounded with no pagination; rebuild_from_sources exception silently serves stale corpus with no in-band error; snapshot_id accepts arbitrary strings (no SHA validation, no ref-existence); KuzuStorage lazy-init has race condition under concurrent tool calls; pydantic missing-field validation silently defaults; **Cypher tool bypasses D8 structural lockdown** (privilege escalation — phase-1-writer can enumerate Decisions despite role_guard deny on `docs/adr/**`); AGENT_ENVELOPE malformed JSON silently degrades to default snapshot. F-406 is particularly dangerous — the documented escape hatch undermines an entire ADR-D8-enforced boundary.
- Pass J: SYNTHESIZED INLINE — full per-finding test-gap analysis was deprioritized; Pass D already did the cluster-level coverage matrix and named 5 missing test surfaces. Test-gap summary by cluster from Pass D: **C8 (verdict-OK) ZERO COVERAGE** across all 9 F-100s; high-priority bugs F-029/F-031/F-015 nominally covered but tests are shallow (mock return-dict, don't inject true exception); **CWD-coupling (F-039 to F-042, F-048 to F-050, F-510 to F-515) has zero test coverage** — no test invokes orchestrator from non-cairn-root cwd. Concretely missing test surfaces: `test_bash_heredoc_role_guard_bypass.py`, `test_agent_envelope_phases_234_synthesis.py`, `test_phase_3_threadpool_worker_failure_isolation.py`, `test_verdict_ok_with_broken_invariant.py`, `test_cwd_coupling_orchestrator_root_resolution.py`.
- Pass K: COMPLETE — 14 new findings across 3 sub-passes. **K-1 live reproduction CONFIRMED F-039/F-040/F-041/F-042 in complex-rag-analysis**: consumer's `.claude/cairn_query/index.kz` is *missing* (cairn's is 40MB); consumer's git slice-history has 15 entries vs cairn's 14; consumer's features dir has 5 vs cairn's 8; lessons.md diverged independently (365 vs 357 lines). Consumer's `.mcp.json` correctly uses `--directory .slice-system` which masks F-039/F-040 in operation, but the underlying CWD coupling remains structural. **K-2 slash-command audit**: of 8 user-facing commands, **only `/catchup` and `/status` are cross-repo safe** (catchup is read-only; status correctly uses CLAUDE_PROJECT_DIR). All others (start-slice, handoff, integration-sweep, refresh-architecture, decision, new-adr) write to wrong tree under CWD-trap conditions. **K-3 hooks/fleet/upgrade-doc**: hooks themselves use CLAUDE_PROJECT_DIR correctly; ADR slug namespace collisions undocumented + unenforced; no hook-install verifier; 3 additional upgrade-doc gaps (PYTHONPATH ambiguity, agent symlink procedure, ADR collision warning).

## Board issues — TBD

One per S1 + S2 finding, deduped against existing backlog (cwd-trap fix, 4 consumer-reported orchestrator findings, log-and-reconciler).

## Stop condition

**Reached: yield collapse on Pass K-3** (4 new findings vs earlier passes' 8-24 average). Bug ceiling (≥75) was hit at finding 75 during batch 1; continued explicitly because yield stayed high and the consumer-bridge dimension was uniquely cross-repo. Coverage condition fully met: all 11 expansion passes ran (A-K), every C1-C10 cluster had at least one targeted probe, consumer-bridge live-reproduced.

**Final finding count: 135** distributed:
- S1 (pipeline integrity / silent correctness): ~58
- S2 (cross-repo blast radius): ~58
- S3 (cross-layer drift, no current user impact): ~19
- S4 (doc/cosmetic): 0

**Time:** ~3.5 hours of agent dispatch + ~1 hour of direct writes (audit doc + lessons.md + edits).

## Top-line themes

The 135 findings cluster into a smaller set of structural diagnoses:

1. **CWD-coupling is systemic.** ~25 findings (F-039 to F-042, F-048 to F-050, F-510 to F-515, plus various) trace to one bad pattern: `Path("...")` constants and `Path.cwd()` instead of an explicit `_resolve_root()` helper. `validate_architecture.py:29-76` is the **only** place that does it right; the lone correct pattern is what the consumer-bridge story needs everywhere. **L-017 captures this lesson.**

2. **Bash-heredoc is a load-bearing enforcement bypass.** F-029 + F-030 + F-034 + many of the verdict-OK class (F-105 through F-107) all root in the same primary gap: agent prompts document the heredoc as a narrow escape; the implementation makes it an unconditional bypass for every write-class enforcement gate. **L-018 captures this lesson.**

3. **Phase-4 verdict OK ≠ user-correct.** F-100 through F-108 (Pass C) enumerate 9 distinct failure classes Phase 4 cannot detect by current design. Two are *definitionally unreachable* by Phase 4 — F-100 (intent codification gap, today's live trigger) and F-107 (Phase-2 amendments ignored) — and require Phase-1/2 widening. **L-016 captures this lesson.**

4. **Instruction-only enforcement is the dominant mode.** Pass G found that 24 of 30 MUST/SHALL/Never rules across slash-command full.md docs have NO code/hook/test enforcement — they exist only in operator/agent self-discipline. The pipeline's safety story rests on prose adherence, not mechanical gates. The most consequential operator-only gates: D1 + D3 completion gates (F-208, F-209) and Phase-5 firm-ADR independent verification (F-218).

5. **Consumer-tenancy model is missing entirely.** F-043 calls this out as a *design gap*, not implementation bug — there's no namespace, no merge story, no separate-but-mergeable corpus model. The cairn-knowledge MCP serves whichever corpus its CWD lands in, with no awareness of consumer-vs-cairn boundary. Live reproduction (F-500 to F-504) confirms consumers DO maintain divergent ADRs/lessons/features that are simply invisible to cairn's substrate. **Follow-up ADR work, not a code patch.**

6. **Silent fail-open is the hook default.** Pass F found that 5 of 6 hooks `exit 0` silently when `jq` or `ruff` is missing (CLAUDE.md flags this as a known hazard). Combined with the silent-fallback paths in path resolution (`PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null \|\| pwd)}"`), enforcement is contingent on perfectly-set env vars and dependency installation — both of which fail open without operator awareness.

7. **Cost discipline (INV-009) is non-load-bearing.** Pass H found INV-009 advisory-only at every layer: thresholds default `None` (inert); breach events are recorded but never raise/abort; the catch-all in dispatch.py:269-278 swallows even hypothetical breach exceptions. The invariant is name-only; nothing enforces it.

## Synthesis recommendations (out of audit scope)

These are not in the find-don't-fix mandate, but the audit naturally suggests follow-up workstreams:

- **Substrate slice — `_resolve_root()` helper** lifting `validate_architecture.py:_repo_root` into `scripts/_root.py` and migrating all `Path()` constants. Addresses ~25 findings in one sweep.
- **Substrate slice — Bash write-class enforcement** in role_guard.py + scope-guard.sh, parsing redirect operators (`>`, `>>`, `tee`, `cat > X <<HEREDOC`). Addresses F-029 + many derivatives.
- **Design ADR — consumer tenancy model** for cairn-knowledge MCP: merge / namespace / separate. Required to fulfill the user's "ADR knowledge should work in other projects" intent.
- **Substrate slice — D1 + D3 completion gates wired into close_slice.** F-208/F-209 are documented promises with no implementation; closing this gap restores the close-time integrity contract.
- **Phase 1 zone-3 widening directive** in phase-1-writer prompt (per L-016), requiring "natural manual probe" enumeration in Verification zone.
- **Hook install verifier** (`scripts/validate_hook_config.sh`) for consumers per F-531.

## Board issue

Single tracking issue filed at https://github.com/firaaz/cairn/issues/1 with a markdown checklist of all 135 findings grouped by audit pass. Triage from the issue checklist; cite this audit doc anchor (`F-NNN`) for evidence.

Existing backlog overlaps to dedupe when filing follow-up slices:
- `/start-slice invocation traps cwd via .slice-system symlink` — overlaps F-001 / F-039 / F-048 / F-510 family.
- 4 consumer-reported orchestrator findings (phase-3 timeout, retry partial-progress, subprocess reaping, cwd misroute).
- Implementation slice `board-as-roadmap-substrate/log-and-reconciler` (D2/D4/D7).

## Next session — triage proposal (deferred)

Per operator directive 2026-04-29: triage to actionable bug issues happens in the next session, not now. The 22-cluster fix-unit grouping below is the working draft to refine and file from.

**Approach:** group findings by root cause / shared fix surface so one bug issue (and ultimately one slice) can address multiple findings. Each row links back to F-NNN anchors above for evidence.

### Group A — Structural / substrate slices (one issue each, multi-finding fix)

| # | Issue title | Findings rolled up | Severity | Fix shape |
|---|---|---|---|---|
| 1 | CWD-coupling: lift `_repo_root()` into `scripts/_root.py` and migrate | F-039, F-040, F-041, F-042, F-048, F-049, F-050, F-510-F-515 (13) | S1 | Substrate slice |
| 2 | Bash write-class parsing in role_guard / scope-guard | F-029, F-030, F-034, F-106, F-218 (5) | S1 | Substrate slice |
| 3 | Close-sequence hardening: catch OSError, partial-wipe recovery, idempotency | F-005, F-006, F-007, F-008, F-009, F-010, F-307 (7) | S1 | Substrate slice |
| 4 | Phase-3 cluster fan-out safety + cost aggregation | F-015, F-016, F-024, F-304 (4) | S1 | Substrate slice |
| 5 | Hook fail-closed on missing deps (jq/ruff/git) | F-063-F-070 (8) | S1 | Substrate slice |
| 6 | Heartbeat + signal lifecycle | F-025, F-026, F-027, F-028, F-306 (5) | S2 | Substrate slice |
| 7 | Resume reconcile: missing rows + run_id correlation | F-019-F-023, F-108 (6) | S2 | Substrate slice |
| 8 | AGENT_ENVELOPE: synthesize for Phases 2-4, validate snapshot SHA | F-031, F-403, F-407 (3) | S1 | Substrate slice |
| 9 | MCP server boundary: error handling + bounded results + pydantic strictness | F-400, F-401, F-402, F-404, F-405 (5) | S1 | Substrate slice |
| 10 | Cypher tool privilege escalation lockdown | F-406 (1) | S2 | Substrate slice |
| 11 | Cost discipline (INV-009) make load-bearing | F-301, F-302, F-303, F-305, F-308, F-309 (6) | S1 | ADR + substrate slice |
| 12 | D1 + D3 completion gates wired into close_slice | F-200, F-201, F-202, F-208, F-209 (5) | S1 | Substrate slice |

### Group B — Design ADRs needed (not code-first)

| # | Issue title | Findings | Severity | Shape |
|---|---|---|---|---|
| 13 | Consumer-tenancy model for cairn-knowledge MCP | F-043, F-044, F-047, F-502, F-530 (5) | S1 | Design ADR |
| 14 | Phase-1 verification-zone widening directive (per L-016) | F-100, F-107 (2) | S1 | Prompt amendment + ADR |
| 15 | Verdict-OK blind-spot remediation roadmap | F-101-F-106 (6) | S1 | Discussion → ADR |
| 16 | Instruction-only enforcement strategy: which to lift, which to accept | F-203-F-207, F-210-F-217, F-219-F-224 (~20) | S1+S2 | Discussion ADR |

### Group C — Doc / config fixes (low-effort PRs)

| # | Issue title | Findings | Severity | Shape |
|---|---|---|---|---|
| 17 | Upgrade-doc consumer-breaking bugs | F-045, F-046, F-531, F-532, F-533 (5) | S2 | Doc PR |
| 18 | Slash-command doc drift (status, integration-sweep, refresh-architecture, etc.) | F-051-F-057 (7) | S2/S3 | Doc PR |
| 19 | `/new-adr` drift: superseded-by format, filename template, status lifecycle | F-058-F-062, F-071 (6) | S2 | Doc + reversibility-guard slice |

### Group D — Single-cause one-offs

| # | Issue title | Findings | Severity |
|---|---|---|---|
| 20 | Triager flow gaps (RAISE_ISSUE shape, target_phase validation, redispatch-cap loop) | F-018, F-032, F-035, F-036, F-037 (5) | S2 |
| 21 | Test-coverage targets (5 missing test files from Pass D) | n/a (synthesized) | S1 |
| 22 | Symlink validation + hook installer doctor (`.slice-system` is a real cairn repo) | F-500, F-503, F-531 (3) | S2 |

**Net:** 22 actionable bug issues from 135 findings (~6× consolidation).

### Open triage decisions for next session

1. **Labels.** Create `severity:S1/S2/S3`, `cluster:CWD-coupling/heredoc-bypass/etc.`, `kind:substrate-slice/design-adr/doc/discussion`? Helps filter the board.
2. **Issue #1 disposition.** Close once the 22 are filed, or keep open as umbrella with the 22 numbers linked back as a checklist?
3. **Grouping refinement.** The 22-cluster proposal is a first cut; the next session may want to split or merge based on operator priorities (e.g., consumer-tenancy is currently 1 design-ADR issue but might warrant 2 — server-side merge model and consumer-side ADR-creation flow).
4. **Order of attack.** S1 substrate slices first, or design ADRs (groups B14/B15) first because they shape downstream slices?
5. **Dedup pass against existing backlog.** The 4 consumer-reported orchestrator findings + log-and-reconciler slice may already cover some of these. Run a dedup grep before filing.
