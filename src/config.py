"""Configuration loader, schema validator, and environment resolver."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class ToolchainConfig:
    test_command: str = "python -m pytest tests/ -v"
    lint_command: Optional[str] = None
    build_command: Optional[str] = None


@dataclass
class TechStackConfig:
    language: str = "Python"
    runtime: str = "Python 3.12+"
    frameworks: List[str] = field(default_factory=list)
    toolchain: ToolchainConfig = field(default_factory=ToolchainConfig)


@dataclass
class LLMConfig:
    provider: str = "gemini"  # gemini | openai | anthropic | mock
    model: str = "gemini-2.5-flash"
    temperature: float = 0.2
    max_output_tokens: int = 4096
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class NotificationConfig:
    notification_email: Optional[str] = None
    notification_webhook: Optional[str] = None
    notify_on_success: bool = True
    notify_on_failure: bool = True
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_to_email: Optional[str] = None


@dataclass
class ProjectConfig:
    # Metadata
    project_name: str
    project_description: str
    project_goals: List[str]
    tech_stack: TechStackConfig

    # Git
    repository_url: str
    base_branch: str = "main"

    # Schedule
    timezone: str = "Asia/Kolkata"
    daily_run_time: str = "18:00"
    project_start_date: str = "2026-10-24"
    project_duration_days: int = 30

    # Automation Rules
    daily_commit_enabled: bool = True
    daily_push_enabled: bool = True
    run_tests_before_commit: bool = True
    require_meaningful_changes: bool = True
    max_retries: int = 3
    daily_execution_timeout_minutes: int = 25

    # Sub-configs
    llm: LLMConfig = field(default_factory=LLMConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)

    # Runtime computed
    workspace_root: Path = field(default_factory=Path.cwd)

    def get_cron_schedule_utc(self) -> str:
        """Convert daily_run_time from configured timezone (default Asia/Kolkata UTC+5:30) to UTC cron expression.
        
        For Asia/Kolkata (UTC+5:30):
        18:00 IST -> 18*60 - 330 mins = 1080 - 330 = 750 mins -> 12:30 UTC -> '30 12 * * *'
        """
        match = re.match(r"^(\d{1,2}):(\d{2})$", self.daily_run_time.strip())
        if not match:
            return "30 12 * * *"  # default safe fallback: 18:00 IST = 12:30 UTC
        
        hour = int(match.group(1))
        minute = int(match.group(2))

        # Timezone offset handling
        # Asia/Kolkata is UTC+05:30
        if "Kolkata" in self.timezone or "IST" in self.timezone:
            total_minutes = hour * 60 + minute - 330
            if total_minutes < 0:
                total_minutes += 24 * 60
            utc_hour = (total_minutes // 60) % 24
            utc_minute = total_minutes % 60
            return f"{utc_minute} {utc_hour} * * *"
        
        # Default assume UTC
        return f"{minute} {hour} * * *"


def load_env_file(dotenv_path: Optional[Path] = None) -> None:
    """Manually parse .env file into os.environ if present without requiring external dotenv pkg."""
    target = dotenv_path or (Path.cwd() / ".env")
    if not target.exists():
        return
    try:
        with open(target, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass


def load_config(config_path: Optional[Path] = None) -> ProjectConfig:
    """Load configuration from project.config.yaml and resolve environment variables."""
    load_env_file()

    path = config_path or (Path.cwd() / "project.config.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f) or {}

    # Extract toolchain
    raw_stack = raw.get("tech_stack", {})
    raw_toolchain = raw_stack.get("toolchain", {}) if isinstance(raw_stack, dict) else {}
    toolchain = ToolchainConfig(
        test_command=raw_toolchain.get("test_command", "pytest tests/ -v"),
        lint_command=raw_toolchain.get("lint_command"),
        build_command=raw_toolchain.get("build_command"),
    )

    tech_stack = TechStackConfig(
        language=raw_stack.get("language", "Python") if isinstance(raw_stack, dict) else "Python",
        runtime=raw_stack.get("runtime", "Python 3.12+") if isinstance(raw_stack, dict) else "Python 3.12+",
        frameworks=raw_stack.get("frameworks", []) if isinstance(raw_stack, dict) else [],
        toolchain=toolchain,
    )

    # Extract LLM Config
    raw_llm = raw.get("llm", {})
    llm_provider = os.getenv("LLM_PROVIDER", raw_llm.get("provider", "gemini")).lower()
    
    # Resolve API Key from env
    api_key = None
    if llm_provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
    elif llm_provider in ("openai", "deepseek", "groq"):
        api_key = os.getenv("OPENAI_API_KEY")
    elif llm_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")

    llm = LLMConfig(
        provider=llm_provider,
        model=os.getenv("LLM_MODEL", raw_llm.get("model", "gemini-2.5-flash")),
        temperature=float(raw_llm.get("temperature", 0.2)),
        max_output_tokens=int(raw_llm.get("max_output_tokens", 4096)),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", raw_llm.get("base_url")),
    )

    # Extract Notifications
    raw_notif = raw.get("notifications", {})
    notif = NotificationConfig(
        notification_email=raw_notif.get("notification_email") or os.getenv("NOTIFICATION_EMAIL"),
        notification_webhook=raw_notif.get("notification_webhook") or os.getenv("NOTIFICATION_WEBHOOK"),
        notify_on_success=bool(raw_notif.get("notify_on_success", True)),
        notify_on_failure=bool(raw_notif.get("notify_on_failure", True)),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", 587)),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        smtp_to_email=os.getenv("SMTP_TO_EMAIL"),
    )

    return ProjectConfig(
        project_name=raw.get("project_name", "Autonomous Software Project"),
        project_description=raw.get("project_description", "An autonomous 30-day software project"),
        project_goals=raw.get("project_goals", ["Build a complete software project in 30 days"]),
        tech_stack=tech_stack,
        repository_url=raw.get("repository_url", ""),
        base_branch=raw.get("base_branch", "main"),
        timezone=raw.get("timezone", "Asia/Kolkata"),
        daily_run_time=raw.get("daily_run_time", "18:00"),
        project_start_date=raw.get("project_start_date", "2026-10-24"),
        project_duration_days=int(raw.get("project_duration_days", 30)),
        daily_commit_enabled=bool(raw.get("daily_commit_enabled", True)),
        daily_push_enabled=bool(raw.get("daily_push_enabled", True)),
        run_tests_before_commit=bool(raw.get("run_tests_before_commit", True)),
        require_meaningful_changes=bool(raw.get("require_meaningful_changes", True)),
        max_retries=int(raw.get("max_retries", 3)),
        daily_execution_timeout_minutes=int(raw.get("daily_execution_timeout_minutes", 25)),
        llm=llm,
        notifications=notif,
        workspace_root=path.parent,
    )
