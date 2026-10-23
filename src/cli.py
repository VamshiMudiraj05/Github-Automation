"""Rich CLI and interactive setup wizard for Autonomous 30-Day Project Builder Agent."""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import click
import yaml

from src.config import load_config, ProjectConfig
from src.planner.generator import RoadmapGenerator
from src.providers.factory import get_llm_provider
from src.scheduler.runner import DailyExecutionRunner
from src.state.manager import StateManager, TaskStatus


@click.group()
def cli():
    """Autonomous 30-Day Project Builder Agent CLI."""
    pass


@cli.command("init")
def cmd_init():
    """Interactive wizard to configure your project, repository, and AI provider."""
    click.secho("\n🚀 Welcome to the Autonomous 30-Day Project Builder Setup Wizard!", fg="cyan", bold=True)
    click.echo("This wizard will configure your 30-day automated software project.\n")

    # 1. Project details
    name = click.prompt("Project Name", default="CloudTelemetry: Distributed Metrics & Tracing Agent")
    desc = click.prompt("Project Description", default="High-performance telemetry ingestion and metrics aggregation engine with real-time alerting and timeseries persistence.")
    
    click.echo("\nEnter up to 4 core goals (press Enter with empty line when finished):")
    goals = []
    default_goals = [
        "Build an asynchronous telemetry collector capable of ingesting high-volume metrics",
        "Implement sliding-window metrics aggregation, quantile calculation, and rate limiting",
        "Provide robust timeseries storage with pluggable persistence adapters (SQLite, in-memory)",
        "Deliver comprehensive unit and benchmark test suites with 90%+ coverage",
    ]
    for i in range(4):
        goal = click.prompt(f"Goal {i+1}", default=default_goals[i] if i < len(default_goals) else "", show_default=True)
        if goal.strip():
            goals.append(goal.strip())

    # 2. Tech stack
    lang = click.prompt("Primary Language", default="Python")
    runtime = click.prompt("Runtime Environment", default="Python 3.12+")

    # 3. Git Repo
    repo_url = click.prompt("GitHub Repository URL", default="https://github.com/vamsh/cloudtelemetry-agent")
    base_branch = click.prompt("Base Branch", default="main")

    # 4. Schedule & Timezone
    timezone_str = click.prompt("Timezone", default="Asia/Kolkata")
    run_time = click.prompt("Daily Run Time (HH:MM)", default="18:00")

    # 5. LLM Provider
    click.echo("\nSelect your LLM Provider:")
    click.echo("  1. Google Gemini (Recommended - gemini-2.5-flash)")
    click.echo("  2. OpenAI / DeepSeek / Groq")
    click.echo("  3. Anthropic Claude")
    click.echo("  4. Mock Provider (Offline testing without API keys)")
    provider_choice = click.prompt("Choice", type=click.IntRange(1, 4), default=1)

    provider_map = {1: "gemini", 2: "openai", 3: "anthropic", 4: "mock"}
    provider_name = provider_map[provider_choice]
    
    default_models = {
        "gemini": "gemini-2.5-flash",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-20241022",
        "mock": "mock-model",
    }
    model_name = click.prompt("Model Name", default=default_models[provider_name])

    api_key = ""
    if provider_name != "mock":
        api_key = click.prompt(f"Enter {provider_name.upper()} API Key (stored in .env)", hide_input=True, default="")

    github_token = click.prompt("Enter GitHub Personal Access Token (stored in .env, optional for dry-run)", hide_input=True, default="")

    # Write project.config.yaml
    config_dict = {
        "project_name": name,
        "project_description": desc,
        "project_goals": goals,
        "tech_stack": {
            "language": lang,
            "runtime": runtime,
            "frameworks": ["Click", "PyYAML", "SQLite", "Pytest"],
            "toolchain": {
                "test_command": "pytest tests/ -v",
                "lint_command": "python -m py_compile src/**/*.py",
                "build_command": "python -m py_compile src/main.py",
            },
        },
        "repository_url": repo_url,
        "base_branch": base_branch,
        "timezone": timezone_str,
        "daily_run_time": run_time,
        "project_start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "project_duration_days": 30,
        "daily_commit_enabled": True,
        "daily_push_enabled": True,
        "run_tests_before_commit": True,
        "require_meaningful_changes": True,
        "max_retries": 3,
        "daily_execution_timeout_minutes": 25,
        "llm": {
            "provider": provider_name,
            "model": model_name,
            "temperature": 0.2,
            "max_output_tokens": 4096,
        },
        "notifications": {
            "notification_email": "",
            "notification_webhook": "",
            "notify_on_success": True,
            "notify_on_failure": True,
        },
    }

    config_path = Path.cwd() / "project.config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_dict, f, sort_keys=False)

    # Write .env
    env_lines = [
        f"LLM_PROVIDER={provider_name}",
        f"LLM_MODEL={model_name}",
    ]
    if provider_name == "gemini" and api_key:
        env_lines.append(f"GEMINI_API_KEY={api_key}")
    elif provider_name == "openai" and api_key:
        env_lines.append(f"OPENAI_API_KEY={api_key}")
    elif provider_name == "anthropic" and api_key:
        env_lines.append(f"ANTHROPIC_API_KEY={api_key}")
    if github_token:
        env_lines.append(f"GITHUB_TOKEN={github_token}")

    env_path = Path.cwd() / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")

    click.secho("\n✅ Configuration saved to project.config.yaml and .env!", fg="green", bold=True)
    click.echo("Next steps:")
    click.echo("  1. Run 'python main.py plan' to generate your 30-day roadmap.")
    click.echo("  2. Run 'python main.py verify' to validate your toolchain and AI connection.")
    click.echo("  3. Run 'python main.py run --day 1' to execute your first day's milestone.\n")


@cli.command("plan")
@click.option("--force", is_flag=True, help="Force regenerate roadmap even if one exists.")
def cmd_plan(force: bool):
    """Generate and view the 30-day technical roadmap."""
    config = load_config()
    state_mgr = StateManager(config.workspace_root / "state" / "agent_state.db")
    generator = RoadmapGenerator(config, state_mgr)

    click.secho(f"\n🗺️ Generating 30-Day Technical Roadmap for: {config.project_name}...", fg="cyan")
    tasks = generator.generate_and_save(force=force)

    click.secho(f"✅ Generated {len(tasks)} daily milestones successfully!", fg="green", bold=True)
    click.echo("Saved to ROADMAP.md, PROGRESS.md, and persistent state database.")


@cli.command("run")
@click.option("--day", type=int, default=None, help="Target specific day number (1-30). Default is next pending day.")
@click.option("--dry-run", is_flag=True, help="Execute coding and testing without committing or pushing.")
@click.option("--force", is_flag=True, help="Force run task even if already marked completed.")
def cmd_run(day: Optional[int], dry_run: bool, force: bool):
    """Execute the daily development workflow."""
    config = load_config()
    runner = DailyExecutionRunner(config)

    click.secho(f"\n⚡ Starting Autonomous Execution Run (Day: {day or 'Auto-Next'})...", fg="cyan", bold=True)
    try:
        run_record = runner.run_daily_cycle(target_day=day, dry_run=dry_run, force=force)
        if run_record.status == "SUCCESS":
            click.secho(f"🎉 Day {run_record.day_number} executed successfully!", fg="green", bold=True)
            click.echo(f"   Commit SHA: {run_record.commit_sha or 'Dry Run'}")
            click.echo(f"   Report: {run_record.report_path}")
            click.echo(f"   Duration: {run_record.duration_seconds}s")
        elif run_record.status == "SKIPPED":
            click.secho(f"⏭️ Day {run_record.day_number} was skipped (already completed).", fg="yellow")
        else:
            click.secho(f"❌ Day {run_record.day_number} failed with status: {run_record.status}", fg="red", bold=True)
            click.echo(f"   Error: {run_record.error_details}")
            sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Execution encountered fatal error: {e}", fg="red", bold=True)
        sys.exit(1)


@cli.command("status")
def cmd_status():
    """Display overall progress, streak, and milestone activity."""
    config = load_config()
    state_mgr = StateManager(config.workspace_root / "state" / "agent_state.db")
    summary = state_mgr.get_progress_summary()
    tasks = state_mgr.get_all_tasks()

    click.secho(f"\n📊 Project Progress: {config.project_name}", fg="cyan", bold=True)
    click.echo(f"Schedule: Daily at {config.daily_run_time} ({config.timezone}) | Target: 30 Days")
    click.echo(f"Overall Progress: {summary['completed']}/{summary['total_tasks']} Milestones ({summary['completion_percentage']}%)")
    click.echo(f"Current Daily Streak: 🔥 {summary['streak']} Days")
    click.echo(f"Current Active Milestone: Day {summary['current_day']}\n")

    click.echo(f"{'Day':<5} {'Title':<45} {'Complexity':<12} {'Status':<15} {'Commit':<10}")
    click.echo("-" * 90)
    for t in sorted(tasks, key=lambda x: x.day_number):
        status_color = "green" if t.status == TaskStatus.COMPLETED else ("yellow" if t.status == TaskStatus.IN_PROGRESS else "white")
        sha = t.commit_sha[:7] if t.commit_sha else "-"
        title_trunc = (t.title[:42] + "...") if len(t.title) > 42 else t.title
        click.echo(
            f"{t.day_number:<5} {title_trunc:<45} {t.complexity:<12} "
            + click.style(f"{t.status.value:<15}", fg=status_color)
            + f" {sha:<10}"
        )


@cli.command("verify")
def cmd_verify():
    """Verify toolchain, git repo, secret scanner, and LLM connectivity."""
    config = load_config()
    click.secho(f"\n🔍 Verifying Agent Environment for: {config.project_name}...", fg="cyan", bold=True)

    # 1. Check Toolchain
    click.echo("1. Checking test toolchain...", nl=False)
    from src.testing.quality_gate import QualityGate
    qgate = QualityGate(config.workspace_root, config.tech_stack.toolchain)
    tests_ok, out = qgate.run_tests()
    if tests_ok:
        click.secho(" [OK]", fg="green")
    else:
        click.secho(f" [WARN: {out[:60]}]", fg="yellow")

    # 2. Check Git
    click.echo("2. Checking Git repository...", nl=False)
    from src.git.client import GitClient
    git = GitClient(config.workspace_root, config.repository_url, config.base_branch)
    if git.is_git_repo():
        status = git.get_status()
        click.secho(f" [OK] Branch: {status.current_branch}", fg="green")
    else:
        click.secho(" [Repository not yet initialized - will auto-init on first run]", fg="yellow")

    # 3. Check LLM Provider
    click.echo(f"3. Checking LLM Provider ({config.llm.provider}: {config.llm.model})...", nl=False)
    provider = get_llm_provider(config.llm)
    if provider.health_check():
        click.secho(" [OK Connected]", fg="green")
    else:
        click.secho(" [WARN: Health check failed - check API key in .env]", fg="yellow")

    click.secho("\nVerification complete.\n", fg="cyan")


@cli.command("daemon")
def cmd_daemon():
    """Run local persistent scheduler daemon that fires every day at configured time."""
    config = load_config()
    click.secho(f"\n⏰ Starting local scheduler daemon for {config.project_name}...", fg="cyan", bold=True)
    click.echo(f"Configured schedule: Every day at {config.daily_run_time} ({config.timezone}).")
    click.echo("Press Ctrl+C to stop.\n")

    runner = DailyExecutionRunner(config)
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        if current_time_str == config.daily_run_time:
            click.echo(f"[{now.isoformat()}] Scheduled trigger time reached! Running daily cycle...")
            try:
                runner.run_daily_cycle()
            except Exception as e:
                click.secho(f"Execution error: {e}", fg="red")
            # Sleep 70 seconds to avoid duplicate firing in the same minute
            time.sleep(70)
        else:
            time.sleep(20)


def main():
    cli()


if __name__ == "__main__":
    main()
