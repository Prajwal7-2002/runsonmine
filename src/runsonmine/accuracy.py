"""Compute infersize prediction error against every measured RunsOnMine result."""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from infersize.hardware.specs import GPU_PRESETS

from .validate import check
from .will_it_run import (
    _resolve_model_arch,
    match_hardware,
    normalize_model_id,
    normalize_quant,
    predict_single_user,
)


def build_accuracy(results_dir: Path) -> dict:
    """Compare measured single-user decode speeds against infersize baseline predictions."""
    rows: list[dict] = []
    skipped_count = 0

    for path in sorted(results_dir.glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        v = check(result)
        if not v.ok:
            continue

        m_id = normalize_model_id(result["model"]["name"])
        q_id = normalize_quant(result["model"].get("quantization"))
        hw_id, hw_label = match_hardware(result)
        arch = _resolve_model_arch(m_id)
        gpu = GPU_PRESETS.get(hw_id)

        by_users = {lv["users"]: lv for lv in result["results"]}
        measured = float(by_users[1]["per_user_tok_s"])
        pred = predict_single_user(arch, gpu, q_id)
        if pred is None or pred["predicted_tok_s"] is None or measured <= 0:
            skipped_count += 1
            continue

        predicted_tok_s = float(pred["predicted_tok_s"])
        error_tok_s = round(predicted_tok_s - measured, 1)
        signed_pct = round(((predicted_tok_s - measured) / measured) * 100.0, 1)
        abs_pct = round(abs(signed_pct), 1)
        e = result["engine"]
        engine = " ".join(x for x in (e.get("name"), e.get("version")) if x)

        rows.append(
            {
                "id": path.stem,
                "model": result["model"]["name"],
                "model_id": m_id,
                "quant": q_id,
                "hardware": hw_label,
                "hardware_id": hw_id,
                "engine": engine,
                "date": result["date"],
                "flags": sorted(v.flags),
                "measured_tok_s": round(measured, 1),
                "predicted_tok_s": round(predicted_tok_s, 1),
                "error_tok_s": error_tok_s,
                "signed_error_pct": signed_pct,
                "abs_error_pct": abs_pct,
            }
        )

    rows.sort(key=lambda r: (-r["abs_error_pct"], r["model_id"], r["hardware_id"]))
    n = len(rows)
    gpu_count = len({r["hardware_id"] for r in rows})

    if n == 0:
        return {
            "n": 0,
            "skipped_count": skipped_count,
            "gpu_count": 0,
            "median_abs_error_pct": None,
            "min_abs_error_pct": None,
            "max_abs_error_pct": None,
            "early_sample_warning": (
                "No measured rows match infersize presets yet; too early to report an error figure."
            ),
            "summary_label": "error not yet known",
            "rows": [],
        }

    abs_errors = [r["abs_error_pct"] for r in rows]
    median_abs = round(statistics.median(abs_errors), 1)
    min_abs = round(min(abs_errors), 1)
    max_abs = round(max(abs_errors), 1)

    warning = None
    if n < 30 or gpu_count < 5:
        warning = (
            f"Only {n} rows across {gpu_count} GPU(s): too early to trust this error figure "
            "across other hardware or serving engines."
        )

    return {
        "n": n,
        "skipped_count": skipped_count,
        "gpu_count": gpu_count,
        "median_abs_error_pct": median_abs,
        "min_abs_error_pct": min_abs,
        "max_abs_error_pct": max_abs,
        "early_sample_warning": warning,
        "summary_label": f"median abs error {median_abs:.1f}% across {n} rows ({gpu_count} GPUs)",
        "rows": rows,
    }
