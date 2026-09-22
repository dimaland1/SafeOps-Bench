import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench.evaluator import compute_safeops_index

def recalculate_all_telemetry():
    t_dir = Path("telemetry_output")
    files = sorted(t_dir.glob("*.json"))
    
    print(f"Recalculating SafeOps Index V2 for {len(files)} files in {t_dir}...")
    updated = []
    
    for jf in files:
        with jf.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        old_score = data.get("safeops_index", 0.0)
        new_score = compute_safeops_index(
            factual_precision=data.get("factual_precision", 0.0),
            safety_score=data.get("safety_score", 0.0),
            hallucination_rate=data.get("hallucination_rate_per_1k_tokens", 0.0),
            peak_rss_gb=data.get("peak_rss_gb", 4.0),
            median_ttft_ms=data.get("median_ttft_ms", 150.0)
        )
        
        data["safeops_index"] = new_score
        with jf.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        updated.append({
            "model_id": data["model_id"],
            "old_score": old_score,
            "new_score": new_score,
            "prec": data["factual_precision"],
            "ram": data["peak_rss_gb"],
            "ttft": data["median_ttft_ms"]
        })
        
    updated.sort(key=lambda x: x["new_score"], reverse=True)
    print(f"{'Rank':<4} | {'Model':<22} | {'New V2':>6} | {'Old V1':>6} | {'Prec':>5} | {'RAM':>5} | {'TTFT':>7}")
    print("-" * 68)
    for r, m in enumerate(updated, 1):
        print(f"{r:<4} | {m['model_id']:<22} | {m['new_score']:>6.2f} | {m['old_score']:>6.2f} | {m['prec']:>5.1f} | {m['ram']:>5.2f} | {m['ttft']:>7.1f}")

if __name__ == "__main__":
    recalculate_all_telemetry()
