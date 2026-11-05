import json

from runsonmine.cli import main


def test_add_validate_and_build_site(result, tmp_path, capsys):
    src = tmp_path / "submitted.json"
    src.write_text(json.dumps(result), encoding="utf-8")
    results_dir = tmp_path / "data" / "results"
    assert main(["add", str(src), "--results-dir", str(results_dir)]) == 0
    assert main(["add", str(src), "--results-dir", str(results_dir)]) == 0  # idempotent
    assert len(list(results_dir.glob("*.json"))) == 1
    assert main(["validate", str(results_dir)]) == 0

    out = tmp_path / "site"
    assert main(["build-site", "--results-dir", str(results_dir), "--out", str(out)]) == 0
    page = (out / "index.html").read_text(encoding="utf-8")
    assert "qwen2.5:0.5b" in page and "NVIDIA GeForce RTX 3050 6GB Laptop GPU" in page
    assert "1 results so far" in page
    data = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert data[0]["model"]["name"] == "qwen2.5:0.5b" and data[0]["flags"] == []


def test_add_rejects_invalid(result, tmp_path):
    result["results"][0]["per_user_tok_s"] = 9999.0
    src = tmp_path / "bad.json"
    src.write_text(json.dumps(result), encoding="utf-8")
    assert main(["add", str(src), "--results-dir", str(tmp_path / "r")]) == 1


def test_site_escapes_html(result, tmp_path):
    result["model"]["name"] = "<script>alert(1)</script>"
    d = tmp_path / "results"
    d.mkdir()
    from runsonmine.validate import content_id

    (d / f"{content_id(result)}.json").write_text(json.dumps(result), encoding="utf-8")
    main(["build-site", "--results-dir", str(d), "--out", str(tmp_path / "site")])
    page = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert "<script>" not in page and "&lt;script&gt;" in page
