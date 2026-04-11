# Session Learning Staging Ground

Append-only. Free-form entries captured at session end. Promotion to CLAUDE.md happens via the 3× rule in a later slice.

## SLICE-002 drift: slice.yaml close exception

intent §4 / ADR-002 L3 say no file survives close. start-slice.md:197 carves out slice.yaml for `status: complete`. Tests encode the weaker reading. Resolve in next slice on start-slice.md or via /new-adr supersede.
