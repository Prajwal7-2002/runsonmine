---
language:
- en
license: apache-2.0
size_categories:
- n<1K
task_categories:
- text-generation
- other
tags:
- serving-benchmarks
- inference
- consumer-gpu
- rtx-3050
- tesla-t4
- ollama
- vllm
- hardware-benchmarks
- evaluation
- memory-bandwidth
pretty_name: "Consumer Silicon LLM Serving Benchmarks (RTX, Tesla T4, Apple Silicon)"
configs:
- config_name: consumer_silicon_benchmarks
  data_files:
  - split: train
    path: consumer_silicon_benchmarks.json
  default: true
- config_name: concurrency_scaling_curves
  data_files:
  - split: train
    path: concurrency_scaling_curves.json
---

# 💻 Consumer Silicon LLM Serving Benchmarks (RTX, Tesla T4, Apple Silicon)

An open-source empirical benchmark dataset containing real physical silicon measurements of
**LLM serving performance** (TTFT, TPOT, ITL, Memory Bandwidth Utilization, and Concurrency
Scaling) across consumer and cloud GPUs (Tesla T4, NVIDIA GeForce RTX 3050 6GB Laptop GPU, AMD Ryzen CPU) running
Ollama (`llama.cpp`) and `mini-infer`.

* **Benchmark Harness:** [Prajwal7-2002/servebench](https://github.com/Prajwal7-2002/servebench) (`pip install servebench`)
* **Community Leaderboard & Collector:** [Prajwal7-2002/runsonmine](https://github.com/Prajwal7-2002/runsonmine)
* **Author:** Prajwal Pujari ([@Prajwal7-2002](https://github.com/Prajwal7-2002))

---

## 📊 Quick Start

Load the measured silicon benchmarks directly in Python:

```python
from datasets import load_dataset

# Load consumer silicon serving benchmarks
dataset = load_dataset("prajwalpujari16/consumer-silicon-benchmarks")

# Inspect master hardware leaderboard
df_silicon = dataset["consumer_silicon_benchmarks"].to_pandas()
print(
    df_silicon[
        [
            "hardware_gpu",
            "model_name",
            "concurrency_users",
            "output_throughput_tok_s",
            "tpot_ms_p50",
        ]
    ]
)

# Inspect concurrency scaling profile (c=1 to c=8)
df_curves = dataset["concurrency_scaling_curves"].to_pandas()
print(df_curves[["concurrency", "output_throughput_tok_s", "ttft_p50_ms", "tpot_p50_ms"]])
```

---

## 🔬 Empirical Silicon Hardware Leaderboard

| Hardware | Accelerator VRAM | Model | Parameters | Quantization | Concurrency | Total Throughput | Per-User Speed | TTFT p50 | TPOT p50 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tesla T4 (Dual T4)** | 30.0 GB | `qwen2.5:0.5b` | 494.0M | Q4_K_M | **c = 1** | **232.0 tok/s** | 246.7 tok/s | **35.4 ms** | **4.1 ms** |
| **Tesla T4 (Dual T4)** | 30.0 GB | `qwen2.5:0.5b` | 494.0M | Q4_K_M | **c = 4** | **229.7 tok/s** | 243.3 tok/s | 1695.2 ms | **4.1 ms** |
| **Tesla T4 (Dual T4)** | 30.0 GB | `qwen2.5:1.5b` | 1.54B | Q4_K_M | **c = 1** | **118.4 tok/s** | 125.1 tok/s | **48.2 ms** | **8.1 ms** |
| **Tesla T4 (Dual T4)** | 30.0 GB | `qwen2.5:3b` | 3.09B | Q4_K_M | **c = 1** | **78.2 tok/s** | 82.5 tok/s | **68.5 ms** | **12.3 ms** |
| **Tesla T4 (Dual T4)** | 30.0 GB | `qwen2.5:7b` | 7.62B | Q4_K_M | **c = 1** | **34.8 tok/s** | 36.4 tok/s | **124.0 ms** | **27.6 ms** |
| **Tesla T4 (Dual T4)** | 30.0 GB | `mistral:7b` | 7.24B | Q4_K_M | **c = 1** | **33.5 tok/s** | 35.1 tok/s | **131.2 ms** | **28.9 ms** |
| **RTX 3050 Laptop** | 6.0 GB | `qwen2.5:0.5b` | 494.0M | Q4_K_M | **c = 1** | **188.9 tok/s** | 188.9 tok/s | **42.9 ms** | **4.9 ms** |
| **RTX 3050 Laptop** | 6.0 GB | `qwen2.5:0.5b` | 494.0M | Q4_K_M | **c = 4** | **198.5 tok/s** | 49.6 tok/s | **103.5 ms** | **8.3 ms** |
| **RTX 3050 Laptop** | 6.0 GB | `qwen2.5:1.5b` | 1.54B | Q4_K_M | **c = 1** | **92.4 tok/s** | 92.4 tok/s | **80.7 ms** | **10.7 ms** |
| **RTX 3050 Laptop** | 6.0 GB | `qwen2.5-coder:3b` | 3.09B | Q4_K_M | **c = 1** | **54.1 tok/s** | 54.1 tok/s | **136.7 ms** | **17.8 ms** |

---

## 📈 Concurrency Scaling Profile ($c = 1 \to 8$)

Measured with `servebench` on NVIDIA GeForce RTX 3050 6GB Laptop GPU running `qwen2.5:0.5b` (Q4_K_M):

| Concurrency ($c$) | Output Throughput | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | TPOT p99 (ms) | ITL Jitter (ms) | SLO Met (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 188.9 tok/s | 42.9 ms | 64.9 ms | 4.9 ms | 5.3 ms | 4.9 ms | 100.0% |
| **2** | 194.2 tok/s | 60.7 ms | 82.1 ms | 5.9 ms | 6.8 ms | 5.8 ms | 100.0% |
| **4** | 198.5 tok/s | 103.5 ms | 142.0 ms | 8.3 ms | 11.2 ms | 8.1 ms | 100.0% |
| **5** | 199.1 tok/s | 148.2 ms | 195.4 ms | 10.4 ms | 14.5 ms | 10.2 ms | 98.4% |
| **6** | 199.8 tok/s | 198.6 ms | 265.1 ms | 12.8 ms | 18.2 ms | 12.6 ms | 95.2% |
| **8** | 200.4 tok/s | 312.4 ms | 445.0 ms | 16.9 ms | 24.1 ms | 16.5 ms | 88.5% |

---

## 🛠️ Reproducing Locally

```bash
# Profile local server capacity with automated roofline analysis
pip install servebench
servebench quick

# Compare hardware benchmarks against the community leaderboard
pip install runsonmine
runsonmine validate data/results
```

---

## 📜 Citation

```bibtex
@misc{pujari2026consumersilicon,
  author = {Prajwal Pujari},
  title = {Consumer Silicon LLM Serving Benchmarks (RTX, Tesla T4, Apple Silicon)},
  year = {2026},
  publisher = {Hugging Face},
  journal = {Hugging Face Data repository},
  howpublished = {\\url{https://huggingface.co/datasets/prajwalpujari16/consumer-silicon-benchmarks}}
}
```
