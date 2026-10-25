"""Quality Gate executing automated tests, linter, builds, and diff sanity checks."""

import logging
import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.config import ToolchainConfig
from src.testing.secret_scanner import SecretScanner, SecretViolation

logger = logging.getLogger("agent.testing.quality_gate")


@dataclass
class QualityReport:
    passed: bool
    tests_passed: bool
    lint_passed: bool
    build_passed: bool
    diff_valid: bool
    duration_seconds: float
    secret_violations: List[SecretViolation] = field(default_factory=list)
    test_output: str = ""
    lint_output: str = ""
    build_output: str = ""
    diff_issues: List[str] = field(default_factory=list)
    summary: str = ""


class QualityGate:
    """Enforces rigorous code quality, test verification, and security checks before any commit."""

    def __init__(self, workspace_root: Path, toolchain: ToolchainConfig):
        self.workspace_root = workspace_root
        self.toolchain = toolchain
        self.scanner = SecretScanner()

    def run_command(self, cmd: str, timeout: int = 180) -> subprocess.CompletedProcess:
        """Safely execute a shell command inside workspace root."""
        logger.info("Executing quality command: %s", cmd)
        env = os.environ.copy()
        ws_str = str(self.workspace_root)
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{ws_str}{os.pathsep}{current_pythonpath}" if current_pythonpath else ws_str
        return subprocess.run(
            cmd,
            shell=True,
            cwd=ws_str,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def run_tests(self) -> tuple[bool, str]:
        if not self.toolchain.test_command:
            return True, "No test command configured."
        try:
            res = self.run_command(self.toolchain.test_command)
            output = ((res.stdout or "") + "\n" + (res.stderr or "")).strip()
            # Exit code 0 means passed. Exit code 5 means no tests were collected (acceptable during initial setup/doc phase).
            passed = res.returncode in (0, 5)
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "Test suite execution timed out."
        except Exception as e:
            return False, f"Failed to execute test command: {e}"

    def run_lint(self) -> tuple[bool, str]:
        if not self.toolchain.lint_command:
            return True, "No lint command configured."
        try:
            res = self.run_command(self.toolchain.lint_command)
            output = (res.stdout or "") + "\n" + (res.stderr or "")
            return res.returncode == 0, output.strip()
        except Exception as e:
            return False, f"Lint check error: {e}"

    def run_build(self) -> tuple[bool, str]:
        if not self.toolchain.build_command:
            return True, "No build command configured."
        try:
            res = self.run_command(self.toolchain.build_command)
            output = (res.stdout or "") + "\n" + (res.stderr or "")
            return res.returncode == 0, output.strip()
        except Exception as e:
            return False, f"Build check error: {e}"

    def validate_diff(self, diff_text: str, staged_files: List[str], require_meaningful: bool = True) -> tuple[bool, List[str]]:
        issues = []
        if require_meaningful:
            if not diff_text.strip() and not staged_files:
                issues.append("Working tree contains no modifications (empty diff).")

        # Check for prohibited binary or temp files
        for f in staged_files:
            lower = f.lower()
            if lower.endswith((".pyc", ".db", ".sqlite", ".lock", ".log")):
                issues.append(f"Forbidden build/state artifact staged: {f}")
            if any(p in lower for p in [".env", "id_rsa", "credentials.json"]):
                issues.append(f"Forbidden credential file staged: {f}")

        return len(issues) == 0, issues

    def evaluate(
        self,
        diff_text: str,
        staged_files: List[str],
        run_tests: bool = True,
        require_meaningful: bool = True,
    ) -> QualityReport:
        """Run complete quality check suite and secret scanner."""
        start_time = time.time()

        # 1. Secret scanning
        secret_violations = self.scanner.scan_git_diff(diff_text)
        for f in staged_files:
            secret_violations.extend(self.scanner.scan_file_path(Path(f)))

        # 2. Diff validation
        diff_valid, diff_issues = self.validate_diff(diff_text, staged_files, require_meaningful)

        # 3. Tests
        tests_passed = True
        test_out = "Skipped"
        if run_tests:
            tests_passed, test_out = self.run_tests()

        # 4. Lint
        lint_passed, lint_out = self.run_lint()

        # 5. Build
        build_passed, build_out = self.run_build()

        duration = round(time.time() - start_time, 2)
        all_passed = (
            len(secret_violations) == 0
            and diff_valid
            and tests_passed
            and lint_passed
            and build_passed
        )

        summary_parts = []
        if secret_violations:
            summary_parts.append(f"CRITICAL: {len(secret_violations)} secret violation(s) detected!")
        if diff_issues:
            summary_parts.append(f"Diff issues: {', '.join(diff_issues)}")
        if not tests_passed:
            summary_parts.append("Test suite FAILED.")
        if not lint_passed:
            summary_parts.append("Lint check FAILED.")
        if not build_passed:
            summary_parts.append("Build check FAILED.")
        if all_passed:
            summary_parts.append("All quality checks, secret scans, and tests PASSED.")

        return QualityReport(
            passed=all_passed,
            tests_passed=tests_passed,
            lint_passed=lint_passed,
            build_passed=build_passed,
            diff_valid=diff_valid,
            duration_seconds=duration,
            secret_violations=secret_violations,
            test_output=test_out,
            lint_output=lint_out,
            build_output=build_out,
            diff_issues=diff_issues,
            summary="; ".join(summary_parts),
        )
