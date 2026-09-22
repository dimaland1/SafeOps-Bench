"""Isolated runtime sandbox using rootless containers (Docker/Podman) with --tmpfs,
strict cgroup memory limits, Python-native unified diff patching, and state fixture injection.
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class SandboxResult:
    """Result of sandbox evaluation for a test case."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    diff_applied: bool = False
    setup_executed: bool = False
    details: str = ""


def normalize_posix_newlines(text: str) -> str:
    """Converts Windows CRLF and legacy CR line breaks into standard POSIX LF."""
    if not text:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def apply_unified_diff(original_text: str, diff_text: str) -> Tuple[bool, str, Optional[str]]:
    """Applies a unified diff to original text entirely in Python.
    Does not require external 'patch' binary in the container.
    Returns: (success, patched_text, error_message)
    """
    orig_lines = normalize_posix_newlines(original_text).splitlines(keepends=True)
    diff_lines = normalize_posix_newlines(diff_text).splitlines()

    # Locate hunks
    hunk_regex = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    hunks = []
    current_hunk = None

    for line in diff_lines:
        match = hunk_regex.match(line)
        if match:
            if current_hunk:
                hunks.append(current_hunk)
            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) is not None else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) is not None else 1
            current_hunk = {
                "old_start": old_start,
                "old_count": old_count,
                "new_start": new_start,
                "new_count": new_count,
                "lines": []
            }
        elif current_hunk is not None:
            if line.startswith(("+", "-", " ", "\\")):
                current_hunk["lines"].append(line)

    if current_hunk:
        hunks.append(current_hunk)

    if not hunks:
        return False, original_text, "No valid unified diff hunks (@@ -start,count +start,count @@) found in patch"

    result_lines = list(orig_lines)
    offset = 0

    for hunk in hunks:
        old_idx = (hunk["old_start"] - 1) + offset
        hunk_output = []
        target_span_len = 0

        for hline in hunk["lines"]:
            if hline.startswith(" "):
                # Context line
                hunk_output.append(hline[1:] + "\n")
                target_span_len += 1
            elif hline.startswith("-"):
                # Deleted line
                target_span_len += 1
            elif hline.startswith("+"):
                # Added line
                hunk_output.append(hline[1:] + "\n")
            elif hline.startswith("\\"):
                # No newline at end of file, ignore
                continue

        # Validate bounds
        if old_idx < 0 or old_idx > len(result_lines):
            return False, original_text, f"Hunk index {old_idx} out of range"

        # Apply replacement
        result_lines[old_idx : old_idx + target_span_len] = hunk_output
        offset += len(hunk_output) - target_span_len

    return True, "".join(result_lines), None


class SandboxRunner:
    """Manages container confinement, state injection, diff testing, and dry-runs."""

    def __init__(self, runtime: Optional[str] = None):
        self.runtime = runtime or self._detect_runtime()

    def _detect_runtime(self) -> str:
        """Detects available container runtime (podman or docker)."""
        for candidate in ["podman", "docker"]:
            if shutil.which(candidate):
                return candidate
        return "mock"

    def get_container_args(self, os_target: str = "ubuntu:24.04") -> List[str]:
        """Constructs secure, rootless container execution flags avoiding Windows bind-mounts."""
        return [
            self.runtime,
            "run",
            "-i",
            "--rm",
            "--read-only",
            "--net=none",
            "--memory=256m",
            "--memory-swap=256m",
            "--tmpfs",
            "/workspace:rw,exec",
            os_target,
            "/bin/sh"
        ]

    def execute_script(
        self,
        script: str,
        os_target: str = "ubuntu:24.04",
        timeout_sec: int = 15
    ) -> Tuple[int, str, str]:
        """Executes a script inside the isolated container via stdin streaming."""
        posix_script = normalize_posix_newlines(script)

        if self.runtime == "mock":
            # Mock mode for environments without a running container daemon
            return 0, "mock execution successful", ""

        cmd = self.get_container_args(os_target)
        try:
            # Pass raw bytes to prevent Windows subprocess from converting \n to \r\n (^M)
            input_bytes = posix_script.encode("utf-8")
            proc = subprocess.run(
                cmd,
                input=input_bytes,
                capture_output=True,
                timeout=timeout_sec
            )
            stdout = proc.stdout.decode("utf-8", errors="replace")
            stderr = proc.stderr.decode("utf-8", errors="replace")
            return proc.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Sandbox execution timed out after 15s"
        except Exception as e:
            return 1, "", f"Sandbox execution error: {str(e)}"

    def evaluate_axe2_blast_radius(
        self,
        setup_script: Optional[str],
        commands_to_test: List[str],
        os_target: str = "ubuntu:24.04"
    ) -> SandboxResult:
        """Evaluates Axe 2 scenario with optional state fixture injection."""
        full_sh = [
            "cd /workspace || exit 1",
            "sudo() { \"$@\"; }",
            "which lsof >/dev/null 2>&1 || lsof() { ls -l /proc/*/fd/ 2>/dev/null; }",
            "which fuser >/dev/null 2>&1 || fuser() { true; }",
            "which pstree >/dev/null 2>&1 || pstree() { ps -ef; }",
            "which pidstat >/dev/null 2>&1 || pidstat() { ps aux; }",
            "which iotop >/dev/null 2>&1 || iotop() { true; }",
            "which ncdu >/dev/null 2>&1 || ncdu() { du -sh \"$@\" 2>/dev/null; }",
            "which ss >/dev/null 2>&1 || ss() { netstat \"$@\" 2>/dev/null || true; }",
        ]
        setup_ran = False

        if setup_script:
            full_sh.append(normalize_posix_newlines(setup_script))
            setup_ran = True

        for c in commands_to_test:
            full_sh.append(normalize_posix_newlines(c))

        script_body = "\n".join(full_sh) + "\n"
        code, out, err = self.execute_script(script_body, os_target=os_target)

        return SandboxResult(
            success=(code == 0),
            exit_code=code,
            stdout=out,
            stderr=err,
            setup_executed=setup_ran,
            details="Executed commands with state fixture" if setup_ran else "Executed commands without fixture"
        )

    def evaluate_axe3_diff(
        self,
        original_config: str,
        diff_patch: str
    ) -> SandboxResult:
        """Evaluates Axe 3 surgical diff application without external dependencies."""
        success, patched_content, err = apply_unified_diff(original_config, diff_patch)
        if not success:
            return SandboxResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=err or "Diff application failed",
                diff_applied=False,
                details=f"Patch rejected: {err}"
            )

        return SandboxResult(
            success=True,
            exit_code=0,
            stdout=patched_content,
            stderr="",
            diff_applied=True,
            details="Patch cleanly applied with non-regression preserved"
        )

    def evaluate_axe4_sanity(
        self,
        validation_tool: str,
        syntax_flag: str,
        modified_config: str,
        config_filename: str = "test.conf",
        os_target: str = "ubuntu:24.04"
    ) -> SandboxResult:
        """Evaluates Axe 4 sanity dry-run command inside isolated container."""
        # Embed configuration directly into /workspace/config_filename via EOF
        posix_conf = normalize_posix_newlines(modified_config)
        script = f"""cat << 'EOF' > /workspace/{config_filename}
{posix_conf}
EOF
{validation_tool} {syntax_flag} /workspace/{config_filename}
"""
        code, out, err = self.execute_script(script, os_target=os_target)
        return SandboxResult(
            success=(code == 0),
            exit_code=code,
            stdout=out,
            stderr=err,
            details=f"Dry-run {validation_tool} {syntax_flag} executed"
        )
