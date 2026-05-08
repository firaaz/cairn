# Phase 0 — Constraint Envelope

Decision: "How does cairn ship as a consumer-installable methodology, replacing the `.slice-system → .` symlink consumption pattern?"

Source: `general-purpose` agent run, 2026-05-08. Categorisations: **HARD** = architectural invariant; **SOFT** = strong preference; **CONTEXT** = bounding background.

## DISTRIBUTION

1. **[HARD]** `.slice-system → .` is a self-referential infinite-depth loop; any tool walking it recursively must explicitly exclude. Source: `CLAUDE.md:18`.
2. **[HARD]** `role_guard.py` does NOT strip `.slice-system/` prefix; only `reversibility-guard.sh:48,76` canonicalises. Future install path must avoid the prefix entirely or extend `role_guard.py` canonicalisation. Source: `CLAUDE.md:11`.
3. **[SOFT]** M5's stated target is `claude plugin install cairn` Claude Code plugin packaging; symlink + `scope-guard.sh:53` prefix-stripping retire with that target. Source: `docs/plans/2026-05-06-cairn-shrink-design.md:158`.
4. **[SOFT]** `.claude/skills/` is on Windsurf's documented cross-agent-compatibility discovery list; skill prose ports to Windsurf for free, but `.claude/agents/` does not. Source: `docs/plans/2026-05-06-cairn-shrink-design.md:125,160,294`.
5. **[CONTEXT]** Plugin packaging is layer 4 of the post-shrink 4-layer model (Document / Enforcement / Protocol / Distribution). Source: `docs/plans/2026-05-06-cairn-shrink-design.md:46-60`.

## AUDIENCE

6. **[HARD]** `CLAUDE.md` today is written for an agent inside cairn itself (self-consumption); a first-time external consumer cannot tell whether maintainer-only safety rules apply to them. Source: `docs/reviews/2026-04-23-from-portfolio-evaluation.md:60-66`.
7. **[SOFT]** One concrete prospective consumer (portfolio evaluator) chose copy-adoption over symlink-adoption, citing pre-v1 instability and audience-split friction. Source: `docs/reviews/2026-04-23-from-portfolio-evaluation.md:32,52,111`.
8. **[SOFT]** Cairn's spec §1 explicitly excludes simple software (CRUD, prototypes, AI wrappers); the install-path audience is the "complex / safety-critical / long-horizon" subset. Source: `docs/spec-v1.md:25-29`.
9. **[CONTEXT]** Portfolio evaluator named handoff-as-pointer, the three hooks, the architecture validator, and the Phase Skill Guide as cairn's most-portable atomic pieces; minimum-viable-cairn subset is an open question. Source: `docs/reviews/2026-04-23-from-portfolio-evaluation.md:103-105`.

## DEPS

10. **[HARD]** All three `checks/*.sh` hooks require `jq`; `reality-check.sh` additionally requires `ruff`; missing deps silently no-op enforcement. Source: `CLAUDE.md:13-16`.
11. **[HARD]** Standing Python dep set is `pydantic + typer + pyyaml` only; new code is function-based Python, no decorators/metaprogramming. Source: `CLAUDE.md:28`.
12. **[HARD]** `role_guard.py`'s pyyaml import is lazy because consumer hooks invoke via bare `python3` and may not have pyyaml; install path must preserve "no-envelope happy path stays stdlib-only" or break consumer invocation. Source: `checks/role_guard.py:90-92`.
13. **[SOFT]** No hardcoded timeouts/sizes in consumer-facing scripts; every knob uses `int(os.environ.get("CAIRN_<KNOB>", default))`. Source: `CLAUDE.md:30`.

## HOOKS

14. **[HARD]** `.claude/settings.json` registers all hooks against `$CLAUDE_PROJECT_DIR/.slice-system/checks/...`; plugin install must reproduce this hook registration shape (or its substitute) in the consumer's `.claude/settings.json`. Source: `.claude/settings.json:27,36,47`.
15. **[HARD]** `checks/role_guard.py` resolves CAIRN_ROOT via `Path(__file__).resolve().parent.parent` and reads `.claude/active-envelope.yaml` from that root; if a plugin install relocates the script, path resolution must still find the consumer's `.claude/`. Source: `checks/role_guard.py:28-29`.
16. **[HARD]** ADR append-only enforcement (`Write` blocked on existing ADRs; `Edit` allowed only on frontmatter `status:`/`superseded-by:`/`firmness:` first-line; `ADR_EDITORIAL_FIX=1` additive escape) is load-bearing across distribution. Source: `CLAUDE.md:20`.
17. **[HARD]** `.claude/active-envelope.yaml` is worktree-scoped, fail-closed, must include a self-pattern when `mode: operator`, and is the operator-session write gate when `AGENT_ROLE` is unset. Source: `CLAUDE.md:24`.

## MIGRATION

18. **[HARD]** ADRs are append-only — to retire any prior commitment, the path is a superseding ADR plus a manual `docs/ARCHITECTURE.md` edit in the same commit. Source: `CLAUDE.md:20`, `docs/why-cairn.md:74`.
19. **[HARD]** INV-001 binding (commit prefixes recognised in `_FALLBACK_REGISTRY`) applies to every commit since `2fb83f6`; M5 commits must use registered prefixes — direct commits with unregistered prefixes are not permitted except by superseding ADR. Source: `docs/ARCHITECTURE.md:13`.
20. **[SOFT]** M5 plugin packaging is the named follow-up that absorbs deferred items: operational-reference.md rewrite, spec-v1.md rewrite, `docs/upgrading-from-pre-compression.md` deletion, `scripts/_root.py` audit, `efficiency_program/` test cleanup. Source: `docs/plans/2026-05-07-cairn-shrink-m4-delete-and-relocate.md:1782-1790`.
21. **[SOFT]** M6 (consumer migration of complex-rag-analysis from `.slice-system → .` to plugin install) was originally deferred to a separate program post-M5. *Brainstorm has since combined M5+M6.* Source: `docs/plans/2026-05-06-cairn-shrink-design.md:349-352`.

## DOCS

22. **[SOFT]** README has no reading order; new consumers can land in spec-v1.md (Layer 2) first and bounce. Documentation tiering presumes consumer enters via operational-reference.md. Source: `docs/reviews/2026-04-23-from-portfolio-evaluation.md:68-79`.
23. **[SOFT]** `templates/` currently holds only `handoff.md`; consumers most need `intent.md` / plan-doc / ADR-frontmatter templates. Source: `docs/reviews/2026-04-23-from-portfolio-evaluation.md:82-85`.
24. **[CONTEXT]** `commands/claude-code/.local/` houses cairn-internal dev aids (`/dev-mode`, `/groom`, `/promote`, etc.) that explicitly do NOT ship to consumers; the `.local/` convention is the existing precedent for maintainer-only surfaces. Source: `docs/ARCHITECTURE.md:144`.

## OTHER

25. **[HARD]** Phase shape is firmly locked at four phases (Reader → Skeptic → Builder → Auditor); phase count, names, and roles cannot change in M5 without a `phase-lock-and-role-declaration` supersession. Source: `docs/ARCHITECTURE.md:42,118`.
26. **[HARD]** Vision commitment #1 (agent-portable substrate, Windsurf as second runtime) and commitment #2 (parallelism-native) are v1 commitments; M5 distribution choices must not lock in single-runtime-only or single-branch-only shape. Source: `docs/operational-reference.md:409`, `docs/why-cairn.md:107-108`.
27. **[CONTEXT]** `bootstrap-exception` is the *only* permitted direct-commit exception for cairn's own development; any M5 step bypassing `/decision` or the dispatch skill needs ADR justification, not folklore. Source: `docs/adr/bootstrap-exception.md:36-39`.
