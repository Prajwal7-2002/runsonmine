import copy
import json
import re

from runsonmine.cli import main
from runsonmine.validate import content_id
from runsonmine.will_it_run import build_lookup


def _write_result(results_dir, payload):
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{content_id(payload)}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_measured_single_and_multiple_results(result, tmp_path):
    d = tmp_path / "results"
    r1 = copy.deepcopy(result)
    r1["date"] = "2026-11-06"
    r1["conditions"]["power_source"] = "battery"
    _write_result(d, r1)

    lookup = build_lookup(d)
    key = ("qwen2.5-0.5b", "q4_k_m", "rtx3050")
    entry = lookup["entries"][f"{key[0]}|{key[1]}|{key[2]}"]
    assert entry["status"] == "measured"
    assert entry["n"] == 1
    assert entry["label"] == "1 measurement"
    assert entry["decode_median_tok_s"] == 200.0
    assert entry["decode_min_tok_s"] == 200.0
    assert entry["decode_max_tok_s"] == 200.0
    assert entry["prefill_median_tok_s"] == round(256 / 0.043, 1)
    assert "Ollama 0.35.1" in entry["engines"]
    assert entry["dates"] == ["2026-11-06"]
    assert "battery" in entry["flags"]

    r2 = copy.deepcopy(result)
    r2["date"] = "2026-11-10"
    r2["results"][0]["per_user_tok_s"] = 180.0
    r2["results"][0]["ttft_ms_p50"] = 50.0
    _write_result(d, r2)

    lookup2 = build_lookup(d)
    entry2 = lookup2["entries"][f"{key[0]}|{key[1]}|{key[2]}"]
    assert entry2["status"] == "measured"
    assert entry2["n"] == 2
    assert entry2["label"] == "Measured (2 measurements)"
    assert entry2["decode_median_tok_s"] == 190.0
    assert entry2["decode_min_tok_s"] == 180.0
    assert entry2["decode_max_tok_s"] == 200.0
    assert entry2["dates"] == ["2026-11-06", "2026-11-10"]


def test_unmeasured_combo_shows_predicted_not_measured(result, tmp_path):
    d = tmp_path / "results"
    _write_result(d, result)

    lookup = build_lookup(d)
    entry = lookup["entries"]["qwen2.5-0.5b|q4_k_m|rtx4090"]
    assert entry["status"] == "predicted"
    assert entry["label"] == "Predicted, not measured"
    assert "error not yet known" in entry["error_note"]
    assert entry["predicted_decode_ceiling_tok_s"] > 0
    assert entry["predicted_vram_gb"] > 0
    assert "servebench" in entry["measure_command"]


def test_oom_combo_reports_does_not_fit_and_memory_need(result, tmp_path):
    d = tmp_path / "results"
    _write_result(d, result)

    lookup = build_lookup(d)
    entry = lookup["entries"]["qwen2.5-32b|fp16|rtx3050"]
    assert entry["status"] == "oom"
    assert "does not fit in memory" in entry["label"].lower()
    assert entry["predicted_vram_gb"] > entry["gpu_vram_gb"]
    assert entry["oom_deficit_gb"] > 0
    assert entry["predicted_decode_ceiling_tok_s"] is None


def test_cpu_unmeasured_and_measured(result, tmp_path):
    d = tmp_path / "results"
    _write_result(d, result)

    lookup = build_lookup(d)
    cpu_entry = lookup["entries"]["qwen2.5-0.5b|q4_k_m|cpu-only"]
    assert cpu_entry["status"] == "unknown"
    assert cpu_entry["predicted_decode_ceiling_tok_s"] is None
    assert "servebench" in cpu_entry["measure_command"]

    cpu_run = copy.deepcopy(result)
    cpu_run["hardware"]["gpus"] = []
    cpu_run["model"]["on_gpu"] = "0%"
    _write_result(d, cpu_run)

    lookup2 = build_lookup(d)
    cpu_entry2 = lookup2["entries"]["qwen2.5-0.5b|q4_k_m|cpu-only"]
    assert cpu_entry2["status"] == "measured"
    assert cpu_entry2["label"] == "1 measurement"
    assert cpu_entry2["decode_median_tok_s"] == 200.0


def test_every_displayed_speed_has_explicit_label(result, tmp_path):
    d = tmp_path / "results"
    _write_result(d, result)
    out = tmp_path / "site"
    assert main(["build-site", "--results-dir", str(d), "--out", str(out)]) == 0

    index_html = (out / "index.html").read_text(encoding="utf-8")
    assert "will-it-run.html" in index_html

    will_html = (out / "will-it-run.html").read_text(encoding="utf-8")
    will_data = json.loads((out / "will-it-run.json").read_text(encoding="utf-8"))

    # Every speed entry in the build-time dataset must carry an explicit label.
    for key, entry in will_data["entries"].items():
        if entry["status"] == "measured":
            assert entry["decode_median_tok_s"] is not None, key
            assert entry["label"] == "1 measurement" or entry["label"].startswith("Measured ("), key
        elif entry["status"] == "predicted":
            assert entry["predicted_decode_ceiling_tok_s"] is not None, key
            assert entry["label"] == "Predicted, not measured", key
        else:
            assert entry["status"] in {"oom", "unknown"}, key
            assert entry.get("predicted_decode_ceiling_tok_s") is None, key

    # Rendered HTML table rows must pair every displayed speed with its explicit label.
    row_matches = re.findall(r"<tr data-row-status='([^']+)'>(.*?)</tr>", will_html, flags=re.S)
    assert len(row_matches) >= 1
    for status, row_html in row_matches:
        if status == "measured":
            assert ("1 measurement" in row_html) or ("Measured (" in row_html)
        elif status == "predicted":
            assert "Predicted, not measured" in row_html
        elif status == "oom":
            assert "Does not fit in memory" in row_html

    # Visible HTML prose/markup (outside style/script blocks) must not use banned hype words.
    visible_html = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>", "", will_html, flags=re.S | re.I
    ).lower()
    for banned in ("zero", "100%", "never fails", "flagship", "blazing", "empirical"):
        assert banned not in visible_html


def test_will_it_run_escapes_html(result, tmp_path):
    bad = copy.deepcopy(result)
    bad["model"]["name"] = "<script>alert(1)</script>"
    d = tmp_path / "results"
    _write_result(d, bad)
    out = tmp_path / "site"
    assert main(["build-site", "--results-dir", str(d), "--out", str(out)]) == 0

    will_html = (out / "will-it-run.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in will_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in will_html
