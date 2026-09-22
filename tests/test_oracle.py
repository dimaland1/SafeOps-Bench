"""Tests validating the FishOracle SQLite database operations and flag detection."""

from pathlib import Path
import pytest
from bench.fish_oracle import FishOracle
from scripts.setup_oracle import bootstrap_database


@pytest.fixture(scope="module")
def oracle_db(tmp_path_factory) -> Path:
    temp_dir = tmp_path_factory.mktemp("oracle_test")
    db_path = temp_dir / "test_completions.sqlite"
    count = bootstrap_database(db_path)
    assert count > 0, "Bootstrap failed to seed database"
    return db_path


def test_oracle_known_commands(oracle_db: Path):
    oracle = FishOracle(oracle_db)
    assert oracle.is_known_command("du")
    assert oracle.is_known_command("tar")
    assert oracle.is_known_command("lsof")
    assert oracle.is_known_command("systemctl")
    assert not oracle.is_known_command("non_existent_binary_xyz")


def test_oracle_valid_flags(oracle_db: Path):
    oracle = FishOracle(oracle_db)
    # Valid flags
    assert oracle.is_valid_flag("du", "-h")
    assert oracle.is_valid_flag("du", "--max-depth")
    assert oracle.is_valid_flag("tar", "-x")
    assert oracle.is_valid_flag("tar", "--strip-components")
    assert oracle.is_valid_flag("lsof", "+L1")

    # Invalid / hallucinated flags
    assert not oracle.is_valid_flag("du", "--fake-hallucinated-size")
    assert not oracle.is_valid_flag("tar", "--auto-clean-everything")
    assert not oracle.is_valid_flag("nginx", "--force-restart-now")


def test_oracle_validate_command_flags(oracle_db: Path):
    oracle = FishOracle(oracle_db)
    tested_flags = ["-h", "--max-depth", "--invented-flag-abc", "-x"]
    valid, hallucinated = oracle.validate_command_flags("du", tested_flags)

    assert "-h" in valid
    assert "--max-depth" in valid
    assert "-x" in valid
    assert "--invented-flag-abc" in hallucinated
