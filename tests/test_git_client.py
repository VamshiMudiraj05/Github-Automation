"""Tests for safe GitClient automation and token sanitization."""

import os
import subprocess
from pathlib import Path
from src.git.client import GitClient


def test_sanitize_tokens():
    client = GitClient(Path("."))
    raw = "fatal: repository 'https://ghp_123456789012345678901234567890123456@github.com/org/repo' not found"
    sanitized = client._sanitize(raw)
    assert "ghp_" not in sanitized
    assert "https://***@github.com" in sanitized


def test_git_init_and_status(tmp_path: Path):
    git = GitClient(tmp_path, base_branch="main")
    assert git.is_git_repo() is False

    # Initialize repository
    initialized = git.init_repo_if_needed()
    assert initialized is True
    assert git.is_git_repo() is True

    # Configure local git user for test commits
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "runner@example.com"], cwd=str(tmp_path), check=True)

    # Create a test file
    test_file = tmp_path / "hello.py"
    test_file.write_text("print('hello')", encoding="utf-8")

    status = git.get_status()
    assert "hello.py" in status.untracked_files

    # Stage and commit
    git.stage_files(["hello.py"])
    sha = git.commit("feat: initial commit")
    assert len(sha) == 40

    status_after = git.get_status()
    assert status_after.is_clean is True
