"""Generates comprehensive daily execution markdown reports under reports/daily/."""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from src.config import ProjectConfig
from src.state.manager import Task, ExecutionRun
from src.testing.quality_gate import QualityReport


class ReportGenerator:
    """Creates structured, permanent audit reports of daily development runs."""

    def __init__(self, workspace_root: Path, config: ProjectConfig):
        self.workspace_root = workspace_root
        self.config = config
        self.reports_dir = workspace_root / "reports" / "daily"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_report(
        self,
        task: Task,
        run: ExecutionRun,
        changed_files: List[str],
        quality_report: Optional[QualityReport] = None,
        next_task: Optional[Task] = None,
    ) -> Path:
        """Write formatted Markdown report for today's run."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        report_filename = f"{date_str}-day-{task.day_number:02d}.md"
        report_path = self.reports_dir / report_filename

        tests_status_badge = "✅ PASSED" if run.tests_passed else "❌ FAILED"
        push_badge = "✅ VERIFIED ON GITHUB" if run.push_verified else "⚪ LOCAL / PENDING"
        commit_badge = f"`{run.commit_sha[:8]}`" if run.commit_sha else "*None (Checks Failed)*"

        lines = [
            f"# 📋 Daily Engineering Report — Day {task.day_number:02d}: {task.title}",
            "",
            f"> **Project:** {self.config.project_name}",
            f"> **Date:** {date_str} | **Execution Duration:** {run.duration_seconds:.2f}s | **Status:** {run.status}",
            "",
            "## 🎯 Milestone Objective",
            f"{task.description}",
            "",
            "### Acceptance Criteria Verification",
        ]

        for ac in task.acceptance_criteria:
            check = "[x]" if run.status == "SUCCESS" else "[ ]"
            lines.append(f"- {check} {ac}")

        lines.extend([
            "",
            "## 🛠️ Work Attempted & Files Changed",
            f"A total of **{len(changed_files)}** file(s) were modified or generated:",
            "",
        ])

        if changed_files:
            for f in changed_files:
                lines.append(f"- `{f}`")
        else:
            lines.append("- *No files modified.*")

        lines.extend([
            "",
            "## 🧪 Quality Assurance & Test Verification",
            "",
            f"- **Automated Tests:** {tests_status_badge}",
            f"- **Diff & Security Validation:** {'✅ Clean (0 secrets detected)' if quality_report and quality_report.diff_valid else '⚠️ Warnings recorded'}",
            f"- **Build Verification:** {'✅ Clean build' if quality_report and quality_report.build_passed else '⚪ Not applicable'}",
            "",
        ])

        if quality_report and quality_report.test_output:
            lines.extend([
                "### Test Execution Details",
                "```text",
                quality_report.test_output[:2000],
                "```",
                "",
            ])

        lines.extend([
            "## 🚀 Git & Deployment Tracking",
            "",
            f"- **Commit SHA:** {commit_badge}",
            f"- **Target Branch:** `{self.config.base_branch}`",
            f"- **Remote Push Status:** {push_badge}",
            "",
            "## 🔄 Errors & Recovery Diagnostics",
        ])

        if run.error_details:
            lines.extend([
                "```text",
                run.error_details[:2000],
                "```",
                "",
            ])
        else:
            lines.append("- *Execution finished cleanly without unhandled exceptions.*")
            lines.append("")

        lines.extend([
            "## ⏭️ Next Scheduled Task",
        ])

        if next_task:
            lines.extend([
                f"- **Upcoming Milestone:** Day {next_task.day_number:02d} — {next_task.title}",
                f"- **Phase:** {next_task.phase}",
                f"- **Scheduled At:** 6:00 PM IST (12:30 UTC)",
            ])
        else:
            lines.append("- 🎉 **Project complete! All 30 milestones executed.**")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return report_path
