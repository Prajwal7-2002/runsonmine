"""Build the static site from data/results/*.json (no JavaScript, no external requests)."""

from __future__ import annotations

import html
import json
import shutil
from collections import defaultdict
from pathlib import Path

from .accuracy import build_accuracy
from .validate import check
from .will_it_run import build_lookup

CSS = """
:root { --bg:#fbfbfa; --fg:#1c1c1a; --muted:#6b6b66; --line:#e3e2de; --accent:#2f6f4f;
        --flag:#9a5b00; --warn:#a13525; --card:#ffffff; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#141414; --fg:#ececea; --muted:#a3a39e; --line:#2c2c2a; --accent:#7cc39c;
          --flag:#e0a24a; --warn:#f08474; --card:#1b1b1a; } }
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
.top-nav { display:flex; gap:16px; margin-bottom:20px; padding-bottom:12px;
           border-bottom:1px solid var(--line); flex-wrap:wrap; }
.top-nav a { font-weight:600; text-decoration:none; }
.controls { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr));
            gap:12px; margin:20px 0; }
@media (max-width:720px) { .controls { grid-template-columns:1fr; } }
.field { display:flex; flex-direction:column; gap:6px; }
.field label { font-size:13px; font-weight:600; color:var(--muted); }
.field select { padding:9px 10px; border:1px solid var(--line); border-radius:6px;
                background:var(--card); color:var(--fg); font:inherit; width:100%; }
.result-card { border:1px solid var(--line); border-radius:8px; background:var(--card);
               padding:20px; }
.pill { display:inline-block; padding:2px 9px; border-radius:999px; font-size:12px;
        font-weight:600; border:1px solid var(--line); }
.pill-measured { color:var(--accent); border-color:var(--accent); }
.pill-predicted { color:var(--flag); border-color:var(--flag); }
.pill-oom { color:var(--warn); border-color:var(--warn); }
.metrics { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));
           gap:14px; margin:16px 0; }
.metric-k { font-size:12px; color:var(--muted); }
.metric-v { font-size:22px; font-weight:700; font-variant-numeric:tabular-nums; }
.cmd-row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:12px; }
.cmd-row code { padding:6px 10px; background:var(--bg); border:1px solid var(--line);
                border-radius:6px; }
.btn { padding:6px 12px; border:1px solid var(--line); border-radius:6px; background:var(--bg);
       color:var(--fg); font:inherit; font-size:13px; cursor:pointer; }
.btn:active { transform:scale(0.98); }
.notice { border:1px solid var(--flag); border-radius:8px; padding:12px 16px;
          background:var(--card); margin:16px 0 20px; }
.chart-wrap { border:1px solid var(--line); border-radius:8px; background:var(--card);
              padding:16px; margin:16px 0 24px; overflow-x:auto; }
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


def _render_entry_card_html(entry: dict) -> str:
    status = entry["status"]
    pill_cls = {
        "measured": "pill-measured",
        "predicted": "pill-predicted",
        "oom": "pill-oom",
    }.get(status, "")
    title = (
        f"{html.escape(entry['model_label'])} ({html.escape(entry['quant'].upper())}) "
        f"on {html.escape(entry['hardware_label'])}"
    )
    pill = f"<span class='pill {pill_cls}'>{html.escape(entry['label'])}</span>"

    if status == "measured":
        prefill = (
            f"{entry['prefill_median_tok_s']:,.1f} tok/s"
            if entry["prefill_median_tok_s"] is not None
            else "n/a"
        )
        d_range = f"{entry['decode_min_tok_s']:,.1f}..{entry['decode_max_tok_s']:,.1f} tok/s"
        p_range = (
            f"{entry['prefill_min_tok_s']:,.1f}..{entry['prefill_max_tok_s']:,.1f} tok/s"
            if entry["prefill_min_tok_s"] is not None
            else "n/a"
        )
        flags_txt = ", ".join(entry["flags"]) if entry["flags"] else "none"
        body = (
            "<div class='metrics'>"
            "<div><div class='metric-k'>Median decode (1 user)</div>"
            f"<div class='metric-v'>{entry['decode_median_tok_s']:,.1f} tok/s</div>"
            f"<div class='sub'>Range: {html.escape(d_range)}</div></div>"
            "<div><div class='metric-k'>Median prefill (effective)</div>"
            f"<div class='metric-v'>{html.escape(prefill)}</div>"
            f"<div class='sub'>Range: {html.escape(p_range)} · "
            f"TTFT p50 {entry['ttft_median_ms']:,.1f} ms</div></div>"
            "<div><div class='metric-k'>Sample count</div>"
            f"<div class='metric-v'>{html.escape(entry['label'])}</div></div>"
            "</div>"
            f"<p class='sub'>Engine: {html.escape(', '.join(entry['engines']))} · "
            f"Dates: {html.escape(', '.join(entry['dates']))} · "
            f"Flags: {html.escape(flags_txt)}</p>"
        )
    elif status == "predicted":
        err = html.escape(entry["error_note"])
        body = (
            "<div class='metrics'>"
            "<div><div class='metric-k'>Predicted decode ceiling</div>"
            f"<div class='metric-v'>{entry['predicted_decode_ceiling_tok_s']:,.1f} tok/s</div>"
            "<div class='sub'>Predicted, not measured "
            f"(<a href='{html.escape(entry.get('accuracy_url') or 'accuracy.html')}'>{err}</a>)"
            "</div></div>"
            "<div><div class='metric-k'>Predicted memory need (2K ctx)</div>"
            f"<div class='metric-v'>{entry['predicted_vram_gb']:,.2f} GB</div>"
            f"<div class='sub'>Device memory: {entry['gpu_vram_gb']:,.1f} GB</div></div>"
            "</div>"
            "<p class='sub'>Want real hardware numbers instead of a spec ceiling? "
            f"<a href='{html.escape(entry['contribute_url'])}'>Measure it yourself</a>:</p>"
            f"<div class='cmd-row'><code>{html.escape(entry['measure_command'])}</code></div>"
        )
    elif status == "oom":
        body = (
            "<div class='metrics'>"
            "<div><div class='metric-k'>Memory check</div>"
            "<div class='metric-v'>Does not fit</div>"
            f"<div class='sub'>Short by {entry['oom_deficit_gb']:,.2f} GB on "
            f"{entry['gpu_vram_gb']:,.1f} GB VRAM</div></div>"
            "<div><div class='metric-k'>Predicted memory need (2K ctx)</div>"
            f"<div class='metric-v'>{entry['predicted_vram_gb']:,.2f} GB</div>"
            f"<div class='sub'>{html.escape(entry['error_note'])}</div></div>"
            "</div>"
            "<p class='sub'>Try a smaller quantisation (such as Q4_K_M) or a smaller model.</p>"
        )
    else:
        body = (
            f"<p>No measurements for this combination yet ({html.escape(entry['error_note'])}).</p>"
            f"<p class='sub'><a href='{html.escape(entry['contribute_url'])}'>"
            "Measure it yourself</a>:</p>"
            f"<div class='cmd-row'><code>{html.escape(entry['measure_command'])}</code></div>"
        )

    return f"<h2>{title}</h2><p>{pill}</p>{body}"


def _summary_row_html(entry: dict) -> str:
    status = entry["status"]
    if status == "measured":
        speed = f"{entry['decode_median_tok_s']:,.1f} tok/s ({html.escape(entry['label'])})"
        extra = html.escape(", ".join(entry["engines"]) or "-")
    elif status == "predicted":
        speed = (
            f"{entry['predicted_decode_ceiling_tok_s']:,.1f} tok/s ceiling "
            f"({html.escape(entry['label'])}; {html.escape(entry['error_note'])})"
        )
        extra = f"{entry['predicted_vram_gb']:,.2f} GB predicted VRAM"
    elif status == "oom":
        speed = html.escape(entry["label"])
        extra = (
            f"Needs {entry['predicted_vram_gb']:,.2f} GB (short {entry['oom_deficit_gb']:,.2f} GB)"
        )
    else:
        speed = html.escape(entry["label"])
        extra = html.escape(entry["error_note"] or "")
    return (
        f"<tr data-row-status='{html.escape(status)}'>"
        f"<td>{html.escape(entry['model_label'])} "
        f"<span class='sub'>{html.escape(entry['quant'].upper())}</span></td>"
        f"<td>{html.escape(entry['hardware_label'])}</td>"
        f"<td>{speed}</td>"
        f"<td>{extra}</td>"
        "</tr>"
    )


def _will_it_run_html(lookup: dict) -> str:
    entries = list(lookup["entries"].values())
    default_entry = next(
        (e for e in entries if e["status"] == "measured"),
        entries[0] if entries else None,
    )
    model_opts = "".join(
        f"<option value='{html.escape(m['id'])}'"
        f"{' selected' if default_entry and m['id'] == default_entry['model'] else ''}>"
        f"{html.escape(m['label'])}</option>"
        for m in lookup["models"]
    )
    quant_opts = "".join(
        f"<option value='{html.escape(q['id'])}'"
        f"{' selected' if default_entry and q['id'] == default_entry['quant'] else ''}>"
        f"{html.escape(q['label'])}</option>"
        for q in lookup["quants"]
    )
    hw_opts = "".join(
        f"<option value='{html.escape(h['id'])}'"
        f"{' selected' if default_entry and h['id'] == default_entry['hardware'] else ''}>"
        f"{html.escape(h['label'])}</option>"
        for h in lookup["hardware"]
    )
    initial_card = _render_entry_card_html(default_entry) if default_entry else "<p>No entries.</p>"

    measured_rows = [e for e in entries if e["status"] == "measured"]
    sample_pred = [e for e in entries if e["status"] == "predicted"][:6]
    sample_oom = [e for e in entries if e["status"] == "oom"][:4]
    table_rows = "".join(_summary_row_html(e) for e in (measured_rows + sample_pred + sample_oom))

    safe_json = (
        json.dumps(lookup).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    )
    contribute_href = "https://github.com/Prajwal7-2002/runsonmine/blob/main/docs/contribute.md"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Will it run? · RunsOnMine</title>
<meta name="description"
  content="Measured local LLM speeds or predicted infersize memory and speed bounds.">
<style>{CSS}</style></head>
<body><main>
<div class="top-nav">
  <a href="index.html">Measured results</a>
  <a href="will-it-run.html">Will it run?</a>
  <a href="accuracy.html">Prediction accuracy</a>
  <a href="{contribute_href}">Measure it yourself</a>
</div>
<h1>Will it run?</h1>
<p class="lead">Pick a model, quantisation, and hardware profile. Shows measured RunsOnMine
data when available, and otherwise shows an
<a href="https://github.com/Prajwal7-2002/infersize">infersize</a> ceiling labelled
<b>Predicted, not measured</b>.</p>
<div class="controls">
  <div class="field"><label for="sel-model">Model</label>
    <select id="sel-model">{model_opts}</select></div>
  <div class="field"><label for="sel-quant">Quantisation</label>
    <select id="sel-quant">{quant_opts}</select></div>
  <div class="field"><label for="sel-hw">GPU, CPU or Mac</label>
    <select id="sel-hw">{hw_opts}</select></div>
</div>
<section class="result-card" id="result-card" aria-live="polite">{initial_card}</section>
<details style="margin-top:28px;">
  <summary style="cursor:pointer;color:var(--muted);">
    Measured results &amp; sample build-time predictions ({len(measured_rows)} measured)
  </summary>
  <div class="wrap" style="margin-top:12px;"><table><thead><tr>
    <th>Model</th><th>Hardware</th><th>Speed &amp; label</th><th>Details</th>
  </tr></thead><tbody>{table_rows}</tbody></table></div>
</details>
<footer>
  <p>Every value on this page is computed at build time from <a href="results.json">results.json</a>
  or <code>infersize</code> (predictions use context = {lookup["context_tokens"]} tokens,
  batch = 1).</p>
</footer>
<script id="lookup-data" type="application/json">{safe_json}</script>
<script>
(function() {{
  const data = JSON.parse(document.getElementById("lookup-data").textContent);
  const selM = document.getElementById("sel-model");
  const selQ = document.getElementById("sel-quant");
  const selH = document.getElementById("sel-hw");
  const card = document.getElementById("result-card");
  function esc(s) {{
    return String(s)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;")
      .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }}
  function fmt(x, d) {{
    if (x == null) return "n/a";
    return Number(x).toLocaleString(
      undefined, {{minimumFractionDigits:d, maximumFractionDigits:d}}
    );
  }}
  function pillFor(status) {{
    if (status === "measured") return "pill-measured";
    if (status === "predicted") return "pill-predicted";
    if (status === "oom") return "pill-oom";
    return "";
  }}
  function render() {{
    const key = selM.value + "|" + selQ.value + "|" + selH.value;
    const e = data.entries[key];
    if (!e) {{ card.innerHTML = "<p>No entry found.</p>"; return; }}
    const url = new URL(window.location);
    url.searchParams.set("model", selM.value);
    url.searchParams.set("quant", selQ.value);
    url.searchParams.set("hw", selH.value);
    window.history.replaceState(null, "", url);
    const pillCls = pillFor(e.status);
    let body = "";
    if (e.status === "measured") {{
      const dRange = fmt(e.decode_min_tok_s,1) + ".." + fmt(e.decode_max_tok_s,1) + " tok/s";
      const pRange = e.prefill_min_tok_s != null
        ? fmt(e.prefill_min_tok_s,1) + ".." + fmt(e.prefill_max_tok_s,1) + " tok/s"
        : "n/a";
      const prefill = e.prefill_median_tok_s != null
        ? fmt(e.prefill_median_tok_s,1) + " tok/s" : "n/a";
      const flagsTxt = e.flags.length ? e.flags.join(", ") : "none";
      body = `<div class="metrics">
        <div><div class="metric-k">Median decode (1 user)</div>
        <div class="metric-v">${{fmt(e.decode_median_tok_s,1)}} tok/s</div>
        <div class="sub">Range: ${{esc(dRange)}}</div></div>
        <div><div class="metric-k">Median prefill (effective)</div>
        <div class="metric-v">${{esc(prefill)}}</div>
        <div class="sub">Range: ${{esc(pRange)}} · TTFT p50 ${{fmt(e.ttft_median_ms,1)}} ms</div>
        </div>
        <div><div class="metric-k">Sample count</div>
        <div class="metric-v">${{esc(e.label)}}</div></div>
      </div>
      <p class="sub">Engine: ${{esc(e.engines.join(", "))}} · Dates: ${{esc(e.dates.join(", "))}}
      · Flags: ${{esc(flagsTxt)}}</p>`;
    }} else if (e.status === "predicted") {{
      const cUrl = esc(e.contribute_url);
      const cmd = esc(e.measure_command);
      body = `<div class="metrics">
        <div><div class="metric-k">Predicted decode ceiling</div>
        <div class="metric-v">${{fmt(e.predicted_decode_ceiling_tok_s,1)}} tok/s</div>
        <div class="sub">Predicted, not measured
        (<a href="${{esc(e.accuracy_url || "accuracy.html")}}">${{esc(e.error_note)}}</a>)
        </div></div>
        <div><div class="metric-k">Predicted memory need (2K ctx)</div>
        <div class="metric-v">${{fmt(e.predicted_vram_gb,2)}} GB</div>
        <div class="sub">Device memory: ${{fmt(e.gpu_vram_gb,1)}} GB</div></div>
      </div>
      <p class="sub">Want real hardware numbers? <a href="${{cUrl}}">Measure it yourself</a>:</p>
      <div class="cmd-row"><code>${{cmd}}</code>
      <button class="btn" type="button" data-copy="${{cmd}}">Copy</button></div>`;
    }} else if (e.status === "oom") {{
      body = `<div class="metrics">
        <div><div class="metric-k">Memory check</div>
        <div class="metric-v">Does not fit</div>
        <div class="sub">Short by ${{fmt(e.oom_deficit_gb,2)}} GB on
        ${{fmt(e.gpu_vram_gb,1)}} GB VRAM</div></div>
        <div><div class="metric-k">Predicted memory need (2K ctx)</div>
        <div class="metric-v">${{fmt(e.predicted_vram_gb,2)}} GB</div>
        <div class="sub">${{esc(e.error_note)}}</div></div>
      </div>
      <p class="sub">Try a smaller quantisation (such as Q4_K_M) or a smaller model.</p>`;
    }} else {{
      const cUrl = esc(e.contribute_url);
      const cmd = esc(e.measure_command);
      body = `<p>No measurements for this combination yet (${{esc(e.error_note)}}).</p>
      <p class="sub"><a href="${{cUrl}}">Measure it yourself</a>:</p>
      <div class="cmd-row"><code>${{cmd}}</code>
      <button class="btn" type="button" data-copy="${{cmd}}">Copy</button></div>`;
    }}
    const heading = `${{esc(e.model_label)}} (${{esc(e.quant.toUpperCase())}}) `
      + `on ${{esc(e.hardware_label)}}`;
    card.innerHTML = `<h2>${{heading}}</h2>`
      + `<p><span class="pill ${{pillCls}}">${{esc(e.label)}}</span></p>${{body}}`;
    const copyBtn = card.querySelector("[data-copy]");
    if (copyBtn && navigator.clipboard) {{
      copyBtn.addEventListener("click", function() {{
        const val = copyBtn.getAttribute("data-copy");
        navigator.clipboard.writeText(val).then(function() {{ copyBtn.textContent = "Copied"; }});
      }});
    }}
  }}
  const p = new URLSearchParams(window.location.search);
  const pick = (sel, key) => {{
    if (p.get(key) && [...sel.options].some(o => o.value === p.get(key))) sel.value = p.get(key);
  }};
  pick(selM, "model");
  pick(selQ, "quant");
  pick(selH, "hw");
  selM.addEventListener("change", render);
  selQ.addEventListener("change", render);
  selH.addEventListener("change", render);
  render();
}})();
</script>
</main></body></html>
"""


def _accuracy_chart_svg(rows: list[dict]) -> str:
    if not rows:
        return "<p class='sub'>No rows available to plot yet.</p>"
    max_val = max(max(r["measured_tok_s"], r["predicted_tok_s"]) for r in rows) or 1.0
    label_w = 240
    bar_max = 360
    row_h = 34
    top_pad = 28
    width = 760
    height = top_pad + len(rows) * row_h + 16
    bars: list[str] = [
        f"<text x='{label_w}' y='16' font-size='12' fill='var(--accent)' font-weight='600'>"
        "Measured tok/s</text>",
        f"<text x='{label_w + 130}' y='16' font-size='12' fill='var(--flag)' font-weight='600'>"
        "Predicted ceiling tok/s</text>",
    ]
    for i, r in enumerate(rows):
        y = top_pad + i * row_h
        mw = max(2.0, (r["measured_tok_s"] / max_val) * bar_max)
        pw = max(2.0, (r["predicted_tok_s"] / max_val) * bar_max)
        short_hw = r["hardware"].replace("NVIDIA GeForce ", "").replace("NVIDIA ", "")
        raw_lbl = f"{r['model']} ({short_hw})"
        if len(raw_lbl) > 34:
            raw_lbl = raw_lbl[:31] + "..."
        lbl = html.escape(raw_lbl)
        diff = (
            f"{r['measured_tok_s']:.1f} vs {r['predicted_tok_s']:.1f} "
            f"({r['signed_error_pct']:+.1f}%)"
        )
        bars.append(
            f"<text x='0' y='{y + 16}' font-size='12' fill='currentColor'>{lbl}</text>"
            f"<rect x='{label_w}' y='{y + 3}' width='{mw:.1f}' height='10' "
            "rx='2' fill='var(--accent)'/>"
            f"<rect x='{label_w}' y='{y + 16}' width='{pw:.1f}' height='10' "
            "rx='2' fill='var(--flag)' opacity='0.78'/>"
            f"<text x='{label_w + bar_max + 12}' y='{y + 17}' font-size='11' "
            f"fill='var(--muted)'>{html.escape(diff)}</text>"
        )
    return (
        f"<svg viewBox='0 0 {width} {height}' width='100%' role='img' "
        f"aria-label='Measured vs predicted decode speeds'>" + "".join(bars) + "</svg>"
    )


def _accuracy_html(acc: dict) -> str:
    contribute_href = "https://github.com/Prajwal7-2002/runsonmine/blob/main/docs/contribute.md"
    med = (
        f"{acc['median_abs_error_pct']:.1f}%" if acc["median_abs_error_pct"] is not None else "n/a"
    )
    err_range = (
        f"{acc['min_abs_error_pct']:.1f}%..{acc['max_abs_error_pct']:.1f}%"
        if acc["min_abs_error_pct"] is not None
        else "n/a"
    )
    warn_html = (
        "<div class='notice'><b>Small sample note:</b> "
        f"{html.escape(acc['early_sample_warning'])}</div>"
        if acc["early_sample_warning"]
        else ""
    )
    table_rows = "".join(
        "<tr>"
        f"<td>{html.escape(r['model'])} "
        f"<span class='sub'>{html.escape(r['quant'].upper())}</span></td>"
        f"<td>{html.escape(r['hardware'])}</td>"
        f"<td>{html.escape(r['engine'])}</td>"
        f"<td class='num'>{r['measured_tok_s']:,.1f}</td>"
        f"<td class='num'>{r['predicted_tok_s']:,.1f}</td>"
        f"<td class='num'>{r['error_tok_s']:+,.1f}</td>"
        f"<td class='num'>{r['signed_error_pct']:+.1f}%</td>"
        f"<td class='num'>{r['abs_error_pct']:.1f}%</td>"
        f"<td>{html.escape(', '.join(r['flags']) or 'none')}</td>"
        f"<td>{html.escape(r['date'])}</td>"
        f"<td><a href='results/{html.escape(r['id'])}.json'>data</a></td>"
        "</tr>"
        for r in acc["rows"]
    )
    body_table = (
        "<div class='wrap'><table><thead><tr>"
        "<th>Model</th><th>Hardware</th><th>Engine</th>"
        "<th class='num'>Measured tok/s</th><th class='num'>Predicted tok/s</th>"
        "<th class='num'>Diff tok/s</th><th class='num'>Signed err</th>"
        "<th class='num'>Abs err</th><th>Flags</th><th>Date</th><th></th>"
        f"</tr></thead><tbody>{table_rows}</tbody></table></div>"
        if acc["rows"]
        else "<p>No matching rows yet.</p>"
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prediction accuracy · RunsOnMine</title>
<meta name="description"
  content="Predicted infersize speed bounds compared against measured RunsOnMine hardware runs.">
<style>{CSS}</style></head>
<body><main>
<div class="top-nav">
  <a href="index.html">Measured results</a>
  <a href="will-it-run.html">Will it run?</a>
  <a href="accuracy.html">Prediction accuracy</a>
  <a href="{contribute_href}">Measure it yourself</a>
</div>
<h1>How accurate are the predictions?</h1>
<p class="lead">Every measured single-user decode run in RunsOnMine compared against
<a href="https://github.com/Prajwal7-2002/infersize">infersize</a>'s default ceiling prediction
(no added per-token overhead). Lower absolute percentage error is closer to real silicon.</p>
<div class="metrics">
  <div><div class="metric-k">Median abs error</div><div class="metric-v">{med}</div></div>
  <div><div class="metric-k">Abs error range</div><div class="metric-v">{err_range}</div></div>
  <div><div class="metric-k">Rows compared (n)</div><div class="metric-v">{acc["n"]}</div></div>
  <div><div class="metric-k">GPUs covered</div><div class="metric-v">{acc["gpu_count"]}</div></div>
</div>
{warn_html}
<div class="chart-wrap">{_accuracy_chart_svg(acc["rows"])}</div>
<h2>Per-row comparison</h2>
{body_table}
<footer>
  <p>Why predictions sit above measured speeds: <code>infersize</code> defaults to
  <code>decode_overhead_ms = 0</code> and 80% memory-bus efficiency, which ignores per-token
  runtime dispatch overhead that dominates small models (e.g. 0.5B).</p>
</footer>
</main></body></html>
"""


def build(results_dir: Path, out_dir: Path) -> int:
    """Write index.html, will-it-run.html, accuracy.html, JSON data files, and raw results."""
    rows = load_results(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results").mkdir(exist_ok=True)
    for rid, *_ in rows:
        shutil.copyfile(results_dir / f"{rid}.json", out_dir / "results" / f"{rid}.json")
    all_results = [{"id": rid, "flags": flags, **r} for rid, r, flags, _ in rows]
    (out_dir / "results.json").write_text(json.dumps(all_results, indent=1), encoding="utf-8")

    acc = build_accuracy(results_dir)
    (out_dir / "accuracy.json").write_text(json.dumps(acc, indent=1), encoding="utf-8")
    (out_dir / "accuracy.html").write_text(_accuracy_html(acc), encoding="utf-8")

    lookup = build_lookup(results_dir, error_note=acc["summary_label"])
    (out_dir / "will-it-run.json").write_text(json.dumps(lookup, indent=1), encoding="utf-8")
    (out_dir / "will-it-run.html").write_text(_will_it_run_html(lookup), encoding="utf-8")

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
<div class="top-nav">
  <a href="index.html">Measured results</a>
  <a href="will-it-run.html">Will it run?</a>
  <a href="accuracy.html">Prediction accuracy</a>
  <a href="https://github.com/Prajwal7-2002/runsonmine/blob/main/docs/contribute.md">Contribute</a>
</div>
<h1>RunsOnMine</h1>
<p class="lead">How fast local AI models really run on real computers. Every number here was
measured on someone's machine with <a href="https://github.com/Prajwal7-2002/servebench">servebench</a>,
not estimated. {len(rows)} results so far. <a href="will-it-run.html">Check Will it run?</a></p>
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
