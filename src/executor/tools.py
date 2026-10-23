"""Safe, workspace-scoped filesystem and execution tools for the Coding Agent."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional


class WorkspaceTools:
    """Provides restricted, sandboxed file operations within the workspace root."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()

    def _resolve_safe(self, rel_path: str) -> Path:
        """Ensure path does not escape the workspace directory."""
        target = (self.workspace_root / rel_path).resolve()
        if not str(target).startswith(str(self.workspace_root)):
            raise PermissionError(f"Security violation: path '{rel_path}' escapes workspace.")
        return target

    def read_file(self, rel_path: str) -> str:
        target = self._resolve_safe(rel_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {rel_path}")
        return target.read_text(encoding="utf-8", errors="replace")

    def write_file(self, rel_path: str, content: str) -> None:
        target = self._resolve_safe(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def file_exists(self, rel_path: str) -> bool:
        target = self._resolve_safe(rel_path)
        return target.exists()

    def list_files(self, rel_dir: str = "", extension: Optional[str] = None) -> List[str]:
        target = self._resolve_safe(rel_dir)
        if not target.exists():
            return []
        files = []
        for p in target.rglob("*"):
            if p.is_file():
                # Ignore .git and caches
                rel = str(p.relative_to(self.workspace_root)).replace("\\", "/")
                if any(ignored in rel for ignored in [".git/", "__pycache__/", "state/", ".pytest_cache/"]):
                    continue
                if extension is None or p.suffix == extension:
                    files.append(rel)
        return sorted(files)

    def run_command(self, cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            shell=True,
            cwd=str(self.workspace_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
