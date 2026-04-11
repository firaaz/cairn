# Substrate + Framework Exploration Notes — 2026-04-11

**Session type:** Exploratory (not a decision session)
**Status:** First of expected two exploratory sessions, then `/decision`
**Context:** SLICE-002 is stopped pending substrate and framework decisions. This session was the first exploration; one more is expected before committing.
**Promote-out:** When you're ready to move this out of slice state, `git mv .claude/current-slice/exploration-notes.md docs/plans/2026-04-11-substrate-and-framework-exploration-notes.md`. Don't close SLICE-002 until this file is moved — slice closure wipes `.claude/current-slice/` per ADR-002 Layer 3.

---

## Session framing

Started as a substrate question ("what language should cairn's code be written in") but reframed three times:

**Reframe 1 (user correction).** "Not only type safety — things like Rust or FP help remove classes of bugs." Broadened the lens from ML-type-safety to include purity, immutability, borrow-checking, exhaustiveness, parse-don't-validate.

**Reframe 2 (user clarification).** "Mac-only; agent-portable = Claude Code + Windsurf, not cross-OS; markdown stays markdown; we want AI to be unable to produce whole classes of bugs." Relaxed distribution constraint; strengthened bug-elimination as the priority; bifurcated the architecture (markdown layer vs code layer) as settled.

**Reframe 3 (user instruction).** "Don't fall into NIH. If these external tools are good enough, take them as-is. I'm willing to change my protocol. We're reconsidering phase structure anyway, this is the best place." Reopened from "what substrate" to "is cairn the right thing to build at all." **This is the biggest reframe of the session** — changed it from a substrate decision into an adopt-vs-build analysis.

---

## Bug-class inventory (derived from reading checks/*.sh and scripts/validate_architecture.py)

**A. JSON shape assumptions in hooks.** `jq -r '.tool_input.file_path // empty'` silently returns empty if shape changes. No schema validation. Hooks default to no-op when confused.

**B. Path manipulation / symlink semantics.** SLICE-001's signature bug class. `__file__.resolve()` canonicalized through `.slice-system → .` made the validator silently read cairn's substrate instead of the consumer's. `REL_FILE="${FILE#$PROJECT_ROOT/}"` is a prefix-strip that produces non-relative paths when input isn't rooted right. `.slice-system` recursion flagged in CLAUDE.md.

**C. String-match denylists pretending to be parsers.** `case "$CMD" in *"rm -rf"*)` catches `rm -rf` but not `rm --recursive --force`, `find -delete`, whitespace variants. Every blocklist is a false-negative farm; every allowlist a false-positive farm.

**D. Hand-rolled markdown/YAML parsing.** `parse_frontmatter` is line-split with a special case for lists. `parse_invariants` regex-matches `**INV-NNN**` — a reformat silently yields zero invariants and Check A trivially passes. Silent false-green.

**E. Silent skip on missing deps.** All three hooks `exit 0` with stderr warning if `jq` is missing. CLAUDE.md flags this as safety-critical. Enforcement silently disabled.

**F. Hook composition / escape hatches.** `EXPAND_ENVELOPE=1`, `ADR_EDITORIAL_FIX=1` — out-of-band env vars bypass hooks. Architectural.

**G. Agent-portability drift.** Commitment #1 says Claude Code AND Windsurf must run the same workflow. Hooks bind to Claude Code's JSON shape. Out of any language's type system.

**H. Protocol drift (markdown-level).** SLICE-002 exists to fix it. `/catchup` skill says one thing, implementing code does another, intent wording drifts. No type system catches this.

---

## The broader-lens reframe (after user correction)

Type-safety-in-the-ML-sense is not the only substrate lever. Other whole-class-elimination features:

1. **Aliasing / shared mutation.** Python allows any function to silently mutate a passed dict. Rust's borrow checker refuses to compile code where two callers hold mutable refs. Haskell removes the class via immutability-by-default.

2. **Hidden side effects.** Haskell's `IO` monad and OCaml's effects force filesystem/network into the type. For a tool whose main job IS filesystem side effects, purity is the difference between "safe to call 1000 times" and "shells out to git." **SLICE-001 was actually an effect-tracking bug, not a type-safety bug** — `__file__.resolve()` silently did symlink IO and the signature gave zero hint.

3. **Exhaustiveness on variant addition.** Add a new slice status (`stopped`, as SLICE-002 did) and Rust/Haskell/OCaml refuse to compile until every `match` handles it. Python's `match` is not exhaustive-checked by default.

4. **Parse-don't-validate.** Construct a `ResolvedProjectRoot` value that CANNOT exist without going through the resolver. Python's analogues (pydantic, NewType) are advisory at runtime.

5. **Totality.** Non-null by default. Non-empty lists as distinct types. Sum types instead of sentinel returns.

---

## Re-scored bug classes against the broader lens

| Bug class | Py+mypy | Rust | Haskell | TS strict (Deno) |
|---|---|---|---|---|
| A JSON shape | weak | **strong** (serde) | **strong** (aeson) | medium (Zod) |
| B paths/symlinks | weak | **strong** (newtypes) | **strong** (newtypes) | medium |
| C denylist-as-parser | same | same | same | same |
| D hand-rolled YAML | library choice | library choice | library choice | library choice |
| E silent skip on missing dep | weak | **strong** (Result) | **strong** (IO/Either) | weak |
| F escape-hatch env vars | architectural | architectural | architectural | architectural |
| G agent portability | native fit | breaks text-distribution (now relaxed) | breaks (now relaxed) | native fit |
| H protocol drift | contract tests | contract tests | contract tests | contract tests |
| + purity / aliasing (new row) | absent | **borrow checker** | **pure by default** | weak (readonly) |
| + exhaustiveness (new row) | opt-in | **enforced** | **enforced** | with `never` trick |

Pre-reframe-3 recommendation was **Rust** — strongest bug-class elimination combined with a large AI corpus so Claude produces idiomatic code. This recommendation is now upstream-blocked by the framework question.

---

## Sunk-cost audit (Explore agent)

| Category | Files | Lines |
|---|---|---|
| REWRITE scope (code) | 5 | **799** |
| KEEP-AS-IS (protocol docs) | 28 | 1,579 |
| RESEARCH to preserve | 13 | 2,051 |
| CONFIG | 13 | 165 |
| SURPRISE | 2 files + 1 symlink | 26 |

Rewrite scope is ~800 lines across 5 files: 3 shell hooks (251 lines) + validator (284) + test suite (326). Protocol docs and research (3,630 lines combined) stay untouched.

### Two surprises worth knowing about

1. **`docs/plans/measurements/*.txt`** — 26 lines of plain-text empirical measurements for ADR-002's context-discipline checkpoint. Orphan state, not referenced from any doc. Promote to an appendix of `docs/plans/2026-04-11-context-discipline-design.md`, or `.gitignore` and recreate on demand.

2. **`.claude/commands/ → commands/claude-code/` symlink.** Undocumented in CLAUDE.md despite being structurally similar to the `.slice-system → .` recursion hazard that IS flagged. Exists to satisfy Claude Code's hardcoded `.claude/commands/` path while keeping cairn's agent-neutral `commands/<agent>/` layout (commitment #1). When Windsurf lands, add a second symlink (`.windsurf/commands/ → commands/windsurf/`). Worth one line in CLAUDE.md's safety-critical rules.

---

## cc-tools correction (don't miss this next session)

First turn I described cc-tools as "closest existing prior art for Claude Code hooks in a compiled language." **That was wrong.** A deep read turned up:

- cc-tools is a **statusline + MCP manager**, not a hooks framework
- Ships **one** hook (`statusLine`, non-gating) — zero PreToolUse, zero PostToolUse, zero tool-call interception
- Zero JSON shape validation, zero Bash parsing, zero path-safety logic
- No plugin API, no hook registry, no extension points
- Project health: MIT, Go 1.24.5, ~35 commits in 6 months, 3 contributors, 49 stars, no tagged releases
- **Verdict: IGNORE.** Nothing to adopt, nothing to fork. The statusline is pretty and can be co-installed as a peer tool — that's the only useful thing.

The first review agent overstated cc-tools' scope. The deep-read agent corrected it. Take-away: adopt-vs-build analysis must read the candidate, not summarize README bullets.

---

## Framework scoring — what each candidate covers of cairn's 6 vision commitments

Scoring: 0 = absent, P = partial, F = full.

| Framework | 1. Agent-portable | 2. Parallelism-native | 3. Soft agent split | 4. Meta-dogfood | 5. Plastic phases | 6. Roles + anti-behaviors |
|---|---|---|---|---|---|---|
| **Superpowers** (obra, ~147k stars) | **F** (CC + Cursor + Codex + Gemini + Copilot + OpenCode) | **F** (worktree skill) | P | P | P | P |
| **Spec Kit** (GitHub, ~87k stars) | F | P | 0 | 0 | **0** (5 phases are doctrine) | P |
| **RIPER-5** (~79 stars, 3 commits, toy) | 0 | 0 | 0 | 0 | 0 | **F** (capability table is best-in-corpus) |
| **ContextKit** (unmaintained) | 0 | 0 | 0 | 0 | 0 | 0 |
| **Claude CodePro / Pilot** (~1.6k stars) | P | F | 0 | 0 | 0 | P |

**Nothing has cairn's full combination** of (phase capability gating) × (runtime hook enforcement) × (ADR supersession) × (worktree parallelism) × (cross-agent portability) × (explicit anti-behaviors). Superpowers covers 4 of 6 at F or P. Everything else covers 1–2.

### The critical observation

**The author already has Superpowers installed.** This session's skill list contains obra's skills: `brainstorming`, `writing-plans`, `executing-plans`, `test-driven-development`, `subagent-driven-development`, `systematic-debugging`, `verification-before-completion`, `using-git-worktrees`, `finishing-a-development-branch`, `receiving-code-review`, `requesting-code-review`, `writing-skills`, `dispatching-parallel-agents`. All Superpowers. All actively in use right now.

---

## Tentative direction (PENDING verification — see "gaps" below)

**ABSORB cairn into Superpowers as a skill + hook pack.** Retire cairn-as-standalone-repo.

### Keep as cairn-specific (the system)

- `/start-slice`, `/catchup`, `/handoff`, `/decision`, `/new-adr`, `/refresh-architecture`, `/integration-sweep`, `/status` — ported to Superpowers SKILL.md format
- ADR discipline (append-only, status/firmness/supersedes, ARCHITECTURE.md ↔ ADR validator)
- `scope-guard`, `reversibility-guard`, `reality-check` — as a Superpowers hook pack
- `.slice-system` symlink convention
- Meta-dogfooding rule
- Contract-conformance test pattern (V1–V7, `trycmd` or equivalent if Rust)

### Delete (duplicates Superpowers — ~30–40% of cairn's scope)

- Own brainstorming, writing-plans, executing-plans, debugging, TDD, worktree management, code-review skills — obra already ships them and the author is already using them
- Own agent-portability implementation — Superpowers already handles CC + Cursor + Codex + Gemini + Copilot + OpenCode, which is MORE than commitment #1 required
- Own skill-loading / context-isolation machinery — Superpowers' SKILL.md format already solved "load without bloat"

### Add (cairn's missing primitive)

A new **`capability-guard`** hook that enforces per-phase capabilities (Read / Write / Execute / Plan / Validate) — borrowed from **RIPER-5's capability table**, which is the single best artifact in the framework-review corpus. cairn's current `scope-guard` is per-slice file allowlists; `capability-guard` is per-phase action gating. That's the "hard context isolation as an external check" property with runtime teeth.

---

## Phase decomposition proposal — 4 → 5 phases

**Orthogonal to the absorption decision; standalone ADR either way.** The author said: "we are also looking into if our 4 phase structure is actually done in the right places and the right level of abstraction, this is the best place to look at such things."

RIPER-5 separates **Research** and **Innovate**. Cairn's current "Intent" conflates "understand the problem" with "propose the approach" — and that conflation is exactly where architects start writing code prematurely. The anti-behavior cairn most wants to prevent.

### Proposed 5-phase evolution

| Now (cairn v0) | Proposed (cairn v1) | Role | Anti-behavior |
|---|---|---|---|
| Intent | **Intent** (research-only) | Reader | does not propose |
| — | **Design** (new) | Architect | does not run tests |
| Validation | **Validation** | Skeptic | does not implement |
| Implementation | **Implementation** | Builder | does not re-litigate |
| Integration | **Integration** | Auditor | does not rewrite |

Answers commitment #5 ("phase shape is plastic through v1") and delivers commitment #6 (explicit cognitive roles with anti-behaviors).

**Do NOT adopt Spec Kit's 5** (Constitution → Specify → Plan → Tasks → Implement). Constitution is project setup, not a per-slice phase; Tasks is bureaucracy RIPER correctly absorbs into Plan.

---

## Verification gaps — the next exploratory session must close these before `/decision`

These are prerequisites to committing to the absorption. **Highest-value first.**

**1. Does Superpowers support third-party skill + hook packs as a first-class extension surface?** The review agent claimed yes but didn't drill. If it's "fork and PR upstream," that's fork, not absorb. If it's "drop a directory at `~/.claude/skills/cairn/` and it's picked up," that's real. **The whole absorption recommendation collapses if the extension surface isn't there.** This is THE question.

**2. Is Superpowers' cross-agent support (CC + Cursor + Codex + Gemini + Copilot + OpenCode) actually working, or aspirational in the README?** Commitment #1 depends on this being real. Find one non-Claude-Code user and read their config before betting.

**3. Bus-factor / release cadence reality check.** 147k stars is a strong signal; "solo-maintained OSS project" is a weak one. Look at issues, PRs, release frequency, who's merging. If obra is the only committer, absorption adds a dependency on one person's time.

**4. Does Superpowers already have an ADR-shaped skill or a `/decision`-shaped skill?** If yes, cairn's `/decision` is duplicate and can be deleted. If no, it's a contribution upstream.

**5. Re-read Superpowers' `brainstorming` skill** (you're using it right now) and compare to cairn's `/decision`. If they collapse into one, that's data. If they're doing different things, that's also data.

**6. How does Superpowers handle hook registration specifically?** Native `.claude/settings.json` hooks only, or does it have its own hook registry that cross-agent hooks plug into?

---

## The decision cascade (answer in order, not at once)

1. **Absorb into Superpowers, or stay standalone?** (biggest call — answer first after closing the verification gaps)
2. **If absorb**: phase count and names — accept 5-phase RIPER-informed split, keep 4-phase, or different?
3. **Hook substrate**: once absorbed, hooks are Superpowers hooks and the question shrinks from "Rust vs Python for everything" to "bash vs Rust for hook performance." Much smaller call. Probably: bash for now, migrate to Rust in a later slice if profiling shows it's needed.
4. **Then** write ADR(s) and run `/decision`.

---

## What NOT to re-derive in the next session

All of these are settled and should not be re-litigated:

- **Bug-class inventory (A–H)** — codebase-derived, stable
- **Re-scored language table** — settled against the broader lens (post-reframe-1)
- **Sunk-cost audit numbers** — 799 lines rewrite, 1,579 docs, 2,051 research, 165 config
- **cc-tools' true nature** — statusline + MCP manager, not a hooks framework
- **Framework matrix scores** — fresh research artifact; rerun if new framework surfaces, but don't re-derive from memory
- **The 6 vision commitments** — they're in `docs/vision.md`, unchanged, still binding
- **SLICE-002 Phase 2 brainstorming outputs** — V1–V7 resolutions, Approach 1+ test design (primitive layer + 7 flat functions), pyramid mapping — all preserved in `.claude/current-slice/validation/approach.md`. Language-independent; survives substrate and framework changes.
- **The phase decomposition proposal** — 5 phases (Intent / Design / Validation / Implementation / Integration) with roles + anti-behaviors. This gets written as its own ADR regardless of the absorption outcome.

---

## What IS open

- Verification gaps 1–6 above
- Whether the 5-phase split is decided before or after the absorption (read: orthogonal, both are standalone ADRs — phase split is safe to write first since it's framework-independent)
- Whether absorption means retiring the cairn repo entirely, OR keeping it as a thin loader that points at Superpowers + the cairn pack, OR keeping the repo as cairn's research/spec home while the runtime code lives as a Superpowers pack
- Whether the existing `.slice-system → .` symlink distribution survives absorption or gets replaced by Superpowers' native distribution (depends on gap #1)
- What SLICE-002 becomes post-decision: resume-against-new-substrate, supersede with a new slice, or retire entirely

---

## Pointers

- `.claude/current-slice/validation/approach.md` — SLICE-002 Phase 2 brainstorming. V1–V7 resolutions, Approach 1+ test design, pyramid mapping. Language-independent, survives any substrate/framework change.
- `.claude/current-slice/intent.md` — SLICE-002 intent (test contract, unchanged)
- `.claude/current-slice/slice.yaml` — `status: stopped`, `stopped-reason` currently cites substrate decision only; update to also cite framework decision when resuming
- `.claude/current-slice/handoff-phase-1.md`, `handoff-phase-2.md` — phase-level notes preserved
- `docs/adr/002-context-discipline-protocol.md` — protocol SLICE-002 implements; unchanged
- `docs/vision.md` — 6 non-negotiable commitments; unchanged, still binding
- `docs/roadmap.md` — Must-land-before-v1 item #1 is the phase rethink; the 5-phase proposal is its candidate resolution
- `CLAUDE.md` — safety rules need: (a) a `.claude/commands/` symlink note, (b) a status decision for `docs/plans/measurements/`
- `checks/{scope-guard,reversibility-guard,reality-check}.sh` — the ~250 lines of hook logic being rewritten
- `scripts/validate_architecture.py` — the ~280-line validator being rewritten
- `tests/unit/test_validate_architecture.py` — the ~320-line test suite; V1–V6 test pattern is the style anchor for any Rust equivalent

---

## Session metadata

- Opus 4.6 (1M context)
- Brainstorming skill invoked at turn ~3 and drove the session shape
- Explore agent dispatched for sunk-cost audit
- Two general-purpose agents with WebFetch dispatched: one for cc-tools deep-read, one for framework-replacement analysis
- First awesome-claude-code review agent was surveyish and got cc-tools wrong; subsequent deep-reads corrected it
- Context did not exceed session budget; one more exploratory session planned before `/decision`

---

# Session 2 — 2026-04-11 — MVP scoping via working-loop trace

**Session type:** Exploratory → scoping. Building on session 1. Not yet `/decision` — still gathering grounds.
**Promote-out:** Same instructions as the top of this file. When SLICE-002 supersedes or resumes, `git mv` to `docs/plans/2026-04-11-substrate-and-framework-exploration-notes.md` and the Session 2 content rides along.

## What this session changed

Session 1 left us with six verification gaps and a tentative direction of "absorb cairn into Superpowers." Session 2 reframed both. The absorption question dissolved; a much sharper problem statement emerged.

## Reframe 1 — Cairn is two parallel sub-projects, not one

**Project 1 — Slice + Phase pipeline.** Operational discipline for the current piece of work. Three distinct purposes:
- 1.1 **Context cleanliness** — clean the AI's context at every phase transition; prevents reasoning laundering.
- 1.2 **Role switching** — new context + new role/viewpoint per phase (Reader / Architect / Skeptic / Builder / Auditor or similar).
- 1.3 **Human reset** — the formal split forces the HUMAN to change cognitive mode. Anti-procrastination, anti-premature-optimization; serves decision quality, not just AI correctness.

**Project 2 — Long-term specs.** Machine- and human-readable "cached mind" of the codebase. ADRs + invariants + live `ARCHITECTURE.md`. When humans lose the mental model (because AI wrote most of the code), the docs provide both AI and humans a current ground truth.

**Critical correction:** the two projects are NOT independent MVPs. They are two sides of the same fight. Without Project 2, Project 1 has nothing to gate against (slices locally correct, globally drifting). Without Project 1, Project 2 has no enforcement opportunity (invariants without a gate are comments). The loop only closes with both.

## Reframe 2 — The target failure is the medium-scale AI-managed cliff

Current SDD approaches beat vibe-coding but break down past medium project size AND AI-managed AND humans don't know the codebase. A discontinuous "cliff" failure mode where further progress requires a mental model nobody has.

**Concrete mechanism:**
1. Slices pass gates locally. Each change correct in isolation.
2. `/refresh-architecture` gets skipped. `ARCHITECTURE.md` goes stale.
3. Integration-sweep Step 2 (human adversarial enumeration) degrades to rubber-stamping because the human doesn't know the code.
4. An unnamed global property gets violated silently.
5. Subsequent slices compound the violation.
6. Cascading failure when a later change needs the violated property to hold.

Cairn's bet: the cliff is unavoidable absent the three-way combination of (enforced phase discipline) × (live machine-readable architecture) × (machine-checkable invariants). No other SDD framework combines all three.

## The three audits — reality check

**Project 1 reality:**
- 4-phase pipeline, git-backed gates. ✓
- Phase gates enforced mechanically (must commit artifact N before phase N+1).
- Scope-guard is the one runtime gate that blocks out-of-envelope writes.
- Reversibility-guard enforces ADR append-only + destructive-op blocks.
- **Context isolation is INSTRUCTED, not hook-enforced.** Phase 1 "don't read source," Phase 2 "don't see Phase 1 reasoning," etc. all honor-system via `/catchup` tier loading. No hook prevents a loader leak.
- NO parallel slices. Singleton `.claude/current-slice/`.
- NO work-type routing. spec-v1 §9 proposed 3-track routing, explicitly marked *"not implemented, friction unproven"*.
- UNRESOLVED DOC CONFLICT: spec-v1 says fail-and-restart for mid-slice abandonment; operational-reference says pause-and-resume. Flagged in the cross-project review.

**Project 2 reality:**
- 2 ADRs total (001 bootstrap, 002 context discipline).
- 2 invariants (INV-001, INV-002).
- **Validator is doc↔doc only.** Check A/B/C all parse markdown. NO code↔invariant binding.
- Invariant→code link is human attestation in `sweep-notes.md` (file:line evidence), not automated.
- Architecture refresh is MANUAL (`/refresh-architecture` skill). Drift window unbounded.
- Integration-sweep Step 2 is HUMAN adversarial enumeration. Step 4 is standard linters/imports/tests — catches structural drift, not semantic.
- NO invariant retirement mechanism.
- NO retroactive enforcement of new invariants against existing code.

**Vision ↔ reality:**
- Commitment 2 (parallelism-native): ASPIRATIONAL.
- Commitment 5 (plastic phases): ASPIRATIONAL (depends on phase rethink).
- Commitment 6 (explicit roles): PARTIAL (named in spec, not mechanized).
- **Cairn is currently 2 slices deep.** Never operated at medium scale. All reasoning below is aspirational until dogfood.
- Empirical base: 3 cited papers for context discipline (Song 2026, Tsui 2025, Kim 2025). Role-reset explicitly flagged *"no direct experimental validation"*.
- "Cliff" framing is NOT in canonical docs — it is user framing, needs canonicalization via ADR.

## The total plan — MVP tiers

**TIER 1 — loop-breaking (without these, cairn cannot work at medium scale even in theory):**

- **D1. Automated architecture refresh.** Post-slice hook fires `/refresh-architecture`; slice-close gates on validator pass. Closes the stale-cached-mind drift window.
- **D2. Code↔invariant binding.** Invariants must have machine-checkable assertions (AST-level, schema-level, or strict-grep at minimum), not just markdown cross-refs. Validator runs the assertions. Closes the "invariants as commentary" gap.
- **D3. Automated unknown-unknown backstop.** At least one automated check beyond Step 2's human enumeration. Minimum form: snapshot structural properties (imports, types, schemas, test coverage per file) at slice-land; diff at next sweep; flag files that changed shape silently. Does not need to be comprehensive; must exist.

**TIER 2 — usability at scale (needed for the system to be livable, not just theoretically correct):**

- Parallel slices (branch-local `.claude/current-slice/`; roadmap items 5/6/9).
- Retroactive invariant enforcement (new invariant validates against existing code at land).
- Resolve the mid-slice abandonment doc conflict (one ADR picks pause-and-resume OR fail-and-restart).

**TIER 3 — polish:**

- Work-type templates (re-open spec-v1 §9 once dogfood provides friction evidence).
- Cached-mind size management (chunking `ARCHITECTURE.md` when invariant count exceeds ~20).

## Scoping sequence — the path

1. **First: draft the "cliff" ADR.** Names the target failure mode, commits to D1/D2/D3 as load-bearing defenses, explicitly defers everything else. Provisional firmness — reassess after dogfood. This grounds every subsequent design decision. *(← current step.)*
2. **Second: design one Tier 1 item in detail.** Lean: **D1 (auto architecture refresh)**, because it is the smallest closed-loop improvement and closes the most visible gap. Produces a buildable slice.
3. **Third: dogfood.** Run cairn against a real medium-scale AI-managed codebase — either cairn itself once it is ~20 slices deep, or an existing external project already showing cliff symptoms. Observe whether D1/D2/D3 catch cliff-shape failures or just feel like process.
4. **Fourth: iterate.** Based on dogfood evidence, either (a) promote the cliff ADR to firm and ship v1 with D1/D2/D3, (b) supersede with a revised defense list, or (c) fundamentally rethink.

## Non-goals for v1

Explicitly deferred, tracked in the roadmap but NOT v1-blocking:
- Parallel slices (despite commitment #2).
- Windsurf port (despite commitment #1).
- Plastic phases / work-type templates (despite commitment #5).
- Role formalization per phase (despite commitment #6 — roles stay instructed, not mechanized).
- Retroactive invariant enforcement.
- Slice pause/resume as a built-in.

This is a narrower v1 than the current roadmap implies. Vision commitments are preserved as post-v1 goals, not abandoned.

## Open questions for next session

- **Is cairn itself the right dogfood target?** It is currently 2 slices deep; reaching medium scale may take months. Alternative: find an existing AI-managed repo already showing cliff symptoms.
- **D3 is the weakest spec.** What is the MINIMUM automated check that would catch the concrete mechanism in "Reframe 2" above? Structural diff? Coverage delta? Property-based snapshots? Something else?
- **Does D2 require a substrate change**, or can it be done in existing Python/bash? If substrate change, SLICE-002's substrate question reopens.
- **Which session-1 gaps still matter under this reframe?** Gap 6 (hook coexistence with Superpowers) is still relevant for the compose-with-Superpowers story during the personal-use phase. The rest can defer indefinitely.

## Process artifacts from this session

- Explore agent A: Project 1 surface audit (commands, hooks, slice schema, phase structure).
- Explore agent B: Project 2 surface audit (ADRs, invariants, validator, refresh mechanism, integration-sweep).
- Explore agent C: Vision↔reality delta (commitments, spec, roadmap, safety, review findings).
- All three returned usable inventories. Combined word count ~3500; distilled into this total plan.

## Pointers (new this session)

- `docs/adr/003-cliff-failure-mode-and-v1-defenses.md` — **to be drafted.** Names the target failure mode + commits to D1/D2/D3. Provisional firmness.
- `scripts/validate_architecture.py` — contains Check A/B/C (doc↔doc only). D2 requires extending this with code-binding assertions.
- `commands/claude-code/refresh-architecture.md` — manual skill. D1 requires hooking this to a post-slice trigger.
- `commands/claude-code/integration-sweep.md` — contains Step 2 (human adversarial). D3 requires automating at least one backstop check.
