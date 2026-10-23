"""Persistent State Manager using SQLite with atomic transactions and crash recovery."""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class Task:
    id: str
    day_number: int
    title: str
    phase: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity: str = "Medium"  # Low, Medium, High
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    commit_sha: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "day_number": self.day_number,
            "title": self.title,
            "phase": self.phase,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "deliverables": self.deliverables,
            "dependencies": self.dependencies,
            "complexity": self.complexity,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "retry_count": self.retry_count,
            "commit_sha": self.commit_sha,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ExecutionRun:
    run_id: str
    day_number: int
    scheduled_time: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    status: str = "IN_PROGRESS"  # SUCCESS, FAILED, RECOVERED, TIMED_OUT
    commit_sha: Optional[str] = None
    push_verified: bool = False
    tests_passed: bool = False
    report_path: Optional[str] = None
    error_details: Optional[str] = None


class StateManager:
    """ACID-compliant persistent state store for the 30-Day Project Agent."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            state_dir = Path.cwd() / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = state_dir / "agent_state.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")  # High reliability concurrency
        return conn

    def _init_database(self) -> None:
        """Create database tables with constraints and indexes."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS project_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    day_number INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    description TEXT NOT NULL,
                    acceptance_criteria TEXT NOT NULL,
                    deliverables TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    complexity TEXT DEFAULT 'Medium',
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    retry_count INTEGER DEFAULT 0,
                    commit_sha TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS execution_runs (
                    run_id TEXT PRIMARY KEY,
                    day_number INTEGER NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL DEFAULT 0.0,
                    status TEXT NOT NULL,
                    commit_sha TEXT,
                    push_verified INTEGER DEFAULT 0,
                    tests_passed INTEGER DEFAULT 0,
                    report_path TEXT,
                    error_details TEXT,
                    FOREIGN KEY(day_number) REFERENCES tasks(day_number)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_day ON tasks(day_number);
                CREATE INDEX IF NOT EXISTS idx_runs_day ON execution_runs(day_number);
            """)
            conn.commit()

    def set_meta(self, key: str, value: Any) -> None:
        now = datetime.now(timezone.utc).isoformat()
        val_str = json.dumps(value) if not isinstance(value, str) else value
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO project_meta(key, value, updated_at) VALUES(?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, val_str, now),
            )
            conn.commit()

    def get_meta(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT value FROM project_meta WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except Exception:
                    return row["value"]
            return default

    def save_roadmap(self, tasks: List[Task]) -> None:
        """Atomically persist or update 30-day roadmap tasks."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            for t in tasks:
                conn.execute(
                    """
                    INSERT INTO tasks (
                        id, day_number, title, phase, description,
                        acceptance_criteria, deliverables, dependencies,
                        complexity, status, retry_count, commit_sha,
                        error_message, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(day_number) DO UPDATE SET
                        title=excluded.title,
                        phase=excluded.phase,
                        description=excluded.description,
                        acceptance_criteria=excluded.acceptance_criteria,
                        deliverables=excluded.deliverables,
                        dependencies=excluded.dependencies,
                        complexity=excluded.complexity,
                        updated_at=excluded.updated_at
                    """,
                    (
                        t.id,
                        t.day_number,
                        t.title,
                        t.phase,
                        t.description,
                        json.dumps(t.acceptance_criteria),
                        json.dumps(t.deliverables),
                        json.dumps(t.dependencies),
                        t.complexity,
                        t.status.value if isinstance(t.status, TaskStatus) else t.status,
                        t.retry_count,
                        t.commit_sha,
                        t.error_message,
                        t.created_at or now,
                        now,
                    ),
                )
            conn.commit()

    def has_roadmap(self) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM tasks")
            row = cursor.fetchone()
            return bool(row and row["count"] >= 30)

    def get_all_tasks(self) -> List[Task]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks ORDER BY day_number ASC")
            return [self._row_to_task(row) for row in cursor.fetchall()]

    def get_task_by_day(self, day_number: int) -> Optional[Task]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM tasks WHERE day_number = ?", (day_number,))
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def get_next_incomplete_task(self) -> Optional[Task]:
        """Return the lowest day_number task that is not COMPLETED or SKIPPED."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM tasks WHERE status NOT IN ('COMPLETED', 'SKIPPED') ORDER BY day_number ASC LIMIT 1"
            )
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

    def mark_task_in_progress(self, day_number: int) -> Optional[Task]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET status = 'IN_PROGRESS', updated_at = ? WHERE day_number = ?",
                (now, day_number),
            )
            conn.commit()
        return self.get_task_by_day(day_number)

    def mark_task_completed(self, day_number: int, commit_sha: Optional[str] = None) -> Optional[Task]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET status = 'COMPLETED', commit_sha = ?, error_message = NULL, updated_at = ? WHERE day_number = ?",
                (commit_sha, now, day_number),
            )
            conn.commit()
        return self.get_task_by_day(day_number)

    def mark_task_failed(self, day_number: int, error_message: str) -> Optional[Task]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE tasks 
                SET status = 'FAILED', 
                    retry_count = retry_count + 1, 
                    error_message = ?, 
                    updated_at = ? 
                WHERE day_number = ?
                """,
                (error_message[:2000], now, day_number),
            )
            conn.commit()
        return self.get_task_by_day(day_number)

    def recover_interrupted_tasks(self) -> List[int]:
        """Find any tasks left in 'IN_PROGRESS' due to abnormal termination and reset them to 'PENDING'."""
        recovered_days: List[int] = []
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT day_number, retry_count FROM tasks WHERE status = 'IN_PROGRESS'")
            rows = cursor.fetchall()
            for r in rows:
                day = r["day_number"]
                conn.execute(
                    """
                    UPDATE tasks 
                    SET status = 'PENDING', 
                        retry_count = retry_count + 1,
                        error_message = 'Recovered from abnormal termination',
                        updated_at = ? 
                    WHERE day_number = ?
                    """,
                    (now, day),
                )
                recovered_days.append(day)
            conn.commit()
        return recovered_days

    def record_run(self, run: ExecutionRun) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO execution_runs (
                    run_id, day_number, scheduled_time, start_time, end_time,
                    duration_seconds, status, commit_sha, push_verified,
                    tests_passed, report_path, error_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    end_time=excluded.end_time,
                    duration_seconds=excluded.duration_seconds,
                    status=excluded.status,
                    commit_sha=excluded.commit_sha,
                    push_verified=excluded.push_verified,
                    tests_passed=excluded.tests_passed,
                    report_path=excluded.report_path,
                    error_details=excluded.error_details
                """,
                (
                    run.run_id,
                    run.day_number,
                    run.scheduled_time,
                    run.start_time,
                    run.end_time,
                    run.duration_seconds,
                    run.status,
                    run.commit_sha,
                    1 if run.push_verified else 0,
                    1 if run.tests_passed else 0,
                    run.report_path,
                    run.error_details,
                ),
            )
            conn.commit()

    def get_progress_summary(self) -> Dict[str, Any]:
        """Calculate overall statistics, completed count, streak, and phase breakdown."""
        tasks = self.get_all_tasks()
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

        current_task = self.get_next_incomplete_task()
        current_day = current_task.day_number if current_task else (total if total > 0 else 1)

        # Calculate streak from consecutive completed tasks starting at day 1
        streak = 0
        for t in sorted(tasks, key=lambda x: x.day_number):
            if t.status == TaskStatus.COMPLETED:
                streak += 1
            else:
                break

        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "current_day": current_day,
            "streak": streak,
            "completion_percentage": round((completed / total * 100), 1) if total > 0 else 0.0,
            "is_finished": total > 0 and completed == total,
        }

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            day_number=row["day_number"],
            title=row["title"],
            phase=row["phase"],
            description=row["description"],
            acceptance_criteria=json.loads(row["acceptance_criteria"]),
            deliverables=json.loads(row["deliverables"]),
            dependencies=json.loads(row["dependencies"]),
            complexity=row["complexity"],
            status=TaskStatus(row["status"]),
            retry_count=row["retry_count"],
            commit_sha=row["commit_sha"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
