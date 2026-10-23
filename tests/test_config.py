"""Tests for configuration loading, validation, and timezone conversions."""

from pathlib import Path
import pytest
from src.config import load_config, ProjectConfig, TechStackConfig, LLMConfig


def test_load_default_config(tmp_path: Path):
    config = load_config(Path("project.config.yaml"))
    assert config.project_name != ""
    assert config.project_duration_days == 30
    assert config.timezone == "Asia/Kolkata"
    assert config.daily_run_time == "18:00"


def test_cron_conversion_ist_to_utc():
    config = ProjectConfig(
        project_name="Test",
        project_description="Test desc",
        project_goals=["Goal 1"],
        tech_stack=TechStackConfig(),
        repository_url="https://github.com/test/repo",
        timezone="Asia/Kolkata",
        daily_run_time="18:00",
    )
    # 18:00 IST is 12:30 UTC
    cron = config.get_cron_schedule_utc()
    assert cron == "30 12 * * *"


def test_cron_conversion_custom_utc():
    config = ProjectConfig(
        project_name="Test",
        project_description="Test desc",
        project_goals=["Goal 1"],
        tech_stack=TechStackConfig(),
        repository_url="https://github.com/test/repo",
        timezone="UTC",
        daily_run_time="14:15",
    )
    cron = config.get_cron_schedule_utc()
    assert cron == "15 14 * * *"
