"""Telemetry and hardware footprint profiling for edge SLM evaluation."""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import psutil


class TelemetryCollector:
    """Profiles memory (RSS), latency (TTFT), throughput, and hardware metrics."""

    def __init__(self, model_id: str, output_dir: Optional[Path] = None):
        self.model_id = model_id
        if output_dir is None:
            project_root = Path(__file__).resolve().parent.parent
            self.output_dir = project_root / "telemetry_output"
        else:
            self.output_dir = Path(output_dir).resolve()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process = psutil.Process()
        self.start_time: float = 0.0
        self.first_token_time: Optional[float] = None
        self.end_time: float = 0.0
        self.peak_rss_bytes: int = 0
        self.tokens_generated: int = 0

    def start_measurement(self) -> None:
        """Start execution timer and initial memory sample."""
        self.start_time = time.perf_counter()
        self.first_token_time = None
        self.peak_rss_bytes = self.process.memory_info().rss
        self.tokens_generated = 0

    def record_first_token(self) -> None:
        """Record timestamp of first token emitted (TTFT)."""
        if self.first_token_time is None:
            self.first_token_time = time.perf_counter()
        self.sample_memory()

    def record_tokens(self, count: int) -> None:
        """Add to total generated tokens count."""
        self.tokens_generated += count
        self.sample_memory()

    def sample_memory(self) -> None:
        """Sample peak RSS memory."""
        rss = self.process.memory_info().rss
        if rss > self.peak_rss_bytes:
            self.peak_rss_bytes = rss

    def stop_measurement(self) -> Dict[str, Any]:
        """Stop measurement and compute final metrics."""
        self.end_time = time.perf_counter()
        self.sample_memory()

        total_duration = max(0.0001, self.end_time - self.start_time)
        ttft_ms = 0.0
        if self.first_token_time:
            ttft_ms = (self.first_token_time - self.start_time) * 1000.0

        throughput = self.tokens_generated / total_duration if self.tokens_generated > 0 else 0.0
        peak_rss_mb = round(self.peak_rss_bytes / (1024 * 1024), 2)
        peak_rss_gb = round(self.peak_rss_bytes / (1024 * 1024 * 1024), 3)

        report = {
            "model_id": self.model_id,
            "total_duration_sec": round(total_duration, 4),
            "ttft_ms": round(ttft_ms, 2),
            "tokens_generated": self.tokens_generated,
            "throughput_tok_per_sec": round(throughput, 2),
            "peak_rss_mb": peak_rss_mb,
            "peak_rss_gb": peak_rss_gb
        }

        # Save to telemetry_output
        report_file = self.output_dir / f"{self.model_id}.json"
        with report_file.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report
