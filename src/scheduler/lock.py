"""Cross-platform single-run execution lock preventing duplicate runs."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agent.scheduler.lock")


class LockAcquisitionError(Exception):
    """Raised when another execution run is already active."""
    pass


class ExecutionLock:
    """Ensures only one instance of the daily agent runs at any time."""

    def __init__(self, workspace_root: Path, stale_timeout_seconds: int = 1800):
        self.lock_file = workspace_root / ".agent.lock"
        self.stale_timeout_seconds = stale_timeout_seconds
        self.acquired = False

    def acquire(self) -> None:
        if self.lock_file.exists():
            if self._is_stale():
                logger.warning("Stale lock detected (> %ds). Removing stale lock...", self.stale_timeout_seconds)
                self.release()
            else:
                try:
                    data = json.loads(self.lock_file.read_text(encoding="utf-8"))
                    pid = data.get("pid")
                    started = data.get("started_at")
                    raise LockAcquisitionError(
                        f"Another agent run is currently active (PID {pid}, started at {started}). Aborting."
                    )
                except Exception as e:
                    if isinstance(e, LockAcquisitionError):
                        raise
                    self.release()

        lock_data = {
            "pid": os.getpid(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": time.time(),
        }
        self.lock_file.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
        self.acquired = True
        logger.info("Acquired single-run lock (PID %d).", os.getpid())

    def release(self) -> None:
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info("Released single-run lock.")
        except Exception as e:
            logger.warning("Failed to remove lock file: %s", e)
        finally:
            self.acquired = False

    def _is_stale(self) -> bool:
        try:
            data = json.loads(self.lock_file.read_text(encoding="utf-8"))
            ts = data.get("timestamp", 0)
            if time.time() - ts > self.stale_timeout_seconds:
                return True
            # Also check if PID is alive on current OS
            pid = data.get("pid")
            if pid and not self._is_pid_alive(pid):
                return True
        except Exception:
            return True
        return False

    def _is_pid_alive(self, pid: int) -> bool:
        if os.name == "nt":
            import subprocess
            try:
                out = subprocess.check_output(f'tasklist /fi "PID eq {pid}"', shell=True, text=True)
                return str(pid) in out
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            self.release()
