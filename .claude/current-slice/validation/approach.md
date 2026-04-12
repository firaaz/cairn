# SLICE-005 Phase 2: Validation Approach

## Ambiguity Resolutions

**A1: `supersedes:` vs `supersedes-sections:` for partial supersession.**
Intent verification explicitly names the `supersedes:` field. Spec detail says "Supersession references use the `supersedes:` frontmatter field AND inline prose." Test checks `supersedes:` field per the intent. The `supersedes-sections:` field may carry additional references but is not required by the intent.

**A2: ADR-005 tooling specifications — specification vs implementation.**
Precedent: ADR-003 D1 specifies "post-slice hook fires `/refresh-architecture` automatically" — behavioral specification, not implementation. ADR-005 specifying what the guard must match (glob patterns, naming scheme) is specification-level. The "no implementation decisions" boundary prohibits code, file edits, build procedures — not behavioral specifications of what must be enforced.

**A3: ADR-004 D4 "excluded items" terminology mismatch.**
Verification item says "each ADR-004 D4 time-boxed item" but ADR-004 D4 items are excluded skills, not time-boxed items (ADR-003 D4 has the time-box). The supersession map clarifies: ADR-007 un-excludes `dispatching-parallel-agents` and `using-git-worktrees`. Test checks those two explicitly and verifies remaining exclusions are addressed.

**A4: ADR-008 INV-002 amendment — conditional.**
ADR-008 must contain an explicit disposition — either "INV-002 accommodates without amendment" or "INV-002 is amended as follows." Test checks for an explicit statement either way.

**A5: ADR-008 token budget interaction.**
ADR-002 Layer 1 sets 150-400 token budget for handoff.md. ADR-008 adds a cross-feature index within that budget. The ADR must address how the index fits within or modifies that budget. Test checks for reference to the token budget.

**A6: Risk Register conditional on firmness.**
Spec detail: "Risk Register (if provisional)." ADR-007 (`firmness: provisional`) requires a Risk Register section. ADR-005/006/008 (`firmness: firm`) do not.

**A7: `superseded-by:` backfill is out of envelope.**
ADR-003 and ADR-004's `superseded-by: null` fields are outside the SLICE-005 envelope. Backfill belongs to a future maintenance pass. Tests do NOT verify backfill.

## Test Strategy

Test file: `tests/unit/test_slice_005_design_decomposition.py`

Maps intent.md verification items V1-V8 to pytest tests. Tests are RED at Phase 2 commit (ADR files don't exist yet) and flip GREEN at Phase 3 commit. One regression canary (index format) is GREEN from the start.

| Test | Verification Item | What it checks |
|------|-------------------|----------------|
| test_v1_four_adr_files_exist | V1 | Glob match for 005-*.md through 008-*.md |
| test_v2_frontmatter_valid | V2 | YAML frontmatter has id, title, status, firmness, date |
| test_v3_adr007_supersession | V3 | `supersedes:` references ADR-003; prose explains partial scope |
| test_v4_adr007_addresses_adr004_d4 | V4 | ADR-007 addresses each ADR-004 D4 excluded skill |
| test_v5_adr008_inv002_statement | V5 | ADR-008 explicitly states INV-002 disposition |
| test_v6_index_updated | V6 | index.md has rows for ADR-005 through ADR-008 |
| test_v7_envelope_compliance | V7 | Only envelope files modified (git diff check) |
| test_v8_no_implementation_decisions | V8 | ADRs have no code blocks with implementation patterns |
| test_adr_required_sections | Spec detail | Each ADR has Context, Decision, Consequences sections |
| test_adr007_provisional_risk_register | A6 | ADR-007 (provisional) has Risk Register section |
| test_adr005_firmness_firm | Spec detail | ADR-005 firmness is firm per intent |
| test_adr006_firmness_firm | Spec detail | ADR-006 firmness is firm per intent |
| test_adr007_firmness_provisional | Spec detail | ADR-007 firmness is provisional per intent |
| test_adr008_firmness_firm | Spec detail | ADR-008 firmness is firm per intent |
| test_adr008_token_budget_reference | A5 | ADR-008 references ADR-002's token budget |
| test_index_format_canary | Canary | index.md table has expected column structure (GREEN from start) |
