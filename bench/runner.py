"""Streaming inference runner with high-precision TTFT, DeepSeek-R1 <think> isolation,
and recursive process tree RSS memory profiling.
Supports llama-cpp-python, direct Ollama streaming, and custom generators.
"""

import json
import re
import threading
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterator, Optional, Tuple
import psutil

# Check if llama_cpp is available
_HAS_LLAMA_CPP = False
try:
    import llama_cpp
    _HAS_LLAMA_CPP = True
except ImportError:
    _HAS_LLAMA_CPP = False


@dataclass
class InferenceResult:
    """Detailed output and telemetry from a single model inference run."""
    model_id: str
    raw_output: str
    thinking_content: str
    clean_payload: str
    ttft_ms: float
    total_duration_sec: float
    tokens_generated: int
    throughput_tok_per_sec: float
    peak_rss_mb: float
    peak_rss_gb: float
    context_window_used: int


class RSSMonitor:
    """Threaded sampler measuring peak RSS of process and all recursive children,
    including Ollama daemon processes when running in Ollama mode.
    """

    def __init__(self, interval_sec: float = 0.01, track_ollama: bool = False):
        self.interval = interval_sec
        self.track_ollama = track_ollama
        self.proc = psutil.Process()
        self.peak_rss_bytes: int = 0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _sample_total_rss(self) -> int:
        try:
            total = self.proc.memory_info().rss
            for child in self.proc.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if self.track_ollama:
                for p in psutil.process_iter(['name', 'memory_info']):
                    try:
                        pname = (p.info['name'] or '').lower()
                        if 'ollama' in pname:
                            total += p.info['memory_info'].rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            return total
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            current_rss = self._sample_total_rss()
            if current_rss > self.peak_rss_bytes:
                self.peak_rss_bytes = current_rss
            time.sleep(self.interval)

    def start(self):
        self.peak_rss_bytes = self._sample_total_rss()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> int:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        final_sample = self._sample_total_rss()
        if final_sample > self.peak_rss_bytes:
            self.peak_rss_bytes = final_sample
        return self.peak_rss_bytes


def extract_thinking_and_payload(raw_text: str) -> Tuple[str, str]:
    """Resiliently extracts reasoning (<think>...</think>) and operational payload.
    Handles:
      1. Normal closed <think>...</think> blocks.
      2. Unclosed <think>... blocks where max_tokens cut off generation.
      3. Markdown code fence extraction (```bash ... ``` or ```diff ... ```).
    """
    if not raw_text:
        return "", ""

    thinking_content = ""
    clean_payload = ""

    # Case 1: Closed <think> tag
    think_match = re.search(r"<think>(.*?)</think>", raw_text, flags=re.DOTALL)
    if think_match:
        thinking_content = think_match.group(1).strip()
        clean_payload = raw_text[think_match.end():].strip()
    # Case 2: Unclosed <think> tag (e.g. truncated generation)
    elif "<think>" in raw_text:
        parts = raw_text.split("<think>", 1)
        body = parts[1]
        # Look for code block start which signals the transition from thought to code
        code_match = re.search(r"(```(?:bash|sh|diff|json)?\s*\n.*)", body, flags=re.DOTALL)
        if code_match:
            thinking_content = body[:code_match.start()].strip()
            clean_payload = code_match.group(1).strip()
        else:
            # Entire generation was thought
            thinking_content = body.strip()
            clean_payload = ""
    else:
        # No think tags
        clean_payload = raw_text.strip()

    # Further isolate operational payload if code fences are present
    all_fences = re.findall(r"```(?:bash|sh|diff|json)?\s*\n(.*?)\n```", clean_payload, flags=re.DOTALL)
    if all_fences:
        clean_payload = "\n".join(f.strip() for f in all_fences)
    else:
        # Fallback to single unclosed fence if present
        fence_match = re.search(r"```(?:bash|sh|diff|json)?\s*\n(.*)", clean_payload, flags=re.DOTALL)
        if fence_match:
            candidate = fence_match.group(1).strip()
            if candidate.endswith("```"):
                candidate = candidate[:-3].strip()
            clean_payload = candidate

    return thinking_content, clean_payload


class InferenceRunner:
    """Manages model loading, dynamic context windows, token streaming, and metrics."""

    def __init__(
        self,
        model_id: str,
        model_path: Optional[Path] = None,
        context_window: Optional[int] = None,
        grammar_path: Optional[Path] = None,
        custom_stream_generator: Optional[Callable[[str], Iterator[str]]] = None,
        ollama_url: Optional[str] = "http://127.0.0.1:11434"
    ):
        self.model_id = model_id
        self.model_path = Path(model_path).resolve() if model_path else None
        self.grammar_path = Path(grammar_path).resolve() if grammar_path else None
        self.custom_stream_generator = custom_stream_generator
        self.ollama_url = ollama_url.rstrip("/") if ollama_url else None
        self.backend = "mock"

        # Dynamic context window calculation
        if context_window is not None:
            self.context_window = context_window
        elif "r1" in model_id.lower() or "deepseek" in model_id.lower():
            # Mandatory 8k floor for DeepSeek-R1 Distill models
            self.context_window = 8192
        else:
            # Standard 4k default
            self.context_window = 4096

        self._llm = None
        self._grammar = None
        self._init_engine()

    def _is_ollama_model_available(self) -> bool:
        """Verifies if the specified model is reachable in local Ollama daemon."""
        if not self.ollama_url:
            return False
        try:
            # Explicitly empty proxy to prevent Windows Docker Desktop proxy loop
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            req = urllib.request.Request(f"{self.ollama_url}/api/tags")
            with opener.open(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                for m in models:
                    if self.model_id == m or self.model_id == m.split(":")[0] or m.startswith(self.model_id):
                        return True
                return False
        except Exception:
            return False

    def _get_ollama_memory_bytes(self) -> int:
        """Queries Ollama /api/ps to extract exact model size in memory (RAM/VRAM)."""
        if not self.ollama_url:
            return 0
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            req = urllib.request.Request(f"{self.ollama_url}/api/ps")
            with opener.open(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    m_name = m.get("name", "")
                    if self.model_id in m_name or m_name in self.model_id:
                        return m.get("size", 0) or m.get("size_vram", 0)
        except Exception:
            pass
        return 0

    def _init_engine(self):
        """Initializes backend: custom generator, llama_cpp, or local Ollama streaming."""
        if self.custom_stream_generator:
            self.backend = "custom"
            return

        if _HAS_LLAMA_CPP and self.model_path and self.model_path.exists():
            self.backend = "llama_cpp"
            self._llm = llama_cpp.Llama(
                model_path=str(self.model_path),
                n_ctx=self.context_window,
                n_batch=512,
                verbose=False
            )
            if self.grammar_path and self.grammar_path.exists():
                self._grammar = llama_cpp.LlamaGrammar.from_file(str(self.grammar_path))
            return

        if self._is_ollama_model_available():
            self.backend = "ollama"
            return

        self.backend = "mock"

    def _ollama_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.2
    ) -> Iterator[str]:
        """Streams tokens from local Ollama HTTP generate endpoint."""
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.context_window,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with opener.open(req, timeout=120) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    chunk = json.loads(line_str)
                    tok = chunk.get("response", "")
                    if tok:
                        yield tok
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    def run_inference(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.2
    ) -> InferenceResult:
        """Executes streaming inference, records TTFT, captures memory, and returns metrics."""
        monitor = RSSMonitor(track_ollama=(self.backend == "ollama"))
        monitor.start()

        full_prompt = prompt
        if system_prompt and self.backend != "ollama":
            full_prompt = f"{system_prompt}\n\n{prompt}"

        tokens_accumulated = []
        ttft_ms = 0.0
        start_time = time.perf_counter()
        first_token_time: Optional[float] = None

        # Select stream source
        stream_iter: Iterator[str]
        if self.custom_stream_generator:
            stream_iter = self.custom_stream_generator(full_prompt)
        elif self.backend == "ollama":
            stream_iter = self._ollama_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
        elif self._llm:
            raw_stream = self._llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                grammar=self._grammar
            )
            def _llama_cpp_stream():
                for chunk in raw_stream:
                    token_text = chunk["choices"][0]["text"]
                    yield token_text
            stream_iter = _llama_cpp_stream()
        else:
            # Fallback mock for testing / unequipped environments
            def _dummy_stream():
                sample = f"```bash\n# Simulated payload for {self.model_id}\ndu -sh /var/*\n```"
                for word in sample.split(" "):
                    time.sleep(0.005)
                    yield word + " "
            stream_iter = _dummy_stream()

        # Stream tokens
        for token in stream_iter:
            if first_token_time is None and token.strip():
                first_token_time = time.perf_counter()
                ttft_ms = (first_token_time - start_time) * 1000.0
            tokens_accumulated.append(token)

        end_time = time.perf_counter()
        peak_rss_bytes = monitor.stop()

        # Augment with Ollama model size from /api/ps if using Ollama
        if self.backend == "ollama":
            ollama_size = self._get_ollama_memory_bytes()
            if ollama_size > peak_rss_bytes:
                peak_rss_bytes = ollama_size

        total_duration = max(0.0001, end_time - start_time)
        raw_output = "".join(tokens_accumulated)
        token_count = len(tokens_accumulated)
        throughput = token_count / total_duration if token_count > 0 else 0.0

        thinking, clean_payload = extract_thinking_and_payload(raw_output)

        peak_rss_mb = round(peak_rss_bytes / (1024 * 1024), 2)
        peak_rss_gb = round(peak_rss_bytes / (1024 * 1024 * 1024), 3)

        return InferenceResult(
            model_id=self.model_id,
            raw_output=raw_output,
            thinking_content=thinking,
            clean_payload=clean_payload,
            ttft_ms=round(ttft_ms, 2),
            total_duration_sec=round(total_duration, 4),
            tokens_generated=token_count,
            throughput_tok_per_sec=round(throughput, 2),
            peak_rss_mb=peak_rss_mb,
            peak_rss_gb=peak_rss_gb,
            context_window_used=self.context_window
        )
