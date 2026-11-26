"""Build-time lookup matrix combining measured RunsOnMine data and infersize predictions."""

from __future__ import annotations

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from infersize.analytics.cost import estimate_serving_cost
from infersize.analytics.vram import estimate_vram_usage
from infersize.hardware.specs import GPU_PRESETS, GPUProfile
from infersize.models.specs import MODEL_PRESETS, ModelArch

from .validate import check

CONTRIBUTE_URL = "https://github.com/Prajwal7-2002/runsonmine/blob/main/docs/contribute.md"
DEFAULT_QUANTS = ["q4_k_m", "q8_0", "fp16"]
CONTEXT_TOKENS = 2048

_OLLAMA_TAGS: dict[str, str] = {
    "qwen2.5-0.5b": "qwen2.5:0.5b",
    "qwen2.5-1.5b": "qwen2.5:1.5b",
    "qwen2.5-3b": "qwen2.5:3b",
    "qwen2.5-7b": "qwen2.5:7b",
    "qwen2.5-14b": "qwen2.5:14b",
    "qwen2.5-32b": "qwen2.5:32b",
    "qwen2.5-72b": "qwen2.5:72b",
    "llama3-8b": "llama3:8b",
    "llama3-70b": "llama3:70b",
    "mistral-7b": "mistral:7b",
    "phi-3-mini": "phi3:mini",
    "mixtral-8x7b": "mixtral:8x7b",
    "qwen2.5-coder-3b": "qwen2.5-coder:3b",
}

_MODEL_ARCH_ALIASES: dict[str, str] = {
    "qwen2.5-coder-3b": "qwen2.5-3b",
}


def normalize_model_id(name: str) -> str:
    """Normalize a model name (e.g. 'qwen2.5:0.5b') into a canonical lookup key."""
    return name.strip().lower().replace(":", "-")


def normalize_quant(quant: str | None) -> str:
    """Normalize quantisation names (e.g. 'Q4_K_M' -> 'q4_k_m')."""
    return (quant or "q4_k_m").strip().lower()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "hardware"


def match_hardware(result: dict) -> tuple[str, str]:
    """Return (hardware_id, display_label) for a validated result payload."""
    gpus = result["hardware"]["gpus"]
    if not gpus:
        return "cpu-only", "CPU only (no dedicated GPU)"

    serving = result["hardware"].get("serving_gpu", 0)
    gpu = gpus[serving]
    raw_name = gpu["name"]
    low = raw_name.lower()
    vram = float(gpu.get("vram_gb") or 0.0)

    if "a100" in low:
        key = "a100-40gb" if 0 < vram <= 48 else "a100-80gb"
        return key, GPU_PRESETS[key].display_name
    if "m3 max" in low:
        key = "m3-max-36gb" if 0 < vram <= 64 else "m3-max-128gb"
        return key, GPU_PRESETS[key].display_name
    if "tesla t4" in low or re.search(r"\bt4\b", low):
        return "t4", GPU_PRESETS["t4"].display_name
    if "h100" in low:
        return "h100-80gb", GPU_PRESETS["h100-80gb"].display_name
    if "h200" in low:
        return "h200-141gb", GPU_PRESETS["h200-141gb"].display_name

    compact = re.sub(r"[^a-z0-9]+", "", low)
    for preset_id, spec in GPU_PRESETS.items():
        token = re.sub(r"[^a-z0-9]+", "", preset_id)
        if token in compact:
            return preset_id, spec.display_name

    return _slug(raw_name), raw_name


def _resolve_model_arch(model_id: str) -> ModelArch | None:
    if model_id in MODEL_PRESETS:
        return MODEL_PRESETS[model_id]
    alias = _MODEL_ARCH_ALIASES.get(model_id)
    if alias and alias in MODEL_PRESETS:
        return MODEL_PRESETS[alias]
    return None


def _measure_command(model_id: str, raw_names: list[str] | None = None) -> str:
    tag = (
        _OLLAMA_TAGS.get(model_id)
        or (raw_names[0] if raw_names else None)
        or model_id.replace("-", ":", 1)
    )
    return f"uvx servebench@latest submit --model {tag}"


def _measured_entry(
    model_id: str,
    model_label: str,
    quant_id: str,
    hw_id: str,
    hw_label: str,
    items: list[tuple[dict, list[str]]],
) -> dict:
    decodes: list[float] = []
    prefills: list[float] = []
    ttfts: list[float] = []
    engines: set[str] = set()
    dates: set[str] = set()
    flags: set[str] = set()
    raw_models: list[str] = []

    for r, run_flags in items:
        raw_models.append(r["model"]["name"])
        by_users = {lv["users"]: lv for lv in r["results"]}
        one = by_users[1]
        decodes.append(float(one["per_user_tok_s"]))
        ttft_ms = float(one["ttft_ms_p50"])
        ttfts.append(ttft_ms)
        input_tok = float(r["test"]["input_tokens"])
        if ttft_ms > 0:
            prefills.append(input_tok / (ttft_ms / 1000.0))
        e = r["engine"]
        eng = " ".join(x for x in (e.get("name"), e.get("version")) if x)
        if eng:
            engines.add(eng)
        dates.add(r["date"])
        flags.update(run_flags)

    n = len(items)
    label = "1 measurement" if n == 1 else f"Measured ({n} measurements)"
    sorted_dates = sorted(dates)
    sorted_flags = sorted(flags)
    return {
        "key": f"{model_id}|{quant_id}|{hw_id}",
        "model": model_id,
        "model_label": model_label,
        "quant": quant_id,
        "hardware": hw_id,
        "hardware_label": hw_label,
        "status": "measured",
        "label": label,
        "n": n,
        "decode_median_tok_s": round(statistics.median(decodes), 1),
        "decode_min_tok_s": round(min(decodes), 1),
        "decode_max_tok_s": round(max(decodes), 1),
        "prefill_median_tok_s": round(statistics.median(prefills), 1) if prefills else None,
        "prefill_min_tok_s": round(min(prefills), 1) if prefills else None,
        "prefill_max_tok_s": round(max(prefills), 1) if prefills else None,
        "ttft_median_ms": round(statistics.median(ttfts), 1),
        "engines": sorted(engines),
        "dates": sorted_dates,
        "flags": sorted_flags,
        "predicted_decode_ceiling_tok_s": None,
        "predicted_vram_gb": None,
        "gpu_vram_gb": None,
        "oom_deficit_gb": None,
        "error_note": None,
        "measure_command": _measure_command(model_id, raw_models),
        "contribute_url": CONTRIBUTE_URL,
    }


def _predicted_entry(
    model_id: str,
    model_label: str,
    quant_id: str,
    hw_id: str,
    hw_label: str,
    arch: ModelArch | None,
    gpu: GPUProfile | None,
) -> dict:
    cmd = _measure_command(model_id)
    base = {
        "key": f"{model_id}|{quant_id}|{hw_id}",
        "model": model_id,
        "model_label": model_label,
        "quant": quant_id,
        "hardware": hw_id,
        "hardware_label": hw_label,
        "n": 0,
        "decode_median_tok_s": None,
        "decode_min_tok_s": None,
        "decode_max_tok_s": None,
        "prefill_median_tok_s": None,
        "prefill_min_tok_s": None,
        "prefill_max_tok_s": None,
        "ttft_median_ms": None,
        "engines": [],
        "dates": [],
        "flags": [],
        "measure_command": cmd,
        "contribute_url": CONTRIBUTE_URL,
    }
    if arch is None or gpu is None:
        return {
            **base,
            "status": "unknown",
            "label": "No measurements yet",
            "predicted_decode_ceiling_tok_s": None,
            "predicted_vram_gb": None,
            "gpu_vram_gb": gpu.vram_gb if gpu else None,
            "oom_deficit_gb": None,
            "error_note": "error not yet known",
        }

    try:
        vram = estimate_vram_usage(
            arch,
            gpu,
            precision=quant_id,
            kv_cache_dtype="fp16",
            batch_size=1,
            context_tokens=CONTEXT_TOKENS,
        )
    except ValueError:
        return {
            **base,
            "status": "unknown",
            "label": "No measurements yet",
            "predicted_decode_ceiling_tok_s": None,
            "predicted_vram_gb": None,
            "gpu_vram_gb": gpu.vram_gb,
            "oom_deficit_gb": None,
            "error_note": "error not yet known",
        }

    if not vram.fits_in_vram:
        deficit = round(abs(vram.free_vram_headroom_gb), 2)
        return {
            **base,
            "status": "oom",
            "label": "Does not fit in memory (predicted)",
            "predicted_decode_ceiling_tok_s": None,
            "predicted_vram_gb": vram.total_required_vram_gb,
            "weight_memory_gb": vram.weight_memory_gb,
            "kv_cache_memory_gb": vram.kv_cache_memory_gb,
            "gpu_vram_gb": vram.gpu_total_vram_gb,
            "oom_deficit_gb": deficit,
            "error_note": "predicted memory need (error not yet known)",
        }

    cost = estimate_serving_cost(
        arch,
        gpu,
        precision=quant_id,
        kv_cache_dtype="fp16",
        batch_size=1,
        context_tokens=CONTEXT_TOKENS,
        custom_hourly_rate=0.0,
    )
    return {
        **base,
        "status": "predicted",
        "label": "Predicted, not measured",
        "predicted_decode_ceiling_tok_s": round(cost.tokens_per_sec_per_user, 1),
        "predicted_vram_gb": vram.total_required_vram_gb,
        "weight_memory_gb": vram.weight_memory_gb,
        "kv_cache_memory_gb": vram.kv_cache_memory_gb,
        "gpu_vram_gb": vram.gpu_total_vram_gb,
        "oom_deficit_gb": None,
        "error_note": "error not yet known",
    }


def build_lookup(results_dir: Path) -> dict:
    """Compute the full build-time (model, quant, hardware) table from results and infersize."""
    grouped: dict[tuple[str, str, str], list[tuple[dict, list[str]]]] = defaultdict(list)
    model_labels: dict[str, str] = {m: m for m in MODEL_PRESETS}
    quant_ids: list[str] = list(DEFAULT_QUANTS)
    hw_labels: dict[str, str] = {
        **{k: v.display_name for k, v in GPU_PRESETS.items()},
        "cpu-only": "CPU only (no dedicated GPU)",
    }

    for path in sorted(results_dir.glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        v = check(result)
        if not v.ok:
            continue
        m_id = normalize_model_id(result["model"]["name"])
        q_id = normalize_quant(result["model"].get("quantization"))
        hw_id, hw_label = match_hardware(result)
        model_labels.setdefault(m_id, result["model"]["name"])
        if q_id not in quant_ids:
            quant_ids.append(q_id)
        hw_labels.setdefault(hw_id, hw_label)
        grouped[(m_id, q_id, hw_id)].append((result, v.flags))

    entries: dict[str, dict] = {}
    all_models = sorted(model_labels)
    all_hw = list(hw_labels)

    for m_id in all_models:
        arch = _resolve_model_arch(m_id)
        m_label = model_labels[m_id]
        for q_id in quant_ids:
            for hw_id in all_hw:
                hw_label = hw_labels[hw_id]
                key = f"{m_id}|{q_id}|{hw_id}"
                if (m_id, q_id, hw_id) in grouped:
                    entries[key] = _measured_entry(
                        m_id, m_label, q_id, hw_id, hw_label, grouped[(m_id, q_id, hw_id)]
                    )
                else:
                    entries[key] = _predicted_entry(
                        m_id,
                        m_label,
                        q_id,
                        hw_id,
                        hw_label,
                        arch,
                        GPU_PRESETS.get(hw_id),
                    )

    return {
        "context_tokens": CONTEXT_TOKENS,
        "models": [{"id": m, "label": model_labels[m]} for m in all_models],
        "quants": [{"id": q, "label": q.upper()} for q in quant_ids],
        "hardware": [{"id": h, "label": hw_labels[h]} for h in all_hw],
        "entries": entries,
    }
