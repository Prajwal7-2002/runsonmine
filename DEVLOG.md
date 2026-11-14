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

## 2026-11-07: v0.2.0 - Contributor guide, Kaggle notebook, upload service

- `docs/contribute.md`: Mac/Windows/Linux steps using `uvx servebench submit` (uv brings its own
  Python; macOS ships 3.9, servebench needs 3.11), model sizes per memory, and a message for friends.
- `contrib/kaggle-runsonmine.ipynb`: free T4/P100 runs (Ollama + 5 Apache-2.0 models).
- `runsonmine.service`: FastAPI upload service for a Hugging Face Space. Validates with the same
  checks as CI, skips duplicates by content hash, opens a GitHub pull request (token limited to this
  repo), rate-limits per IP in memory, stores nothing. `space/` holds the Space config.
- Live check: the GitHub client's read calls work against the real repo; the write path is tested
  with a fake GitHub until the Space is deployed. 21 tests.

## 2026-11-07: v0.3.0 - First Kaggle results; better throttling rule; serving GPU

First cloud results (Kaggle "GPU T4 x2", Ollama 0.40.15) exposed two problems:
- **Wrong GPU monitored.** Ollama ran 3 of 5 models on the second T4 while servebench monitored the
  first, so those files reported an idle GPU (0% busy, 585 MHz). Speeds were right, conditions wrong:
  only the 2 runs on the monitored GPU (qwen2.5:0.5b, mistral:7b) were added; the others will be
  re-run. Fixes: new optional `hardware.serving_gpu` (which GPU served and was monitored; the ceiling
  uses it); the notebook pins Ollama to GPU 0; servebench 1.1.6 picks the GPU holding the model.
- **False "throttled" flag.** A 70 W Tesla T4 at full load runs at its power limit and clocks down
  (654 of 1590 MHz) by design. New rule: flag below 25% of max clock regardless (the laptop left at a
  10 W cap: 210 of 2100 MHz), or below 50% only when the GPU is not at its power limit.
- Also: Ollama 0.40.15 serves one request at a time by default, so on Kaggle 4 users got no more
  total throughput than 1 (qwen2.5:0.5b: 232 tok/s at 1, 2 and 4 users) while first-token time grew
  to 1.7 s; the laptop's Ollama 0.35.1 batched (417 tok/s at 4 users). Engine settings matter as much
  as the GPU; recording them is a future format addition.
- Notebook: `env -u PYTHONPATH` (Kaggle's sitecustomize needs `wrapt`), errors are no longer hidden.

## 2026-11-07: Kaggle T4 re-run (servebench 1.1.6)

- qwen2.5 1.5b/3b/7b re-measured with `serving_gpu: 0`; the GPU is genuinely busy (80-97%, 65-66 W of
  70 W) and speeds match the first run (136 / 77 / 29 tok/s for 1 user). 8 results total.
- Notebook bug: `!` lines in Jupyter substitute `{var}` only if the whole line parses; a grep pattern
  containing braces made `{model}` go through literally (servebench asked Ollama for "{model}"). The
  models cell is now plain Python (subprocess), restarts Ollama if it stops, and keeps errors visible.

## 2026-11-14: v0.3.1 - Native dataset builder, expanded GPU bandwidths, servebench 1-click upload

- `runsonmine build-dataset`: native CLI command and module `runsonmine.dataset` extracting verified
  runs from `data/results/` into Hugging Face CSV and JSON tables (`hf_dataset/consumer_silicon_benchmarks.csv`
  and `concurrency_scaling_curves.csv`).
- Expanded GPU bandwidths (`src/runsonmine/gpus.py`): added RTX 4070/4070 Ti Super, RTX 3060/3070/3080 Ti,
  RTX 20-series, GTX 1660 series, AMD Radeon RX 7000/6000 series (RX 7900 XTX 960 GB/s to RX 6600 224 GB/s),
  Intel Arc (A770 560 GB/s down to A380), and Snapdragon X Elite (136 GB/s) to prevent false unknown-GPU flags.
- `servebench submit --upload`: integrated 1-click submission flag uploading directly to the RunsOnMine
  FastAPI Space endpoint with PR link display, duplicate handling, and physics rejection feedback.
- 26 tests passing in runsonmine; 12 submit tests passing in servebench.

