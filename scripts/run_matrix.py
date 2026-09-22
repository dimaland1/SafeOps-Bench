"""SafeOps-Bench Matrix Runner: automated, idempotent evaluation of the model matrix
with checkpoint resuming, strict per-case timeouts, and continuous dashboard/leaderboard recompilation.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bench.evaluator import BenchmarkEvaluator
from bench.runner import InferenceRunner
from dashboard.generator import (
    generate_dashboard_html,
    generate_markdown_summary,
    load_all_telemetry,
)

# Canonical benchmark matrix catalog
MODEL_CATALOG = {
    "micro-edge": [
        "qwen2.5:3b",
        "phi4-mini:latest",
        "qwen2.5-coder:1.5b",
        "ministral-3:3b",
        "llama3.2:3b",
        "gemma2:2b",
        "deepseek-r1:1.5b",
    ],
    "workstation": [
        "qwen2.5-coder:7b",
        "mistral:7b",
        "llama3.1:8b",
        "gemma2:9b",
        "deepseek-r1:7b",
    ],
}


def create_dry_run_generator(model_id: str):
    """Produces a deterministic mock generator for dry-run testing."""
    def mock_stream(prompt: str):
        p_lower = prompt.lower()
        # Simulate RCA response
        if "oomkilled" in p_lower or "exit code 137" in p_lower:
            yield "<think>Analyzing crashlog</think>\n```bash\n# Diagnostic: OOMKilled code 137 due to memory limit 512Mi\n```"
        elif "nginx" in p_lower and "syntax" in p_lower:
            yield "<think>Checking configuration</think>\n```bash\nnginx -t\n```"
        elif "diff" in p_lower or "patch" in p_lower:
            yield "```diff\n--- a/nginx.conf\n+++ b/nginx.conf\n@@ -1,3 +1,3 @@\n-worker_processes 1;\n+worker_processes auto;\n```"
        elif "nettoie" in p_lower or "disque" in p_lower or "disk" in p_lower:
            yield "<think>Need safe inspection first</think>\n```bash\ndu -sh /var/log/*\nlsof +L1\n```"
        else:
            yield "<think>Investigating system state</think>\n```bash\nsystemctl status\n```"
    return mock_stream


def run_matrix(
    models: Optional[List[str]] = None,
    division: str = "all",
    force: bool = False,
    dry_run: bool = False,
    timeout: int = 60,
    output_dir: Optional[Path] = None,
    dashboard_out: Optional[Path] = None,
    results_out: Optional[Path] = None,
):
    """Executes benchmark across selected models with checkpointing and real-time dashboard updates."""
    out_dir = Path(output_dir).resolve() if output_dir else (PROJECT_ROOT / "telemetry_output")
    dash_path = Path(dashboard_out).resolve() if dashboard_out else (PROJECT_ROOT / "dashboard" / "index.html")
    res_path = Path(results_out).resolve() if results_out else (PROJECT_ROOT / "RESULTS.md")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine list of models to evaluate
    if models and len(models) > 0:
        target_models = models
    elif division == "micro-edge":
        target_models = MODEL_CATALOG["micro-edge"]
    elif division == "workstation":
        target_models = MODEL_CATALOG["workstation"]
    else:  # "all"
        target_models = MODEL_CATALOG["micro-edge"] + MODEL_CATALOG["workstation"]

    print("=" * 76)
    print("SafeOps-Bench Matrix Runner 🛡️")
    print("=" * 76)
    print(f"Division target     : {division}")
    print(f"Candidate models    : {len(target_models)} -> {', '.join(target_models)}")
    print(f"Per-case timeout    : {timeout}s")
    print(f"Output directory    : {out_dir}")
    print(f"Dashboard target    : {dash_path}")
    print(f"Results target      : {res_path}")
    print(f"Dry-run mode        : {dry_run}")
    print(f"Force re-run        : {force}")
    print("=" * 76)
    print()

    # Pre-check Ollama availability if not in dry-run
    available_ollama_models = set()
    if not dry_run:
        try:
            import urllib.request
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with opener.open(req, timeout=3) as resp:
                tags_data = json.loads(resp.read().decode("utf-8"))
                for m in tags_data.get("models", []):
                    m_name = m.get("name", "")
                    available_ollama_models.add(m_name)
                    # Also register without tag if :latest
                    if ":latest" in m_name:
                        available_ollama_models.add(m_name.replace(":latest", ""))
                    if ":" in m_name:
                        available_ollama_models.add(m_name.split(":")[0])
        except Exception as e:
            print(f"[WARN] Could not connect to local Ollama daemon: {e}")

    evaluated_count = 0
    skipped_count = 0

    for idx, model_id in enumerate(target_models, 1):
        safe_model_id = re.sub(r'[^a-zA-Z0-9_\.-]', '_', model_id)
        report_file = out_dir / f"{safe_model_id}.json"

        # Checkpoint: skip if already evaluated and not --force
        if report_file.exists() and not force:
            print(f"[{idx}/{len(target_models)}] [SKIP] {model_id} already evaluated -> {report_file.name}")
            skipped_count += 1
            continue

        # Check model presence if not dry-run
        if not dry_run and available_ollama_models:
            is_avail = (
                model_id in available_ollama_models or
                any(model_id == m or m.startswith(model_id) for m in available_ollama_models)
            )
            if not is_avail:
                print(f"[{idx}/{len(target_models)}] [SKIP-UNAVAILABLE] {model_id} not present in Ollama. Pull it or use --dry-run.")
                skipped_count += 1
                continue

        print(f"[{idx}/{len(target_models)}] [RUN] Starting evaluation for {model_id}...")
        t_start = time.perf_counter()

        # Instantiate runner
        if dry_run:
            mock_stream = create_dry_run_generator(model_id)
            runner = InferenceRunner(
                model_id=model_id,
                custom_stream_generator=mock_stream
            )
        else:
            runner = InferenceRunner(model_id=model_id)

        evaluator = BenchmarkEvaluator(
            runner=runner,
            output_dir=out_dir,
            case_timeout=timeout
        )

        all_cases = evaluator.load_all_cases()
        print(f"       Loaded {len(all_cases)} evaluation cases. Running benchmark pipeline...")

        report = evaluator.evaluate_all(cases=all_cases)
        elapsed = time.perf_counter() - t_start

        print(
            f"       [DONE] in {elapsed:.1f}s | SafeOps Index: {report.safeops_index:.2f} | "
            f"Factual: {report.factual_precision:.1f}% | Safety: {report.safety_score:.1f}% | "
            f"RAM: {report.peak_rss_gb:.2f} GB | TTFT: {report.median_ttft_ms:.1f} ms"
        )
        evaluated_count += 1

        # Real-time dashboard & leaderboard recompilation after each model finishes
        telemetry_data = load_all_telemetry(out_dir)
        generate_dashboard_html(telemetry_data, dash_path)
        generate_markdown_summary(telemetry_data, res_path)
        print(f"       [SYNC] Recompiled {dash_path.name} and {res_path.name} ({len(telemetry_data)} models in leaderboard)\n")

    print("=" * 76)
    print("SafeOps-Bench Matrix Run Complete! 🎉")
    print(f"Evaluated: {evaluated_count} | Skipped: {skipped_count} | Total: {len(target_models)}")
    print(f"Dashboard : {dash_path}")
    print(f"Leaderboard: {res_path}")
    print("=" * 76)


def main():
    parser = argparse.ArgumentParser(
        description="SafeOps-Bench Matrix Runner: batch evaluation, checkpointing, and real-time dashboard updates."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Specific model name(s) or IDs to evaluate (e.g. --models qwen2.5:3b phi4-mini:latest)"
    )
    parser.add_argument(
        "--division",
        choices=["all", "micro-edge", "workstation"],
        default="all",
        help="Model division to target (default: all)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-evaluate models even if telemetry output JSON already exists"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in mock streaming mode without loading local LLM weights (useful for pipeline verification)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Per-case evaluation timeout in seconds (default: 60)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save telemetry JSON files (default: telemetry_output)"
    )
    parser.add_argument(
        "--dashboard-out",
        type=str,
        default=None,
        help="Path for generated HTML dashboard (default: dashboard/index.html)"
    )
    parser.add_argument(
        "--results-out",
        type=str,
        default=None,
        help="Path for generated markdown leaderboard (default: RESULTS.md)"
    )

    args = parser.parse_args()

    run_matrix(
        models=args.models,
        division=args.division,
        force=args.force,
        dry_run=args.dry_run,
        timeout=args.timeout,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        dashboard_out=Path(args.dashboard_out) if args.dashboard_out else None,
        results_out=Path(args.results_out) if args.results_out else None,
    )


if __name__ == "__main__":
    main()
