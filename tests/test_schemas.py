"""Tests validating all dataset scenarios against Pydantic v2 schemas."""

from pathlib import Path
import pytest
from schemas.test_case import TestCase, EvaluationAxis


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def datasets_dir(repo_root: Path) -> Path:
    return repo_root / "datasets"


def test_rca_cases_schema(datasets_dir: Path):
    rca_file = datasets_dir / "rca_cases.json"
    assert rca_file.exists(), f"File {rca_file} not found"

    cases = TestCase.load_from_file(rca_file)
    assert len(cases) >= 3
    for case in cases:
        assert case.axis == EvaluationAxis.RCA
        assert case.id.startswith("SO-")
        assert len(case.expected_ground_truth) > 0
        assert case.context.strip() != ""


def test_blast_radius_cases_schema(datasets_dir: Path):
    blast_file = datasets_dir / "blast_radius_cases.json"
    assert blast_file.exists(), f"File {blast_file} not found"

    cases = TestCase.load_from_file(blast_file)
    assert len(cases) >= 2
    for case in cases:
        assert case.axis == EvaluationAxis.BLAST_RADIUS
        assert case.blast_radius is not None
        assert len(case.blast_radius.banned_tokens) > 0
        assert len(case.blast_radius.required_read_only_commands) > 0
        # Check setup_script fixture existence on SO-0104
        if case.id == "SO-0104":
            assert case.setup_script is not None
            assert "unlink" in case.setup_script


def test_diff_cases_schema(datasets_dir: Path):
    diff_file = datasets_dir / "diff_cases.json"
    assert diff_file.exists(), f"File {diff_file} not found"

    cases = TestCase.load_from_file(diff_file)
    assert len(cases) >= 2
    for case in cases:
        assert case.axis == EvaluationAxis.SURGICAL_DIFF
        assert len(case.expected_ground_truth) > 0


def test_sanity_cases_schema(datasets_dir: Path):
    sanity_file = datasets_dir / "sanity_cases.json"
    assert sanity_file.exists(), f"File {sanity_file} not found"

    cases = TestCase.load_from_file(sanity_file)
    assert len(cases) >= 2
    for case in cases:
        assert case.axis == EvaluationAxis.SANITY_CHECK
        assert case.validation is not None
        assert len(case.validation.syntax_flag) > 0
        assert case.validation.expected_exit_code == 0
