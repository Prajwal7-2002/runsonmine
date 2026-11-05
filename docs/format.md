# RunsOnMine result format, v1

One file = one measured run of one model on one machine. Files are JSON, created by
`servebench submit` (servebench 1.1.5 or later), and stored in `data/results/`. The machine-readable
schema is [`src/runsonmine/schema/result-v1.schema.json`](../src/runsonmine/schema/result-v1.schema.json).

## What is in a result

| Field | Contents |
| :--- | :--- |
| `schema` | Always `runsonmine/result/v1`. |
| `date` | Day the test ran (UTC), e.g. `2026-11-06`. No time of day. |
| `tool` | The program that ran the test: `{"name": "servebench", "version": "1.1.5"}`. |
| `test` | The standard test's settings (below). Results are only comparable when these match. |
| `hardware` | `gpus` (name, VRAM in GB, driver), `cpu` (model name), `ram_gb`, `os` (e.g. `Windows 11`). |
| `engine` | Serving engine name and version as it reports them, e.g. `Ollama` `0.35.1`. |
| `model` | `name` as the engine knows it; when the engine reports them, `parameter_count`, `parameters` (e.g. `494.03M`), `quantization` (e.g. `Q4_K_M`), `weights_gb` (size of the weights) and `on_gpu` (e.g. `100%`). |
| `results` | One entry per user count (below). |
| `conditions` | How the machine was running: `power_source` (`ac` / `battery`), average and maximum GPU clock, average power and the power limit, average GPU utilisation, peak temperature. Missing values are left out. |

### The standard test (`standard-v1`)

- 1, then 2, then 4 users at once (closed loop: each user sends the next request when the previous one finishes).
- 16 requests per level after 2 warm-up requests; synthetic prompts of about 256 tokens, fixed seed.
- Exactly 128 output tokens per request (`ignore_eos`), temperature 0.

### One result entry

| Field | Meaning |
| :--- | :--- |
| `users` | How many users at once. |
| `ok`, `failed` | Requests that completed / failed. |
| `output_tok_s` | Generated tokens per second, all users together. |
| `per_user_tok_s` | Generation speed one user sees (1 / median time per output token). |
| `ttft_ms_p50`, `ttft_ms_p90` | Time to first token, median and 90th percentile. |
| `tpot_ms_p50` | Median time per output token after the first. |

## Privacy

A result contains **no** hostname, username, IP address, server URL, file path, prompt or response
text. `servebench submit` prints the whole file before you share it, and its tests fail if the file
contains the machine's hostname, username, the server address or a local path.

## Checks applied to every result

`runsonmine validate` runs these on every file (CI runs it on every pull request):

| Check | Outcome |
| :--- | :--- |
| File matches the schema | **rejected** if not |
| Single-user speed is above the physical ceiling (memory bandwidth of the GPU ÷ size of the weights, +15% tolerance) | **rejected**: the hardware cannot do that, so the run or its metadata is wrong |
| Ran on battery | flagged `battery` |
| GPU busy (≥ 50%) but clocked below half its maximum | flagged `throttled` |
| Model not fully on the GPU | flagged `partial-offload` |
| Any failed requests | flagged `failed-requests` |
| Engine did not report the weights size | flagged `size-unknown` (no ceiling check possible) |
| GPU not in the bandwidth table | flagged `unknown-gpu` (no ceiling check possible) |

Flagged results are kept and shown with their flags; the site leaves them out of "best result"
summaries.

## File names

`data/results/<first 12 hex characters of the SHA-256 of the file>.json`, so the same run cannot be
added twice. `runsonmine add <file>` validates a file and copies it in under the right name.

## Licence

Result files are licensed under [CC BY 4.0](../data/LICENSE.md): use them freely, credit
RunsOnMine. The code in this repository is Apache 2.0.
