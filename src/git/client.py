"""Safe, robust Git and GitHub automation client."""

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger("agent.git.client")


@dataclass
class GitStatus:
    is_repo: bool
    current_branch: str
    modified_files: List[str]
    untracked_files: List[str]
    staged_files: List[str]
    is_clean: bool


class GitClient:
    """Automates Git staging, committing, pushing, and remote verification safely."""

    def __init__(self, workspace_root: Path, repository_url: str = "", base_branch: str = "main"):
        self.workspace_root = workspace_root
        self.repository_url = repository_url
        self.base_branch = base_branch

    def _run_git(self, args: List[str], check: bool = True, timeout: int = 60) -> Tuple[int, str, str]:
        cmd = ["git"] + args
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            # Redact any accidental tokens in output
            stdout = self._sanitize(res.stdout)
            stderr = self._sanitize(res.stderr)
            if check and res.returncode != 0:
                logger.error("Git command '%s' failed: %s", " ".join(args), stderr)
                raise RuntimeError(f"Git failed ({res.returncode}): {stderr}")
            return res.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git command timed out: {' '.join(args)}")

    def _sanitize(self, text: str) -> str:
        """Strip embedded tokens from git URLs and error output."""
        if not text:
            return ""
        return re.sub(r"https://[^@\s]+@", "https://***@", text)

    def is_git_repo(self) -> bool:
        """Check if workspace_root is itself a git repository (not merely inside a parent repository)."""
        git_dir = self.workspace_root / ".git"
        if git_dir.exists():
            return True
        code, out, _ = self._run_git(["rev-parse", "--show-toplevel"], check=False)
        if code == 0 and out.strip():
            try:
                top_level = Path(out.strip()).resolve()
                return top_level == self.workspace_root.resolve()
            except Exception:
                return False
        return False

    def clone_or_init_repo(self) -> bool:
        """Ensure the target repository is checked out and tracking remote."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        auth_url = self.get_authenticated_remote_url()

        if not self.is_git_repo():
            # If target dir is completely empty, attempt git clone first
            is_empty = not any(self.workspace_root.iterdir())
            if self.repository_url and is_empty:
                logger.info("Attempting to clone target repo %s into %s...", self.repository_url, self.workspace_root)
                code, _, stderr = self._run_git(["clone", auth_url, "."], check=False, timeout=60)
                if code == 0:
                    logger.info("Target repository cloned successfully.")
                    self.setup_remote()
                    return True
                else:
                    logger.warning("Clone failed (%s), will initialize local repository instead.", stderr)

            logger.info("Initializing new local git repository at %s", self.workspace_root)
            self._run_git(["init"])
            self._run_git(["checkout", "-B", self.base_branch], check=False)
            self.setup_remote()
            if self.repository_url:
                self.fetch_remote()
                # Attempt to pull remote branch if it already exists
                self._run_git(["pull", "origin", self.base_branch, "--allow-unrelated-histories"], check=False)
            return True
        else:
            self.setup_remote()
            self.fetch_remote()
            self._run_git(["checkout", self.base_branch], check=False)
            self._run_git(["pull", "origin", self.base_branch], check=False)
            return True

    def init_repo_if_needed(self) -> bool:
        return self.clone_or_init_repo()

    def get_status(self) -> GitStatus:
        if not self.is_git_repo():
            return GitStatus(False, "", [], [], [], True)

        _, branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=False)
        current_branch = branch.strip() or self.base_branch

        code, out, _ = self._run_git(["status", "--porcelain"], check=False)
        modified = []
        untracked = []
        staged = []

        for line in out.splitlines():
            if not line:
                continue
            index_status = line[0]
            work_status = line[1]
            filepath = line[3:].strip()

            if index_status in ("M", "A", "R"):
                staged.append(filepath)
            if work_status == "M":
                modified.append(filepath)
            elif index_status == "?" and work_status == "?":
                untracked.append(filepath)

        is_clean = len(modified) == 0 and len(untracked) == 0 and len(staged) == 0
        return GitStatus(
            is_repo=True,
            current_branch=current_branch,
            modified_files=modified,
            untracked_files=untracked,
            staged_files=staged,
            is_clean=is_clean,
        )

    def get_diff(self, staged: bool = False) -> str:
        args = ["diff", "--cached"] if staged else ["diff"]
        _, out, _ = self._run_git(args, check=False)
        return out

    def stage_files(self, file_paths: List[str]) -> None:
        """Stage specific modified or new files."""
        if not file_paths:
            return
        # Ensure path format works across platforms
        cleaned = [p.replace("\\", "/") for p in file_paths]
        # Automatically create target .gitignore if none exists
        target_gitignore = self.workspace_root / ".gitignore"
        if not target_gitignore.exists():
            default_ignore = (
                "__pycache__/\n*.py[cod]\n*$py.class\n.pytest_cache/\n"
                ".coverage\nhtmlcov/\n*.tmp\n.env\n.env.*\n*.db-shm\n*.db-wal\n"
            )
            target_gitignore.write_text(default_ignore, encoding="utf-8")
            cleaned.append(".gitignore")

        # Stage existing files
        existing = [p for p in cleaned if (self.workspace_root / p).exists()]
        if existing:
            self._run_git(["add"] + existing)

    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes ready to be committed."""
        code, _, _ = self._run_git(["diff", "--cached", "--quiet"], check=False)
        return code != 0

    def commit(self, message: str) -> str:
        """Create a commit with the specified message and return its SHA."""
        if not message.strip():
            raise ValueError("Commit message cannot be empty.")
        
        # Configure user if not globally set
        code, name, _ = self._run_git(["config", "user.name"], check=False)
        if not name.strip():
            self._run_git(["config", "user.name", os.getenv("GITHUB_ACTOR", "Autonomous Project Agent")])
        code, email, _ = self._run_git(["config", "user.email"], check=False)
        if not email.strip():
            self._run_git(["config", "user.email", os.getenv("GITHUB_EMAIL", "agent@autonomous-project.local")])

        self._run_git(["commit", "-m", message])
        _, sha, _ = self._run_git(["rev-parse", "HEAD"])
        return sha.strip()

    def get_authenticated_remote_url(self) -> str:
        """Resolve remote URL with token if GH_PAT or GITHUB_TOKEN is present in env."""
        url = self.repository_url
        token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
        if token and url.startswith("https://github.com/"):
            # Insert token for auth
            return url.replace("https://github.com/", f"https://x-access-token:{token}@github.com/")
        return url

    def setup_remote(self, remote_name: str = "origin") -> None:
        """Configure origin remote if not present or update it."""
        if not self.repository_url:
            return
        code, out, _ = self._run_git(["remote"], check=False)
        remotes = [r.strip() for r in out.splitlines()]
        auth_url = self.get_authenticated_remote_url()

        if remote_name in remotes:
            self._run_git(["remote", "set-url", remote_name, auth_url])
        else:
            self._run_git(["remote", "add", remote_name, auth_url])

    def fetch_remote(self, remote: str = "origin") -> bool:
        try:
            self._run_git(["fetch", remote, self.base_branch], check=False, timeout=30)
            return True
        except Exception:
            return False

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Push committed changes to remote branch without force push."""
        target_branch = branch or self.base_branch
        self.setup_remote(remote)

        logger.info("Pushing changes to %s %s...", remote, target_branch)
        code, out, err = self._run_git(["push", remote, f"HEAD:{target_branch}"], check=False, timeout=60)
        if code != 0:
            logger.error("Push failed: %s", err)
            return False
        return True

    def verify_remote_commit(self, expected_sha: str, remote: str = "origin") -> bool:
        """Query remote refs to verify commit exists on remote."""
        if not expected_sha:
            return False
        try:
            auth_url = self.get_authenticated_remote_url()
            # Run ls-remote to check head of remote branch
            code, out, _ = self._run_git(["ls-remote", auth_url, f"refs/heads/{self.base_branch}"], check=False, timeout=30)
            if code == 0 and out.strip():
                remote_head = out.split()[0].strip()
                return remote_head.startswith(expected_sha) or expected_sha.startswith(remote_head)
        except Exception as e:
            logger.warning("Could not verify remote commit via ls-remote: %s", e)
        return False
