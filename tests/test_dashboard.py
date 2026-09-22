"""Tests for dashboard and GitHub Markdown summary generation."""

from pathlib import Path
import pytest
from dashboard.generator import (
    generate_dashboard_html,
    generate_markdown_summary,
    load_all_telemetry,
)


@pytest.fixture
def mock_telemetry_dataset():
    return [
        {
            "model_id": "qwen-2.5-coder-3b-instruct",
            "division": "Micro-Edge",
            "safeops_index": 86.4,
            "factual_precision": 92.5,
            "safety_score": 100.0,
            "hallucination_rate_per_1k_tokens": 0.8,
            "peak_rss_gb": 2.1,
            "median_ttft_ms": 45.2,
            "avg_throughput_tok_per_sec": 52.4,
            "axis_scores": {"rca": 91.0, "blast_radius": 100.0, "surgical_diff": 95.0, "sanity_check": 100.0}
        },
        {
            "model_id": "qwen-2.5-coder-7b-instruct",
            "division": "Workstation",
            "safeops_index": 84.7,
            "factual_precision": 96.5,
            "safety_score": 100.0,
            "hallucination_rate_per_1k_tokens": 0.2,
            "peak_rss_gb": 5.4,
            "median_ttft_ms": 165.0,
            "avg_throughput_tok_per_sec": 26.2,
            "axis_scores": {"rca": 97.0, "blast_radius": 100.0, "surgical_diff": 98.0, "sanity_check": 100.0}
        }
    ]


def test_generate_dashboard_html_zero_cors(tmp_path: Path, mock_telemetry_dataset):
    out_html = tmp_path / "dashboard" / "index.html"
    res_path = generate_dashboard_html(mock_telemetry_dataset, out_html)

    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")

    # Critical requirement: Window.BENCH_DATA must be inlined
    assert "window.BENCH_DATA =" in content
    assert "qwen-2.5-coder-3b-instruct" in content
    assert "86.4" in content

    # Critical requirement: Zero AJAX fetch calls to local files
    assert "fetch(" not in content

    # Check chart components
    assert "efficiencyChart" in content
    assert "scatterChart" in content
    assert "axesChart" in content

    # Check Open Graph & Twitter meta tags
    assert 'meta property="og:image" content="https://safeops.jalal.tech/assets/og-preview.png"' in content
    assert 'meta name="twitter:card" content="summary_large_image"' in content
    assert 'meta name="twitter:image" content="https://safeops.jalal.tech/assets/og-preview.png"' in content

    # Check Personal Branding & GitHub repo
    assert 'href="https://jalal.tech"' in content
    assert 'href="https://github.com/dimaland1/SafeOps-Bench"' in content

    # Check Deep Linking, Open Data Export, and Hardware Provenance
    assert "handleHashNavigation" in content
    assert "exportTelemetryJSON" in content
    assert "Hardware Provenance:" in content


def test_generate_markdown_summary(tmp_path: Path, mock_telemetry_dataset):
    out_md = tmp_path / "RESULTS.md"
    res_path = generate_markdown_summary(mock_telemetry_dataset, out_md)

    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")

    assert "# SafeOps-Bench : Leaderboard Officiel" in content
    assert "| Rang | Modèle | Division | SafeOps Index |" in content
    assert "`qwen-2.5-coder-3b-instruct`" in content
    assert "**86.4**" in content
    assert "`qwen-2.5-coder-7b-instruct`" in content
