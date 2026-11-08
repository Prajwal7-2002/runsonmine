"""Build standalone, zero-dependency Static Web Studio for RunsOnMine."""

import json
from pathlib import Path


def generate_html(benchmarks_data: list, scaling_data: list) -> str:
    bench_json_str = json.dumps(benchmarks_data)
    scaling_json_str = json.dumps(scaling_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RunsOnMine ⚡ Empirical Silicon LLM Benchmark & Submission Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f293d;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #10b981;
      --accent-glow: rgba(16, 185, 129, 0.15);
      --cyan: #06b6d4;
      --purple: #8b5cf6;
      --amber: #f59e0b;
      --rose: #f43f5e;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text-main);
      font-family: var(--font-sans);
      line-height: 1.5;
      padding-bottom: 60px;
    }}

    header {{
      background: rgba(17, 24, 39, 0.9);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 14px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .logo-group {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .logo-badge {{
      background: linear-gradient(135deg, #10b981, #f59e0b);
      color: #0b0f19;
      font-weight: 800;
      font-size: 14px;
      padding: 4px 8px;
      border-radius: 6px;
      font-family: var(--font-mono);
      letter-spacing: -0.5px;
    }}
    .logo-title {{
      font-weight: 700;
      font-size: 18px;
      letter-spacing: -0.3px;
    }}
    .logo-sub {{
      font-size: 13px;
      color: var(--text-muted);
      margin-left: 6px;
    }}
    .header-links {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    .btn-link {{
      background: #1e293b;
      color: var(--text-main);
      text-decoration: none;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      border: 1px solid var(--card-border);
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .btn-link:hover {{
      background: #334155;
      border-color: #475569;
    }}

    .container {{
      max-width: 1360px;
      margin: 0 auto;
      padding: 24px;
    }}

    .hero {{
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, rgba(11, 15, 25, 0) 100%);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px 28px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .hero-h1 {{
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 6px;
    }}
    .hero-p {{
      color: var(--text-muted);
      font-size: 14px;
      max-width: 820px;
    }}
    .hero-stats {{
      display: flex;
      gap: 20px;
    }}
    .stat-box {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 10px 16px;
      text-align: center;
    }}
    .stat-val {{
      font-size: 20px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: var(--accent);
    }}
    .stat-lbl {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 2px;
    }}

    .tab-bar {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
      overflow-x: auto;
      padding-bottom: 4px;
    }}
    .tab-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 14px;
      font-weight: 600;
      padding: 10px 18px;
      border-radius: 8px 8px 0 0;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-bottom: 2px solid transparent;
      white-space: nowrap;
    }}
    .tab-btn:hover {{
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.03);
    }}
    .tab-btn.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
      background: rgba(16, 185, 129, 0.05);
    }}

    .tab-content {{
      display: none;
    }}
    .tab-content.active {{
      display: block;
    }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .card-title {{
      font-size: 17px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .card-sub {{
      font-size: 13px;
      color: var(--text-muted);
    }}

    .control-group {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .pill-btn {{
      background: #1e293b;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .pill-btn:hover {{
      color: var(--text-main);
      border-color: #475569;
    }}
    .pill-btn.active {{
      background: var(--accent);
      color: #0b0f19;
      border-color: var(--accent);
    }}

    .chart-container {{
      position: relative;
      width: 100%;
      height: 420px;
      background: #0d1322;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      overflow: hidden;
    }}
    svg.interactive-plot {{
      width: 100%;
      height: 100%;
    }}

    .data-table-wrapper {{
      overflow-x: auto;
      border: 1px solid var(--card-border);
      border-radius: 8px;
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }}
    table.data-table th {{
      background: #131c31;
      padding: 10px 14px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--card-border);
    }}
    table.data-table td {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }}
    table.data-table tr:hover {{
      background: rgba(255, 255, 255, 0.02);
    }}

    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      font-family: var(--font-mono);
    }}
    .badge-t4 {{ background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-rtx {{ background: rgba(6, 182, 212, 0.15); color: #06b6d4; border: 1px solid rgba(6, 182, 212, 0.3); }}

    .code-box {{
      background: #0d1322;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px;
      font-family: var(--font-mono);
      font-size: 13px;
      color: #e2e8f0;
      position: relative;
      overflow-x: auto;
      line-height: 1.6;
    }}
    .copy-btn {{
      position: absolute;
      top: 10px;
      right: 10px;
      background: #1e293b;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
    }}
    .copy-btn:hover {{
      color: var(--text-main);
      background: #334155;
    }}

    footer {{
      margin-top: 50px;
      border-top: 1px solid var(--card-border);
      padding: 30px 24px;
      text-align: center;
      color: var(--text-muted);
      font-size: 13px;
    }}
    footer a {{
      color: var(--accent);
      text-decoration: none;
    }}
    footer a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="logo-group">
      <div class="logo-badge">RUNSONMINE</div>
      <div class="logo-title">Empirical Silicon LLM Benchmark Database</div>
      <span class="logo-sub">Community Benchmark Registry</span>
    </div>
    <div class="header-links">
      <a class="btn-link" href="https://huggingface.co/datasets/prajwalpujari16/consumer-silicon-benchmarks" target="_blank">
        🤗 HF Dataset (24 Empirical Points)
      </a>
      <a class="btn-link" href="https://github.com/Prajwal7-2002/runsonmine" target="_blank">
        ★ GitHub
      </a>
      <a class="btn-link" href="https://github.com/Prajwal7-2002/servebench" target="_blank">
        ⚡ servebench
      </a>
    </div>
  </header>

  <div class="container">

    <!-- Hero -->
    <div class="hero">
      <div>
        <h1 class="hero-h1">Real-World Consumer Silicon LLM Benchmark Telemetry</h1>
        <p class="hero-p">
          Empirical inference performance measurements captured with <strong>servebench</strong> across consumer laptop GPUs and cloud accelerators. Explore concurrency scaling curves, compare engines, and submit your local GPU results.
        </p>
      </div>
      <div class="hero-stats">
        <div class="stat-box">
          <div class="stat-val">24</div>
          <div class="stat-lbl">Empirical Runs</div>
        </div>
        <div class="stat-box">
          <div class="stat-val">231.9</div>
          <div class="stat-lbl">Max Tok/s (T4)</div>
        </div>
        <div class="stat-box">
          <div class="stat-val">100%</div>
          <div class="stat-lbl">SLA Attainment</div>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-bar">
      <button class="tab-btn active" onclick="switchTab('explorer')">📊 Silicon Benchmarks Database</button>
      <button class="tab-btn" onclick="switchTab('scaling')">📈 Concurrency Scaling Curve (c=1..8)</button>
      <button class="tab-btn" onclick="switchTab('submit')">📝 Submit Your Hardware Benchmark</button>
    </div>

    <!-- TAB 1: EXPLORER -->
    <div id="tab-explorer" class="tab-content active">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Empirical Benchmark Database (24 Hardware Runs)</div>
            <div class="card-sub">Measured on physical Dual Tesla T4 (30 GB VRAM) & RTX 3050 Laptop (6 GB VRAM)</div>
          </div>
          <div class="control-group">
            <button class="pill-btn active" onclick="filterGPU('all')">All Hardware</button>
            <button class="pill-btn" onclick="filterGPU('Tesla T4')">Dual Tesla T4</button>
            <button class="pill-btn" onclick="filterGPU('RTX 3050')">RTX 3050 Laptop</button>
          </div>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Hardware GPU</th>
                <th>VRAM</th>
                <th>Engine</th>
                <th>Model</th>
                <th>Quant</th>
                <th>Concurrency</th>
                <th>Throughput (tok/s)</th>
                <th>TTFT P50 (ms)</th>
                <th>TPOT P50 (ms)</th>
              </tr>
            </thead>
            <tbody id="bench-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 2: CONCURRENCY SCALING -->
    <div id="tab-scaling" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Concurrency Scaling on RTX 3050 6GB Laptop GPU</div>
            <div class="card-sub">Throughput & TTFT behavior as concurrent clients scale from 1 to 8 on Qwen2.5-0.5B</div>
          </div>
        </div>

        <div class="chart-container" id="chart-box">
          <svg class="interactive-plot" id="scaling-svg"></svg>
        </div>

        <div style="margin-top: 16px;" class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Concurrency (Users)</th>
                <th>Output Tok/s</th>
                <th>Input Tok/s</th>
                <th>TTFT P50 (ms)</th>
                <th>TTFT P99 (ms)</th>
                <th>TPOT P50 (ms)</th>
                <th>E2E P50 (ms)</th>
                <th>SLO Attainment %</th>
              </tr>
            </thead>
            <tbody id="scaling-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 3: SUBMIT BENCHMARK -->
    <div id="tab-submit" class="tab-content">
      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Contribute Your Silicon Benchmark to the Registry</div>
            <div class="card-sub">Run servebench locally and submit your measurements via pull request</div>
          </div>
        </div>

        <div style="margin-bottom: 20px;">
          <div style="font-size: 13px; font-weight: 600; color: var(--accent); margin-bottom: 8px;">
            Step 1: Run servebench on your local machine
          </div>
          <div class="code-box">
# Benchmark your local Ollama or vLLM instance
pip install servebench
servebench quick --model qwen2.5:0.5b --output my_gpu_benchmark.json
            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
          </div>
        </div>

        <div>
          <div style="font-size: 13px; font-weight: 600; color: var(--cyan); margin-bottom: 8px;">
            Step 2: Submit your result via 1-Click Pull Request
          </div>
          <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
            Upload your generated JSON file to the <a href="https://github.com/Prajwal7-2002/runsonmine/tree/main/incoming" target="_blank">incoming/</a> directory on GitHub. Our automated CI verifies the telemetry format and merges it into the community benchmark registry!
          </p>
          <a class="btn-link" style="background:var(--accent); color:#0b0f19; font-weight:700;" href="https://github.com/Prajwal7-2002/runsonmine/new/main?filename=incoming/my_benchmark.json" target="_blank">
            🚀 Open Pull Request on GitHub
          </a>
        </div>
      </div>
    </div>

  </div>

  <!-- Footer -->
  <footer>
    <p>
      <strong>RunsOnMine ⚡</strong> &bull; Crafted by <a href="https://github.com/Prajwal7-2002" target="_blank">Prajwal Pujari</a> &bull;
      Zero-Cold-Start Static Web Space &bull;
      <a href="https://huggingface.co/datasets/prajwalpujari16/consumer-silicon-benchmarks" target="_blank">Hugging Face Dataset</a> &bull;
      <a href="https://github.com/Prajwal7-2002/runsonmine" target="_blank">GitHub Repository</a>
    </p>
  </footer>

  <script>
    const BENCH_DATA = {bench_json_str};
    const SCALING_DATA = {scaling_json_str};

    let currentGpuFilter = 'all';

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      event.currentTarget.classList.add('active');
      document.getElementById('tab-' + tabId).classList.add('active');

      if (tabId === 'scaling') {{
        renderScalingPlot();
      }}
    }}

    function filterGPU(gpu) {{
      currentGpuFilter = gpu;
      document.querySelectorAll('#tab-explorer .control-group button').forEach(b => {{
        b.classList.toggle('active', (gpu === 'all' && b.innerText.includes('All')) || (gpu !== 'all' && b.innerText.includes(gpu)));
      }});
      renderBenchTable();
    }}

    function renderBenchTable() {{
      const tbody = document.getElementById('bench-tbody');
      tbody.innerHTML = '';

      const filtered = BENCH_DATA.filter(d => {{
        if (currentGpuFilter === 'Tesla T4') return d.hardware_gpu.includes('T4');
        if (currentGpuFilter === 'RTX 3050') return d.hardware_gpu.includes('3050');
        return true;
      }});

      filtered.forEach(d => {{
        const isT4 = d.hardware_gpu.includes('T4');
        const badgeClass = isT4 ? 'badge-t4' : 'badge-rtx';

        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="font-family:var(--font-mono); color:var(--text-muted);">${{d.run_id}}</td>
          <td>
            <strong>${{d.hardware_gpu}}</strong>
            <span class="badge ${{badgeClass}}" style="margin-left:6px;">${{isT4 ? '2x GPU' : 'Laptop'}}</span>
          </td>
          <td style="font-family:var(--font-mono);">${{d.total_vram_gb}} GB</td>
          <td>${{d.serving_engine}} v${{d.engine_version}}</td>
          <td style="font-family:var(--font-mono); font-weight:600;">${{d.model_name}}</td>
          <td style="font-family:var(--font-mono);">${{d.quantization}}</td>
          <td style="font-family:var(--font-mono); text-align:center;">${{d.concurrency_users}}</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--accent);">${{d.output_throughput_tok_s.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.ttft_p50_ms.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.tpot_p50_ms.toFixed(1)}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function renderScalingPlot() {{
      const svg = document.getElementById('scaling-svg');
      const box = document.getElementById('chart-box');
      const w = box.clientWidth || 900;
      const h = box.clientHeight || 420;
      svg.setAttribute('viewBox', `0 0 ${{w}} ${{h}}`);
      svg.innerHTML = '';

      const padL = 70;
      const padR = 40;
      const padT = 30;
      const padB = 50;
      const plotW = w - padL - padR;
      const plotH = h - padT - padB;

      const maxC = 8;
      const maxTok = 220;

      const scaleX = c => padL + ((c - 1) / (maxC - 1)) * plotW;
      const scaleY = t => padT + plotH - (t / maxTok) * plotH;

      // Axis line
      const axisG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      axisG.setAttribute('stroke', '#1f293d');
      axisG.setAttribute('stroke-width', '1');

      for (let i = 0; i <= 4; i++) {{
        const tok = (i / 4) * maxTok;
        const yPos = scaleY(tok);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padL);
        line.setAttribute('x2', padL + plotW);
        line.setAttribute('y1', yPos);
        line.setAttribute('y2', yPos);
        axisG.appendChild(line);

        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', padL - 10);
        txt.setAttribute('y', yPos + 4);
        txt.setAttribute('fill', '#64748b');
        txt.setAttribute('font-size', '11');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('text-anchor', 'end');
        txt.textContent = tok.toFixed(0);
        svg.appendChild(txt);
      }}

      // Concurrency ticks
      SCALING_DATA.forEach(d => {{
        const xPos = scaleX(d.concurrency);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', xPos);
        line.setAttribute('x2', xPos);
        line.setAttribute('y1', padT);
        line.setAttribute('y2', padT + plotH);
        axisG.appendChild(line);

        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', xPos);
        txt.setAttribute('y', padT + plotH + 20);
        txt.setAttribute('fill', '#64748b');
        txt.setAttribute('font-size', '11');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('text-anchor', 'middle');
        txt.textContent = 'c=' + d.concurrency;
        svg.appendChild(txt);
      }});
      svg.appendChild(axisG);

      // Line path
      let pathD = `M ${{scaleX(SCALING_DATA[0].concurrency)}} ${{scaleY(SCALING_DATA[0].output_throughput_tok_s)}}`;
      for (let i = 1; i < SCALING_DATA.length; i++) {{
        pathD += ` L ${{scaleX(SCALING_DATA[i].concurrency)}} ${{scaleY(SCALING_DATA[i].output_throughput_tok_s)}}`;
      }}

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', pathD);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', '#10b981');
      path.setAttribute('stroke-width', '3');
      svg.appendChild(path);

      // Dots
      SCALING_DATA.forEach(d => {{
        const cx = scaleX(d.concurrency);
        const cy = scaleY(d.output_throughput_tok_s);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', '6');
        circle.setAttribute('fill', '#10b981');
        circle.setAttribute('stroke', '#0b0f19');
        circle.setAttribute('stroke-width', '2');
        svg.appendChild(circle);

        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', cx);
        label.setAttribute('y', cy - 12);
        label.setAttribute('fill', '#fff');
        label.setAttribute('font-size', '11');
        label.setAttribute('font-family', 'JetBrains Mono');
        label.setAttribute('font-weight', '700');
        label.setAttribute('text-anchor', 'middle');
        label.textContent = d.output_throughput_tok_s.toFixed(1) + ' tok/s';
        svg.appendChild(label);
      }});
    }}

    function renderScalingTable() {{
      const tbody = document.getElementById('scaling-tbody');
      tbody.innerHTML = '';

      SCALING_DATA.forEach(d => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--cyan);">${{d.concurrency}}</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--accent);">${{d.output_throughput_tok_s.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.input_throughput_tok_s.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.ttft_p50_ms.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.ttft_p99_ms.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.tpot_p50_ms.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono);">${{d.e2e_p50_ms.toFixed(1)}}</td>
          <td style="font-family:var(--font-mono); color:var(--accent);">${{d.slo_attainment_pct.toFixed(0)}}%</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function copyCode(btn) {{
      const text = btn.parentElement.innerText.replace('Copy', '').trim();
      navigator.clipboard.writeText(text);
      btn.textContent = '✓ Copied';
      setTimeout(() => {{
        btn.textContent = 'Copy';
      }}, 2000);
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      renderBenchTable();
      renderScalingTable();
      renderScalingPlot();
      window.addEventListener('resize', renderScalingPlot);
    }});
  </script>
</body>
</html>"""
    return html_content


def main():
    root = Path(__file__).resolve().parent.parent

    bench_json_path = root / "hf_dataset" / "consumer_silicon_benchmarks.json"
    scaling_json_path = root / "hf_dataset" / "concurrency_scaling_curves.json"

    if not bench_json_path.exists() or not scaling_json_path.exists():
        raise FileNotFoundError("Dataset files not found. Run generate_silicon_dataset.py first!")

    bench_data = json.loads(bench_json_path.read_text(encoding="utf-8"))
    scaling_data = json.loads(scaling_json_path.read_text(encoding="utf-8"))

    html_content = generate_html(bench_data, scaling_data)

    space_dir = root / "hf_space"
    space_dir.mkdir(parents=True, exist_ok=True)
    space_html_path = space_dir / "index.html"
    space_html_path.write_text(html_content, encoding="utf-8")
    print(f"✓ Wrote {space_html_path} ({len(html_content)} bytes)")

    space_readme = r"""---
title: RunsOnMine - Empirical Silicon Benchmark Studio
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: static
pinned: false
license: apache-2.0
short_description: Real consumer GPU LLM serving benchmarks & PR registry.
---

# RunsOnMine ⚡ Empirical Silicon Benchmark Studio

Interactive consumer GPU inference benchmark database, concurrency scaling curves, and 1-click pull request submission portal.

* **GitHub Repository:** [Prajwal7-2002/runsonmine](https://github.com/Prajwal7-2002/runsonmine)
* **HF Benchmark Dataset:** [prajwalpujari16/consumer-silicon-benchmarks](https://huggingface.co/datasets/prajwalpujari16/consumer-silicon-benchmarks)
* **Author:** Prajwal Pujari ([@Prajwal7-2002](https://github.com/Prajwal7-2002))
"""
    (space_dir / "README.md").write_text(space_readme, encoding="utf-8")
    print(f"✓ Wrote {space_dir / 'README.md'}")

    # Copy to brain artifact directory for preview
    brain_dir = Path(r"C:\Users\ADMIN\.gemini\antigravity\brain\b4bc2e58-a6e6-4dec-a3a6-5013100d2137")
    if brain_dir.exists():
        artifact_path = brain_dir / "runsonmine_studio_preview.html"
        artifact_path.write_text(html_content, encoding="utf-8")
        print(f"✓ Wrote artifact preview: {artifact_path}")

    print("\n🎉 RunsOnMine Interactive Static Studio build completed successfully!")


if __name__ == "__main__":
    main()
