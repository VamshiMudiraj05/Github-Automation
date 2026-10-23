"""Daily Execution Runner orchestrating the complete unattended development cycle."""

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.config import ProjectConfig, load_config
from src.executor.agent import CodingAgent, ExecutionResult
from src.executor.tools import WorkspaceTools
from src.git.client import GitClient
from src.notifications.notifier import NotificationService
from src.planner.generator import RoadmapGenerator
from src.planner.roadmap_writer import RoadmapWriter
from src.providers.factory import get_llm_provider
from src.reporting.report_generator import ReportGenerator
from src.scheduler.lock import ExecutionLock, LockAcquisitionError
from src.state.manager import ExecutionRun, StateManager, Task, TaskStatus
from src.testing.quality_gate import QualityGate

logger = logging.getLogger("agent.scheduler.runner")


class DailyExecutionRunner:
    """Master orchestrator for unattended daily runs."""

    def __init__(self, config: Optional[ProjectConfig] = None):
        self.config = config or load_config()
        self.workspace_root = self.config.workspace_root
        self.target_root = self.config.target_project_root

        state_dir = self.workspace_root / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        self.state_manager = StateManager(state_dir / f"{self.config.project_id}_state.db")

        self.lock = ExecutionLock(self.workspace_root, stale_timeout_seconds=self.config.daily_execution_timeout_minutes * 60)
        self.git = GitClient(self.target_root, self.config.repository_url, self.config.base_branch)
        self.notifier = NotificationService(self.config.notifications, self.config.project_name)
        self.reporter = ReportGenerator(self.workspace_root, self.config)
        self.writer = RoadmapWriter(self.target_root, self.config)
        self.provider = get_llm_provider(self.config.llm)

    def run_daily_cycle(self, target_day: Optional[int] = None, dry_run: bool = False, force: bool = False) -> ExecutionRun:
        """Execute the master daily development cycle."""
        run_id = f"run-{uuid.uuid4().hex[:10]}"
        start_time_dt = datetime.now(timezone.utc)
        start_time_iso = start_time_dt.isoformat()
        start_perf = time.time()

        # Step 1: Acquire single-run lock
        self.lock.acquire()
        try:
            # Step 2: Recover any interrupted tasks from prior crashes
            recovered = self.state_manager.recover_interrupted_tasks()
            if recovered:
                logger.info("Recovered %d interrupted task(s) from previous run: %s", len(recovered), recovered)

            # Step 3: Ensure 30-day roadmap exists
            if not self.state_manager.has_roadmap():
                logger.info("Initializing 30-day roadmap...")
                planner = RoadmapGenerator(self.config, self.state_manager, self.provider)
                planner.generate_and_save()

            # Step 4: Identify target task
            if target_day is not None:
                task = self.state_manager.get_task_by_day(target_day)
                if not task:
                    raise ValueError(f"Task for Day {target_day} not found in roadmap.")
            else:
                task = self.state_manager.get_next_incomplete_task()

            if not task:
                logger.info("All 30 milestones are already completed! Nothing to run.")
                summary = self.state_manager.get_progress_summary()
                return ExecutionRun(
                    run_id=run_id,
                    day_number=30,
                    scheduled_time=self.config.daily_run_time,
                    start_time=start_time_iso,
                    end_time=datetime.now(timezone.utc).isoformat(),
                    duration_seconds=round(time.time() - start_perf, 2),
                    status="COMPLETED",
                    tests_passed=True,
                    push_verified=True,
                )

            # Idempotency check: If task is already completed and not force
            if task.status == TaskStatus.COMPLETED and not force:
                logger.info("Day %d (%s) is already COMPLETED. Use --force to rerun.", task.day_number, task.title)
                return ExecutionRun(
                    run_id=run_id,
                    day_number=task.day_number,
                    scheduled_time=self.config.daily_run_time,
                    start_time=start_time_iso,
                    end_time=datetime.now(timezone.utc).isoformat(),
                    duration_seconds=round(time.time() - start_perf, 2),
                    status="SKIPPED",
                    commit_sha=task.commit_sha,
                    tests_passed=True,
                )

            logger.info("Starting execution for Day %02d: %s", task.day_number, task.title)
            self.state_manager.mark_task_in_progress(task.day_number)

            # Step 5: Verify Git environment
            self.git.clone_or_init_repo()

            # Step 6: Execute task via CodingAgent inside target_root
            tools = WorkspaceTools(self.target_root)
            quality_gate = QualityGate(self.target_root, self.config.tech_stack.toolchain)
            agent = CodingAgent(self.config, provider=self.provider, tools=tools, quality_gate=quality_gate)
            exec_result = agent.execute_task(task)

            # Step 7: Check quality gate results
            tests_passed = bool(exec_result.quality_report and exec_result.quality_report.tests_passed)
            quality_passed = exec_result.success

            commit_sha: Optional[str] = None
            push_verified = False

            if not quality_passed:
                error_msg = exec_result.error_message or "Quality checks failed."
                logger.error("Execution failed for Day %d: %s", task.day_number, error_msg)
                self.state_manager.mark_task_failed(task.day_number, error_msg)
                status = "FAILED"
            else:
                # Step 8: Update tracking docs so they get committed alongside the code
                self.state_manager.mark_task_completed(task.day_number)
                all_tasks = self.state_manager.get_all_tasks()
                self.writer.write_roadmap_md(all_tasks)
                self.writer.write_progress_md(all_tasks, self.state_manager.get_progress_summary())

                # Stage changed files + updated docs in target_root
                stage_targets = list(exec_result.changed_files)
                for doc in ["ROADMAP.md", "PROGRESS.md"]:
                    if (self.target_root / doc).exists():
                        stage_targets.append(doc)

                # Step 9: Commit changes
                if self.config.daily_commit_enabled and not dry_run:
                    commit_type = "feat" if task.day_number <= 19 else ("test" if task.day_number <= 25 else "release")
                    commit_message = f"{commit_type}: [Day {task.day_number:02d}] {task.title}"
                    
                    self.git.stage_files(stage_targets)
                    commit_sha = self.git.commit(commit_message)
                    logger.info("Created Git commit: %s (%s)", commit_sha[:8], commit_message)

                    # Update changelog with commit SHA
                    self.writer.update_changelog(task.day_number, task.title, commit_sha, task.description)
                    self.state_manager.mark_task_completed(task.day_number, commit_sha)

                    # Step 10: Push to remote
                    if self.config.daily_push_enabled and self.config.repository_url:
                        push_ok = self.git.push()
                        if push_ok:
                            push_verified = self.git.verify_remote_commit(commit_sha)
                            logger.info("Remote push verification result: %s", push_verified)
                        else:
                            logger.warning("Remote push could not be completed.")

                status = "SUCCESS"

            # Step 11: Generate report
            duration = round(time.time() - start_perf, 2)
            end_time_iso = datetime.now(timezone.utc).isoformat()
            next_task = self.state_manager.get_next_incomplete_task()

            run_record = ExecutionRun(
                run_id=run_id,
                day_number=task.day_number,
                scheduled_time=self.config.daily_run_time,
                start_time=start_time_iso,
                end_time=end_time_iso,
                duration_seconds=duration,
                status=status,
                commit_sha=commit_sha,
                push_verified=push_verified,
                tests_passed=tests_passed,
                error_details=exec_result.error_message,
            )

            report_path = self.reporter.generate_daily_report(
                task=task,
                run=run_record,
                changed_files=exec_result.changed_files,
                quality_report=exec_result.quality_report,
                next_task=next_task,
            )
            run_record.report_path = str(report_path)

            # Record run in SQLite
            self.state_manager.record_run(run_record)

            # Step 12: Notifications
            self.notifier.notify_run_result(task, run_record, success=(status == "SUCCESS"))

            logger.info("Day %d execution cycle finished with status '%s' in %.2fs.", task.day_number, status, duration)
            return run_record

        finally:
            self.lock.release()
