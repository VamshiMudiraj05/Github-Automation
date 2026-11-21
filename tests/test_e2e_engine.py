"""End-to-end integration tests for DailyExecutionRunner."""

import subprocess
from pathlib import Path
from src.config import load_config
from src.providers.mock_provider import MockLLMProvider
from src.scheduler.runner import DailyExecutionRunner
from src.state.manager import TaskStatus


def test_e2e_daily_run_cycle(tmp_path: Path):
    config = load_config(Path("project.config.yaml"))
    config.workspace_root = tmp_path
    config.daily_push_enabled = False  # Offline test (local commits only)
    config.tech_stack.toolchain.test_command = "python -c \"exit(0)\""
    config.tech_stack.toolchain.lint_command = ""
    config.tech_stack.toolchain.build_command = ""

    # Initialize a clean git repo in tmp_path
    subprocess.run(["git", "init", "-b", "main"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "CI Runner"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=str(tmp_path), check=True)

    # Initialize runner with mock provider
    runner = DailyExecutionRunner(config)
    runner.provider = MockLLMProvider()

    # Run Day 1
    run1 = runner.run_daily_cycle(target_day=1)
    assert run1.status == "SUCCESS"
    assert run1.day_number == 1
    assert run1.commit_sha is not None
    assert Path(run1.report_path).exists()

    # Verify multiple granular commits were created (dark green activity)
    rev_count = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=str(runner.target_root),
        capture_output=True,
        text=True,
        check=True,
    )
    assert int(rev_count.stdout.strip()) >= 3

    # Verify task 1 is marked COMPLETED in state store
    t1 = runner.state_manager.get_task_by_day(1)
    assert t1.status == TaskStatus.COMPLETED
    assert t1.commit_sha == run1.commit_sha

    # Verify next incomplete task is now Day 2
    next_task = runner.state_manager.get_next_incomplete_task()
    assert next_task.day_number == 2

    # Verify daily report exists and has markdown content
    report_content = Path(run1.report_path).read_text(encoding="utf-8")
    assert "Daily Engineering Report — Day 01" in report_content
    assert "Acceptance Criteria Verification" in report_content

    # Idempotency check: Re-running Day 1 should be skipped
    run1_repeat = runner.run_daily_cycle(target_day=1)
    assert run1_repeat.status == "SKIPPED"


def test_e2e_resume_interrupted_run(tmp_path: Path):
    config = load_config(Path("project.config.yaml"))
    config.workspace_root = tmp_path
    config.daily_push_enabled = False
    config.tech_stack.toolchain.test_command = "python -c \"exit(0)\""
    config.tech_stack.toolchain.lint_command = ""
    config.tech_stack.toolchain.build_command = ""

    subprocess.run(["git", "init", "-b", "main"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "CI Runner"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=str(tmp_path), check=True)

    runner = DailyExecutionRunner(config)
    runner.provider = MockLLMProvider()

    # Pre-populate roadmap
    from src.planner.generator import RoadmapGenerator
    planner = RoadmapGenerator(config, runner.state_manager, runner.provider)
    planner.generate_and_save()

    # Artificially leave Day 2 in IN_PROGRESS
    runner.state_manager.mark_task_completed(1, commit_sha="dummy1")
    runner.state_manager.mark_task_in_progress(2)

    # Next run should recover Day 2 to PENDING and then successfully execute it
    run_recovery = runner.run_daily_cycle()
    assert run_recovery.day_number == 2
    assert run_recovery.status == "SUCCESS"

    t2 = runner.state_manager.get_task_by_day(2)
    assert t2.status == TaskStatus.COMPLETED


def test_e2e_all_milestones_completed(tmp_path: Path):
    config = load_config(Path("project.config.yaml"))
    config.workspace_root = tmp_path
    config.daily_push_enabled = False

    subprocess.run(["git", "init", "-b", "main"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "CI Runner"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=str(tmp_path), check=True)

    runner = DailyExecutionRunner(config)
    runner.provider = MockLLMProvider()

    from src.planner.generator import RoadmapGenerator
    planner = RoadmapGenerator(config, runner.state_manager, runner.provider)
    planner.generate_and_save()

    # Mark all tasks as completed
    for task in runner.state_manager.get_all_tasks():
        runner.state_manager.mark_task_completed(task.day_number, commit_sha=f"sha_{task.day_number}")

    # Running daily cycle when all are completed should return COMPLETED status
    run_completed = runner.run_daily_cycle()
    assert run_completed.status == "COMPLETED"
    assert run_completed.day_number == len(runner.state_manager.get_all_tasks())


def test_cli_run_handles_completed_status(monkeypatch, tmp_path: Path):
    from click.testing import CliRunner
    from src.cli import cli
    from src.state.manager import ExecutionRun

    # Mock runner.run_daily_cycle to return COMPLETED status
    mock_run = ExecutionRun(
        run_id="test_run",
        day_number=30,
        scheduled_time="06:17",
        start_time="2026-11-21T00:00:00Z",
        duration_seconds=1.5,
        status="COMPLETED",
        tests_passed=True,
        push_verified=True,
    )

    class DummyRunner:
        def __init__(self, config):
            pass
        def run_daily_cycle(self, target_day=None, dry_run=False, force=False):
            return mock_run

    monkeypatch.setattr("src.cli.DailyExecutionRunner", DummyRunner)

    runner = CliRunner()
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0
    assert "All milestones are completed!" in result.output

