"""
Action: send_email

Sends an alert or report email using SMTP (configurable via env vars).
Falls back to a mock/log-only mode if SMTP is not configured —
useful for development and demos.

Env vars:
    SMTP_HOST     (default: localhost)
    SMTP_PORT     (default: 587)
    SMTP_USER
    SMTP_PASSWORD
    SMTP_FROM     (default: oraculo@company.com)
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from actions.base import Action, ActionContext, ActionResult, ActionStatus

logger = logging.getLogger(__name__)

_BODY_TEMPLATE = """
<html><body>
<h2 style="color:#1a1a2e">🔮 Oráculo AI — Alerta Automático</h2>
<p><strong>Fonte:</strong> {source_name}</p>
<p><strong>Motivo:</strong> {trigger_reason}</p>
<hr/>
{body_html}
<hr/>
<p style="color:gray;font-size:12px">Enviado automaticamente pelo Oráculo AI</p>
</body></html>
"""


class SendEmailAction(Action):
    name = "send_email"
    description = (
        "Sends an email alert or report to one or more recipients. "
        "Use when a critical anomaly is detected or when the user requests "
        "a summary to be sent by email."
    )
    required_params = ["to"]
    optional_params = ["subject", "body", "cc"]

    def execute(self, ctx: ActionContext) -> ActionResult:
        to_raw = ctx.params["to"]
        recipients = [e.strip() for e in to_raw.split(",")] if isinstance(to_raw, str) else to_raw
        subject = ctx.params.get("subject") or self._default_subject(ctx)
        body_html = ctx.params.get("body") or self._build_body(ctx)
        cc = ctx.params.get("cc", "")

        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_user = os.getenv("SMTP_USER", "")
        from_addr = os.getenv("SMTP_FROM", "oraculo@company.com")

        if not smtp_host or not smtp_user:
            # Dev mode: log only
            logger.info(
                f"[MOCK EMAIL] To: {recipients} | Subject: {subject}\n"
                f"Body (first 200 chars): {body_html[:200]}"
            )
            return ActionResult(
                action_name=self.name,
                status=ActionStatus.SUCCESS,
                message=f"Email simulado (SMTP não configurado) para {recipients}",
                details={
                    "mode": "mock",
                    "to": recipients,
                    "subject": subject,
                    "body_preview": body_html[:300],
                },
            )

        # Real SMTP send
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)
        if cc:
            msg["Cc"] = cc
        msg.attach(MIMEText(body_html, "html"))

        port = int(os.getenv("SMTP_PORT", 587))
        password = os.getenv("SMTP_PASSWORD", "")
        with smtplib.SMTP(smtp_host, port) as server:
            server.starttls()
            server.login(smtp_user, password)
            server.sendmail(from_addr, recipients, msg.as_string())

        return ActionResult(
            action_name=self.name,
            status=ActionStatus.SUCCESS,
            message=f"Email enviado para {recipients}",
            details={"to": recipients, "subject": subject},
        )

    def dry_run_description(self, ctx: ActionContext) -> str:
        to = ctx.params.get("to", "?")
        return (
            f"Would send email to '{to}' with subject: "
            f"'{self._default_subject(ctx)}'"
        )

    def _default_subject(self, ctx: ActionContext) -> str:
        if ctx.anomalies:
            sev = ctx.anomalies[0].get("severity", "warning").upper()
            return f"[Oráculo AI] {sev}: Anomalia detectada em '{ctx.source_name}'"
        return f"[Oráculo AI] Relatório automático — {ctx.source_name}"

    def _build_body(self, ctx: ActionContext) -> str:
        lines = []

        if ctx.kpis:
            lines.append("<h3>📊 KPIs Principais</h3><ul>")
            for k in ctx.kpis[:6]:
                val = k.get("value", "")
                unit = k.get("unit", "")
                lines.append(f"<li><strong>{k['name']}</strong>: {val} {unit}</li>")
            lines.append("</ul>")

        if ctx.anomalies:
            lines.append("<h3>⚠️ Anomalias Detectadas</h3><ul>")
            for a in ctx.anomalies[:5]:
                emoji = {"critical": "🚨", "warning": "⚠️"}.get(a.get("severity", ""), "ℹ️")
                lines.append(f"<li>{emoji} {a.get('message', '')}</li>")
            lines.append("</ul>")

        if ctx.user_instruction:
            lines.append(f"<p><em>Instrução: {ctx.user_instruction}</em></p>")

        body_html = "\n".join(lines) or "<p>Análise automática concluída.</p>"
        trigger_reason = ctx.user_instruction or (
            f"{len(ctx.anomalies)} anomalia(s) detectada(s)" if ctx.anomalies
            else "Relatório programado"
        )
        return _BODY_TEMPLATE.format(
            source_name=ctx.source_name,
            trigger_reason=trigger_reason,
            body_html=body_html,
        )
