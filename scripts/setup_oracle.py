"""Autonomous database bootstrapper for SafeOps-Bench CLI flag oracle.
Generates data/completions.sqlite with zero external dependencies across Windows, Linux, and macOS.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List

# Core verified seed dictionary of standard Linux commands and flags
CRITICAL_COMMAND_SEEDS: Dict[str, List[str]] = {
    "du": [
        "-h", "-s", "-a", "-c", "-k", "-m", "-b", "-L", "-x", "-0",
        "--max-depth", "--apparent-size", "--exclude", "--total",
        "--summarize", "--human-readable", "--bytes", "--all"
    ],
    "df": [
        "-h", "-T", "-i", "-k", "-m", "-a", "-l", "-P",
        "--total", "--human-readable", "--print-type", "--inodes"
    ],
    "lsof": [
        "+L1", "-i", "-n", "-P", "-p", "-u", "-c", "-t", "-a", "+D", "+d",
        "-b", "-F", "-l", "-N", "-s", "-U", "-w"
    ],
    "tar": [
        "-x", "-v", "-z", "-f", "-j", "-J", "-c", "-t", "-C", "-p", "-k",
        "--strip-components", "--exclude", "--same-owner", "--numeric-owner",
        "--auto-compress", "--gzip", "--bzip2", "--xz", "--extract", "--create"
    ],
    "systemctl": [
        "status", "start", "stop", "restart", "reload", "enable", "disable",
        "is-active", "is-failed", "is-enabled", "daemon-reload", "list-units",
        "-u", "--no-pager", "--failed", "--all", "--type", "--state", "-l",
        "--now", "--user", "--system"
    ],
    "journalctl": [
        "-u", "-e", "-f", "-n", "-r", "-b", "-k", "-p", "-x", "-a",
        "--since", "--until", "--no-pager", "--unit", "--lines",
        "--boot", "--dmesg", "--priority", "--catalog", "--output"
    ],
    "nginx": [
        "-t", "-T", "-s", "-c", "-g", "-p", "-v", "-V", "-q"
    ],
    "find": [
        "-type", "-name", "-iname", "-size", "-mtime", "-atime", "-ctime",
        "-maxdepth", "-mindepth", "-exec", "-execdir", "-delete", "-print",
        "-empty", "-perm", "-user", "-group", "-path", "-regex", "-prune"
    ],
    "ps": [
        "aux", "-ef", "-u", "-p", "-o", "-e", "-f", "-L", "-w",
        "--sort", "--forest", "-C", "-A"
    ],
    "top": [
        "-b", "-n", "-d", "-p", "-u", "-c", "-H", "-w", "-S"
    ],
    "kill": [
        "-9", "-15", "-1", "-2", "-l", "-s", "-q"
    ],
    "rm": [
        "-r", "-f", "-v", "-i", "-I", "-d", "--no-preserve-root", "--preserve-root"
    ],
    "visudo": [
        "-c", "-f", "-s", "-q", "-x", "--check", "--file", "--quiet", "--strict"
    ],
    "sshd": [
        "-t", "-T", "-f", "-p", "-d", "-D", "-e", "-q"
    ],
    "promtool": [
        "check", "config", "rules", "--help"
    ],
    "haproxy": [
        "-c", "-f", "-q", "-V", "-D", "-W", "-db", "-d"
    ],
    "named-checkconf": [
        "-v", "-z", "-p", "-j", "-t"
    ],
    "named-checkzone": [
        "-q", "-d", "-v", "-k", "-m", "-n", "-o"
    ],
    "systemd-analyze": [
        "verify", "blame", "critical-chain", "time", "plot", "dot", "dump", "cat-config",
        "--no-pager", "--user", "--system", "-q"
    ],
    "apache2ctl": [
        "configtest", "graceful", "restart", "start", "stop", "status",
        "-t", "-k", "-v", "-V", "-M", "-S"
    ],
    "httpd": [
        "-t", "-k", "-v", "-V", "-M", "-S"
    ],
    "docker": [
        "compose", "config", "ps", "run", "build", "inspect", "logs", "exec", "stop", "rm",
        "--version", "-v", "-f", "--file"
    ],
    "bash": [
        "-n", "-c", "-x", "-e", "-u", "-v", "--version"
    ],
    "fuser": [
        "-v", "-k", "-m", "-n", "-s", "-u", "-a"
    ],
    "pstree": [
        "-p", "-a", "-u", "-h", "-c", "-g", "-s", "-t", "-A", "-U"
    ],
    "ss": [
        "-t", "-u", "-l", "-p", "-n", "-a", "-e", "-i", "-m", "-o", "-s",
        "--numeric", "--listening", "--processes"
    ],
    "netstat": [
        "-t", "-u", "-l", "-p", "-n", "-a", "-r", "-i", "-s", "-c"
    ],
    "pidstat": [
        "-d", "-u", "-r", "-s", "-v", "-w", "-p", "-t", "-h", "-C"
    ],
    "iotop": [
        "-b", "-n", "-d", "-p", "-u", "-P", "-a", "-o", "-q"
    ],
    "readlink": [
        "-f", "-e", "-m", "-n", "-q", "-s", "-v", "--canonicalize", "--silent", "--verbose"
    ],
    "stat": [
        "-c", "-f", "-L", "-t", "--format", "--file-system", "--printf"
    ],
    "pgrep": [
        "-f", "-l", "-a", "-u", "-x", "-n", "-o", "-P"
    ],
    "pkill": [
        "-f", "-u", "-x", "-n", "-o", "-P"
    ],
    "ncdu": [
        "-x", "-r", "-q", "-o", "-f", "--exclude"
    ],
    "tail": [
        "-n", "-f", "-c", "-q", "-v", "--follow", "--lines", "--bytes"
    ],
    "head": [
        "-n", "-c", "-q", "-v", "--lines", "--bytes"
    ],
    "wc": [
        "-l", "-c", "-m", "-w", "-L", "--lines", "--bytes", "--words"
    ],
    "curl": [
        "-s", "-S", "-f", "-L", "-v", "-k", "-I", "-X", "-H", "-d",
        "-o", "-O", "-u", "-m", "-w",
        "--max-time", "--connect-timeout", "--silent", "--show-error",
        "--fail", "--location", "--insecure", "--head", "--request", "--header"
    ],
    "iptables": [
        "-L", "-n", "-v", "-A", "-D", "-I", "-F", "-X", "-Z", "-P",
        "-t", "-p", "-s", "-d", "-i", "-o", "-j", "-m",
        "--dport", "--sport", "--state", "--comment", "--line-numbers"
    ],
    "ufw": [
        "status", "enable", "disable", "reload", "reset", "allow", "deny",
        "reject", "limit", "delete", "insert", "route", "logging",
        "--dry-run", "--force", "numbered", "verbose"
    ]
}


def bootstrap_database(db_path: Path) -> int:
    """Creates and seeds the completions.sqlite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_flags (
            command TEXT NOT NULL,
            flag TEXT NOT NULL,
            description TEXT,
            PRIMARY KEY (command, flag)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cmd ON command_flags(command)")

    inserted_count = 0
    for cmd, flags in CRITICAL_COMMAND_SEEDS.items():
        for flag in flags:
            cursor.execute(
                "INSERT OR IGNORE INTO command_flags (command, flag, description) VALUES (?, ?, ?)",
                (cmd, flag, f"Verified option for {cmd}")
            )
            inserted_count += cursor.rowcount

    # Optional enrichment if fish completions are installed locally (Linux/macOS)
    fish_completions_dir = Path("/usr/share/fish/completions")
    if fish_completions_dir.exists() and fish_completions_dir.is_dir():
        import re
        flag_pattern = re.compile(r"-s\s+([a-zA-Z0-9])|-l\s+([a-zA-Z0-9_-]+)")
        for comp_file in fish_completions_dir.glob("*.fish"):
            cmd_name = comp_file.stem
            try:
                content = comp_file.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    if line.strip().startswith("complete -c"):
                        matches = flag_pattern.findall(line)
                        for short_opt, long_opt in matches:
                            if short_opt:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO command_flags (command, flag, description) VALUES (?, ?, ?)",
                                    (cmd_name, f"-{short_opt}", "Imported from fish")
                                )
                                inserted_count += cursor.rowcount
                            if long_opt:
                                cursor.execute(
                                    "INSERT OR IGNORE INTO command_flags (command, flag, description) VALUES (?, ?, ?)",
                                    (cmd_name, f"--{long_opt}", "Imported from fish")
                                )
                                inserted_count += cursor.rowcount
            except Exception:
                pass

    conn.commit()
    conn.close()
    return inserted_count


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    target_db = project_root / "data" / "completions.sqlite"
    count = bootstrap_database(target_db)
    print(f"[SafeOps-Bench] Seeded database at: {target_db} (Total entries: {count})")
