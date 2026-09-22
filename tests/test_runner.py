"""Tests for InferenceRunner: dynamic context, TTFT streaming, <think> isolation, and RSS tracking."""

import time
import pytest
from bench.runner import (
    InferenceRunner,
    InferenceResult,
    RSSMonitor,
    extract_thinking_and_payload,
)


def test_dynamic_context_window_allocation():
    # DeepSeek-R1 Distill variants must have forced 8192 context window floor
    r1_runner = InferenceRunner(model_id="deepseek-r1-distill-qwen-1.5b")
    assert r1_runner.context_window == 8192

    r1_llama_runner = InferenceRunner(model_id="DeepSeek-R1-Distill-Llama-8B")
    assert r1_llama_runner.context_window == 8192

    # Standard instruct models default to 4096
    qwen_runner = InferenceRunner(model_id="qwen-2.5-coder-3b-instruct")
    assert qwen_runner.context_window == 4096

    gemma_runner = InferenceRunner(model_id="gemma-2-2.6b-it")
    assert gemma_runner.context_window == 4096

    # Custom override
    custom_runner = InferenceRunner(model_id="custom-model", context_window=16384)
    assert custom_runner.context_window == 16384


def test_extract_thinking_closed_tag():
    raw = "<think>\nAnalyzing the issue with Nginx...\nRoot cause is SAN mismatch.\n</think>\n```bash\nopenssl s_client -connect 127.0.0.1:443\n```"
    thinking, payload = extract_thinking_and_payload(raw)
    assert "Analyzing the issue with Nginx..." in thinking
    assert "SAN mismatch" in thinking
    assert payload == "openssl s_client -connect 127.0.0.1:443"


def test_extract_thinking_unclosed_tag_resilience():
    # Truncated by max_tokens before </think> is closed
    raw = "<think>\nInvestigating disk saturation on /var\nNeed to inspect open files\n```bash\nlsof +L1\n```"
    thinking, payload = extract_thinking_and_payload(raw)
    assert "Investigating disk saturation" in thinking
    assert payload == "lsof +L1"


def test_extract_thinking_no_tags():
    raw = "```bash\njournalctl -u nginx -n 50 --no-pager\n```"
    thinking, payload = extract_thinking_and_payload(raw)
    assert thinking == ""
    assert payload == "journalctl -u nginx -n 50 --no-pager"


def test_extract_raw_command_without_fences():
    raw = "du -sh /var/*"
    thinking, payload = extract_thinking_and_payload(raw)
    assert thinking == ""
    assert payload == "du -sh /var/*"


def test_rss_monitor():
    monitor = RSSMonitor(interval_sec=0.01)
    monitor.start()
    time.sleep(0.05)
    # Allocate a temporary buffer to ensure RSS is detected
    buf = [0] * (1024 * 1024)
    time.sleep(0.02)
    peak = monitor.stop()
    del buf
    assert peak > 0


def test_runner_streaming_ttft_and_metrics():
    # Mock generator simulating streaming chunks with delays
    def mock_stream(prompt: str):
        chunks = [
            "<think>\nProcessing prompt: ",
            f"{prompt[:10]}...\n",
            "</think>\n",
            "```bash\n",
            "ps aux --sort=-%cpu | head -n 5\n",
            "```"
        ]
        for c in chunks:
            time.sleep(0.01)
            yield c

    runner = InferenceRunner(
        model_id="deepseek-r1-distill-qwen-1.5b",
        custom_stream_generator=mock_stream
    )

    result = runner.run_inference(prompt="Investigate runaway CPU usage")

    assert isinstance(result, InferenceResult)
    assert result.ttft_ms > 0.0
    assert result.tokens_generated == 6
    assert result.throughput_tok_per_sec > 0.0
    assert result.peak_rss_mb > 0.0
    assert "Processing prompt" in result.thinking_content
    assert result.clean_payload == "ps aux --sort=-%cpu | head -n 5"
    assert result.context_window_used == 8192
