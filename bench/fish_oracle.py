"""Fish Shell completions oracle for fast, deterministic CLI option validation."""

import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple


class FishOracle:
    """Deterministic ground-truth oracle for Linux CLI command flags."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent
            self.db_path = project_root / "data" / "completions.sqlite"
        else:
            self.db_path = Path(db_path).resolve()

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Oracle database not found at {self.db_path}. "
                f"Please run 'python scripts/setup_oracle.py' first."
            )

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def is_known_command(self, command: str) -> bool:
        """Check if command exists in the oracle database."""
        cmd = command.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM command_flags WHERE command = ? LIMIT 1",
                (cmd,)
            )
            return cursor.fetchone() is not None

    def get_known_flags(self, command: str) -> Set[str]:
        """Retrieve all verified flags for a given command."""
        cmd = command.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT flag FROM command_flags WHERE command = ?",
                (cmd,)
            )
            return {row[0] for row in cursor.fetchall()}

    def is_valid_flag(self, command: str, flag: str) -> bool:
        """Check whether a specific flag is officially valid for the command."""
        cmd = command.strip().lower()
        f = flag.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM command_flags WHERE command = ? AND flag = ? LIMIT 1",
                (cmd, f)
            )
            return cursor.fetchone() is not None

    def validate_command_flags(
        self, command: str, flags: Iterable[str]
    ) -> Tuple[List[str], List[str]]:
        """Splits an iterable of flags into (valid_flags, hallucinated_flags).
        If the command is unknown to the oracle, flags are not penalized.
        """
        cmd = command.strip().lower()
        known_flags = self.get_known_flags(cmd)
        if not known_flags:
            # Command not in oracle database, pass through
            return list(flags), []

        valid = []
        hallucinated = []
        for flag in flags:
            if flag in known_flags:
                valid.append(flag)
            else:
                hallucinated.append(flag)
        return valid, hallucinated
