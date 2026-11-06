import json

from runsonmine.gpus import peak_bandwidth
from runsonmine.validate import check, check_file, content_id


def test_valid_result_passes(result):
    v = check(result)
    assert v.ok, v.errors
    assert v.flags == []
    assert v.ceiling_tok_s == round(168 / 0.398, 1)


def test_unknown_fields_are_rejected(result):
    result["hardware"]["hostname"] = "my-laptop"  # private data must never get in
    v = check(result)
    assert not v.ok and any("hostname" in e for e in v.errors)


def test_non_standard_test_is_rejected(result):
    result["test"]["output_tokens"] = 64
    assert not check(result).ok


def test_faster_than_physics_is_rejected(result):
    result["results"][0]["per_user_tok_s"] = 600.0  # ceiling 168 GB/s / 0.398 GB = 422
    v = check(result)
    assert not v.ok and "physical ceiling" in v.errors[0]


def test_wrong_model_size_is_caught_by_the_ceiling(result):
    result["model"]["weights_gb"] = 4.0  # claims an 8B-size model at 200 tok/s on a 3050
    assert not check(result).ok


def test_flags(result):
    result["conditions"]["power_source"] = "battery"
    result["conditions"]["gpu_clock_avg_mhz"] = 210.0  # busy but at idle clocks
    result["model"]["on_gpu"] = "73%"
    result["results"][2]["failed"] = 2
    assert check(result).flags == ["battery", "throttled", "partial-offload", "failed-requests"]


def test_low_clock_with_low_utilisation_is_not_throttling(result):
    # a CPU-bound engine leaves the GPU idle; the clock drops, but nothing is throttled
    result["conditions"].update(gpu_clock_avg_mhz=810.0, gpu_util_avg_pct=32.0)
    assert "throttled" not in check(result).flags


def test_unknown_gpu_and_size_skip_the_ceiling(result):
    result["hardware"]["gpus"] = [{"name": "Mystery Accelerator 9000"}]
    del result["model"]["weights_gb"]
    v = check(result)
    assert v.ok and v.ceiling_tok_s is None
    assert v.flags == ["unknown-gpu", "size-unknown"]


def test_gpu_table_longest_match():
    assert peak_bandwidth("NVIDIA GeForce RTX 3050 6GB Laptop GPU") == 168.0
    assert peak_bandwidth("NVIDIA GeForce RTX 3050 Laptop GPU") == 192.0
    assert peak_bandwidth("NVIDIA L40S") == 864.0  # not the L4's 300
    assert peak_bandwidth("Tesla T4") == 320.0
    assert peak_bandwidth("Apple M3 Max GPU (unified memory)") == 400.0
    assert peak_bandwidth(None) is None


def test_file_name_must_be_the_content_hash(result, tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    good = d / f"{content_id(result)}.json"
    good.write_text(json.dumps(result), encoding="utf-8")
    assert check_file(good).ok
    bad = d / "anything.json"
    bad.write_text(json.dumps(result), encoding="utf-8")
    assert not check_file(bad).ok


def test_content_id_ignores_key_order(result):
    shuffled = dict(reversed(list(result.items())))
    assert content_id(shuffled) == content_id(result)


def test_power_limited_datacentre_gpu_is_not_throttled(result):
    # Tesla T4 under full load: 97% busy at its 70 W limit, clock 654 of 1590 MHz (normal)
    result["hardware"]["gpus"] = [{"name": "Tesla T4", "vram_gb": 15.0}]
    result["conditions"].update(
        gpu_clock_avg_mhz=653.7,
        gpu_clock_max_mhz=1590.0,
        gpu_power_avg_w=66.9,
        gpu_power_limit_w=70.0,
        gpu_util_avg_pct=97.1,
    )
    assert "throttled" not in check(result).flags


def test_capped_laptop_gpu_is_throttled_even_at_its_power_limit(result):
    # laptop GPU left at a 10 W cap after battery: 210 of 2100 MHz, at the (lowered) limit
    result["conditions"].update(
        gpu_clock_avg_mhz=210.0,
        gpu_clock_max_mhz=2100.0,
        gpu_power_avg_w=10.4,
        gpu_power_limit_w=10.0,
        gpu_util_avg_pct=95.0,
    )
    assert "throttled" in check(result).flags


def test_serving_gpu_selects_the_ceiling_gpu(result):
    result["hardware"]["gpus"] = [
        {"name": "Tesla T4"},
        {"name": "NVIDIA GeForce RTX 3050 6GB Laptop GPU"},
    ]
    result["hardware"]["serving_gpu"] = 1
    assert check(result).ceiling_tok_s == round(168 / 0.398, 1)
    result["hardware"]["serving_gpu"] = 5
    assert not check(result).ok
