"""Daily Execution Runner orchestrating the complete unattended development cycle."""

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

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
                self.state_manager.mark_task_completed(task.day_number)
                all_tasks = self.state_manager.get_all_tasks()

                # Step 8-10: Granular multi-commit & multi-push strategy (3-5 commits per day for dark green graph)
                commit_sha, push_verified, all_shas = self._commit_and_push_milestone(
                    task=task,
                    all_tasks=all_tasks,
                    changed_files=exec_result.changed_files,
                    dry_run=dry_run,
                )
                if commit_sha:
                    self.state_manager.mark_task_completed(task.day_number, commit_sha)

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

    def _commit_and_push_milestone(
        self,
        task: Task,
        all_tasks: List[Task],
        changed_files: List[str],
        dry_run: bool,
    ) -> Tuple[Optional[str], bool, List[str]]:
        """Commit daily changes in 3-5 granular stages and push to remote for dark-green GitHub activity."""
        if not self.config.daily_commit_enabled or dry_run:
            return None, False, []

        commit_shas: List[str] = []

        # Partition files into logical functional tiers
        code_files = [
            f for f in changed_files
            if not f.startswith("tests/") and not f.startswith("docs/") and not f.endswith(".md")
        ]
        test_files = [
            f for f in changed_files
            if f.startswith("tests/") or "test_" in f
        ]
        doc_files = [
            f for f in changed_files
            if f.startswith("docs/") or (f.endswith(".md") and f not in ("ROADMAP.md", "PROGRESS.md", "CHANGELOG.md"))
        ]
        other_files = [
            f for f in changed_files
            if f not in code_files and f not in test_files and f not in doc_files
        ]

        def _do_commit(msg: str, files_to_stage: List[str]) -> Optional[str]:
            if files_to_stage:
                self.git.stage_files(files_to_stage)
            if self.git.has_staged_changes():
                sha = self.git.commit(msg)
                logger.info("Created granular commit [%d/5]: %s (%s)", len(commit_shas) + 1, sha[:8], msg)
                commit_shas.append(sha)
                if self.config.daily_push_enabled and self.config.repository_url:
                    self.git.push()
                return sha
            return None

        commit_prefix = "feat" if task.day_number <= 19 else ("test" if task.day_number <= 25 else "release")

        # 1. Implementation files (split into 2 commits if multiple exist)
        if len(code_files) > 1:
            mid = max(1, len(code_files) // 2)
            _do_commit(f"{commit_prefix}(core): [Day {task.day_number:02d}] implement {task.title} components", code_files[:mid])
            _do_commit(f"{commit_prefix}(service): [Day {task.day_number:02d}] add domain logic and utilities for {task.title}", code_files[mid:])
        elif code_files:
            _do_commit(f"{commit_prefix}(core): [Day {task.day_number:02d}] implement {task.title}", code_files)
        elif doc_files and len(doc_files) > 1:
            mid = max(1, len(doc_files) // 2)
            _do_commit(f"docs(spec): [Day {task.day_number:02d}] define specifications for {task.title}", doc_files[:mid])
            _do_commit(f"docs(spec): [Day {task.day_number:02d}] document contracts for {task.title}", doc_files[mid:])
        elif other_files:
            _do_commit(f"{commit_prefix}(scaffold): [Day {task.day_number:02d}] scaffold assets for {task.title}", other_files)

        # 2. Test suite & verification specs
        if test_files:
            _do_commit(f"test(unit): [Day {task.day_number:02d}] add automated unit tests and assertions for {task.title}", test_files)
        elif not code_files and doc_files and not self.git.has_staged_changes() and len(commit_shas) < 2:
            _do_commit(f"docs(arch): [Day {task.day_number:02d}] add architecture specifications for {task.title}", doc_files)

        # 3. Milestone Documentation & Roadmap
        self.writer.write_roadmap_md(all_tasks)
        roadmap_targets = ["ROADMAP.md"]
        if doc_files:
            roadmap_targets.extend(doc_files)
        _do_commit(f"docs(roadmap): [Day {task.day_number:02d}] update 30-day technical roadmap", roadmap_targets)

        # 4. Changelog release notes
        last_sha = commit_shas[-1] if commit_shas else "milestone"
        self.writer.update_changelog(task.day_number, task.title, last_sha, task.description)
        _do_commit(f"chore(changelog): [Day {task.day_number:02d}] record changelog release notes for {task.title}", ["CHANGELOG.md"])

        # 5. Progress tracker & streak metrics
        self.writer.write_progress_md(all_tasks, self.state_manager.get_progress_summary())
        _do_commit(f"chore(tracker): [Day {task.day_number:02d}] update milestone progress and streak metrics", ["PROGRESS.md"])

        # Stage any remaining modified or untracked workspace files
        status = self.git.get_status()
        remaining = [f for f in (status.modified_files + status.untracked_files) if not f.startswith("state/")]
        if remaining:
            _do_commit(f"chore(sync): [Day {task.day_number:02d}] synchronize workspace artifacts", remaining)

        # Guarantee at least 3 to 5 commits if milestone had few files
        while len(commit_shas) < 3:
            self.writer.write_progress_md(all_tasks, self.state_manager.get_progress_summary())
            c_sha = _do_commit(f"chore(checkpoint): [Day {task.day_number:02d}] verify automated execution checkpoint ({len(commit_shas) + 1})", ["PROGRESS.md"])
            if not c_sha:
                break

        final_sha = commit_shas[-1] if commit_shas else None
        push_verified = False
        if final_sha and self.config.daily_push_enabled and self.config.repository_url:
            self.git.push()
            push_verified = self.git.verify_remote_commit(final_sha)

        logger.info("Milestone Day %d completed with %d granular commit(s) pushed.", task.day_number, len(commit_shas))
        return final_sha, push_verified, commit_shas
