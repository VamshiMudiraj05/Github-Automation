"""Tests for QualityGate verification, diff inspection, and test runner."""

from pathlib import Path
from src.config import ToolchainConfig
from src.testing.quality_gate import QualityGate


def test_quality_gate_evaluates_clean_code(tmp_path: Path):
    toolchain = ToolchainConfig(
        test_command="python -c \"print('All tests passed')\"",
        lint_command="python -c \"exit(0)\"",
        build_command="python -c \"exit(0)\"",
    )
    qgate = QualityGate(tmp_path, toolchain)

    diff = """
diff --git a/src/math.py b/src/math.py
--- a/src/math.py
+++ b/src/math.py
@@ -0,0 +1,2 @@
+def multiply(a, b):
+    return a * b
"""
    report = qgate.evaluate(diff, staged_files=["src/math.py"])
    assert report.passed is True
    assert report.tests_passed is True
    assert report.diff_valid is True
    assert len(report.secret_violations) == 0


def test_quality_gate_rejects_empty_diff_when_meaningful_required(tmp_path: Path):
    toolchain = ToolchainConfig(test_command="python -c \"exit(0)\"")
    qgate = QualityGate(tmp_path, toolchain)

    report = qgate.evaluate(diff_text="", staged_files=[], require_meaningful=True)
    assert report.passed is False
    assert report.diff_valid is False
    assert any("empty" in issue.lower() for issue in report.diff_issues)


def test_quality_gate_rejects_failing_tests(tmp_path: Path):
    toolchain = ToolchainConfig(test_command="python -c \"import sys; sys.exit(1)\"")
    qgate = QualityGate(tmp_path, toolchain)

    report = qgate.evaluate(diff_text="valid diff", staged_files=["file.py"], run_tests=True)
    assert report.passed is False
    assert report.tests_passed is False
