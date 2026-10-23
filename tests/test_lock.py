"""Tests for single-instance execution lock and concurrency protection."""

from pathlib import Path
import pytest
from src.scheduler.lock import ExecutionLock, LockAcquisitionError


def test_lock_acquire_and_release(tmp_path: Path):
    lock = ExecutionLock(tmp_path)
    assert not (tmp_path / ".agent.lock").exists()

    lock.acquire()
    assert (tmp_path / ".agent.lock").exists()
    assert lock.acquired is True

    lock.release()
    assert not (tmp_path / ".agent.lock").exists()
    assert lock.acquired is False


def test_prevents_duplicate_concurrent_run(tmp_path: Path):
    lock1 = ExecutionLock(tmp_path)
    lock1.acquire()

    lock2 = ExecutionLock(tmp_path)
    with pytest.raises(LockAcquisitionError) as exc_info:
        lock2.acquire()
    assert "Another agent run is currently active" in str(exc_info.value)

    lock1.release()
    # Now lock2 can acquire
    lock2.acquire()
    assert lock2.acquired is True
    lock2.release()


def test_context_manager_behavior(tmp_path: Path):
    lock = ExecutionLock(tmp_path)
    with lock:
        assert (tmp_path / ".agent.lock").exists()
    assert not (tmp_path / ".agent.lock").exists()
