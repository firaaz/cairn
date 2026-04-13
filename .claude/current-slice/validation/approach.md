# SLICE-008 Phase 2 — Validation Approach

## Ambiguity Resolution

Seven ambiguities identified; all resolved from ARCHITECTURE.md and ADR-003 without human escalation.

| # | Ambiguity | Resolution Source | Outcome |
|---|-----------|-------------------|---------|
| A1 | "runs /refresh-architecture logic" — Python call or protocol text? | Intent boundary section: "gate lives in protocol text, not a git hook" | Protocol text in start-slice.full.md Step 7 |
| A2 | Where does bypass log / rolling window logic live? No new Python module in envelope. | Envelope analysis: only markdown files + unchanged validator | Protocol instructions, not executable code. Tests verify protocol text content. |
| A3 | Rolling window "last 10 slices by numeric suffix" — gaps, fewer than 10? | ADR-003 D1 + intent spec | Window = [max(current-9, 1), current]. Gaps allowed. Fewer than 10 is fine. |
| A4 | "Three bypasses triggers" — exactly 3 or >= 3? | ADR-003 D1: "a third bypass... is itself a trigger" | >= 3 triggers warning |
| A5 | "Triggers D1 design review" — blocking or advisory? | Intent V4: "triggers a warning message" | Advisory warning, not blocking gate |
| A6 | Session isolation testability | Intent: protocol text constraints | Test verifies markdown contains explicit isolation instructions |
| A7 | Bypass check timing — at write or separately? | Intent V3 and V4 are separate verification items | Write bypass (V3), then check window (V4), both during slice-close |

## Test Strategy

Contract-conformance tests against protocol files, matching the existing pattern in `test_context_discipline_protocol.py`. Six tests map 1:1 to the six intent verification items:

- **V1**: Step 7 references refresh-architecture and validate_architecture, describes blocking on failure
- **V2**: Step 7 instructs printing validator output, mentions ADR_D1_BYPASS escape hatch
- **V3**: Step 7 documents bypass log path, format (`<slice-id> <YYYY-MM-DD> <reason>`), append-only semantics
- **V4**: Step 7 documents rolling-window check (3 bypasses, 10 slices, numeric suffix, warning trigger)
- **V5**: Step 7 documents session isolation (loads ADR corpus + ARCHITECTURE.md, excludes current-slice and phase-role artifacts, excludes index.md/superseded)
- **V6**: refresh-architecture.md/.full.md mentions D1 auto-invocation while preserving manual path

Primitives reused from SLICE-002 test suite: `slice_section`, `contains_all`, `proximity`.

## Design Decision

No new Python module was introduced for bypass log parsing. The intent declares `validate_architecture.py` unchanged, and the envelope contains no other Python source. The rolling window check is protocol text — the agent executing `/start-slice complete` follows the instructions, not a Python function. Tests verify the instructions exist and are complete, consistent with how cairn's other protocol tests work.
