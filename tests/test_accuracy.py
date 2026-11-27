import copy
import json
import re

from runsonmine.accuracy import build_accuracy
from runsonmine.cli import main
from runsonmine.validate import content_id


def _write_result(results_dir, payload):
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{content_id(payload)}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_accuracy_per_row_median_and_early_warning(result, tmp_path):
    d = tmp_path / "results"
    _write_result(d, result)

    r2 = copy.deepcopy(result)
    r2["model"]["name"] = "qwen2.5:1.5b"
    r2["model"]["parameter_count"] = 1_540_000_000
    r2["model"]["parameters"] = "1.54B"
    r2["model"]["weights_gb"] = 1.0
    r2["results"][0]["per_user_tok_s"] = 95.0
    _write_result(d, r2)

    acc = build_accuracy(d)
    assert acc["n"] == 2
    assert acc["gpu_count"] == 1
    assert len(acc["rows"]) == 2
    assert acc["early_sample_warning"]
    assert "too early" in acc["early_sample_warning"].lower()

    for row in acc["rows"]:
        expected_err = round(row["predicted_tok_s"] - row["measured_tok_s"], 1)
        expected_abs = round(
            abs(row["predicted_tok_s"] - row["measured_tok_s"]) / row["measured_tok_s"] * 100.0,
            1,
        )
        assert row["error_tok_s"] == expected_err
        assert row["abs_error_pct"] == expected_abs

    abs_vals = sorted(r["abs_error_pct"] for r in acc["rows"])
    assert acc["median_abs_error_pct"] == round(sum(abs_vals) / 2.0, 1)


def test_accuracy_empty_and_unmodeled_rows(result, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    empty_acc = build_accuracy(empty_dir)
    assert empty_acc["n"] == 0
    assert empty_acc["median_abs_error_pct"] is None
    assert "not yet known" in empty_acc["summary_label"].lower()

    d = tmp_path / "mixed"
    _write_result(d, result)
    cpu_run = copy.deepcopy(result)
    cpu_run["hardware"]["gpus"] = []
    cpu_run["model"]["on_gpu"] = "0%"
    _write_result(d, cpu_run)

    mixed = build_accuracy(d)
    assert mixed["n"] == 1
    assert mixed["skipped_count"] == 1


def test_build_site_renders_accuracy_page_chart_and_links(result, tmp_path):
    d = tmp_path / "results"
    _write_result(d, result)
    out = tmp_path / "site"
    assert main(["build-site", "--results-dir", str(d), "--out", str(out)]) == 0

    index_html = (out / "index.html").read_text(encoding="utf-8")
    will_html = (out / "will-it-run.html").read_text(encoding="utf-8")
    acc_html = (out / "accuracy.html").read_text(encoding="utf-8")
    acc_json = json.loads((out / "accuracy.json").read_text(encoding="utf-8"))
    will_json = json.loads((out / "will-it-run.json").read_text(encoding="utf-8"))

    assert "accuracy.html" in index_html
    assert "accuracy.html" in will_html
    assert "<svg" in acc_html and "qwen2.5:0.5b" in acc_html
    assert "too early" in acc_html.lower()
    assert acc_json["n"] == 1

    # With >= 1 measured result, M3 predictions must cite the M4 measured error note.
    pred_entry = will_json["entries"]["qwen2.5-0.5b|q4_k_m|rtx4090"]
    assert "median abs error" in pred_entry["error_note"].lower()
    assert pred_entry["accuracy_url"] == "accuracy.html"

    # Visible HTML prose must avoid banned hype words.
    no_blocks = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", acc_html, flags=re.S | re.I)
    visible_text = re.sub(r"<[^>]+>", " ", no_blocks).lower()
    for banned in ("zero", "100%", "never fails", "flagship", "blazing", "empirical"):
        assert banned not in visible_text


def test_accuracy_escapes_html(result, tmp_path):
    bad = copy.deepcopy(result)
    bad["engine"]["name"] = "<script>alert(1)</script>"
    d = tmp_path / "results"
    _write_result(d, bad)
    out = tmp_path / "site"
    assert main(["build-site", "--results-dir", str(d), "--out", str(out)]) == 0

    acc_html = (out / "accuracy.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in acc_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in acc_html
