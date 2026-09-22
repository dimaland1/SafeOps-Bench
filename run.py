"""SafeOps-Bench Unified CLI Entrypoint.
Orchestrates live evaluation, realistic multi-model mock generation, and static dashboard compilation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from bench.evaluator import BenchmarkEvaluator, ModelEvaluationReport, compute_safeops_index
from bench.runner import InferenceRunner
from bench.fish_oracle import FishOracle
from bench.sandbox import SandboxRunner
from dashboard.generator import (
    generate_dashboard_html,
    generate_markdown_summary,
    load_all_telemetry,
)

# Realistic multi-model mock catalog for Phase 3 benchmarking and dashboard rendering
MOCK_MODELS_DATA: List[Dict[str, Any]] = [
    # Division A: Micro-Edge (≤4B, low RAM, fast TTFT)
    {
        "model_id": "qwen-2.5-coder-3b-instruct",
        "division": "Micro-Edge",
        "factual_precision": 92.5,
        "safety_score": 100.0,
        "hallucination_rate_per_1k_tokens": 0.8,
        "peak_rss_mb": 2150.0,
        "peak_rss_gb": 2.1,
        "median_ttft_ms": 45.2,
        "avg_throughput_tok_per_sec": 52.4,
        "total_tokens_generated": 1420,
        "context_window": 4096,
        "cases_passed": 9,
        "total_cases": 9,
        "axis_scores": {"rca": 91.0, "blast_radius": 100.0, "surgical_diff": 95.0, "sanity_check": 100.0}
    },
    {
        "model_id": "phi-4-mini-instruct",
        "division": "Micro-Edge",
        "factual_precision": 88.0,
        "safety_score": 95.0,
        "hallucination_rate_per_1k_tokens": 1.2,
        "peak_rss_mb": 2660.0,
        "peak_rss_gb": 2.6,
        "median_ttft_ms": 58.1,
        "avg_throughput_tok_per_sec": 44.1,
        "total_tokens_generated": 1380,
        "context_window": 4096,
        "cases_passed": 8,
        "total_cases": 9,
        "axis_scores": {"rca": 93.0, "blast_radius": 95.0, "surgical_diff": 80.0, "sanity_check": 90.0}
    },
    {
        "model_id": "deepseek-r1-distill-qwen-1.5b",
        "division": "Micro-Edge",
        "factual_precision": 87.0,
        "safety_score": 95.0,
        "hallucination_rate_per_1k_tokens": 1.5,
        "peak_rss_mb": 1430.0,
        "peak_rss_gb": 1.4,
        "median_ttft_ms": 112.5,
        "avg_throughput_tok_per_sec": 38.6,
        "total_tokens_generated": 2150,
        "context_window": 8192,
        "cases_passed": 8,
        "total_cases": 9,
        "axis_scores": {"rca": 96.0, "blast_radius": 95.0, "surgical_diff": 75.0, "sanity_check": 85.0}
    },
    {
        "model_id": "gemma-2-2.6b-it",
        "division": "Micro-Edge",
        "factual_precision": 85.0,
        "safety_score": 92.0,
        "hallucination_rate_per_1k_tokens": 1.6,
        "peak_rss_mb": 1940.0,
        "peak_rss_gb": 1.9,
        "median_ttft_ms": 38.4,
        "avg_throughput_tok_per_sec": 61.2,
        "total_tokens_generated": 1290,
        "context_window": 4096,
        "cases_passed": 7,
        "total_cases": 9,
        "axis_scores": {"rca": 88.0, "blast_radius": 92.0, "surgical_diff": 75.0, "sanity_check": 85.0}
    },
    {
        "model_id": "llama-3.2-3b-instruct",
        "division": "Micro-Edge",
        "factual_precision": 82.5,
        "safety_score": 90.0,
        "hallucination_rate_per_1k_tokens": 2.1,
        "peak_rss_mb": 2250.0,
        "peak_rss_gb": 2.2,
        "median_ttft_ms": 48.0,
        "avg_throughput_tok_per_sec": 54.0,
        "total_tokens_generated": 1310,
        "context_window": 4096,
        "cases_passed": 7,
        "total_cases": 9,
        "axis_scores": {"rca": 84.0, "blast_radius": 90.0, "surgical_diff": 70.0, "sanity_check": 80.0}
    },

    # Division B: Workstation Grade (7B–9B, high memory, higher precision)
    {
        "model_id": "qwen-2.5-coder-7b-instruct",
        "division": "Workstation",
        "factual_precision": 96.5,
        "safety_score": 100.0,
        "hallucination_rate_per_1k_tokens": 0.2,
        "peak_rss_mb": 5520.0,
        "peak_rss_gb": 5.4,
        "median_ttft_ms": 165.0,
        "avg_throughput_tok_per_sec": 26.2,
        "total_tokens_generated": 1510,
        "context_window": 4096,
        "cases_passed": 9,
        "total_cases": 9,
        "axis_scores": {"rca": 97.0, "blast_radius": 100.0, "surgical_diff": 98.0, "sanity_check": 100.0}
    },
    {
        "model_id": "deepseek-r1-distill-qwen-7b",
        "division": "Workstation",
        "factual_precision": 96.0,
        "safety_score": 98.0,
        "hallucination_rate_per_1k_tokens": 0.3,
        "peak_rss_mb": 5930.0,
        "peak_rss_gb": 5.8,
        "median_ttft_ms": 285.0,
        "avg_throughput_tok_per_sec": 21.0,
        "total_tokens_generated": 2840,
        "context_window": 8192,
        "cases_passed": 9,
        "total_cases": 9,
        "axis_scores": {"rca": 99.0, "blast_radius": 98.0, "surgical_diff": 92.0, "sanity_check": 95.0}
    },
    {
        "model_id": "llama-3.1-8b-instruct",
        "division": "Workstation",
        "factual_precision": 91.0,
        "safety_score": 96.0,
        "hallucination_rate_per_1k_tokens": 0.9,
        "peak_rss_mb": 6240.0,
        "peak_rss_gb": 6.1,
        "median_ttft_ms": 192.0,
        "avg_throughput_tok_per_sec": 24.5,
        "total_tokens_generated": 1450,
        "context_window": 4096,
        "cases_passed": 8,
        "total_cases": 9,
        "axis_scores": {"rca": 92.0, "blast_radius": 96.0, "surgical_diff": 85.0, "sanity_check": 90.0}
    },
    {
        "model_id": "mistral-7b-instruct-v0.3",
        "division": "Workstation",
        "factual_precision": 89.0,
        "safety_score": 94.0,
        "hallucination_rate_per_1k_tokens": 1.1,
        "peak_rss_mb": 5730.0,
        "peak_rss_gb": 5.6,
        "median_ttft_ms": 178.0,
        "avg_throughput_tok_per_sec": 25.8,
        "total_tokens_generated": 1400,
        "context_window": 4096,
        "cases_passed": 8,
        "total_cases": 9,
        "axis_scores": {"rca": 90.0, "blast_radius": 94.0, "surgical_diff": 82.0, "sanity_check": 88.0}
    },
    {
        "model_id": "gemma-2-9b-it",
        "division": "Workstation",
        "factual_precision": 92.0,
        "safety_score": 93.0,
        "hallucination_rate_per_1k_tokens": 0.8,
        "peak_rss_mb": 6960.0,
        "peak_rss_gb": 6.8,
        "median_ttft_ms": 215.0,
        "avg_throughput_tok_per_sec": 22.0,
        "total_tokens_generated": 1490,
        "context_window": 4096,
        "cases_passed": 8,
        "total_cases": 9,
        "axis_scores": {"rca": 93.0, "blast_radius": 93.0, "surgical_diff": 88.0, "sanity_check": 92.0}
    }
]


def populate_mock_telemetry(output_dir: Path) -> List[Dict[str, Any]]:
    """Computes exact SafeOps Index for each mock model and writes JSON telemetry."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    for item in MOCK_MODELS_DATA:
        score = compute_safeops_index(
            factual_precision=item["factual_precision"],
            safety_score=item["safety_score"],
            hallucination_rate=item["hallucination_rate_per_1k_tokens"],
            peak_rss_gb=item["peak_rss_gb"]
        )
        record = dict(item)
        record["safeops_index"] = score
        record["case_results"] = []

        out_file = output_dir / f"{record['model_id']}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        generated.append(record)

    return generated


def main():
    parser = argparse.ArgumentParser(
        description="SafeOps-Bench: Deterministic Benchmark for Non-Invasive DevOps Companions."
    )
    parser.add_argument("--model", type=str, help="Specific model ID to evaluate")
    parser.add_argument("--model-path", type=str, help="Path to GGUF model weights file")
    parser.add_argument("--case", type=str, help="Specific case ID to evaluate (e.g. SO-0104)")
    parser.add_argument("--ollama-url", type=str, default="http://127.0.0.1:11434", help="Ollama daemon API URL")
    parser.add_argument("--division", choices=["all", "micro-edge", "workstation"], default="all")
    parser.add_argument("--mock", action="store_true", help="Generate realistic multi-model mock telemetry for the 2026 leaderboard")
    parser.add_argument("--generate-dashboard", action="store_true", help="Render dashboard/index.html and RESULTS.md from telemetry")
    parser.add_argument("--output-dir", type=str, default="telemetry_output", help="Directory for telemetry outputs")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    telemetry_dir = project_root / args.output_dir
    dashboard_html = project_root / "dashboard" / "index.html"
    results_md = project_root / "RESULTS.md"

    print("=" * 70)
    print("🛡️  SafeOps-Bench CLI — Autonomous Evaluation Engine")
    print("=" * 70)

    if args.mock:
        print(f"[SafeOps] Seeding realistic mock evaluation dataset ({len(MOCK_MODELS_DATA)} models)...")
        models = populate_mock_telemetry(telemetry_dir)
        print(f"[SafeOps] Generated {len(models)} telemetry profiles in {telemetry_dir}")

    elif args.model:
        model_id = args.model
        print(f"[SafeOps] Initializing evaluation for model: {model_id}...")
        runner = InferenceRunner(
            model_id=model_id,
            model_path=Path(args.model_path) if args.model_path else None,
            ollama_url=args.ollama_url
        )
        oracle = FishOracle()
        sandbox = SandboxRunner()
        evaluator = BenchmarkEvaluator(runner=runner, oracle=oracle, sandbox=sandbox, output_dir=telemetry_dir)

        target_cases = None
        if args.case:
            all_cases = evaluator.load_all_cases()
            target_cases = [c for c in all_cases if c.id.lower() == args.case.lower()]
            if not target_cases:
                print(f"[SafeOps] ❌ Error: Case '{args.case}' not found in any dataset.")
                sys.exit(1)
            print(f"[SafeOps] 🎯 Filtered execution to case: {target_cases[0].id} - {target_cases[0].title}")

        report = evaluator.evaluate_all(cases=target_cases)
        print("=" * 70)
        print(f"[SafeOps] ✅ Evaluation complete: {report.model_id}")
        print(f"[SafeOps] 📊 SafeOps Index        : {report.safeops_index} / 100.0")
        print(f"[SafeOps] 🎯 Factual Precision    : {report.factual_precision}%")
        print(f"[SafeOps] 🛡️ Safety Score         : {report.safety_score}%")
        print(f"[SafeOps] ⚡ Median TTFT          : {report.median_ttft_ms} ms")
        print(f"[SafeOps] 🚀 Avg Throughput       : {report.avg_throughput_tok_per_sec} tok/sec")
        print(f"[SafeOps] 💾 Peak RSS / VRAM      : {report.peak_rss_mb} MB ({report.peak_rss_gb} GB)")
        print(f"[SafeOps] 🏷️ Division             : {report.division}")
        print(f"[SafeOps] 📈 Passed Cases         : {report.cases_passed}/{report.total_cases}")
        print("=" * 70)

        if args.case and report.case_results:
            cr = report.case_results[0]
            print(f"[SafeOps] Details for {cr['case_id']}:")
            print(f"  • Safe Execution : {cr['executed_safely']}")
            print(f"  • Diagnostic     : {cr['details']}")
            print(f"  • Payload Output :\n{cr['raw_payload']}")

    if args.generate_dashboard or args.mock:
        print(f"[SafeOps] Compiling static dashboard and GitHub leaderboard...")
        data = load_all_telemetry(telemetry_dir)
        if not data:
            print(f"[SafeOps] Warning: No telemetry files found in {telemetry_dir}.")
            sys.exit(0)

        html_path = generate_dashboard_html(data, dashboard_html)
        md_path = generate_markdown_summary(data, results_md)

        print(f"[SafeOps] ✅ HTML Dashboard generated : {html_path}")
        print(f"[SafeOps] ✅ GitHub Markdown summary  : {md_path}")
        print(f"[SafeOps] Top Model : {data[0]['model_id']} (SafeOps Index: {data[0]['safeops_index']})")


if __name__ == "__main__":
    main()
