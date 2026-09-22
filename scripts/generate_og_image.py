"""Generates a high-resolution (1200x630) Open Graph & Twitter Card preview image for SafeOps-Bench.
Renders the Pareto Frontier, certified hardware provenance (NVIDIA RTX 4090), and V2 Leaderboard.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def generate_og_image():
    # 1200x630 px at 100 dpi
    fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor('#09090b')
    ax.set_facecolor('#0c0c0e')

    # Data from certified 12-model RTX 4090 run under SafeOps Index V2
    models = [
        {"name": "ministral-3:3b", "ram": 2.54, "score": 59.85, "div": "micro", "p": 62.0},
        {"name": "qwen2.5-coder:7b", "ram": 4.42, "score": 54.13, "div": "ws", "p": 59.7},
        {"name": "qwen2.5:3b", "ram": 2.01, "score": 53.87, "div": "micro", "p": 53.9},
        {"name": "gemma2:2b", "ram": 1.79, "score": 49.80, "div": "micro", "p": 49.8},
        {"name": "phi4-mini:latest", "ram": 2.88, "score": 48.28, "div": "micro", "p": 53.3},
        {"name": "qwen2.5-coder:1.5b", "ram": 1.09, "score": 44.20, "div": "micro", "p": 45.1},
        {"name": "mistral:7b", "ram": 4.61, "score": 43.63, "div": "ws", "p": 47.8},
        {"name": "llama3.1:8b", "ram": 4.91, "score": 43.29, "div": "ws", "p": 49.4},
        {"name": "llama3.2:3b", "ram": 2.38, "score": 41.42, "div": "micro", "p": 44.4},
        {"name": "gemma2:9b", "ram": 5.83, "score": 35.80, "div": "ws", "p": 45.3},
        {"name": "deepseek-r1:1.5b", "ram": 1.27, "score": 24.04, "div": "micro", "p": 36.4},
        {"name": "deepseek-r1:7b", "ram": 4.78, "score": 21.24, "div": "ws", "p": 49.8},
    ]

    # Chart boundaries
    ax.set_xlim(0.5, 6.5)
    ax.set_ylim(15, 70)
    ax.set_position([0.08, 0.16, 0.58, 0.60])

    # Grid & Spines
    ax.grid(True, linestyle='--', color='#27272a', alpha=0.6, zorder=0)
    for spine in ax.spines.values():
        spine.set_color('#27272a')
        spine.set_linewidth(1.2)

    # Threshold 4GB line
    ax.axvline(x=4.0, color='#ef4444', linestyle=':', alpha=0.7, linewidth=1.5, zorder=1)
    ax.text(4.08, 18, '4 GB Bastion Threshold', color='#f87171', fontsize=9, fontfamily='monospace', weight='bold')

    # Scatter points
    micro_x = [m["ram"] for m in models if m["div"] == "micro"]
    micro_y = [m["score"] for m in models if m["div"] == "micro"]
    ws_x = [m["ram"] for m in models if m["div"] == "ws"]
    ws_y = [m["score"] for m in models if m["div"] == "ws"]

    ax.scatter(micro_x, micro_y, color='#10b981', s=130, edgecolors='#34d399', linewidths=1.5, zorder=4, label='Micro-Edge (<= 4 GB)')
    ax.scatter(ws_x, ws_y, color='#71717a', s=110, edgecolors='#a1a1aa', linewidths=1.5, zorder=4, label='Workstation (7B-9B)')

    # Label top models on chart
    for m in models:
        offset_y = 1.3
        offset_x = 0.08
        if m["name"] == "ministral-3:3b":
            ax.annotate(f"{m['name']} ({m['score']:.1f}) #1", (m["ram"], m["score"]),
                        xytext=(m["ram"] + offset_x, m["score"] + offset_y),
                        color='#34d399', fontsize=9.5, weight='bold', fontfamily='monospace')
        elif m["name"] in ["qwen2.5:3b", "gemma2:2b", "phi4-mini:latest"]:
            ax.annotate(f"{m['name']}", (m["ram"], m["score"]),
                        xytext=(m["ram"] + offset_x, m["score"] + offset_y),
                        color='#e4e4e7', fontsize=8, fontfamily='monospace')
        elif m["name"] == "qwen2.5-coder:7b":
            ax.annotate(f"{m['name']} ({m['score']:.1f})", (m["ram"], m["score"]),
                        xytext=(m["ram"] + offset_x, m["score"] + offset_y),
                        color='#a1a1aa', fontsize=8, fontfamily='monospace')

    # Axis labels
    ax.set_xlabel('Peak Memory RSS (GB)', color='#a1a1aa', fontsize=11, fontfamily='monospace', labelpad=8)
    ax.set_ylabel('SafeOps Index V2 (0-100)', color='#a1a1aa', fontsize=11, fontfamily='monospace', labelpad=8)
    ax.tick_params(colors='#a1a1aa', labelsize=10)

    # Legend
    legend = ax.legend(loc='upper right', facecolor='#18181b', edgecolor='#27272a', fontsize=9, framealpha=0.9)
    for text in legend.get_texts():
        text.set_color('#d4d4d8')

    # Title Banner (Top)
    fig.text(0.08, 0.92, "SafeOps-Bench", color='#ffffff', fontsize=22, weight='bold', fontfamily='sans-serif')
    fig.text(0.28, 0.925, "v0.2.0-beta", color='#10b981', fontsize=11, fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#064e3b', edgecolor='#059669', linewidth=1))
    fig.text(0.08, 0.865, "Deterministic SLM DevOps Benchmark * Zero LLM-as-a-Judge * SafeOps Index V2",
             color='#9ca3af', fontsize=12, fontfamily='sans-serif')

    # Right Side Summary Cards
    # Card 1: Certified Hardware
    card1 = patches.FancyBboxPatch((0.70, 0.64), 0.25, 0.20, transform=fig.transFigure,
                                  boxstyle="round,pad=0.015,rounding_size=0.02",
                                  facecolor='#121215', edgecolor='#27272a', linewidth=1.2)
    fig.patches.append(card1)
    fig.text(0.72, 0.80, "CERTIFIED HARDWARE", color='#71717a', fontsize=9, fontfamily='monospace', weight='bold')
    fig.text(0.72, 0.74, "NVIDIA RTX 4090", color='#10b981', fontsize=15, fontfamily='sans-serif', weight='bold')
    fig.text(0.72, 0.69, "24GB VRAM * Single Node * CUDA 12.8", color='#d4d4d8', fontsize=9, fontfamily='monospace')
    fig.text(0.72, 0.66, "RunPod Dedicated Environment", color='#a1a1aa', fontsize=8, fontfamily='sans-serif')

    # Card 2: Leaderboard Best (Ministral 3B)
    card2 = patches.FancyBboxPatch((0.70, 0.40), 0.25, 0.21, transform=fig.transFigure,
                                  boxstyle="round,pad=0.015,rounding_size=0.02",
                                  facecolor='#121215', edgecolor='#27272a', linewidth=1.2)
    fig.patches.append(card2)
    fig.text(0.72, 0.57, "TOP PRODUCTION COPILOT (#1)", color='#71717a', fontsize=9, fontfamily='monospace', weight='bold')
    fig.text(0.72, 0.51, "ministral-3:3b", color='#38bdf8', fontsize=14, fontfamily='monospace', weight='bold')
    fig.text(0.72, 0.46, "Index: 59.85 * Factual: 62.0%", color='#34d399', fontsize=10, fontfamily='monospace', weight='bold')
    fig.text(0.72, 0.42, "Safety: 100% * RAM: 2.54 GB * 88 tok/s", color='#a1a1aa', fontsize=9, fontfamily='monospace')

    # Card 3: Key Takeaway
    card3 = patches.FancyBboxPatch((0.70, 0.16), 0.25, 0.21, transform=fig.transFigure,
                                  boxstyle="round,pad=0.015,rounding_size=0.02",
                                  facecolor='#121215', edgecolor='#27272a', linewidth=1.2)
    fig.patches.append(card3)
    fig.text(0.72, 0.33, "REAL-WORLD BENCHMARK CRITERIA", color='#71717a', fontsize=9, fontfamily='monospace', weight='bold')
    fig.text(0.72, 0.27, "Capped RAM & TTFT Penalties", color='#f59e0b', fontsize=12, fontfamily='sans-serif', weight='bold')
    fig.text(0.72, 0.22, "Competence > Material Anorexia", color='#f59e0b', fontsize=12, fontfamily='sans-serif', weight='bold')
    fig.text(0.72, 0.18, "50 Incidents * 12 Models Tested", color='#a1a1aa', fontsize=9, fontfamily='monospace')

    # Footer Branding
    fig.text(0.08, 0.05, "https://safeops.jalal.tech", color='#34d399', fontsize=12, fontfamily='monospace', weight='bold')
    fig.text(0.38, 0.05, "- Created by Jalal Azouzout (AI Platform Engineer)", color='#d4d4d8', fontsize=11, fontfamily='sans-serif')
    fig.text(0.80, 0.05, "Apache-2.0", color='#71717a', fontsize=10, fontfamily='monospace')

    # Save to docs and dashboard
    docs_assets = Path("docs/assets")
    docs_assets.mkdir(parents=True, exist_ok=True)
    dash_assets = Path("dashboard/assets")
    dash_assets.mkdir(parents=True, exist_ok=True)

    out_docs = docs_assets / "og-preview.png"
    out_dash = dash_assets / "og-preview.png"

    plt.savefig(out_docs, dpi=100, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.savefig(out_dash, dpi=100, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    print(f"Generated OG image: {out_docs} ({out_docs.stat().st_size} bytes)")
    print(f"Generated OG image: {out_dash} ({out_dash.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_og_image()
