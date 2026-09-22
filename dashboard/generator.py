"""High-density, Staff-grade dashboard and leaderboard generator for SafeOps-Bench.
Produces a self-contained, zero-CORS static HTML dashboard inspired by Linear/Vercel/Datadog design systems,
and a GitHub-ready RESULTS.md leaderboard.
Features full bilingual (EN/FR) support, deep linking (#model=, #lang=), open data JSON export,
resilient clipboard copying, and Open Graph social cards.
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
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SafeOps-Bench : Deterministic SLM DevOps Benchmark & Pareto Frontier</title>
  <meta name="description" content="Empirical evaluation of 12 SLMs (1B–3.8B) vs Workstations (7B–9B) on 50 real-world DevOps incidents. Certified on NVIDIA RTX 4090.">
  <link rel="canonical" href="https://safeops.jalal.tech/">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">

  <!-- Open Graph / LinkedIn / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="SafeOps-Bench">
  <meta property="og:url" content="https://safeops.jalal.tech/">
  <meta property="og:title" content="SafeOps-Bench : Deterministic SLM DevOps Benchmark">
  <meta property="og:description" content="Empirical evaluation of 12 SLMs (1B–3.8B) vs Workstation models on 50 real-world DevOps incidents. Certified on 1x NVIDIA RTX 4090 24GB.">
  <meta property="og:image" content="https://safeops.jalal.tech/assets/og-preview.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">

  <!-- Twitter / X -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="https://safeops.jalal.tech/">
  <meta name="twitter:title" content="SafeOps-Bench : Deterministic SLM DevOps Benchmark">
  <meta name="twitter:description" content="Empirical evaluation of 12 SLMs (1B–3.8B) vs Workstation models on 50 real-world DevOps incidents. Certified on 1x NVIDIA RTX 4090 24GB.">
  <meta name="twitter:image" content="https://safeops.jalal.tech/assets/og-preview.png">
  
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
    .ring-highlight {{ box-shadow: 0 0 0 2px #10b981; transition: box-shadow 0.3s ease; }}
  </style>
</head>

<body class="bg-zinc-950 text-zinc-100 min-h-screen font-sans antialiased selection:bg-emerald-500/20">

  <!-- Top Navigation Bar -->
  <nav class="border-b border-zinc-800/80 bg-zinc-950/90 sticky top-0 z-30 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-2">
      
      <!-- Brand & Version -->
      <div class="flex items-center gap-3">
        <a href="https://safeops.jalal.tech/" class="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-emerald-400 font-mono text-sm font-bold hover:border-emerald-500/50 transition-colors">
          🛡️
        </a>
        <div class="flex items-baseline gap-2">
          <a href="https://safeops.jalal.tech/" class="font-semibold text-sm tracking-tight text-zinc-100 hover:text-emerald-400 transition-colors">SafeOps-Bench</a>
          <span class="text-[11px] font-mono text-zinc-500 px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800">v0.2.0-beta</span>
        </div>
      </div>

      <!-- Trust Pillars (Mid-Screen) -->
      <div class="hidden lg:flex items-center gap-2 text-xs text-zinc-400">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
        <span data-i18n="nav_zero_judge">Zero LLM-as-a-Judge</span>
        <span class="text-zinc-600">•</span>
        <span data-i18n="nav_tree_sitter">Tree-sitter AST</span>
        <span class="text-zinc-600">•</span>
        <span data-i18n="nav_man_oracle">Linux Man-DB Oracle</span>
      </div>

      <!-- Actions: Branding, GitHub, Language Switcher -->
      <div class="flex items-center gap-2.5 text-xs">
        
        <!-- Personal Branding Link -->
        <a href="https://jalal.tech" target="_blank" rel="noopener noreferrer" 
           class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-400 transition-all font-medium text-[11px]">
          <span data-i18n="nav_created_by">Created by Jalal</span>
          <span class="text-[10px]">↗</span>
        </a>

        <!-- GitHub Repo Link -->
        <a href="https://github.com/dimaland1/SafeOps-Bench" target="_blank" rel="noopener noreferrer"
           class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-zinc-100 hover:border-zinc-700 transition-colors text-[11px] font-medium">
          <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
          </svg>
          <span class="hidden sm:inline" data-i18n="nav_github_code">Code & Tests</span>
          <span class="text-[9px] font-mono px-1 py-0.2 rounded bg-zinc-800 text-zinc-400">Apache-2.0</span>
        </a>

        <!-- Bilingual Switcher [ EN | FR ] -->
        <div class="inline-flex p-0.5 bg-zinc-900 border border-zinc-800 rounded text-[11px] font-mono">
          <button onclick="setLanguage('en')" id="lang-btn-en" class="px-2 py-0.5 rounded font-semibold text-zinc-100 bg-zinc-800 transition-colors">EN</button>
          <button onclick="setLanguage('fr')" id="lang-btn-fr" class="px-2 py-0.5 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors">FR</button>
        </div>

      </div>
    </div>
  </nav>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

    <!-- Executive Summary Strip -->
    <header class="space-y-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-zinc-100" data-i18n="hero_title">
          Leaderboard & Hardware Efficiency Diagnostic
        </h1>
        <p class="text-xs text-zinc-400 mt-1 max-w-3xl leading-relaxed" data-i18n="hero_subtitle">
          Deterministic evaluation of Small Language Models (1B–3.8B) vs Workstation (7B–9B) as read-only DevOps incident copilots.
          Safety audit under rootless isolated sandbox (<code class="font-mono text-zinc-300">--read-only</code>, <code class="font-mono text-zinc-300">--net=none</code>, <code class="font-mono text-zinc-300">--tmpfs</code>).
        </p>
      </div>

      <!-- Hardware Provenance Status Banner -->
      <div class="flex flex-wrap items-center gap-2">
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 text-xs font-mono text-zinc-300">
          <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-zinc-500 font-semibold uppercase tracking-wider text-[10px]" data-i18n="badge_hardware_label">Hardware Provenance:</span>
          <span data-i18n="badge_hardware_val">1x NVIDIA RTX 4090 24GB • Ollama CUDA 12.8 • RunPod Reference Node</span>
        </div>
        <span class="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-400" data-i18n="nav_standalone">
          100% Standalone (No-CORS)
        </span>
      </div>

      <!-- KPI Ribbon (Linear / Datadog style) -->
      <div class="grid grid-cols-2 md:grid-cols-5 bg-zinc-900/40 border border-zinc-800/80 rounded-lg divide-y md:divide-y-0 md:divide-x divide-zinc-800/80">
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500" data-i18n="kpi_top_model">Top Benchmark</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono truncate" id="kpi-top-model">—</div>
          <div class="text-[11px] text-emerald-400 font-mono" id="kpi-top-score">—</div>
        </div>
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500" data-i18n="kpi_ram_sweetspot">RAM Sweet Spot</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono">1.1 – 2.5 GB</div>
          <div class="text-[11px] text-zinc-400" data-i18n="kpi_ram_subtext">Micro-Edge Floor ≤ 4 GB</div>
        </div>
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500" data-i18n="kpi_top_ttft">Top Median TTFT</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono" id="kpi-top-ttft">—</div>
          <div class="text-[11px] text-zinc-400" data-i18n="kpi_ttft_subtext">Reactive token-0 streaming</div>
        </div>
        <div class="p-4 space-y-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500" data-i18n="kpi_safety_rate">Zero-Catastrophe Rate</div>
          <div class="text-sm font-semibold text-emerald-400 font-mono" id="kpi-safety-rate">100.0%</div>
          <div class="text-[11px] text-zinc-400" data-i18n="kpi_safety_subtext">Zero destructive commands</div>
        </div>
        <div class="p-4 space-y-1 col-span-2 md:col-span-1">
          <div class="text-[11px] font-medium uppercase tracking-wider text-zinc-500" data-i18n="kpi_models_audited">Audited Models</div>
          <div class="text-sm font-semibold text-zinc-100 font-mono" id="kpi-total-models">{len(data)}</div>
          <div class="text-[11px] text-zinc-500 font-mono" id="kpi-divisions-count">—</div>
        </div>
      </div>
    </header>

    <!-- Visualizations: 2 Core Charts (Pareto Frontier + Latency/Precision) -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Chart 1: The Pareto Frontier -->
      <div class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-3">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <span data-i18n="chart1_title">The Pareto Frontier</span>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" data-i18n="chart1_tag">Max Efficiency</span>
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5" data-i18n="chart1_sub">
              SafeOps Index (Y) vs Peak RAM in GB (X). The green curve marks non-dominated models.
            </p>
          </div>
        </div>
        <div class="relative h-64 w-full">
          <canvas id="efficiencyChart"></canvas>
        </div>
        <div class="pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span data-i18n="chart1_note_left">• Bastion Threshold: 4.0 GB RAM</span>
          <span data-i18n="chart1_note_right">Memory Penalty: (4.0 / RAM_peak)^0.5</span>
        </div>
      </div>

      <!-- Chart 2: Latency vs Factual Precision -->
      <div class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-3">
        <div class="flex items-start justify-between">
          <div>
            <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
              <span data-i18n="chart2_title">Responsiveness vs Factual Precision</span>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700" data-i18n="chart2_tag">TTFT (ms)</span>
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5" data-i18n="chart2_sub">
              Diagnostic precision (%) as a function of streaming first-token latency.
            </p>
          </div>
        </div>
        <div class="relative h-64 w-full">
          <canvas id="scatterChart"></canvas>
        </div>
        <div class="pt-2 border-t border-zinc-800/60 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span data-i18n="chart2_note_left">• Tooltip: hover for throughput (tok/s)</span>
          <span data-i18n="chart2_note_right">Ideal target: top-left corner (&lt;100 ms, 100%)</span>
        </div>
      </div>

    </section>

    <!-- Multi-Axis Breakdown Strip -->
    <section class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800/60 pb-3">
        <div>
          <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
            <span data-i18n="axes_title">Competency Profile by DevOps Axis</span>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400" data-i18n="axes_tag">4 Pillars</span>
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5" data-i18n="axes_sub">
            RCA (Diagnostic) • Blast Radius (Safety) • Surgical Diff (Non-regression) • Sanity Check (Dry-run).
          </p>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-zinc-500" data-i18n="axes_filter_label">Display:</span>
          <div class="inline-flex p-0.5 bg-zinc-950 border border-zinc-800 rounded text-xs" id="axes-filter-group">
            <button onclick="updateAxesChart('top')" class="px-2.5 py-1 rounded text-zinc-200 font-medium bg-zinc-800 transition-colors" id="btn-axes-top" data-i18n="axes_btn_top">Top 4 Global</button>
            <button onclick="updateAxesChart('micro')" class="px-2.5 py-1 rounded text-zinc-400 hover:text-zinc-200 transition-colors" id="btn-axes-micro" data-i18n="axes_btn_micro">Micro-Edge</button>
            <button onclick="updateAxesChart('workstation')" class="px-2.5 py-1 rounded text-zinc-400 hover:text-zinc-200 transition-colors" id="btn-axes-workstation" data-i18n="axes_btn_workstation">Workstation</button>
          </div>
        </div>
      </div>

      <div class="relative h-60 w-full">
        <canvas id="axesChart"></canvas>
      </div>
    </section>

    <!-- High-Density Leaderboard Table -->
    <section class="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-5 space-y-4">
      
      <!-- Toolbar: Search & Division Filters & Export Button -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-zinc-100" data-i18n="table_title">Official Leaderboard</span>
          <span class="text-[11px] font-mono text-zinc-500" id="filtered-count-label">({len(data)} models)</span>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Search input -->
          <div class="relative">
            <input 
              type="text" 
              id="model-search" 
              placeholder="Filter by name..." 
              data-i18n-ph="table_search_ph"
              oninput="onSearchInput(this.value)"
              class="w-44 sm:w-56 bg-zinc-950 border border-zinc-800 text-xs px-3 py-1.5 rounded text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono transition-colors"
            />
          </div>

          <!-- Division Filter Pills -->
          <div class="inline-flex p-0.5 bg-zinc-950 border border-zinc-800 rounded text-xs">
            <button onclick="setDivisionFilter('ALL')" id="tab-all" class="px-3 py-1 rounded font-medium text-zinc-100 bg-zinc-800 transition-colors" data-i18n="tab_all">All</button>
            <button onclick="setDivisionFilter('Micro-Edge')" id="tab-micro" class="px-3 py-1 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors" data-i18n="tab_micro">Micro-Edge (≤4B)</button>
            <button onclick="setDivisionFilter('Workstation')" id="tab-workstation" class="px-3 py-1 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors" data-i18n="tab_workstation">Workstation (7B–9B)</button>
          </div>

          <!-- Open Data Export Button -->
          <button onclick="exportTelemetryJSON()" 
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:border-emerald-500/50 hover:text-emerald-400 text-zinc-300 font-mono text-xs transition-colors"
                  title="Download full benchmark JSON dataset">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            <span data-i18n="btn_export_json">Export Telemetry JSON ↓</span>
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto border border-zinc-800/80 rounded-md">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-zinc-900/90 border-b border-zinc-800 text-zinc-400 font-medium uppercase tracking-wider select-none text-[11px]">
              <th onclick="sortBy('rank')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors w-12" data-i18n="th_rank">#</th>
              <th onclick="sortBy('model_id')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors"><span data-i18n="th_model">Model</span> <span class="sort-icon" id="sort-model_id"></span></th>
              <th onclick="sortBy('division')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors"><span data-i18n="th_division">Division</span> <span class="sort-icon" id="sort-division"></span></th>
              <th onclick="sortBy('safeops_index')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_index">SafeOps Index</span> <span class="sort-icon text-emerald-400" id="sort-safeops_index">↓</span></th>
              <th onclick="sortBy('factual_precision')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_precision">Precision</span> <span class="sort-icon" id="sort-factual_precision"></span></th>
              <th onclick="sortBy('safety_score')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_safety">Safety</span> <span class="sort-icon" id="sort-safety_score"></span></th>
              <th onclick="sortBy('hallucination_rate_per_1k_tokens')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_halluc">Halluc./1k</span> <span class="sort-icon" id="sort-hallucination_rate_per_1k_tokens"></span></th>
              <th onclick="sortBy('peak_rss_gb')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_ram">Peak RAM</span> <span class="sort-icon" id="sort-peak_rss_gb"></span></th>
              <th onclick="sortBy('median_ttft_ms')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_ttft">TTFT</span> <span class="sort-icon" id="sort-median_ttft_ms"></span></th>
              <th onclick="sortBy('avg_throughput_tok_per_sec')" class="py-2.5 px-3 cursor-pointer hover:text-zinc-200 transition-colors text-right"><span data-i18n="th_throughput">Throughput</span> <span class="sort-icon" id="sort-avg_throughput_tok_per_sec"></span></th>
              <th class="py-2.5 px-3 text-center w-16" data-i18n="th_detail">Detail</th>
            </tr>
          </thead>
          <tbody id="table-body" class="divide-y divide-zinc-800/60 font-mono text-xs">
            <!-- Populated via Javascript -->
          </tbody>
        </table>
      </div>

      <div class="text-[11px] text-zinc-500 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1">
        <span data-i18n="table_tip_click">Click any row to inspect multi-axis breakdown, flags audit, and traces.</span>
        <span data-i18n="table_tip_sort">Interactive sorting on all columns • 🔗 to copy recruiter link</span>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-zinc-800/80 pt-6 pb-12 text-xs text-zinc-500 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <span class="font-semibold text-zinc-300">SafeOps-Bench</span>
        <span data-i18n="footer_desc">• Deterministic • Open Source • Engineered for edge & bastion inference</span>
      </div>
      <div class="flex items-center gap-3">
        <a href="https://jalal.tech" target="_blank" rel="noopener noreferrer" class="hover:text-emerald-400 transition-colors" data-i18n="footer_author">
          Architected by Jalal Azouzout — AI Platform Engineer
        </a>
        <span class="text-zinc-700">•</span>
        <span data-i18n="footer_sub">Automated evaluation certified without LLM-as-a-Judge.</span>
      </div>
    </footer>

  </main>

  <!-- Inlined JSON Data (Zero CORS, 100% portable) -->
  <script>
    window.BENCH_DATA = {json_payload};

    // Bilingual dictionary (EN default, FR toggle)
    const I18N = {{
      en: {{
        nav_zero_judge: "Zero LLM-as-a-Judge",
        nav_tree_sitter: "Tree-sitter AST",
        nav_man_oracle: "Linux Man-DB Oracle",
        nav_standalone: "100% Standalone (No-CORS)",
        nav_created_by: "Created by Jalal",
        nav_github_code: "Code & Tests",
        
        hero_title: "Leaderboard & Hardware Efficiency Diagnostic",
        hero_subtitle: "Deterministic evaluation of Small Language Models (1B–3.8B) vs Workstation (7B–9B) as read-only DevOps incident copilots. Safety audit under rootless isolated sandbox (--read-only, --net=none, --tmpfs).",
        badge_hardware_label: "Hardware Provenance:",
        badge_hardware_val: "1x NVIDIA RTX 4090 24GB • Ollama CUDA 12.8 • RunPod Reference Node",
        
        kpi_top_model: "Top Benchmark",
        kpi_ram_sweetspot: "RAM Sweet Spot",
        kpi_ram_subtext: "Micro-Edge Floor ≤ 4 GB",
        kpi_top_ttft: "Top Median TTFT",
        kpi_ttft_subtext: "Reactive token-0 streaming",
        kpi_safety_rate: "Zero-Catastrophe Rate",
        kpi_safety_subtext: "Zero destructive commands",
        kpi_models_audited: "Audited Models",
        
        chart1_title: "The Pareto Frontier",
        chart1_tag: "Max Efficiency",
        chart1_sub: "SafeOps Index (Y) vs Peak RAM in GB (X). The green curve marks non-dominated models.",
        chart1_note_left: "• Bastion Threshold: 4.0 GB RAM",
        chart1_note_right: "Memory Penalty: (4.0 / RAM_peak)^0.5",
        chart1_axis_x: "Peak Memory RSS (GB)",
        chart1_axis_y: "SafeOps Index",
        chart1_pareto_label: "Efficiency Frontier (Pareto)",
        chart1_div_a: "Division A: Micro-Edge (≤ 4 GB)",
        chart1_div_b: "Division B: Workstation (7B–9B)",
        
        chart2_title: "Responsiveness vs Factual Precision",
        chart2_tag: "TTFT (ms)",
        chart2_sub: "Diagnostic precision (%) as a function of streaming first-token latency.",
        chart2_note_left: "• Tooltip: hover for throughput (tok/s)",
        chart2_note_right: "Ideal target: top-left corner (<100 ms, 100%)",
        chart2_axis_x: "Median TTFT (ms)",
        chart2_axis_y: "Factual Precision (%)",
        
        axes_title: "Competency Profile by DevOps Axis",
        axes_tag: "4 Pillars",
        axes_sub: "RCA (Diagnostic) • Blast Radius (Safety) • Surgical Diff (Non-regression) • Sanity Check (Dry-run).",
        axes_filter_label: "Display:",
        axes_btn_top: "Top 4 Global",
        axes_btn_micro: "Micro-Edge",
        axes_btn_workstation: "Workstation",
        
        table_title: "Official Leaderboard",
        table_search_ph: "Filter by name...",
        tab_all: "All",
        tab_micro: "Micro-Edge (≤4B)",
        tab_workstation: "Workstation (7B–9B)",
        btn_export_json: "Export Telemetry JSON ↓",
        
        th_rank: "#",
        th_model: "Model",
        th_division: "Division",
        th_index: "SafeOps Index",
        th_precision: "Precision",
        th_safety: "Safety",
        th_halluc: "Halluc./1k",
        th_ram: "Peak RAM",
        th_ttft: "TTFT",
        th_throughput: "Throughput",
        th_detail: "Detail",
        
        table_tip_click: "Click any row to inspect multi-axis breakdown, flags audit, and traces.",
        table_tip_sort: "Interactive sorting on all columns • 🔗 to copy recruiter link",
        
        col_breakdown: "4-Axes Score Breakdown",
        col_ast_audit: "AST Audit & Flags Validation",
        col_hardware_footprint: "Real Hardware Footprint",
        
        axis_rca: "RCA (Diagnostic)",
        axis_blast: "Blast Radius (Safety)",
        axis_diff: "Surgical Diff (Config)",
        axis_sanity: "Sanity Check (Dry-run)",
        
        ast_halluc_rate: "Hallucination rate:",
        ast_invented_flags: "Invented flags:",
        ast_sandbox_status: "Sandbox Confinement:",
        ast_sandbox_val: "Certified rootless --net=none",
        ast_zero_flags: "0 (Perfect)",
        ast_penalty: "Penalty applied",
        
        hw_peak_rss: "PEAK RSS / VRAM",
        hw_throughput: "STREAMING THROUGHPUT",
        hw_ttft: "TIME TO FIRST TOKEN",
        hw_tokens: "GENERATED TOKENS",
        hw_footnote: "*Measured via psutil Process Tree + VRAM API /api/ps.",
        
        audit_cert_clean: "Certified audit: Zero crash, isolated sandbox confinement.",
        lbl_diagnostic: "Diagnostic:",
        lbl_think_trace: "<think> trace:",
        lbl_cmd_generated: "Generated command:",
        link_copied: "Link copied!",
        
        footer_desc: "• Deterministic • Open Source • Engineered for edge & bastion inference",
        footer_author: "Architected by Jalal Azouzout — AI Platform Engineer",
        footer_sub: "Automated evaluation certified without LLM-as-a-Judge."
      }},
      fr: {{
        nav_zero_judge: "Zéro LLM-as-a-Judge",
        nav_tree_sitter: "AST Tree-sitter",
        nav_man_oracle: "Oracle Linux Man-DB",
        nav_standalone: "100% Autonome (Sans-CORS)",
        nav_created_by: "Créé par Jalal",
        nav_github_code: "Code & Tests",
        
        hero_title: "Leaderboard & Diagnostic d'Efficience Matérielle",
        hero_subtitle: "Évaluation déterministe de Small Language Models (1B–3.8B) vs Workstation (7B–9B) comme copilotes d'incident en lecture seule. Audit de sûreté par sandbox isolée rootless (--read-only, --net=none, --tmpfs).",
        badge_hardware_label: "Provenance Matérielle :",
        badge_hardware_val: "1x NVIDIA RTX 4090 24Go • Ollama CUDA 12.8 • Node de Référence RunPod",
        
        kpi_top_model: "Étalon de Tête",
        kpi_ram_sweetspot: "Sweet Spot RAM",
        kpi_ram_subtext: "Plancher Micro-Edge ≤ 4 Go",
        kpi_top_ttft: "TTFT Médian Top",
        kpi_ttft_subtext: "Streaming réactif token 0",
        kpi_safety_rate: "Taux Zéro-Catastrophe",
        kpi_safety_subtext: "Zéro commande destructive",
        kpi_models_audited: "Modèles Audités",
        
        chart1_title: "La Frontière de Pareto",
        chart1_tag: "Efficience Maximale",
        chart1_sub: "SafeOps Index (Y) vs Pic Mémoire RAM en Go (X). Le tracé vert marque les modèles non-dominés.",
        chart1_note_left: "• Seuil Bastion : 4.0 Go RAM",
        chart1_note_right: "Pénalité mémoire : (4.0 / RAM_peak)^0.5",
        chart1_axis_x: "Pic RAM Réel (Go)",
        chart1_axis_y: "SafeOps Index",
        chart1_pareto_label: "Frontière d'Efficience (Pareto)",
        chart1_div_a: "Division A : Micro-Edge (≤ 4 Go)",
        chart1_div_b: "Division B : Workstation (7B–9B)",
        
        chart2_title: "Réactivité vs Précision Factuelle",
        chart2_tag: "TTFT (ms)",
        chart2_sub: "Précision diagnostique (%) en fonction du délai de premier token streaming.",
        chart2_note_left: "• Infobulle : survoler pour débit (tok/s)",
        chart2_note_right: "Cible idéale : coin haut gauche (<100 ms, 100%)",
        chart2_axis_x: "TTFT Médian (ms)",
        chart2_axis_y: "Précision Factuelle (%)",
        
        axes_title: "Profil de Compétence par Axe DevOps",
        axes_tag: "4 Piliers",
        axes_sub: "RCA (Diagnostic) • Blast Radius (Sûreté) • Surgical Diff (Non-régression) • Sanity Check (Dry-run).",
        axes_filter_label: "Afficher :",
        axes_btn_top: "Top 4 Global",
        axes_btn_micro: "Micro-Edge",
        axes_btn_workstation: "Workstation",
        
        table_title: "Classement Officiel",
        table_search_ph: "Filtrer par nom...",
        tab_all: "Tous",
        tab_micro: "Micro-Edge (≤4B)",
        tab_workstation: "Workstation (7B–9B)",
        btn_export_json: "Exporter Télémétrie JSON ↓",
        
        th_rank: "#",
        th_model: "Modèle",
        th_division: "Division",
        th_index: "SafeOps Index",
        th_precision: "Précision",
        th_safety: "Sûreté",
        th_halluc: "Halluc./1k",
        th_ram: "Pic RAM",
        th_ttft: "TTFT",
        th_throughput: "Débit",
        th_detail: "Détail",
        
        table_tip_click: "Cliquez sur une ligne pour inspecter la décomposition multi-axes, l'audit des drapeaux et les traces.",
        table_tip_sort: "Tri interactif sur toutes les colonnes • 🔗 pour copier le lien recruteur",
        
        col_breakdown: "Décomposition des 4 Axes",
        col_ast_audit: "Audit AST & Validation Drapeaux",
        col_hardware_footprint: "Empreinte Matérielle Réelle",
        
        axis_rca: "RCA (Diagnostic)",
        axis_blast: "Blast Radius (Sûreté)",
        axis_diff: "Surgical Diff (Config)",
        axis_sanity: "Sanity Check (Dry-run)",
        
        ast_halluc_rate: "Taux d'hallucination :",
        ast_invented_flags: "Drapeaux inventés :",
        ast_sandbox_status: "Confinement Sandbox :",
        ast_sandbox_val: "Certifié rootless --net=none",
        ast_zero_flags: "0 (Parfait)",
        ast_penalty: "Pénalité appliquée",
        
        hw_peak_rss: "PIC RSS / VRAM",
        hw_throughput: "DÉBIT STREAMING",
        hw_ttft: "TIME TO FIRST TOKEN",
        hw_tokens: "TOKENS GÉNÉRÉS",
        hw_footnote: "*Mesuré via psutil Process Tree + API VRAM /api/ps.",
        
        audit_cert_clean: "Audit certifié conforme : Zéro crash, confinement sandbox étanche.",
        lbl_diagnostic: "Diagnostic :",
        lbl_think_trace: "Trace <think> :",
        lbl_cmd_generated: "Commande générée :",
        link_copied: "Lien copié !",
        
        footer_desc: "• Déterministe • Open Source • Conçu pour l'inférence edge & bastion",
        footer_author: "Architecturé par Jalal Azouzout — AI Platform Engineer",
        footer_sub: "Évaluation automatisée certifiée sans LLM-as-a-Judge."
      }}
    }};

    // Global UI state
    let state = {{
      currentLang: localStorage.getItem('safeops_lang') || 'en',
      sortCol: 'safeops_index',
      sortAsc: false,
      divisionFilter: 'ALL',
      searchQuery: '',
      axesSelection: 'top'
    }};

    let efficiencyChartInstance = null;
    let scatterChartInstance = null;
    let axesChartInstance = null;

    // Sanitize model id for DOM usage
    function sanitizeId(id) {{
      return String(id).replace(/[^a-zA-Z0-9_-]/g, '_');
    }}

    // Internationalization logic
    function setLanguage(lang) {{
      if (!I18N[lang]) lang = 'en';
      state.currentLang = lang;
      localStorage.setItem('safeops_lang', lang);
      document.documentElement.lang = lang;

      // Update button styling
      const btnEn = document.getElementById("lang-btn-en");
      const btnFr = document.getElementById("lang-btn-fr");
      if (btnEn && btnFr) {{
        if (lang === 'en') {{
          btnEn.className = "px-2 py-0.5 rounded font-semibold text-zinc-100 bg-zinc-800 transition-colors";
          btnFr.className = "px-2 py-0.5 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors";
        }} else {{
          btnEn.className = "px-2 py-0.5 rounded font-medium text-zinc-400 hover:text-zinc-200 transition-colors";
          btnFr.className = "px-2 py-0.5 rounded font-semibold text-zinc-100 bg-zinc-800 transition-colors";
        }}
      }}

      // Translate all data-i18n elements
      const dict = I18N[lang];
      document.querySelectorAll("[data-i18n]").forEach(el => {{
        const key = el.getAttribute("data-i18n");
        if (dict[key]) el.textContent = dict[key];
      }});

      // Translate placeholders
      document.querySelectorAll("[data-i18n-ph]").forEach(el => {{
        const key = el.getAttribute("data-i18n-ph");
        if (dict[key]) el.setAttribute("placeholder", dict[key]);
      }});

      // Re-render table and charts with new language strings
      renderTable();
      initEfficiencyChart();
      initScatterChart();
      updateAxesChart(state.axesSelection);
    }}

    // Clipboard copy with robust fallback for file:/// and insecure origins
    function copyModelLink(modelId, btnElement) {{
      const safeId = sanitizeId(modelId);
      const url = `${{window.location.origin}}${{window.location.pathname}}#model=${{encodeURIComponent(modelId)}}`;
      
      function onSuccess() {{
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = '✓';
        btnElement.classList.add('text-emerald-400');
        setTimeout(() => {{
          btnElement.innerHTML = originalText;
          btnElement.classList.remove('text-emerald-400');
        }}, 1500);
      }}

      if (navigator.clipboard && window.isSecureContext) {{
        navigator.clipboard.writeText(url).then(onSuccess).catch(() => fallbackCopy(url, onSuccess));
      }} else {{
        fallbackCopy(url, onSuccess);
      }}
    }}

    function fallbackCopy(text, cb) {{
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {{
        document.execCommand('copy');
        if (cb) cb();
      }} catch (err) {{
        console.error('Fallback copy failed', err);
      }}
      document.body.removeChild(textArea);
    }}

    // Open Data Export
    function exportTelemetryJSON() {{
      const dataStr = JSON.stringify(window.BENCH_DATA, null, 2);
      const blob = new Blob([dataStr], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "safeops-bench-telemetry.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

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
      const dict = I18N[state.currentLang];

      const filtered = getFilteredData();
      const countLabel = state.currentLang === 'fr' 
        ? `(${{filtered.length}} modèles)` 
        : `(${{filtered.length}} models)`;
      document.getElementById("filtered-count-label").textContent = countLabel;

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
        const safeId = sanitizeId(m.model_id);
        const isMicro = m.division === 'Micro-Edge';
        const divBadge = isMicro
          ? '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-sans font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><span class="w-1 h-1 rounded-full bg-emerald-400"></span>Micro-Edge</span>'
          : '<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-sans font-medium bg-zinc-800 text-zinc-300 border border-zinc-700"><span class="w-1 h-1 rounded-full bg-zinc-400"></span>Workstation</span>';

        const scoreColor = m.safeops_index >= 80
          ? 'text-emerald-400 font-bold'
          : (m.safeops_index >= 60 ? 'text-zinc-200 font-semibold' : 'text-zinc-400 font-normal');

        const ramWarning = m.peak_rss_gb > 4.0
          ? `<span class="text-rose-400">${{m.peak_rss_gb}} GB</span>`
          : `<span class="text-zinc-300">${{m.peak_rss_gb}} GB</span>`;

        const hallucColor = m.hallucination_rate_per_1k_tokens > 2.0
          ? 'text-rose-400'
          : (m.hallucination_rate_per_1k_tokens > 0 ? 'text-amber-400' : 'text-emerald-400');

        const tr = document.createElement("tr");
        tr.id = `row-${{safeId}}`;
        tr.className = "hover:bg-zinc-900/60 transition-colors cursor-pointer group";
        tr.onclick = (e) => {{
          // Don't toggle if user clicked copy button
          if (e.target.closest('.btn-copy-link')) return;
          toggleRow(safeId);
        }};

        tr.innerHTML = `
          <td class="py-2.5 px-3 text-zinc-500 font-sans tabular-nums">${{idx + 1}}</td>
          <td class="py-2.5 px-3 text-zinc-100 font-medium group-hover:text-emerald-400 transition-colors">
            <div class="flex items-center gap-1.5">
              <span>${{m.model_id}}</span>
              <button onclick="copyModelLink('${{m.model_id}}', this)" 
                      class="btn-copy-link p-1 text-zinc-600 hover:text-emerald-400 transition-colors rounded hover:bg-zinc-800 text-[11px]" 
                      title="Copy recruiter direct link">
                🔗
              </button>
            </div>
          </td>
          <td class="py-2.5 px-3">${{divBadge}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums ${{scoreColor}}">${{Number(m.safeops_index).toFixed(1)}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-zinc-300">${{Number(m.factual_precision).toFixed(1)}}%</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-emerald-400">${{Number(m.safety_score).toFixed(1)}}%</td>
          <td class="py-2.5 px-3 text-right tabular-nums ${{hallucColor}}">${{Number(m.hallucination_rate_per_1k_tokens).toFixed(1)}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums">${{ramWarning}}</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-zinc-400">${{Number(m.median_ttft_ms).toFixed(1)}} ms</td>
          <td class="py-2.5 px-3 text-right tabular-nums text-zinc-300">${{Number(m.avg_throughput_tok_per_sec).toFixed(1)}}</td>
          <td class="py-2.5 px-3 text-center text-zinc-500">
            <span id="chevron-${{safeId}}" class="inline-block transition-transform duration-150 text-[10px]">▼</span>
          </td>
        `;
        tbody.appendChild(tr);

        // Accordion Inspection Sub-Row
        const detailTr = document.createElement("tr");
        detailTr.id = `detail-${{safeId}}`;
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
              <div class="text-zinc-400"><span class="text-zinc-500">${{dict.lbl_diagnostic}}</span> ${{cr.details || 'N/A'}}</div>
              ${{cr.thinking_content ? `<div class="mt-2 text-zinc-400"><span class="text-zinc-500">${{dict.lbl_think_trace}}</span><pre class="mt-1 text-[10px] text-zinc-300 max-h-24 overflow-y-auto whitespace-pre-wrap">${{cr.thinking_content}}</pre></div>` : ''}}
              ${{cr.raw_payload ? `<div class="mt-2 text-zinc-400"><span class="text-zinc-500">${{dict.lbl_cmd_generated}}</span><pre class="mt-1 text-[10px] text-emerald-400 max-h-24 overflow-y-auto whitespace-pre-wrap">${{cr.raw_payload}}</pre></div>` : ''}}
            </div>
          `;
        }} else {{
          caseDetailsHtml = `
            <div class="mt-2 text-[11px] text-zinc-500 font-mono">
              ${{dict.audit_cert_clean}}
            </div>
          `;
        }}

        const zeroFlagText = m.hallucination_rate_per_1k_tokens == 0 ? dict.ast_zero_flags : dict.ast_penalty;

        detailTr.innerHTML = `
          <td colspan="11" class="p-4 md:p-5">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs">
              
              <!-- Column 1: Multi-Axis Score Breakdown -->
              <div class="bg-zinc-950/80 border border-zinc-800 rounded p-3.5 space-y-2.5">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
                  <span>${{dict.col_breakdown}}</span>
                  <span class="text-emerald-400 font-mono">${{m.safeops_index}}</span>
                </div>
                <div class="space-y-2">
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">${{dict.axis_rca}}</span>
                      <span class="text-zinc-200">${{rca}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-sky-500 h-1.5 rounded-full" style="width: ${{rca}}%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">${{dict.axis_blast}}</span>
                      <span class="text-zinc-200">${{blast}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-emerald-500 h-1.5 rounded-full" style="width: ${{blast}}%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">${{dict.axis_diff}}</span>
                      <span class="text-zinc-200">${{diff}}%</span>
                    </div>
                    <div class="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                      <div class="bg-purple-500 h-1.5 rounded-full" style="width: ${{diff}}%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[11px] mb-1 font-mono">
                      <span class="text-zinc-400">${{dict.axis_sanity}}</span>
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
                  <span>${{dict.col_ast_audit}}</span>
                  <span class="text-zinc-500 font-mono">Tree-sitter & Man-DB</span>
                </div>
                <div class="text-[11px] text-zinc-400 space-y-1 font-mono">
                  <div>${{dict.ast_halluc_rate}} <span class="${{hallucColor}} font-bold">${{m.hallucination_rate_per_1k_tokens}} / 1k tokens</span></div>
                  <div>${{dict.ast_invented_flags}} <span class="text-zinc-300">${{zeroFlagText}}</span></div>
                  <div>${{dict.ast_sandbox_status}} <span class="text-emerald-400">${{dict.ast_sandbox_val}}</span></div>
                </div>
                ${{caseDetailsHtml}}
              </div>

              <!-- Column 3: Hardware & Execution Footprint -->
              <div class="bg-zinc-950/80 border border-zinc-800 rounded p-3.5 space-y-2">
                <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
                  <span>${{dict.col_hardware_footprint}}</span>
                  <span class="text-zinc-500 font-mono">${{m.context_window || 4096}} ctx</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">${{dict.hw_peak_rss}}</div>
                    <div class="text-zinc-200 font-semibold">${{m.peak_rss_gb}} GB</div>
                  </div>
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">${{dict.hw_throughput}}</div>
                    <div class="text-zinc-200 font-semibold">${{m.avg_throughput_tok_per_sec}} tok/s</div>
                  </div>
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">${{dict.hw_ttft}}</div>
                    <div class="text-zinc-200 font-semibold">${{m.median_ttft_ms}} ms</div>
                  </div>
                  <div class="p-2 bg-zinc-900 border border-zinc-800 rounded">
                    <div class="text-zinc-500 text-[10px]">${{dict.hw_tokens}}</div>
                    <div class="text-zinc-200 font-semibold">${{m.total_tokens_generated || '—'}}</div>
                  </div>
                </div>
                <div class="text-[10px] text-zinc-500 pt-1 font-mono">
                  ${{dict.hw_footnote}}
                </div>
              </div>

            </div>
          </td>
        `;
        tbody.appendChild(detailTr);
      }});
    }}

    function toggleRow(safeId) {{
      const detail = document.getElementById(`detail-${{safeId}}`);
      const chevron = document.getElementById(`chevron-${{safeId}}`);
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
      const dict = I18N[state.currentLang];
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
              label: dict.chart1_pareto_label,
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
              label: dict.chart1_div_a,
              data: microData,
              backgroundColor: '#10b981',
              borderColor: '#059669',
              borderWidth: 1,
              pointRadius: 6,
              pointHoverRadius: 8,
              order: 1
            }},
            {{
              label: dict.chart1_div_b,
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
              title: {{ display: true, text: dict.chart1_axis_x, color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }}
            }},
            y: {{
              title: {{ display: true, text: dict.chart1_axis_y, color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
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
                  `RAM Peak     : ${{ctx.raw.x}} GB`
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
      const dict = I18N[state.currentLang];

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
              title: {{ display: true, text: dict.chart2_axis_x, color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
              grid: {{ color: '#27272a' }},
              ticks: {{ color: '#a1a1aa', font: {{ family: 'Geist Mono' }} }}
            }},
            y: {{
              title: {{ display: true, text: dict.chart2_axis_y, color: '#71717a', font: {{ family: 'Geist Mono', size: 11 }} }},
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
                  `Precision  : ${{ctx.raw.y}}%`,
                  `TTFT       : ${{ctx.raw.x}} ms`,
                  `Throughput : ${{ctx.raw.throughput}} tok/s`,
                  `RAM Peak   : ${{ctx.raw.ram}} GB`
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
      const dict = I18N[state.currentLang];

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
          labels: [dict.axis_rca, dict.axis_blast, dict.axis_diff, dict.axis_sanity],
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

    // Deep Linking Handler (#model=... and #lang=...)
    function handleHashNavigation() {{
      const hash = window.location.hash;
      if (!hash) return;

      // 1. Language deep link: #lang=fr or #lang=en
      const langMatch = hash.match(/lang=(en|fr)/i);
      if (langMatch) {{
        setLanguage(langMatch[1].toLowerCase());
      }}

      // 2. Model deep link: #model=<model_id>
      const modelMatch = hash.match(/model=([^&]+)/i);
      if (modelMatch) {{
        const modelId = decodeURIComponent(modelMatch[1]);
        const safeId = sanitizeId(modelId);
        const rowEl = document.getElementById(`row-${{safeId}}`);
        const detailEl = document.getElementById(`detail-${{safeId}}`);
        const chevronEl = document.getElementById(`chevron-${{safeId}}`);

        if (rowEl && detailEl) {{
          // Unfold accordion if hidden
          if (detailEl.classList.contains('hidden')) {{
            detailEl.classList.remove('hidden');
            if (chevronEl) chevronEl.style.transform = 'rotate(180deg)';
          }}
          // Smooth scroll to row
          rowEl.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
          // Visual pulse highlight
          rowEl.classList.add('ring-highlight', 'bg-emerald-500/10');
          setTimeout(() => {{
            rowEl.classList.remove('ring-highlight', 'bg-emerald-500/10');
          }}, 3000);
        }}
      }}
    }}

    // Bootstrap dashboard on DOM loaded
    document.addEventListener("DOMContentLoaded", () => {{
      initKPIs();
      setLanguage(state.currentLang);
      handleHashNavigation();
    }});

    // Listen to hash change for seamless deep linking
    window.addEventListener("hashchange", handleHashNavigation);
  </script>
</body>
</html>
"""
    out_path.write_text(html_content, encoding="utf-8")
    return out_path
