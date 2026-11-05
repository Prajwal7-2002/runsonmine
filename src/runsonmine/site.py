"""Build the static site from data/results/*.json (no JavaScript, no external requests)."""

from __future__ import annotations

import html
import json
import shutil
from collections import defaultdict
from pathlib import Path

from .validate import check

CSS = """
:root { --bg:#fbfbfa; --fg:#1c1c1a; --muted:#6b6b66; --line:#e3e2de; --accent:#2f6f4f;
        --flag:#9a5b00; --card:#ffffff; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#141414; --fg:#ececea; --muted:#a3a39e; --line:#2c2c2a; --accent:#7cc39c;
          --flag:#e0a24a; --card:#1b1b1a; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
main { max-width:1080px; margin:0 auto; padding:32px 16px 64px; }
h1 { font-size:28px; margin:0 0 4px; } h2 { font-size:19px; margin:36px 0 8px; }
p.lead { color:var(--muted); margin:0 0 20px; max-width:720px; }
.wrap { overflow-x:auto; border:1px solid var(--line); border-radius:8px; background:var(--card); }
table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }
th,td { padding:8px 10px; border-bottom:1px solid var(--line); text-align:left;
        white-space:nowrap; }
th { font-weight:600; font-size:13px; color:var(--muted); }
td.num, th.num { text-align:right; }
tr:last-child td { border-bottom:0; }
.flag { color:var(--flag); font-size:12px; }
.sub { color:var(--muted); font-size:12px; }
a { color:var(--accent); }
nav a { margin-right:12px; }
footer { margin-top:40px; color:var(--muted); font-size:13px; }
code { font-size:13px; }
"""


def load_results(results_dir: Path) -> list[tuple[str, dict, list[str], float | None]]:
    """(id, result, flags, ceiling) for every valid result file."""
    rows = []
    for path in sorted(results_dir.glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        v = check(result)
        if v.ok:
            rows.append((path.stem, result, v.flags, v.ceiling_tok_s))
    return rows


def _gpu(result: dict) -> str:
    gpus = result["hardware"]["gpus"]
    return gpus[0]["name"] if gpus else "CPU only"


def _fmt(x: float | None, digits: int = 1) -> str:
    return "" if x is None else f"{x:,.{digits}f}"


def _row(rid: str, r: dict, flags: list[str], ceiling: float | None) -> str:
    by_users = {lv["users"]: lv for lv in r["results"]}
    one, four = by_users[1], by_users[4]
    m, e = r["model"], r["engine"]
    engine = " ".join(x for x in (e.get("name"), e.get("version")) if x)
    flag_txt = f'<div class="flag">{html.escape(", ".join(flags))}</div>' if flags else ""
    return (
        "<tr>"
        f"<td>{html.escape(m['name'])}<div class='sub'>{html.escape(m.get('parameters', ''))} "
        f"{html.escape(m.get('quantization', ''))}</div>{flag_txt}</td>"
        f"<td>{html.escape(engine)}</td>"
        f"<td class='num'>{_fmt(one['per_user_tok_s'])}</td>"
        f"<td class='num'>{_fmt(one['ttft_ms_p50'], 0)}</td>"
        f"<td class='num'>{_fmt(four['output_tok_s'])}</td>"
        f"<td class='num'>{_fmt(four['per_user_tok_s'])}</td>"
        f"<td class='num'>{_fmt(ceiling, 0)}</td>"
        f"<td>{html.escape(r['date'])}</td>"
        f"<td><a href='results/{rid}.json'>data</a></td>"
        "</tr>"
    )


def build(results_dir: Path, out_dir: Path) -> int:
    """Write index.html, results.json and the raw files to out_dir. Returns result count."""
    rows = load_results(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results").mkdir(exist_ok=True)
    for rid, *_ in rows:
        shutil.copyfile(results_dir / f"{rid}.json", out_dir / "results" / f"{rid}.json")
    all_results = [{"id": rid, "flags": flags, **r} for rid, r, flags, _ in rows]
    (out_dir / "results.json").write_text(json.dumps(all_results, indent=1), encoding="utf-8")

    by_gpu: dict[str, list] = defaultdict(list)
    for row in rows:
        by_gpu[_gpu(row[1])].append(row)

    sections = []
    for gpu in sorted(by_gpu):
        items = sorted(
            by_gpu[gpu], key=lambda x: (bool(x[2]), -(x[1]["results"][0]["per_user_tok_s"] or 0))
        )
        body = "".join(_row(*item) for item in items)
        anchor = html.escape(gpu.lower().replace(" ", "-"))
        sections.append(
            f"<h2 id='{anchor}'>{html.escape(gpu)}</h2><div class='wrap'><table><thead><tr>"
            "<th>Model</th><th>Engine</th><th class='num'>1 user tok/s</th>"
            "<th class='num'>1 user TTFT ms</th><th class='num'>4 users total tok/s</th>"
            "<th class='num'>4 users each tok/s</th><th class='num'>Ceiling tok/s</th>"
            f"<th>Date</th><th></th></tr></thead><tbody>{body}</tbody></table></div>"
        )
    nav = " ".join(
        f"<a href='#{html.escape(g.lower().replace(' ', '-'))}'>{html.escape(g)}</a>"
        for g in sorted(by_gpu)
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RunsOnMine</title>
<meta name="description" content="Measured local LLM speeds on real machines: which models run
well on your GPU, laptop or Mac.">
<style>{CSS}</style></head>
<body><main>
<h1>RunsOnMine</h1>
<p class="lead">How fast local AI models really run on real computers. Every number here was
measured on someone's machine with <a href="https://github.com/Prajwal7-2002/servebench">servebench</a>,
not estimated. {len(rows)} results so far.</p>
<nav>{nav}</nav>
{"".join(sections) or "<p>No results yet.</p>"}
<footer>
<p><b>Columns.</b> <i>1 user tok/s</i>: generation speed one person sees. <i>TTFT</i>: time to the
first word. <i>4 users total</i>: everything the machine generates for 4 people at once.
<i>Ceiling</i>: the most the GPU's memory bandwidth allows for this model's size; real engines
reach 40-90% of it. Flags such as <i>battery</i> or <i>throttled</i> mean the run is probably slower
than the machine can do.</p>
<p>Add your machine: <code>pip install servebench</code>, start your model in Ollama, llama.cpp or
LM Studio, then <code>servebench submit</code> and open a pull request with the file on
<a href="https://github.com/Prajwal7-2002/runsonmine">GitHub</a>.
Data: <a href="results.json">results.json</a> (CC BY 4.0).</p>
</footer>
</main></body></html>
"""
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    return len(rows)
