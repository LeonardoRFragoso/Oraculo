"""
Action: generate_report

Generates a structured JSON/HTML/Markdown report from analysis results.
Saves to the reports directory and returns the file path.

Params:
    format   : "json" | "markdown" | "html"  (default: "markdown")
    filename : override default filename
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from actions.base import Action, ActionContext, ActionResult, ActionStatus

logger = logging.getLogger(__name__)

_REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "../dados/reports"))


class GenerateReportAction(Action):
    name = "generate_report"
    description = (
        "Generates a structured report (Markdown, HTML, or JSON) from KPIs and anomalies. "
        "Use when the user asks for a report, summary document, or export of analysis results."
    )
    required_params = []
    optional_params = ["format", "filename"]

    def execute(self, ctx: ActionContext) -> ActionResult:
        fmt = ctx.params.get("format", "markdown").lower()
        _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        default_name = f"oraculo_report_{ctx.source_name.replace(' ', '_')}_{timestamp}"
        filename = ctx.params.get("filename") or default_name
        if not filename.endswith(f".{fmt}") and fmt != "html":
            filename = f"{filename}.{fmt}"
        elif fmt == "html" and not filename.endswith(".html"):
            filename = f"{filename}.html"

        path = _REPORTS_DIR / filename

        if fmt == "json":
            content = self._build_json(ctx)
            path.write_text(json.dumps(content, ensure_ascii=False, indent=2))
        elif fmt == "html":
            content = self._build_html(ctx)
            path.write_text(content, encoding="utf-8")
        else:
            content = self._build_markdown(ctx)
            path.write_text(content, encoding="utf-8")

        logger.info(f"Report generated: {path}")
        return ActionResult(
            action_name=self.name,
            status=ActionStatus.SUCCESS,
            message=f"Relatório gerado: {path.name}",
            artifact=str(path),
            details={
                "format": fmt,
                "path": str(path),
                "size_bytes": path.stat().st_size,
            },
        )

    def dry_run_description(self, ctx: ActionContext) -> str:
        fmt = ctx.params.get("format", "markdown")
        return f"Would generate a {fmt.upper()} report for '{ctx.source_name}'"

    # ------------------------------------------------------------------
    # Format builders
    # ------------------------------------------------------------------

    def _build_markdown(self, ctx: ActionContext) -> str:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"# 🔮 Oráculo AI — Relatório de Análise",
            f"**Fonte:** {ctx.source_name}  ",
            f"**Gerado em:** {now}  ",
            "",
        ]

        if ctx.kpis:
            lines += ["## 📊 KPIs Principais", ""]
            lines += ["| KPI | Valor | Status |", "|-----|-------|--------|"]
            for k in ctx.kpis[:10]:
                icon = {"good": "✅", "warning": "⚠️", "critical": "🚨", "info": "ℹ️"}.get(
                    k.get("status", "info"), "ℹ️"
                )
                val = k.get("value", "")
                unit = k.get("unit", "")
                lines.append(f"| {k['name']} | {val} {unit} | {icon} |")
            lines.append("")

        if ctx.anomalies:
            lines += ["## ⚠️ Anomalias Detectadas", ""]
            for a in ctx.anomalies:
                emoji = {"critical": "🚨", "warning": "⚠️"}.get(a.get("severity", ""), "ℹ️")
                lines.append(f"- {emoji} **[{a.get('severity','').upper()}]** {a.get('message','')}")
            lines.append("")

        if ctx.sql_results and ctx.sql_results.get("rows"):
            lines += ["## 📋 Dados Estruturados", ""]
            cols = ctx.sql_results.get("columns", [])
            rows = ctx.sql_results.get("rows", [])[:20]
            if cols:
                lines.append("| " + " | ".join(cols) + " |")
                lines.append("|" + "---|" * len(cols))
                for row in rows:
                    vals = [str(row.get(c, "")) for c in cols]
                    lines.append("| " + " | ".join(vals) + " |")
            lines.append("")

        lines += ["---", "_Relatório gerado automaticamente pelo Oráculo AI_"]
        return "\n".join(lines)

    def _build_json(self, ctx: ActionContext) -> Dict[str, Any]:
        return {
            "report": {
                "source": ctx.source_name,
                "generated_at": datetime.utcnow().isoformat(),
                "trigger": ctx.trigger,
            },
            "kpis": ctx.kpis,
            "anomalies": ctx.anomalies,
            "sql_results": ctx.sql_results,
        }

    def _build_html(self, ctx: ActionContext) -> str:
        md = self._build_markdown(ctx)
        # Minimal HTML wrapper around markdown-like content
        rows_html = ""
        if ctx.kpis:
            kpi_rows = "".join(
                f"<tr><td>{k['name']}</td><td>{k.get('value','')} {k.get('unit','')}</td>"
                f"<td>{'✅' if k.get('status')=='good' else '⚠️' if k.get('status')=='warning' else '🚨' if k.get('status')=='critical' else 'ℹ️'}</td></tr>"
                for k in ctx.kpis[:10]
            )
            rows_html = f"""
            <h2>📊 KPIs</h2>
            <table border="1" cellpadding="6" style="border-collapse:collapse">
              <tr><th>KPI</th><th>Valor</th><th>Status</th></tr>
              {kpi_rows}
            </table>"""

        anomaly_html = ""
        if ctx.anomalies:
            items = "".join(
                f"<li><strong>[{a.get('severity','').upper()}]</strong> {a.get('message','')}</li>"
                for a in ctx.anomalies
            )
            anomaly_html = f"<h2>⚠️ Anomalias</h2><ul>{items}</ul>"

        return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Oráculo AI — {ctx.source_name}</title>
<style>body{{font-family:Arial,sans-serif;max-width:960px;margin:auto;padding:24px}}</style>
</head><body>
<h1>🔮 Oráculo AI — Relatório de Análise</h1>
<p><strong>Fonte:</strong> {ctx.source_name}</p>
{rows_html}
{anomaly_html}
<hr/><small>Gerado automaticamente pelo Oráculo AI</small>
</body></html>"""
