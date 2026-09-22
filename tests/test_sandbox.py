"""Tests for SandboxRunner: container argument isolation, unified diff patching, and newline normalization."""

import pytest
from bench.sandbox import (
    SandboxRunner,
    SandboxResult,
    apply_unified_diff,
    normalize_posix_newlines,
)


def test_normalize_posix_newlines():
    windows_text = "line1\r\nline2\r\nline3\r\n"
    posix_text = normalize_posix_newlines(windows_text)
    assert posix_text == "line1\nline2\nline3\n"
    assert "\r" not in posix_text


def test_apply_unified_diff_success():
    original = """server {
    listen 80;
    server_name example.com;
}
"""
    diff_patch = """--- nginx.conf
+++ nginx.conf
@@ -1,4 +1,5 @@
 server {
     listen 80;
+    listen 443 ssl;
     server_name example.com;
 }
"""
    success, patched, err = apply_unified_diff(original, diff_patch)
    assert success is True
    assert err is None
    assert "listen 443 ssl;" in patched
    assert "server_name example.com;" in patched


def test_apply_unified_diff_hsts_addition():
    original = """server {
    listen 443 ssl;
    server_name api.local;
    location / {
        proxy_pass http://upstream;
    }
}
"""
    diff_patch = """@@ -3,3 +3,4 @@
     server_name api.local;
+    add_header Strict-Transport-Security "max-age=31536000" always;
     location / {
"""
    success, patched, err = apply_unified_diff(original, diff_patch)
    assert success is True
    assert "add_header Strict-Transport-Security" in patched


def test_apply_unified_diff_malformed():
    original = "line 1\nline 2\n"
    diff_patch = "This is not a unified diff format"
    success, patched, err = apply_unified_diff(original, diff_patch)
    assert success is False
    assert "No valid unified diff hunks" in err


def test_sandbox_container_arguments():
    runner = SandboxRunner(runtime="podman")
    args = runner.get_container_args("ubuntu:24.04")

    assert "--read-only" in args
    assert "--net=none" in args
    assert "--memory=256m" in args
    assert "--memory-swap=256m" in args
    assert "--tmpfs" in args
    assert "/workspace:rw,exec" in args
    assert "--rm" in args
    assert "-i" in args
    assert "ubuntu:24.04" in args


def test_evaluate_axe3_diff():
    runner = SandboxRunner(runtime="mock")
    orig = "wal_level = minimal\nmax_wal_size = 1GB\n"
    patch = """@@ -1,2 +1,2 @@
-wal_level = minimal
+wal_level = replica
 max_wal_size = 1GB
"""
    result = runner.evaluate_axe3_diff(orig, patch)
    assert isinstance(result, SandboxResult)
    assert result.success is True
    assert result.diff_applied is True
    assert "wal_level = replica" in result.stdout


def test_evaluate_axe2_blast_radius_mock():
    runner = SandboxRunner(runtime="mock")
    result = runner.evaluate_axe2_blast_radius(
        setup_script="echo setup",
        commands_to_test=["du -sh /var/*", "lsof +L1"],
        os_target="debian:12"
    )
    assert result.success is True
    assert result.setup_executed is True


def test_evaluate_axe4_sanity_mock():
    runner = SandboxRunner(runtime="mock")
    result = runner.evaluate_axe4_sanity(
        validation_tool="nginx",
        syntax_flag="-t",
        modified_config="events {} http { server { listen 80; } }",
        os_target="ubuntu:24.04"
    )
    assert result.success is True
    assert "Dry-run nginx -t executed" in result.details
