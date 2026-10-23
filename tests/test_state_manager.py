"""Tests for ACID SQLite State Manager, task tracking, and crash recovery."""

from pathlib import Path
import pytest
from src.state.manager import StateManager, Task, TaskStatus, ExecutionRun


@pytest.fixture
def state_mgr(tmp_path: Path) -> StateManager:
    db_file = tmp_path / "test_state.db"
    return StateManager(db_file)


def test_init_and_save_roadmap(state_mgr: StateManager):
    tasks = [
        Task(
            id=f"task-day-{i:02d}",
            day_number=i,
            title=f"Milestone {i}",
            phase="Phase 1",
            description=f"Desc {i}",
            acceptance_criteria=[f"Criteria {i}"],
            deliverables=[f"file_{i}.py"],
            dependencies=[],
            status=TaskStatus.PENDING,
        )
        for i in range(1, 31)
    ]
    state_mgr.save_roadmap(tasks)
    assert state_mgr.has_roadmap() is True

    loaded = state_mgr.get_all_tasks()
    assert len(loaded) == 30
    assert loaded[0].day_number == 1
    assert loaded[29].day_number == 30


def test_task_status_lifecycle(state_mgr: StateManager):
    tasks = [
        Task(
            id="task-day-01",
            day_number=1,
            title="Milestone 1",
            phase="Phase 1",
            description="Desc 1",
            acceptance_criteria=["C1"],
            deliverables=["d1.py"],
            status=TaskStatus.PENDING,
        )
    ]
    state_mgr.save_roadmap(tasks)

    # Next incomplete task should be Day 1
    next_task = state_mgr.get_next_incomplete_task()
    assert next_task is not None
    assert next_task.day_number == 1

    # Mark in progress
    in_prog = state_mgr.mark_task_in_progress(1)
    assert in_prog.status == TaskStatus.IN_PROGRESS

    # Mark completed with SHA
    completed = state_mgr.mark_task_completed(1, commit_sha="abc12345")
    assert completed.status == TaskStatus.COMPLETED
    assert completed.commit_sha == "abc12345"

    # Next incomplete task should now be None
    assert state_mgr.get_next_incomplete_task() is None


def test_crash_recovery_resets_in_progress(state_mgr: StateManager):
    tasks = [
        Task(
            id="task-day-01",
            day_number=1,
            title="Milestone 1",
            phase="Phase 1",
            description="Desc 1",
            status=TaskStatus.PENDING,
        ),
        Task(
            id="task-day-02",
            day_number=2,
            title="Milestone 2",
            phase="Phase 1",
            description="Desc 2",
            status=TaskStatus.PENDING,
        ),
    ]
    state_mgr.save_roadmap(tasks)
    state_mgr.mark_task_completed(1, commit_sha="commit1")
    state_mgr.mark_task_in_progress(2)

    # Simulate abrupt process crash while day 2 was IN_PROGRESS
    recovered = state_mgr.recover_interrupted_tasks()
    assert recovered == [2]

    # Day 2 should now be PENDING with incremented retry count
    t2 = state_mgr.get_task_by_day(2)
    assert t2.status == TaskStatus.PENDING
    assert t2.retry_count == 1
    assert "abnormal" in t2.error_message.lower()


def test_progress_summary_and_streak(state_mgr: StateManager):
    tasks = [
        Task(
            id=f"task-day-{i:02d}",
            day_number=i,
            title=f"Milestone {i}",
            phase="Phase 1",
            description=f"Desc {i}",
            status=TaskStatus.COMPLETED if i <= 3 else TaskStatus.PENDING,
        )
        for i in range(1, 6)
    ]
    state_mgr.save_roadmap(tasks)

    summary = state_mgr.get_progress_summary()
    assert summary["completed"] == 3
    assert summary["total_tasks"] == 5
    assert summary["streak"] == 3
    assert summary["current_day"] == 4
    assert summary["completion_percentage"] == 60.0
