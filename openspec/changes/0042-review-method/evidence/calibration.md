# Calibration

One line per fixture, scored by [D10](../design.md#d10)'s answer key. Workers sum the review and security files'
`workers:`; duration is the status log's `start` to `done`; tokens are the agent log's model usage, cache reads included.

seeded-standard: 5 of 5 · standard · workers 2 · duration 567s · tokens 4234144
seeded-high: 5 of 5 · high · workers 89 · duration 3020s · tokens 55602349
clean-standard: no blocker
clean-high: no blocker

The `seeded-high` and `clean-high` runs predate the verifier ceiling and the pass worker: neither shows that the current
high tier finishes, and no run has measured the ceiling.
