"""
Notification Service.
Sends alerts via multiple channels when analytics identify critical findings.
Supports logging (always), email (via SES/SendGrid), and Slack webhooks.
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends analytics alerts through configured channels."""

    def __init__(self):
        self.channels = self._configure_channels()
        self._alert_history = []

    def send_alert(self, alert):
        """
        Send an alert through all configured channels.

        Args:
            alert: dict with 'type', 'message', and 'priority'.
        """
        alert["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._alert_history.append(alert)

        logger.info(
            f"[ALERT] [{alert.get('priority', 'info').upper()}] "
            f"{alert.get('type')}: {alert.get('message')}"
        )

        for channel in self.channels:
            try:
                channel.send(alert)
            except Exception as e:
                logger.error(f"Failed to send via {channel.name}: {e}")

    def send_daily_summary(self, results):
        """Send a formatted daily analytics summary."""
        summary_lines = [
            "=== Salesforce Analytics Daily Summary ===",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]

        # Lead scoring summary
        lead_data = results.get("lead_scoring", {})
        if lead_data:
            dist = lead_data.get("distribution", {})
            summary_lines.extend([
                "--- Lead Scoring ---",
                f"Total leads scored: {lead_data.get('leads_scored', 0)}",
                f"Average score: {dist.get('average_score', 'N/A')}",
                f"Critical priority: {dist.get('priority_breakdown', {}).get('Critical', 0)}",
                f"High priority: {dist.get('priority_breakdown', {}).get('High', 0)}",
                "",
            ])

        # Pipeline health summary
        pipeline_data = results.get("pipeline_health", {})
        if pipeline_data:
            health = pipeline_data.get("health_score", {})
            summary_lines.extend([
                "--- Pipeline Health ---",
                f"Health score: {health.get('score', 'N/A')}/100 ({health.get('rating', 'N/A')})",
                f"Risks identified: {len(pipeline_data.get('risk_indicators', []))}",
                "",
            ])

        # Churn risk summary
        churn_data = results.get("churn_prediction", {})
        if churn_data:
            summary_lines.extend([
                "--- Churn Risk ---",
                f"Total accounts: {churn_data.get('total_accounts', 0)}",
                f"High risk: {churn_data.get('risk_breakdown', {}).get('High', 0)}",
                f"Revenue at risk: £{churn_data.get('total_revenue_at_risk', 0):,.0f}",
                "",
            ])

        # Recommendations
        recommendations = pipeline_data.get("recommendations", [])
        if recommendations:
            summary_lines.append("--- Recommendations ---")
            for rec in recommendations:
                summary_lines.append(f"• {rec}")

        summary = "\n".join(summary_lines)
        self.send_alert({
            "type": "daily_summary",
            "message": summary,
            "priority": "info",
        })
        return summary

    def get_alert_history(self, limit=50):
        """Return recent alert history."""
        return self._alert_history[-limit:]

    def _configure_channels(self):
        """Set up notification channels based on environment configuration."""
        channels = [LogChannel()]

        # AWS SES email channel
        if os.environ.get("AWS_SES_SENDER"):
            channels.append(SESEmailChannel(
                sender=os.environ["AWS_SES_SENDER"],
                recipients=os.environ.get("ALERT_RECIPIENTS", "").split(","),
                region=os.environ.get("AWS_REGION", "eu-west-1"),
            ))

        # Slack webhook channel
        if os.environ.get("SLACK_WEBHOOK_URL"):
            channels.append(SlackChannel(
                webhook_url=os.environ["SLACK_WEBHOOK_URL"],
            ))

        return channels


class LogChannel:
    """Always-on channel that logs alerts."""
    name = "log"

    def send(self, alert):
        logger.info(f"[{self.name}] Alert dispatched: {alert['type']}")


class SESEmailChannel:
    """Send alerts via AWS SES."""
    name = "ses_email"

    def __init__(self, sender, recipients, region):
        self.sender = sender
        self.recipients = [r.strip() for r in recipients if r.strip()]
        self.region = region

    def send(self, alert):
        if not self.recipients:
            return

        import boto3
        ses = boto3.client("ses", region_name=self.region)

        priority = alert.get("priority", "info").upper()
        ses.send_email(
            Source=self.sender,
            Destination={"ToAddresses": self.recipients},
            Message={
                "Subject": {
                    "Data": f"[{priority}] Salesforce Analytics Alert: {alert['type']}",
                },
                "Body": {
                    "Text": {"Data": alert.get("message", "No details provided.")},
                },
            },
        )
        logger.info(f"[{self.name}] Email sent to {len(self.recipients)} recipients")


class SlackChannel:
    """Send alerts via Slack webhook."""
    name = "slack"

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, alert):
        import requests

        priority = alert.get("priority", "info")
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "info": "🔵"}.get(
            priority, "⚪"
        )

        payload = {
            "text": f"{emoji} *[{priority.upper()}] {alert['type']}*\n{alert['message']}",
        }
        response = requests.post(self.webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"[{self.name}] Slack notification sent")
