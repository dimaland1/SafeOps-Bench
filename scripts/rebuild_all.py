import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard.generator import load_all_telemetry, generate_dashboard_html, generate_markdown_summary

def main():
    telemetry = load_all_telemetry(Path("telemetry_output"))
    print(f"Loaded {len(telemetry)} profiles.")
    print(f"Top Model: {telemetry[0]['model_id']} (SafeOps Index V2: {telemetry[0]['safeops_index']})")
    
    generate_dashboard_html(telemetry, Path("dashboard/index.html"))
    generate_dashboard_html(telemetry, Path("docs/index.html"))
    generate_markdown_summary(telemetry, Path("RESULTS.md"))
    print("Successfully recompiled dashboard/index.html, docs/index.html, and RESULTS.md")

if __name__ == "__main__":
    main()
