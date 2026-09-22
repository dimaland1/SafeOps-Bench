"""Canonical data contracts for SafeOps-Bench evaluation scenarios."""

from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvaluationAxis(str, Enum):
    """The 4 standardized pillars of non-invasive DevOps evaluation."""
    RCA = "rca"
    BLAST_RADIUS = "blast_radius"
    SURGICAL_DIFF = "surgical_diff"
    SANITY_CHECK = "sanity_check"


class BlastRadiusRule(BaseModel):
    """Safety and blast-radius constraints for high-pressure scenarios."""
    model_config = ConfigDict(extra="forbid")

    banned_tokens: List[str] = Field(
        description="Destructive or mutagenic commands strictly prohibited (e.g., rm -rf, reboot, kill -9)"
    )
    required_read_only_commands: List[str] = Field(
        default_factory=list,
        description="Safe read-only inspection commands expected (e.g., du, lsof, journalctl, ncdu)"
    )
    allow_privileged_execution: bool = Field(
        default=False,
        description="Whether sudo or root execution is permitted for safe introspection"
    )


class StaticValidationTarget(BaseModel):
    """Syntax check and dry-run expectations prior to reloading services."""
    model_config = ConfigDict(extra="forbid")

    tool: str = Field(description="Target CLI tool (e.g., nginx, sshd, visudo, bash)")
    syntax_flag: str = Field(description="Mandatory syntax check or test flag (e.g., -t, -c)")
    expected_exit_code: int = Field(
        default=0,
        description="Expected exit code of the validation command"
    )


class TestCase(BaseModel):
    """Complete specification of a single benchmark evaluation scenario."""
    __test__ = False  # Prevent pytest from treating this data model as a test class
    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        pattern=r"^SO-[0-9]{4}$",
        description="Unique identifier in format SO-XXXX"
    )
    axis: EvaluationAxis = Field(description="Target evaluation axis")
    title: str = Field(description="Short human-readable title of the scenario")
    context: str = Field(description="Raw logs, existing configuration, or incident state")
    prompt: str = Field(description="User prompt submitted to the model")
    setup_script: Optional[str] = Field(
        default=None,
        description="State fixture: bash/python script executed in sandbox prior to evaluation to inject the fault"
    )
    blast_radius: Optional[BlastRadiusRule] = Field(
        default=None,
        description="Safety rules for Axe 2 scenarios"
    )
    validation: Optional[StaticValidationTarget] = Field(
        default=None,
        description="Mandatory dry-run check for Axe 4 scenarios"
    )
    expected_ground_truth: List[str] = Field(
        default_factory=list,
        description="Expected factual tokens, error codes, diff chunks, or diagnostic paths"
    )
    os_target: str = Field(
        default="ubuntu:24.04",
        description="Target distribution environment for verification"
    )

    @classmethod
    def load_from_file(cls, file_path: Path) -> List["TestCase"]:
        """Load and validate a list of test cases from a JSON file using pathlib.Path."""
        import json
        resolved_path = Path(file_path).resolve()
        with resolved_path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [cls.model_validate(item) for item in raw_data]
