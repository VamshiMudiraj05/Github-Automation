"""Formats and writes ROADMAP.md, PROGRESS.md, and CHANGELOG.md."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List
from src.config import ProjectConfig
from src.state.manager import Task, TaskStatus


class RoadmapWriter:
    """Renders persistent documentation files representing project state."""

    def __init__(self, workspace_root: Path, config: ProjectConfig):
        self.workspace_root = workspace_root
        self.config = config

    def write_roadmap_md(self, tasks: List[Task]) -> Path:
        """Render complete 30-day roadmap with phase groupings, acceptance criteria, and status badges."""
        out_path = self.workspace_root / "ROADMAP.md"

        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        total = len(tasks)
        pct = round((completed / total * 100), 1) if total else 0.0

        lines = [
            f"# 🗺️ 30-Day Engineering Roadmap: {self.config.project_name}",
            "",
            f"> **Project Objective:** {self.config.project_description}",
            f"> **Start Date:** {self.config.project_start_date} | **Schedule:** Daily at {self.config.daily_run_time} ({self.config.timezone})",
            f"> **Overall Progress:** {completed}/{total} Days Completed ({pct}%)",
            "",
            "## 📊 Progress Overview",
            "",
            "| Phase | Days | Focus Area | Status |",
            "| :--- | :--- | :--- | :--- |",
            "| **Phase 1: Foundation** | Days 1–5 | Architecture, Models, Persistence, CI Setup | In Progress |",
            "| **Phase 2: Core Functionality** | Days 6–12 | End-to-End Ingestion, Aggregation, Processing | Planned |",
            "| **Phase 3: Advanced Features** | Days 13–19 | Alerts, Query Engine, Anomaly Detection, Exporters | Planned |",
            "| **Phase 4: Reliability & Polish** | Days 20–25 | Benchmarks, Concurrency, Hardening, 90%+ Test Coverage | Planned |",
            "| **Phase 5: Release & Deployment** | Days 26–30 | Packaging, Docker, Production Verification, Final Docs | Planned |",
            "",
            "---",
            "",
            "## 🗓️ Detailed 30-Day Milestone Breakdown",
            "",
        ]

        current_phase = ""
        for t in sorted(tasks, key=lambda x: x.day_number):
            if t.phase != current_phase:
                current_phase = t.phase
                lines.append(f"### {current_phase}")
                lines.append("")

            status_icon = "⚪ Planned"
            if t.status == TaskStatus.COMPLETED:
                status_icon = "✅ Completed"
            elif t.status == TaskStatus.IN_PROGRESS:
                status_icon = "🔄 In Progress"
            elif t.status == TaskStatus.FAILED:
                status_icon = "❌ Failed (Retrying)"

            sha_str = f" (`{t.commit_sha[:7]}`)" if t.commit_sha else ""
            lines.append(f"#### Day {t.day_number:02d}: {t.title} — {status_icon}{sha_str}")
            lines.append(f"- **Description:** {t.description}")
            lines.append(f"- **Complexity:** `{t.complexity}` | **Dependencies:** `{', '.join(t.dependencies) if t.dependencies else 'None'}`")
            lines.append("- **Acceptance Criteria:**")
            for ac in t.acceptance_criteria:
                checked = "[x]" if t.status == TaskStatus.COMPLETED else "[ ]"
                lines.append(f"  - {checked} {ac}")
            lines.append("- **Key Deliverables:**")
            for d in t.deliverables:
                lines.append(f"  - `{d}`")
            lines.append("")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return out_path

    def write_progress_md(self, tasks: List[Task], summary_stats: dict) -> Path:
        """Write current real-time PROGRESS.md document."""
        out_path = self.workspace_root / "PROGRESS.md"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        completed = summary_stats.get("completed", 0)
        total = summary_stats.get("total_tasks", len(tasks))
        streak = summary_stats.get("streak", 0)
        current_day = summary_stats.get("current_day", 1)
        pct = summary_stats.get("completion_percentage", 0.0)

        # Create progress bar
        bar_len = 25
        filled = int(bar_len * (completed / total)) if total else 0
        progress_bar = f"[{'█' * filled}{'░' * (bar_len - filled)}] {pct}%"

        lines = [
            f"# 📈 Development Progress Tracker — {self.config.project_name}",
            "",
            f"*Last Updated: {now_str}*",
            "",
            "## 🎯 Current Status",
            "",
            f"- **Active Milestone:** Day {current_day:02d} / {total}",
            f"- **Completion:** `{progress_bar}`",
            f"- **Consecutive Daily Streak:** 🔥 **{streak} Days**",
            f"- **Successful Milestones:** {completed} / {total}",
            f"- **Next Execution:** Scheduled at {self.config.daily_run_time} {self.config.timezone}",
            "",
            "## 📋 Milestone Activity Log",
            "",
            "| Day | Title | Complexity | Status | Commit SHA | Last Updated |",
            "| :---: | :--- | :---: | :---: | :---: | :--- |",
        ]

        for t in sorted(tasks, key=lambda x: x.day_number):
            status_text = {
                TaskStatus.COMPLETED: "✅ Completed",
                TaskStatus.IN_PROGRESS: "🔄 In Progress",
                TaskStatus.FAILED: "❌ Failed",
                TaskStatus.PENDING: "⚪ Pending",
                TaskStatus.SKIPPED: "⏭️ Skipped",
            }.get(t.status, str(t.status))

            sha = f"`{t.commit_sha[:7]}`" if t.commit_sha else "-"
            updated = (t.updated_at or t.created_at or "-")[:19]
            lines.append(f"| {t.day_number:02d} | {t.title} | `{t.complexity}` | {status_text} | {sha} | {updated} |")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return out_path

    def update_changelog(self, day_number: int, title: str, commit_sha: str, summary: str) -> Path:
        """Append an entry to CHANGELOG.md following Keep a Changelog standards."""
        out_path = self.workspace_root / "CHANGELOG.md"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        entry = (
            f"\n### Day {day_number:02d} — {title} ({today})\n\n"
            f"- **Commit:** `{commit_sha[:8] if commit_sha else 'Uncommitted'}`\n"
            f"- **Summary:** {summary}\n"
        )

        if not out_path.exists():
            header = (
                f"# Changelog — {self.config.project_name}\n\n"
                "All notable daily development milestones and changes are documented here.\n\n"
                "## Daily Milestone Releases\n"
            )
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(header + entry)
        else:
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(entry)

        return out_path
