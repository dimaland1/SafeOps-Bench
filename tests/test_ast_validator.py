"""Tests validating AST command extraction and compound flag normalization."""

import pytest
from bench.tree_sitter_ast import extract_commands_from_script, normalize_flags


def test_normalize_flags_compound():
    # Compound short flags
    flags = normalize_flags(["-xvzf"])
    assert flags == {"-x", "-v", "-z", "-f"}

    flags_rf = normalize_flags(["-rf"])
    assert flags_rf == {"-r", "-f"}


def test_normalize_flags_long_with_values():
    flags = normalize_flags(["--max-depth=1", "--exclude=*.log", "-h"])
    assert flags == {"--max-depth", "--exclude", "-h"}


def test_normalize_flags_special():
    # Special flags like lsof '+L1' and numeric 'kill -9'
    flags = normalize_flags(["+L1", "-9"])
    assert "+L1" in flags
    assert "-9" in flags


def test_extract_commands_basic():
    script = "du -h --max-depth=1 /var/log | sort -hr | head -n 10"
    commands = extract_commands_from_script(script)
    cmd_names = [c[0] for c in commands]
    assert "du" in cmd_names
    assert "sort" in cmd_names
    assert "head" in cmd_names


def test_extract_commands_with_sudo():
    script = "sudo lsof +L1 && sudo systemctl reload nginx"
    commands = extract_commands_from_script(script)
    cmd_names = [c[0] for c in commands]
    # Sudo should be stripped so the target command is identified
    assert "lsof" in cmd_names
    assert "systemctl" in cmd_names


def test_extract_commands_markdown_wrapped():
    wrapped_script = """```bash
# Diagnostic command
du -sh /var/* 2>/dev/null
lsof +L1
```"""
    commands = extract_commands_from_script(wrapped_script)
    cmd_names = [c[0] for c in commands]
    assert "du" in cmd_names
    assert "lsof" in cmd_names
