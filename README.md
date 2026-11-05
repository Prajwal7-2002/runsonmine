# RunsOnMine

**How fast do local AI models really run on real computers?** RunsOnMine collects *measured*
speeds (not estimates) from people's own laptops, desktops and Macs, so you can see what will run
well on yours before you download a model or buy hardware.

[![CI](https://github.com/Prajwal7-2002/runsonmine/actions/workflows/ci.yml/badge.svg)](https://github.com/Prajwal7-2002/runsonmine/actions/workflows/ci.yml)
[![Code: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-green.svg)](data/LICENSE.md)

Site: https://prajwal7-2002.github.io/runsonmine/

## Why measured

"Can I run it?" calculators estimate speed from specs. Estimates miss what really decides speed:
the engine's overhead, the quantization format, and the laptop's real memory clock. On one RTX 3050
laptop, a roofline estimate said 444 tokens/s for a small model; Ollama really did 164. Every number
here comes from a real run.

## Add your machine (about 2 minutes)

1. Start a model in Ollama, llama.cpp or LM Studio on your computer, plugged in (not on battery).
2. Run:
   ```bash
   pip install -U servebench
   servebench submit
   ```
   It runs a standard test (1, 2 and 4 users), prints the whole result file, and saves it as
   `runsonmine-<engine>-<model>.json`.
3. Open a pull request adding that file to [`data/results/`](data/results/). CI checks it
   automatically. (A one-command upload is coming.)

**What is shared:** GPU/CPU model names, RAM, OS, engine and model details, the measured speeds,
and run conditions (AC or battery, GPU clock and power). **Never:** hostname, username, IP
address, file paths, prompts or responses. Details: [docs/format.md](docs/format.md).

## How results are checked

Every result is validated in CI: it must match the [result format](docs/format.md), and its
single-user speed must be physically possible (below the GPU's memory bandwidth divided by the
model's size). Runs on battery, throttled, partly offloaded to the CPU, or with failed requests are
kept but flagged, and left out of "best" summaries.

## For developers

```bash
uv sync
uv run runsonmine validate data/results     # check every result
uv run runsonmine add path/to/result.json   # validate and add under its content hash
uv run runsonmine build-site --out site     # build the static site
uv run pytest
```

## Licence

Code: Apache 2.0. Data (`data/results/`): CC BY 4.0, free to use with credit to RunsOnMine.
