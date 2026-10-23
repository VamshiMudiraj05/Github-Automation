"""Tests for secret scanner preventing credential leaks."""

from pathlib import Path
from src.testing.secret_scanner import SecretScanner


def test_detects_prohibited_filenames():
    scanner = SecretScanner()
    violations = scanner.scan_file_path(Path(".env"))
    assert len(violations) > 0
    assert "Prohibited" in violations[0].rule_name

    key_violations = scanner.scan_file_path(Path("keys/server.key"))
    assert len(key_violations) > 0


def test_detects_private_key_blocks():
    scanner = SecretScanner()
    sample = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0mFk4nB2...\n"
        "-----END RSA PRIVATE KEY-----\n"
    )
    violations = scanner.scan_content(sample)
    assert len(violations) > 0
    assert "Private Key" in violations[0].rule_name


def test_detects_github_pat():
    scanner = SecretScanner()
    token_sample = "github_pat_11AEXAMPLE000000000000000000000000000000000000000000000000000000000000000000000000"
    violations = scanner.scan_content(f"export GITHUB_TOKEN='{token_sample}'")
    assert len(violations) > 0
    assert "GitHub" in violations[0].rule_name


def test_detects_secrets_in_diff():
    scanner = SecretScanner()
    diff = """
diff --git a/src/config.py b/src/config.py
--- a/src/config.py
+++ b/src/config.py
@@ -1,3 +1,4 @@
 import os
+OPENAI_KEY = "sk-proj-123456789012345678901234567890123456789012345"
 def init():
     pass
"""
    violations = scanner.scan_git_diff(diff)
    assert len(violations) > 0
    assert "OpenAI" in violations[0].rule_name


def test_clean_diff_passes():
    scanner = SecretScanner()
    diff = """
diff --git a/src/math.py b/src/math.py
--- a/src/math.py
+++ b/src/math.py
@@ -1,2 +1,3 @@
 def add(a, b):
+    # safe calculation
     return a + b
"""
    violations = scanner.scan_git_diff(diff)
    assert len(violations) == 0
