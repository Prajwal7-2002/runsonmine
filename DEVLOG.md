# DEVLOG

## 2026-11-06: v0.1.0 - Result format, validator and static site

- Why: "can I run it?" tools estimate; estimates miss engine overhead, quantization formats and laptop
  memory clocks. A day of auditing showed a roofline estimate of 444 tok/s for a small model that
  Ollama really ran at 164 tok/s on an RTX 3050 laptop, and a battery-capped GPU measuring 12x slower
  with no error. RunsOnMine stores only measured runs, with the conditions needed to trust them.
- Result format v1 (`docs/format.md`, JSON schema in the package): standard test, hardware model
  names, engine and model facts, results at 1/2/4 users, run conditions. Unknown fields are rejected
  (keeps private data out by construction).
- `runsonmine validate`: schema; physical ceiling (single-user speed must not exceed GPU bandwidth /
  weights size, +15%); flags for battery, throttled (busy GPU below half its max clock), partial
  offload, failed requests, unknown GPU or size. A CPU-bound engine (low clock but low utilisation)
  is not flagged as throttled.
- `runsonmine add`: validates and stores a result under its content hash (no duplicates).
- `runsonmine build-site`: static HTML (no JavaScript, light/dark) plus `results.json`.
- Results are produced by `servebench submit` (servebench 1.1.5).
- 14 tests; CI on Windows/macOS/Linux validates every submitted result; Pages workflow deploys the site.
