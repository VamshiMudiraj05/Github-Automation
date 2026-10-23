"""Dispatches execution alerts and daily summaries via Webhooks (Discord/Slack) and Email."""

import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import requests

from src.config import NotificationConfig
from src.state.manager import Task, ExecutionRun

logger = logging.getLogger("agent.notifications")


class NotificationService:
    """Delivers milestone progress notifications and critical error alerts."""

    def __init__(self, config: NotificationConfig, project_name: str):
        self.config = config
        self.project_name = project_name

    def notify_run_result(
        self,
        task: Task,
        run: ExecutionRun,
        success: bool,
    ) -> None:
        """Send notifications if enabled."""
        if success and not self.config.notify_on_success:
            return
        if not success and not self.config.notify_on_failure:
            return

        subject = (
            f"[{'SUCCESS' if success else 'FAILURE'}] {self.project_name} — Day {task.day_number:02d}: {task.title}"
        )
        body = (
            f"Project: {self.project_name}\n"
            f"Milestone: Day {task.day_number:02d} - {task.title}\n"
            f"Status: {run.status}\n"
            f"Tests Passed: {run.tests_passed}\n"
            f"Commit: {run.commit_sha or 'None'}\n"
            f"Push Verified: {run.push_verified}\n"
            f"Duration: {run.duration_seconds:.2f}s\n"
        )
        if run.error_details:
            body += f"\nErrors:\n{run.error_details[:1000]}"

        # 1. Send webhook
        if self.config.notification_webhook:
            self._send_webhook(subject, body, success)

        # 2. Send email
        if self.config.smtp_host and self.config.smtp_to_email:
            self._send_email(subject, body)

    def _send_webhook(self, title: str, text: str, success: bool) -> None:
        try:
            url = self.config.notification_webhook
            color = 0x00FF00 if success else 0xFF0000
            payload = {
                "username": "Autonomous 30-Day Agent",
                "content": title,
                "embeds": [
                    {
                        "title": title,
                        "description": f"```{text}```",
                        "color": color,
                    }
                ],
            }
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.warning("Failed to deliver webhook notification: %s", e)

    def _send_email(self, subject: str, body: str) -> None:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_user or "agent@autonomous-project.local"
            msg["To"] = self.config.smtp_to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=15) as server:
                server.starttls()
                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)
        except Exception as e:
            logger.warning("Failed to send email notification: %s", e)
