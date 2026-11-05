import copy

import pytest

VALID = {
    "schema": "runsonmine/result/v1",
    "date": "2026-11-06",
    "tool": {"name": "servebench", "version": "1.1.5"},
    "test": {
        "name": "standard-v1",
        "users": [1, 2, 4],
        "requests_per_level": 16,
        "input_tokens": 256,
        "output_tokens": 128,
        "warmup_requests": 2,
        "seed": 1,
        "ignore_eos": True,
        "temperature": 0.0,
    },
    "hardware": {
        "gpus": [
            {"name": "NVIDIA GeForce RTX 3050 6GB Laptop GPU", "vram_gb": 6.0, "driver": "551.76"}
        ],
        "cpu": "AMD Ryzen 5 6600H with Radeon Graphics",
        "ram_gb": 15.3,
        "os": "Windows 11",
    },
    "engine": {"name": "Ollama", "version": "0.35.1"},
    "model": {
        "name": "qwen2.5:0.5b",
        "parameter_count": 494032768,
        "parameters": "494.03M",
        "quantization": "Q4_K_M",
        "weights_gb": 0.398,
        "on_gpu": "100%",
    },
    "results": [
        {
            "users": 1,
            "ok": 16,
            "failed": 0,
            "output_tok_s": 190.9,
            "per_user_tok_s": 200.0,
            "ttft_ms_p50": 43.0,
            "ttft_ms_p90": 47.0,
            "tpot_ms_p50": 5.0,
        },
        {
            "users": 2,
            "ok": 16,
            "failed": 0,
            "output_tok_s": 315.1,
            "per_user_tok_s": 170.0,
            "ttft_ms_p50": 58.0,
            "ttft_ms_p90": 66.0,
            "tpot_ms_p50": 5.9,
        },
        {
            "users": 4,
            "ok": 16,
            "failed": 0,
            "output_tok_s": 406.1,
            "per_user_tok_s": 120.0,
            "ttft_ms_p50": 85.0,
            "ttft_ms_p90": 112.0,
            "tpot_ms_p50": 8.3,
        },
    ],
    "conditions": {
        "power_source": "ac",
        "gpu_clock_avg_mhz": 1640.0,
        "gpu_clock_max_mhz": 2100.0,
        "gpu_power_avg_w": 42.0,
        "gpu_power_limit_w": 60.0,
        "gpu_util_avg_pct": 85.0,
        "gpu_temp_max_c": 65.0,
    },
}


@pytest.fixture
def result():
    return copy.deepcopy(VALID)
