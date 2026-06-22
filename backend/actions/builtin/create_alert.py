"""
Action: create_alert

Persists an alert to a JSON log file and optionally emits a webhook.
Useful for dashboards, PagerDuty-style notifications, or audit trails.

Params:
    severity    : "critical" | "warning" | "info"
    title       : short alert title
    message     : detailed message (auto-generated from anomalies if omitted)
    webhook_url : optional URL for HTTP POST notification
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from actions.base import Action, ActionContext, ActionResult, ActionStatus

logger = logging.getLogger(__name__)

_ALERTS_FILE = Path(os.getenv("ALERTS_FILE", "../dados/alerts/alerts.jsonl"))


class CreateAlertAction(Action):
    name = "create_alert"
    description = (
        "Creates a persistent alert record in the system alert log. "
        "Use when a critical anomaly needs to be tracked, acknowledged, or sent to a webhook."
    )
    required_params = []
    optional_params = ["severity", "title", "message", "webhook_url"]

    def execute(self, ctx: ActionContext) -> ActionResult:
        severity = ctx.params.get("severity") or self._infer_severity(ctx)
        title = ctx.params.get("title") or self._default_title(ctx, severity)
        message = ctx.params.get("message") or self._build_message(ctx)
        webhook_url = ctx.params.get("webhook_url", "")

        alert = {
            "id": f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            "created_at": datetime.utcnow().isoformat(),
            "source_id": ctx.source_id,
            "source_name": ctx.source_name,
            "severity": severity,
            "title": title,
            "message": message,
            "trigger": ctx.trigger,
            "anomaly_count": len(ctx.anomalies),
        }

        # Persist to JSONL log
        _ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _ALERTS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(alert, ensure_ascii=False) + "\n")

        # Optional webhook
        webhook_result = None
        if webhook_url:
            webhook_result = self._send_webhook(webhook_url, alert)

        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(severity, "ℹ️")
        return ActionResult(
            action_name=self.name,
            status=ActionStatus.SUCCESS,
            message=f"{emoji} Alerta criado: '{title}' [{severity}]",
            artifact=str(_ALERTS_FILE),
            details={
                "alert_id": alert["id"],
                "severity": severity,
                "persisted_to": str(_ALERTS_FILE),
                "webhook": webhook_result,
            },
        )

    def dry_run_description(self, ctx: ActionContext) -> str:
        severity = ctx.params.get("severity") or self._infer_severity(ctx)
        return (
            f"Would create a [{severity}] alert for '{ctx.source_name}' "
            f"with {len(ctx.anomalies)} anomaly(ies)"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _infer_severity(self, ctx: ActionContext) -> str:
        severities = [a.get("severity", "info") for a in ctx.anomalies]
        if "critical" in severities:
            return "critical"
        if "warning" in severities:
            return "warning"
        return "info"

    def _default_title(self, ctx: ActionContext, severity: str) -> str:
        emoji = {"critical": "🚨", "warning": "⚠️"}.get(severity, "ℹ️")
        return f"{emoji} Oráculo AI — {severity.upper()} em '{ctx.source_name}'"

    def _build_message(self, ctx: ActionContext) -> str:
        if not ctx.anomalies:
            return f"Análise de '{ctx.source_name}' concluída — nenhuma anomalia crítica."
        lines = [f"Anomalias detectadas em '{ctx.source_name}':"]
        for a in ctx.anomalies[:5]:
            lines.append(f"  • [{a.get('severity','').upper()}] {a.get('message','')}")
        return "\n".join(lines)

    def _send_webhook(self, url: str, payload: Dict[str, Any]) -> str:
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return f"HTTP {resp.status}"
        except Exception as e:
            logger.warning(f"Webhook failed: {e}")
            return f"failed: {e}"
