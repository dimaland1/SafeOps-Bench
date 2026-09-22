"""SafeOps-Bench Core Evaluation and AST Engine."""

from .tree_sitter_ast import extract_commands_from_script, normalize_flags
from .fish_oracle import FishOracle
from .telemetry import TelemetryCollector

__all__ = [
    "extract_commands_from_script",
    "normalize_flags",
    "FishOracle",
    "TelemetryCollector",
]
