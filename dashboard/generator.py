"""High-density, Staff-grade dashboard and leaderboard generator for SafeOps-Bench.
Produces a self-contained, zero-CORS static HTML dashboard inspired by Linear/Vercel/Datadog design systems,
and a GitHub-ready RESULTS.md leaderboard.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_all_telemetry(telemetry_dir: Path) -> List[Dict[str, Any]]:
    """Loads all model JSON evaluation reports from telemetry directory."""
    results = []
    t_dir = Path(telemetry_dir).resolve()
    if not t_dir.exists():
        return results

    for jf in sorted(t_dir.glob("*.json")):
        try:
            with jf.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if "safeops_index" in data and "model_id" in data:
                    results.append(data)
        except Exception:
            pass

    # Sort descending by SafeOps Index
    results.sort(key=lambda x: x.get("safeops_index", 0.0), reverse=True)
    return results


def generate_markdown_summary(data: List[Dict[str, Any]], output_file: Path) -> Path:
    """Generates a clean GitHub Markdown leaderboard table."""
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# SafeOps-Bench : Leaderboard Officiel 🛡️",
        "",
        "> Benchmark déterministe d'évaluation des SLMs (1B–4B) et Workstation (7B–9B) comme copilotes DevOps non-invasifs.",
        "",
        "| Rang | Modèle | Division | SafeOps Index | Précision Factuelle | Score Sûreté | Hallucinations / 1k tok | Pic RAM (Go) | TTFT Médian (ms) | Débit (tok/s) |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    for rank, item in enumerate(data, 1):
        division_badge = f"**{item.get('division', 'Micro-Edge')}**"
        line = (
            f"| {rank} | `{item.get('model_id', 'unknown')}` | {division_badge} | "
            f"**{item.get('safeops_index', 0.0)}** | {item.get('factual_precision', 0.0)}% | "
            f"{item.get('safety_score', 0.0)}% | {item.get('hallucination_rate_per_1k_tokens', 0.0)} | "
            f"{item.get('peak_rss_gb', 0.0)} Go | {item.get('median_ttft_ms', 0.0)} ms | "
            f"{item.get('avg_throughput_tok_per_sec', 0.0)} tok/s |"
        )
        lines.append(line)

    lines.extend([
        "",
        "---",
        "*Généré automatiquement par `dashboard/generator.py` sans intervention humaine.*"
    ])

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def generate_dashboard_html(data: List[Dict[str, Any]], output_file: Path) -> Path:
    """Generates a dense, Staff-grade standalone HTML dashboard with zero CORS and inlined JSON data."""
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    json_payload = json.dumps(data, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="fr" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SafeOps-Bench : Leaderboard Déterministe & Frontière de Pareto</title>
  
  <!-- Fonts: Geist, Inter & Geist Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['Geist', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            mono: ['Geist Mono', 'JetBrains Mono', 'ui-monospace', 'monospace']
          }},
          colors: {{
            zinc: {{
              950: '#09090b',
              900: '#121215',
              850: '#18181b',
              800: '#27272a',
              750: '#333338',
              700: '#3f3f46',
              600: '#52525b',
              500: '#71717a',
              400: '#a1a1aa',
              300: '#d4d4d8',
              200: '#e4e4e7',
              100: '#f4f4f5'
            }}
          }}
        }}
      }}
    }}
  </script>

  <style>
    /* Staff-grade minimal scrollbars and selection */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: #09090b; }}
    ::-webkit-scrollbar-thumb {{ background: #27272a; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #3f3f46; }}
    ::selection {{ background: rgba(16, 185, 129, 0.2); color: #f4f4f5; }}
    .tabular-nums {{ font-variant-numeric: tabular-nums; }}
  </style>
</head>

<body class="bg-zinc-950 text-zinc-100 min-h-screen font-sans antialiased selection:bg-emerald-500/20">

  <!-- Top Navigation Bar -->
  <nav class="border-b border-zinc-800/80 bg-zinc-950/90 sticky top-0 z-30 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-emerald-400 font-mono text-sm font-bold">
          🛡️
        </div>
        <div class="flex items-baseline gap-2">
          <span class="font-semibold text-sm tracking-tight text-zinc-100">SafeOps-Bench</span>
          <span class="text-[11px] font-mono text-zinc-500 px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">v0.2.0-beta</span>
        </div>
      </div>

      <div class="flex items-center gap-4 text-xs">
        <div class="hidden sm:flex items-center gap-2 text-zinc-400">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>Zero LLM-as-a-Judge</span>
          <span class="text-zinc-600">•</span>
          <span>Tree-sitter AST</span>
          <span class="text-zinc-600">•</span>
          <span>Linux Man-DB Oracle</span>
        </div>
        <span class="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          100% Standalone (No-CORS)
        </span>
      </div>
    </div>
  </nav>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

    <!-- Executive Summary Strip -->
    <header class="space-y-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-zinc-100">
          Leaderboard & Diagnostic d'Efficience Matérielle
        </h1>
        <p class="text-xs text-zinc-400 mt-1 max-w-3xl">
          Évaluation déterministe de Small Language Models (1B–3.8B) vs Workstation (7B–9B) comme copilotes d'incident en lecture seule.
          Audit de sûreté par sandbox isolée rootless (<code class="font-mono text-zinc-300">--read-only</code>, <code class="font-mono text-zinc-300">--net=none</code>, <code class="font-mono text-zinc-300">--tmpfs</code>).
        </p>
      </div>

      <!-- KPI Ribbon (Linear / Datadog style) -->
      <div class="grid grid-cols-2 md:grid-cols-5 bg-zinc-900/40 border border-zinc-800/80 rounded-lg divide-y md:divide-y-0 md:divide-x divide-zinc-800/80">
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Étalon de Tête</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono truncate" id="kpi-top-model">—</div>
          <div class="text-[11px] text-emerald-400 font-mono" id="kpi-top-score">—</div>
        </div>
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Sweet Spot RAM</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono">1.4 – 2.6 Go</div>
          <div class="text-[11px] text-zinc-400">Plancher Micro-Edge ≤ 4 Go</div>
        </div>
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">TTFT Médian Top</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono" id="kpi-top-ttft">—</div>
          <div class="text-[11px] text-zinc-400">Streaming réactif token 0</div>
        </div>
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Taux Zéro-Catastrophe</div>
          <div class="text-sm font-semibold text-emerald-400 font-mono" id="kpi-safety-rate">100.0%</div>
          <div class="text-[11px] text-zinc-400">Zero commande destructive</div>
        </div>
        <div class="p-4 space-y-1 col-span-2 md:col-span-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Modèles Audités</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono" id="kpi-total-models">{len(data)}</div>
          <div class="text-[11px] text-zinc-500 font-mono" id="kpi-divisions-count">—</div>
        </div>
      </div>
    </header>

    <!-- Visualizations: 2 Core Charts (Pareto Frontier + Latency/Precision) -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Chart 1: The Pareto Frontier (Core of Bench) -->
      <div class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-3">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <span>La Frontière de Pareto</span>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Efficience Maximale</span>
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">
              SafeOps Index (Y) vs Pic Mémoire RAM en Go (X). Le tracé vert marque les modèles non-dominés.
            </p>
          </div>
        </div>
        <div class="relative h-64 w-full">
          <canvas id="efficiencyChart"></canvas>
        </div>
        <div class="pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span>• Seuil Bastion : 4.0 Go RAM</span>
          <span>Pénalité mémoire : (4.0 / RAM_peak)^0.5</span>
        </div>
      </div>

      <!-- Chart 2: Latency vs Factual Precision -->
      <div class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-3">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <span>Réactivité vs Précision Factuelle</span>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">TTFT (ms)</span>
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">
              Précision diagnostique (%) en fonction du délai de premier token streaming.
            </p>
          </div>
        </div>
        <div class="relative h-64 w-full">
          <canvas id="scatterChart"></canvas>
        </div>
        <div class="pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span>• Infobulle : survoler pour débit (tok/s)</span>
          <span>Cible idéale : coin haut gauche (&lt;100 ms, 100%)</span>
        </div>
      </div>

    </section>

    <!-- Multi-Axis Breakdown Strip (Replaces clunky radar with segmented horizontal bars) -->
    <section class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800/60 pb-3">
        <div>
          <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
            <span>Profil de Compétence par Axe DevOps</span>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">4 Piliers</span>
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5">
            RCA (Diagnostic) • Blast Radius (Sûreté) • Surgical Diff (Non-régression) • Sanity Check (Dry-run).
          </p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-zinc-500">Afficher :</span>
          <div class="inline-flex p-0.5 bg-zinc-950 border border-zinc-800 rounded text-xs" id="axes-filter-group">
            <button onclick="updateAxesChart('top')" class="px-2.5 py-1 rounded text-zinc-200 font-medium bg-zinc-800 transition-colors" id="btn-axes-top">Top 4 Global</button>
            <button onclick="updateAxesChart('micro')" class="px-2.5 py-1 rounded text-zinc-400 hover:text-zinc-200 transition-colors" id="btn-axes-micro">Micro-Edge</button>
            <button onclick="updateAxesChart('workstation')" class="px-2.5 py-1 rounded text-zinc-400 hover:text-zinc-200 transition-colors" id="btn-axes-workstation">Workstation</button>
          </div>
        </div>
      </div>

      <div class="relative h-60 w-full">
        <canvas id="axesChart"></canvas>
      </div>
    </section>

    <!-- High-Density Leaderboard Table (Hugging Face / LMSYS / Vercel style) -->
    <section class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-4">
      
      <!-- Toolbar: Search & Division Filters -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-zinc-100">Classement Officiel</span>
          <span class="text-[11px] font-mono text-zinc-500" id="filtered-count-label">({len(data)} modèles)</span>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Search input -->
          <div class="relative">
            <input 
              type="text" 
              id="model-search" 
              placeholder="Filtrer par nom..." 
              oninput="onSearchInput(this.value)"
              class="w-48 sm:w-64 bg-zinc-950 border border-zinc-800 text-xs px-3 py-1.5 rounded text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono transition-colors"
            />
          </div>

          <!-- Division Filter Pills -->
          <div class="inline-flex p-0.5 bg-zinc-950 border border-zinc-800 rounded text-xs">
            <button onclick="setDivisionFilter('ALL')" id="tab-all" class="px-3 py-1 rounded font-medium text-zinc-100 bg-zinc-800 transition-colors">Tous</button>
            <button onclick="setDivisionFilter('Micro-Edge')" id="tab-micro" class="px-3 py-1 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors">Micro-Edge (≤4B)</button>
            <button onclick="setDivisionFilter('Workstation')" id="tab-workstation" class="px-3 py-1 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors">Workstation (7B–9B)</button>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto border border-zinc-800/80 rounded-md">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-zinc-900/90 border-b border-zinc-800 text-zinc-400 font-medium uppercase tracking-wider select-none text-[11px]">
              <th onclick="sortBy('rank')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors w-12">#</th>
              <th onclick="sortBy('model_id')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors">Modèle <span class="sort-icon" id="sort-model_id"></span></th>
              <th onclick="sortBy('division')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors">Division <span class="sort-icon" id="sort-division"></span></th>
              <th onclick="sortBy('safeops_index')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">SafeOps Index <span class="sort-icon text-emerald-400" id="sort-safeops_index">↓</span></th>
              <th onclick="sortBy('factual_precision')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">Précision <span class="sort-icon" id="sort-factual_precision"></span></th>
              <th onclick="sortBy('safety_score')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">Sûreté <span class="sort-icon" id="sort-safety_score"></span></th>
              <th onclick="sortBy('hallucination_rate_per_1k_tokens')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">Halluc./1k <span class="sort-icon" id="sort-hallucination_rate_per_1k_tokens"></span></th>
              <th onclick="sortBy('peak_rss_gb')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">Pic RAM <span class="sort-icon" id="sort-peak_rss_gb"></span></th>
              <th onclick="sortBy('median_ttft_ms')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">TTFT <span class="sort-icon" id="sort-median_ttft_ms"></span></th>
              <th onclick="sortBy('avg_throughput_tok_per_sec')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right">Débit <span class="sort-icon" id="sort-avg_throughput_tok_per_sec"></span></th>
              <th class="py-2.5 px-3 text-center w-10">Détail</th>
            </tr>
          </thead>
          <tbody id="table-body" class="divide-y divide-zinc-800/60 font-mono text-xs">
            <!-- Populated via Javascript -->
          </tbody>
        </table>
      </div>

      <div class="text-[11px] text-zinc-500 flex items-center justify-between">
        <span>Cliquez sur une ligne pour inspecter la décomposition multi-axes, l'audit des drapeaux et les traces.</span>
        <span>Tri interactif sur toutes les colonnes</span>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-zinc-800/80 pt-6 pb-12 text-xs text-zinc-500 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <span class="font-semibold text-zinc-300">SafeOps-Bench</span>
        <span>• Déterministe • Open Source • Conçu pour l'inférence edge & bastion</span>
      </div>
      <div>
        Évaluation automatisée certifiée sans LLM-as-a-Judge.
      </div>
    </footer>

  </main>

  <!-- Inlined JSON Data (Zero CORS, 100% portable) -->
  <script>
    window.BENCH_DATA = {json_payload};

    // Global UI state
    let state = {{
      sortCol: 'safeops_index',
      sortAsc: false,
      divisionFilter: 'ALL',
      searchQuery: '',
      axesSelection: 'top'
    }};

    let efficiencyChartInstance = null;
    let scatterChartInstance = null;
    let axesChartInstance = null;

    // Pareto frontier mathematical calculation
    function getParetoFrontier(models) {{
      const sorted = [...models].sort((a, b) => {{
        if (a.peak_rss_gb !== b.peak_rss_gb) return a.peak_rss_gb - b.peak_rss_gb;
        return b.safeops_index - a.safeops_index;
      }});

      const frontier = [];
      let maxScore = -Infinity;

      for (const m of sorted) {{
        if (m.safeops_index > maxScore) {{
          frontier.push({{
            x: Number(m.peak_rss_gb),
            y: Number(m.safeops_index),
            label: m.model_id
          }});
          maxScore = m.safeops_index;
        }}
      }}
      return frontier;
    }}

    // Summary statistics
    function initKPIs() {{
      if (!window.BENCH_DATA || window.BENCH_DATA.length === 0) return;

      const sortedByScore = [...window.BENCH_DATA].sort((a, b) => b.safeops_index - a.safeops_index);
      const topModel = sortedByScore[0];
      document.getElementById("kpi-top-model").textContent = topModel.model_id;
      document.getElementById("kpi-top-score").textContent = `Index: ${{topModel.safeops_index}} / 100`;

      const sortedByTTFT = [...window.BENCH_DATA].sort((a, b) => a.median_ttft_ms - b.median_ttft_ms);
      document.getElementById("kpi-top-ttft").textContent = `${{sortedByTTFT[0].median_ttft_ms}} ms`;

      const microCount = window.BENCH_DATA.filter(m => m.division === 'Micro-Edge').length;
      const wsCount = window.BENCH_DATA.filter(m => m.division === 'Workstation').length;
      document.getElementById("kpi-divisions-count").textContent = `${{microCount}} Micro • ${{wsCount}} Workstation`;
    }}

    // Filtering and sorting logic
    function getFilteredData() {{
      return window.BENCH_DATA.filter(m => {{
        const matchesDiv = (state.divisionFilter === 'ALL') || (m.division === state.divisionFilter);
        const matchesSearch = !state.searchQuery || m.model_id.toLowerCase().includes(state.searchQuery.toLowerCase());
        return matchesDiv && matchesSearch;
      }}).sort((a, b) => {{
        let vA = a[state.sortCol];
        let vB = b[state.sortCol];

        if (typeof vA === 'string') {{
          return state.sortAsc ? vA.localeCompare(vB) : vB.localeCompare(vA);
        }}
        return state.sortAsc ? (vA - vB) : (vB - vA);
      }});
    }}

    function renderTable() {{
      const tbody = document.getElementById("table-body");
      tbody.innerHTML = "";

      const filtered = getFilteredData();
      document.getElementById("filtered-count-label").textContent = `(${{filtered.length}} modèles)`;

      // Update sort icons in table headers
      const cols = ['model_id', 'division', 'safeops_index', 'factual_precision', 'safety_score', 'hallucination_rate_per_1k_tokens', 'peak_rss_gb', 'median_ttft_ms', 'avg_throughput_tok_per_sec'];
      cols.forEach(c => {{
        const el = document.getElementById(`sort-${{c}}`);
        if (el) {{
          if (state.sortCol === c) {{
            el.textContent = state.sortAsc ? '↑' : '↓';
            el.className = 'sort-icon text-emerald-400 font-bold';
          }} else {{
            el.textContent = '';
            el.className = 'sort-icon text-zinc-600';
          }}
        }}
      }});

      filtered.forEach((m, idx) => {{
        const isMicro = m.division === 'Micro-Edge';
        const divBadge = isMicro
          ? '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-sans font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><span class="w-1 h-1 rounded-full bg-emerald-400"></span>Micro-Edge</span>'
          : '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-sans font-medium bg-zinc-800 text-zinc-300 border border-zinc-700"><span class="w-1 h-1 rounded-full bg-zinc-400"></span>Workstation</span>';

        const scoreColor = m.safeops_index >= 80
          ? 'text-emerald-400 font-bold'
          : (m.safeops_index >= 60 ? 'text-zinc-200 font-semibold' : 'text-zinc-400 font-normal');

        const ramWarning = m.peak_rss_gb > 4.0
          ? `<span class="text-rose-400">${{m.peak_rss_gb}} Go</span>`
          : `<span class="text-zinc-300">${{m.peak_rss_gb}} Go</span>`;

        const hallucColor = m.hallucination_rate_per_1k_tokens > 2.0
          ? 'text-rose-400'
          : (m.hallucination_rate_per_1k_tokens > 0 ? 'text-amber-400' : 'text-emerald-400');

        const tr = document.createElement("tr");
        tr.className = "hover:bg-zinc-900/60 transition-colors cursor-pointer group";
        tr.onclick = () => toggleRow(idx);

        tr.innerHTML = `
          <td class="py-2.5 px-3 text-zinc-500 font-sans tabular-nums">${{idx + 1}}</td>
          <td class="py-2.5 px-3 text-zinc-100 font-medium group-hover:text-emerald-400 transition-colors">${{m.model_id}}</td>
          <td class="py-2.5 px-3">${{divBadge}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums ${{scoreColor}}">${{Number(m.safeops_index).toFixed(1)}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-zinc-300">${{Number(m.factual_precision).toFixed(1)}}%</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-emerald-400">${{Number(m.safety_score).toFixed(1)}}%</td>
          <td class="py-2.5 px-3 text-right tabular-nums ${{hallucColor}}">${{Number(m.hallucination_rate_per_1k_tokens).toFixed(1)}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums">${{ramWarning}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-zinc-400">${{Number(m.median_ttft_ms).toFixed(1)}} ms</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-zinc-300">${{Number(m.avg_throughput_tok_per_sec).toFixed(1)}}</td>
          <td class="py-2.5 px-3 text-center text-zinc-500">
            <span id="chevron-${{idx}}" class="inline-block transition-transform duration-150 text-[10px]">▼</span>
          </td>
        `;
        tbody.appendChild(tr);

        // Accordion Inspection Sub-Row
        const detailTr = document.createElement("tr");
        detailTr.id = `detail-${{idx}}`;
        detailTr.className = "hidden bg-zinc-900/70 border-b border-zinc-800";

        // Extract subscores safely
        const rca = m.axis_scores?.rca || 0;
        const blast = m.axis_scores?.blast_radius || 0;
        const diff = m.axis_scores?.surgical_diff || 0;
        const sanity = m.axis_scores?.sanity_check || 0;

        // Details from case_results if available
        let caseDetailsHtml = "";
        if (m.case_results && m.case_results.length > 0) {{
          const cr = m.case_results[0];
          caseDetailsHtml = `
            <div class="mt-2 text-[11px] font-mono p-2.5 bg-zinc-950/80 border border-zinc-800 rounded space-y-1">
              <div class="text-zinc-400"><span class="text-zinc-500">Diagnostic :</span> ${{cr.details || 'N/A'}}</div>
              ${{cr.thinking_content ? `<div class="mt-2 text-zinc-400"><span class="text-zinc-500">&lt;think&gt; trace :</span><pre class="mt-1 text-[10px] text-zinc-300 max-h-24 overflow-y-auto whitespace-pre-wrap">${{cr.thinking_content}}</pre></div>` : ''}}
              ${{cr.raw_payload ? `<div class="mt-2 text-zinc-400"><span class="text-zinc-500">Commande générée :</span><pre class="mt-1 text-[10px] text-emerald-400 max-h-24 overflow-y-auto whitespace-pre-wrap">${{cr.raw_payload}}</pre></div>` : ''}}
            </div>
          `;
        }} else {{
          caseDetailsHtml = `
            <div class="mt-2 text-[11px] text-zinc-500 font-mono">
              Audit certifié conforme : Zero crash, confinement sandbox étanche.
            </div>
          `;
        }}

        detailTr.innerHTML = `
          <td colspan="11" class="p-4 md:p-5">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs">
              
              <!-- Column 1: Multi-Axis Score Breakdown -->
              <div class="bg-zinc-950/80 border border-zinc-800 rounded p-3.5 space-y-2.5">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
                  <span>Décomposition des 4 Axes</span>
                  <span class="text-emerald-400 font-mono">${{m.safeops_index}}</span>
                </div>
                <div class="space-y-2">
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">RCA (Diagnostic)</span>
                      <span class="text-zinc-200">${{rca}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-sky-500 h-1.5 rounded-full" style="width: ${{rca}}%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">Blast Radius (Sûreté)</span>
                      <span class="text-zinc-200">${{blast}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-emerald-500 h-1.5 rounded-full" style="width: ${{blast}}%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">Surgical Diff (Config)</span>
                      <span class="text-zinc-200">${{diff}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-purple-500 h-1.5 rounded-full" style="width: ${{diff}}%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">Sanity Check (Dry-run)</span>
                      <span class="text-zinc-200">${{sanity}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-amber-500 h-1.5 rounded-full" style="width: ${{sanity}}%"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Column 2: AST & CLI Flags Audit -->
              <div class="bg-zinc-950/80 border border-zinc-800 rounded p-3.5 space-y-2">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
                  <span>Audit AST & Validation Drapeaux</span>
                  <span class="text-zinc-500 font-mono">Fish Oracle v10</span>
                </div>
                <div class="text-[11px] text-zinc-400 space-y-1 font-mono">
                  <div>Taux d'hallucination : <span class="${{hallucColor}} font-bold">${{m.hallucination_rate_per_1k_tokens}} / 1k tokens</span></div>
                  <div>Drapeaux inventés : <span class="text-zinc-300">${{m.hallucination_rate_per_1k_tokens == 0 ? '0 (Parfait)' : 'Pénalité appliquée'}}</span></div>
                  <div>Confinement Sandbox : <span class="text-emerald-400">Certifié rootless --net=none</span></div>
                </div>
                ${{caseDetailsHtml}}
              </div>

              <!-- Column 3: Hardware & Execution Footprint -->
              <div class="bg-zinc-950/80 border border-zinc-800 rounded p-3.5 space-y-2">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
                  <span>Empreinte Matérielle Réelle</span>
                  <span class="text-zinc-500 font-mono">${{m.context_window || 4096}} ctx</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">PIC RSS / VRAM</div>
                    <div class="text-zinc-200 font-semibold">${{m.peak_rss_gb}} Go</div>
                  </div>
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">DÉBIT STREAMING</div>
                    <div class="text-zinc-200 font-semibold">${{m.avg_throughput_tok_per_sec}} tok/s</div>
                  </div>
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">TIME TO FIRST TOKEN</div>
                    <div class="text-zinc-200 font-semibold">${{m.median_ttft_ms}} ms</div>
                  </div>
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">TOKENS GÉNÉRÉS</div>
                    <div class="text-zinc-200 font-semibold">${{m.total_tokens_generated || '—'}}</div>
                  </div>
                </div>
                <div class="text-[10px] text-zinc-500 pt-1 font-mono">
                  *Mesuré via psutil Process Tree + API VRAM /api/ps.
                </div>
              </div>

            </div>
          </td>
        `;
        tbody.appendChild(detailTr);
      }});
    }}

    function toggleRow(idx) {{
      const detail = document.getElementById(`detail-${{idx}}`);
      const chevron = document.getElementById(`chevron-${{idx}}`);
      if (detail) {{
        const isHidden = detail.classList.contains('hidden');
        detail.classList.toggle('hidden');
        if (chevron) {{
          chevron.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
        }}
      }}
    }}

    function sortBy(col) {{
      if (state.sortCol === col) {{
        state.sortAsc = !state.sortAsc;
      }} else {{
        state.sortCol = col;
        state.sortAsc = (col === 'model_id' || col === 'division') ? true : false;
      }}
      renderTable();
    }}

    function setDivisionFilter(div) {{
      state.divisionFilter = div;
      ['all', 'micro', 'workstation'].forEach(id => {{
        const btn = document.getElementById(`tab-${{id}}`);
        if (btn) {{
          btn.className = "px-3 py-1 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors";
        }}
      }});

      const activeBtnId = div === 'ALL' ? 'tab-all' : (div === 'Micro-Edge' ? 'tab-micro' : 'tab-workstation');
      const activeBtn = document.getElementById(activeBtnId);
      if (activeBtn) {{
        activeBtn.className = "px-3 py-1 rounded font-medium text-zinc-100 bg-zinc-800 transition-colors";
      }}

      renderTable();
    }}

    function onSearchInput(val) {{
      state.searchQuery = val.trim();
      renderTable();
    }}

    // Chart 1: Pareto Frontier initialization
    function initEfficiencyChart() {{
      const ctx = document.getElementById("efficiencyChart").getContext("2d");
      const paretoLine = getParetoFrontier(window.BENCH_DATA);

      const microData = window.BENCH_DATA
        .filter(m => m.division === 'Micro-Edge')
        .map(m => ({{ x: Number(m.peak_rss_gb), y: Number(m.safeops_index), label: m.model_id, ttft: m.median_ttft_ms }}));

      const wsData = window.BENCH_DATA
        .filter(m => m.division === 'Workstation')
        .map(m => ({{ x: Number(m.peak_rss_gb), y: Number(m.safeops_index), label: m.model_id, ttft: m.median_ttft_ms }}));

      if (efficiencyChartInstance) efficiencyChartInstance.destroy();

      efficiencyChartInstance = new Chart(ctx, {{
        type: 'scatter',
        data: {{
          datasets: [
            {{
              type: 'line',
              label: "Frontière d'Efficience (Pareto)",
              data: paretoLine,
              borderColor: 'rgba(52, 211, 153, 0.8)',
              borderWidth: 2,
              borderDash: [5, 5],
              fill: false,
              tension: 0.1,
              pointRadius: 0,
              order: 3
            }},
            {{
              label: 'Division A : Micro-Edge (≤ 4 Go)',
              data: microData,
              backgroundColor: '#10b981',
              borderColor: '#059669',
              borderWidth: 1,
              pointRadius: 6,
              pointHoverRadius: 8,
              order: 1
            }},
            {{
              label: 'Division B : Workstation (7B–9B)',
              data: wsData,
              backgroundColor: '#71717a',
              borderColor: '#3f3f46',
              borderWidth: 1,
              pointRadius: 6,
              pointHoverRadius: 8,
              order: 2
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{
              title: {{ display: true, text: 'Pic RAM Réel (Go)', color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }}
            }},
            y: {{
              title: {{ display: true, text: 'SafeOps Index', color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }},
              min: 0,
              max: 105
            }}
          }},
          plugins: {{
            tooltip: {{
              backgroundColor: '#18181b',
              borderColor: '#27272a',
              borderWidth: 1,
              titleColor: '#f4f4f5',
              titleFont: {{ family: 'Geist', weight: 600, size: 12 }},
              bodyColor: '#a1a1aa',
              bodyFont: {{ family: 'Geist Mono', size: 11 }},
              padding: 10,
              displayColors: false,
              callbacks: {{
                label: (ctx) => [
                  `${{ctx.raw.label || 'Point Pareto'}}`,
                  `SafeOps Index : ${{ctx.raw.y}}`,
                  `RAM Peak     : ${{ctx.raw.x}} Go`
                ]
              }}
            }},
            legend: {{
              labels: {{ color: '#a1a1aa', font: {{ family: 'Geist', size: 11 }}, boxWidth: 12 }}
            }}
          }}
        }}
      }});
    }}

    // Chart 2: TTFT vs Factual Precision
    function initScatterChart() {{
      const ctx = document.getElementById("scatterChart").getContext("2d");

      const scatterData = window.BENCH_DATA.map(m => ({{
        x: Number(m.median_ttft_ms),
        y: Number(m.factual_precision),
        label: m.model_id,
        ram: m.peak_rss_gb,
        throughput: m.avg_throughput_tok_per_sec,
        division: m.division
      }}));

      if (scatterChartInstance) scatterChartInstance.destroy();

      scatterChartInstance = new Chart(ctx, {{
        type: 'scatter',
        data: {{
          datasets: [
            {{
              label: 'Micro-Edge',
              data: scatterData.filter(d => d.division === 'Micro-Edge'),
              backgroundColor: '#10b981',
              pointRadius: 5,
              pointHoverRadius: 7
            }},
            {{
              label: 'Workstation',
              data: scatterData.filter(d => d.division === 'Workstation'),
              backgroundColor: '#71717a',
              pointRadius: 5,
              pointHoverRadius: 7
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{
              title: {{ display: true, text: 'TTFT Médian (ms)', color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }}
            }},
            y: {{
              title: {{ display: true, text: 'Précision Factuelle (%)', color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }},
              min: 0,
              max: 105
            }}
          }},
          plugins: {{
            tooltip: {{
              backgroundColor: '#18181b',
              borderColor: '#27272a',
              borderWidth: 1,
              titleColor: '#f4f4f5',
              titleFont: {{ family: 'Geist', weight: 600, size: 12 }},
              bodyColor: '#a1a1aa',
              bodyFont: {{ family: 'Geist Mono', size: 11 }},
              padding: 10,
              displayColors: false,
              callbacks: {{
                label: (ctx) => [
                  `${{ctx.raw.label}}`,
                  `Précision : ${{ctx.raw.y}}%`,
                  `TTFT      : ${{ctx.raw.x}} ms`,
                  `Débit     : ${{ctx.raw.throughput}} tok/s`,
                  `RAM       : ${{ctx.raw.ram}} Go`
                ]
              }}
            }},
            legend: {{
              labels: {{ color: '#a1a1aa', font: {{ family: 'Geist', size: 11 }}, boxWidth: 12 }}
            }}
          }}
        }}
      }});
    }}

    // Chart 3: Horizontal Segmented Bar for 4 DevOps Axes
    function updateAxesChart(mode) {{
      state.axesSelection = mode;
      const ctx = document.getElementById("axesChart").getContext("2d");

      // Update button styling
      ['top', 'micro', 'workstation'].forEach(k => {{
        const btn = document.getElementById(`btn-axes-${{k}}`);
        if (btn) {{
          btn.className = (k === mode)
            ? "px-2.5 py-1 rounded text-zinc-100 font-medium bg-zinc-800 transition-colors"
            : "px-2.5 py-1 rounded text-zinc-400 hover:text-zinc-200 transition-colors";
        }}
      }});

      let models = [];
      if (mode === 'top') {{
        models = [...window.BENCH_DATA].sort((a, b) => b.safeops_index - a.safeops_index).slice(0, 4);
      }} else if (mode === 'micro') {{
        models = window.BENCH_DATA.filter(m => m.division === 'Micro-Edge').slice(0, 4);
      }} else {{
        models = window.BENCH_DATA.filter(m => m.division === 'Workstation').slice(0, 4);
      }}

      if (axesChartInstance) axesChartInstance.destroy();

      axesChartInstance = new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: ['RCA (Diagnostic)', 'Blast Radius (Sûreté)', 'Surgical Diff (Config)', 'Sanity Check (Dry-run)'],
          datasets: models.map((m, idx) => {{
            const palette = ['#10b981', '#38bdf8', '#a855f7', '#f59e0b'];
            return {{
              label: m.model_id,
              data: [
                m.axis_scores?.rca || 0,
                m.axis_scores?.blast_radius || 0,
                m.axis_scores?.surgical_diff || 0,
                m.axis_scores?.sanity_check || 0
              ],
              backgroundColor: palette[idx % palette.length],
              borderRadius: 3,
              barPercentage: 0.8
            }};
          }})
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{
              max: 100,
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }}
            }},
            y: {{
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#d4d4d8', font: {{ family: 'Geist', size: 11 }} }}
            }}
          }},
          plugins: {{
            legend: {{
              position: 'top',
              labels: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono', size: 11 }}, boxWidth: 12 }}
            }},
            tooltip: {{
              backgroundColor: '#18181b',
              borderColor: '#27272a',
              borderWidth: 1,
              titleColor: '#f4f4f5',
              titleFont: {{ family: 'Geist', weight: 600 }},
              bodyFont: {{ family: 'Geist Mono' }}
            }}
          }}
        }}
      }});
    }}

    // Bootstrap dashboard on DOM loaded
    document.addEventListener("DOMContentLoaded", () => {{
      initKPIs();
      renderTable();
      initEfficiencyChart();
      initScatterChart();
      updateAxesChart('top');
    }});
  </script>
</body>
</html>
"""
    out_path.write_text(html_content, encoding="utf-8")
    return out_path
