---
contract:
  must-satisfy:
    - every body line names a thread with a resolvable pointer
    - each thread declares state ∈ {open, blocked, deferred}
  must-not-violate:
    - no narrative prose; no multi-sentence entries
  wrong-if:
    - any pointer fails to resolve on read
  evidence:
    - tests/unit/test_handoff_contract.py passes
---
- <pointer> <state> [<short context>]
- gh:<org>/<repo>#<num> open <short-slug-context>
- docs/adr/<slug>.md blocked <named-blocker>
- docs/plans/<filename>.md deferred <trigger-condition>
- <commit-sha-7-or-40> open <short-slug-context>
