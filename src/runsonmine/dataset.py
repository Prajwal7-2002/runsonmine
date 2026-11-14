"""Generate empirical consumer silicon serving benchmarks and concurrency scaling curves."""

from __future__ import annotations

import csv
import json
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Any


@cache
def _dataset_card() -> str:
    return (
        resources.files("runsonmine").joinpath("schema/dataset_card.md").read_text(encoding="utf-8")
    )


def build_dataset(
    results_dir: Path,
    out_dir: Path,
    servebench_result_file: Path | None = None,
) -> tuple[int, int]:
    """Extract measured silicon runs into structured CSV and JSON dataset files.

    Returns (num_master_rows, num_scaling_rows).
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Master Hardware Leaderboard from runsonmine results
    master_rows: list[dict[str, Any]] = []

    for json_file in sorted(results_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        run_id = json_file.stem
        gpus = data.get("hardware", {}).get("gpus", [])
        gpu_name = gpus[0].get("name", "Unknown GPU") if gpus else "CPU Only"
        gpu_count = len(gpus)
        vram_gb = sum(g.get("vram_gb", 0.0) for g in gpus)
        cpu = data.get("hardware", {}).get("cpu", "Unknown CPU")
        os_name = data.get("hardware", {}).get("os", "Linux")
        engine = data.get("engine", {}).get("name", "Ollama")
        engine_ver = data.get("engine", {}).get("version", "0.4.0")

        model_name = data.get("model", {}).get("name", "Unknown")
        params = data.get("model", {}).get("parameters", "Unknown")
        quant = data.get("model", {}).get("quantization", "Q4_K_M")
        weights_gb = data.get("model", {}).get("weights_gb", 0.0)
        gpu_clock = data.get("conditions", {}).get("gpu_clock_avg_mhz", 0.0)
        date = data.get("date", "2026-11-06")

        for res in data.get("results", []):
            master_rows.append(
                {
                    "run_id": run_id,
                    "hardware_gpu": gpu_name,
                    "gpu_count": gpu_count,
                    "total_vram_gb": round(vram_gb, 1),
                    "hardware_cpu": cpu,
                    "operating_system": os_name,
                    "serving_engine": engine,
                    "engine_version": engine_ver,
                    "model_name": model_name,
                    "parameters": params,
                    "quantization": quant,
                    "weights_gb": round(weights_gb, 3),
                    "concurrency_users": res.get("users", 1),
                    "output_throughput_tok_s": round(res.get("output_tok_s", 0.0), 2),
                    "per_user_tok_s": round(res.get("per_user_tok_s", 0.0), 2),
                    "ttft_p50_ms": round(res.get("ttft_ms_p50", 0.0), 1),
                    "ttft_p90_ms": round(res.get("ttft_ms_p90", 0.0), 1),
                    "tpot_p50_ms": round(res.get("tpot_ms_p50", 0.0), 1),
                    "gpu_clock_mhz": round(gpu_clock, 1),
                    "measured_date": date,
                }
            )

    if master_rows:
        master_csv = out_dir / "consumer_silicon_benchmarks.csv"
        with open(master_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(master_rows[0].keys()))
            writer.writeheader()
            writer.writerows(master_rows)

        (out_dir / "consumer_silicon_benchmarks.json").write_text(
            json.dumps(master_rows, indent=2), encoding="utf-8"
        )

    # 2. Concurrency Scaling Curves
    scaling_rows: list[dict[str, Any]] = []
    if servebench_result_file and servebench_result_file.exists():
        with open(servebench_result_file, encoding="utf-8") as f:
            sb_data = json.load(f)

        hw_info = sb_data.get("environment", {})
        gpu_str = hw_info.get("gpus", ["NVIDIA GeForce RTX 3050 6GB Laptop GPU"])[0]
        model_str = sb_data.get("config", {}).get("model", "qwen2.5:0.5b")

        for lvl in sb_data.get("levels", []):
            c_val = int(lvl.get("value", 1.0))
            s = lvl.get("summary", {})
            ttft = s.get("ttft", {})
            tpot = s.get("tpot", {})
            itl = s.get("itl", {})
            e2e = s.get("e2e", {})

            scaling_rows.append(
                {
                    "concurrency": c_val,
                    "hardware": gpu_str.split(",")[0].strip(),
                    "model": model_str,
                    "output_throughput_tok_s": round(s.get("output_throughput", 0.0), 1),
                    "input_throughput_tok_s": round(s.get("input_throughput", 0.0), 1),
                    "ttft_p50_ms": round(ttft.get("p50", 0.0) * 1000, 1),
                    "ttft_p90_ms": round(ttft.get("p90", 0.0) * 1000, 1),
                    "ttft_p99_ms": round(ttft.get("p99", 0.0) * 1000, 1),
                    "tpot_p50_ms": round(tpot.get("p50", 0.0) * 1000, 1),
                    "tpot_p99_ms": round(tpot.get("p99", 0.0) * 1000, 1),
                    "itl_p50_ms": round(itl.get("p50", 0.0) * 1000, 1),
                    "itl_p99_ms": round(itl.get("p99", 0.0) * 1000, 1),
                    "e2e_p50_ms": round(e2e.get("p50", 0.0) * 1000, 1),
                    "slo_attainment_pct": round(s.get("slo_attainment", 1.0) * 100, 1),
                }
            )

    if scaling_rows:
        scaling_csv = out_dir / "concurrency_scaling_curves.csv"
        with open(scaling_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(scaling_rows[0].keys()))
            writer.writeheader()
            writer.writerows(scaling_rows)

        (out_dir / "concurrency_scaling_curves.json").write_text(
            json.dumps(scaling_rows, indent=2), encoding="utf-8"
        )

    # 3. Dataset Card README.md
    (out_dir / "README.md").write_text(_dataset_card(), encoding="utf-8")
    return len(master_rows), len(scaling_rows)
