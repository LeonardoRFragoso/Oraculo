"""
Sprint 6 — Action Planner

Given a user instruction (or a set of anomalies), decides which
Oracle Actions to execute and what parameters to use.

Two modes:
  1. Rule-based (free, no LLM):
       "enviar email"      → send_email
       "gerar relatório"   → generate_report
       "criar alerta"      → create_alert
       critical anomaly    → create_alert (auto)

  2. LLM-assisted (optional, falls back to rule-based):
       Sends action catalog + context to Claude, parses JSON plan.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from actions.base import ActionContext, ActionResult
from actions.registry import registry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword → action mapping (rule-based planner)
# ---------------------------------------------------------------------------

_KEYWORD_MAP: Dict[str, Tuple[str, Dict[str, Any]]] = {
    # Email
    r"envi(ar|e)\s+(email|e-mail|relat)": ("send_email", {}),
    r"notific(ar|e)": ("send_email", {}),
    r"alert(ar|e)\s+(por\s+)?email": ("send_email", {}),
    # Report
    r"gerar?\s+relat": ("generate_report", {}),
    r"export(ar|e)": ("generate_report", {}),
    r"relat[oó]rio": ("generate_report", {}),
    r"pdf|html|markdown": ("generate_report", {}),
    # Alert
    r"criar?\s+alerta": ("create_alert", {}),
    r"registrar?\s+alerta": ("create_alert", {}),
    r"salvar?\s+alerta": ("create_alert", {}),
}


class ActionPlanner:
    """
    Decides which action(s) to execute given a natural language
    instruction and/or analysis context (anomalies, KPIs).

    Usage:
        planner = ActionPlanner()
        results = planner.plan_and_run(
            instruction="Gerar relatório e enviar email para cfo@corp.com",
            ctx=ActionContext(...),
        )
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self._llm = None
        # Import built-ins to register them
        import actions.builtin  # noqa: F401

    def plan_and_run(
        self,
        instruction: Optional[str],
        ctx: ActionContext,
    ) -> List[ActionResult]:
        """
        Determine action plan and execute all planned actions.
        Returns list of ActionResult (one per action).
        """
        plan = self._build_plan(instruction, ctx)
        results = []
        for action_name, extra_params in plan:
            action = registry.get(action_name)
            if action is None:
                logger.warning(f"Action not found: {action_name}")
                continue
            # Merge extra params
            merged_ctx = ActionContext(
                trigger=ctx.trigger,
                source_id=ctx.source_id,
                source_name=ctx.source_name,
                params={**ctx.params, **extra_params},
                kpis=ctx.kpis,
                anomalies=ctx.anomalies,
                sql_results=ctx.sql_results,
                user_instruction=instruction,
                dry_run=ctx.dry_run,
            )
            results.append(action.run(merged_ctx))
        return results

    def plan_only(
        self,
        instruction: Optional[str],
        ctx: ActionContext,
    ) -> List[Dict[str, Any]]:
        """Return the plan (action names + params) without executing."""
        plan = self._build_plan(instruction, ctx)
        return [{"action": name, "params": params} for name, params in plan]

    # ------------------------------------------------------------------
    # Planning logic
    # ------------------------------------------------------------------

    def _build_plan(
        self,
        instruction: Optional[str],
        ctx: ActionContext,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Returns list of (action_name, extra_params) pairs."""
        # 1. Automatic: critical anomaly with no explicit instruction → alert
        if not instruction and ctx.anomalies:
            critical = [a for a in ctx.anomalies if a.get("severity") == "critical"]
            if critical:
                return [("create_alert", {})]
            return []

        if not instruction:
            return []

        # 2. Try LLM planning first (if enabled and available)
        if self.use_llm:
            llm_plan = self._llm_plan(instruction, ctx)
            if llm_plan:
                return llm_plan

        # 3. Rule-based fallback
        return self._rule_plan(instruction, ctx)

    def _rule_plan(
        self, instruction: str, ctx: ActionContext
    ) -> List[Tuple[str, Dict[str, Any]]]:
        plan: List[Tuple[str, Dict[str, Any]]] = []
        instr_lower = instruction.lower()

        # Extract email address from instruction
        emails = re.findall(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", instruction)
        email_param = {"to": emails[0]} if emails else {}

        # Extract format hint
        fmt_match = re.search(r"\b(json|html|markdown|pdf)\b", instr_lower)
        fmt_param = {"format": fmt_match.group(1)} if fmt_match else {}

        seen = set()
        for pattern, (action_name, base_params) in _KEYWORD_MAP.items():
            if re.search(pattern, instr_lower) and action_name not in seen:
                extra = dict(base_params)
                if action_name == "send_email":
                    extra.update(email_param)
                if action_name == "generate_report":
                    extra.update(fmt_param)
                plan.append((action_name, extra))
                seen.add(action_name)

        # Fallback: if nothing matched but there are anomalies → create alert
        if not plan and ctx.anomalies:
            plan.append(("create_alert", {}))

        return plan

    def _llm_plan(
        self, instruction: str, ctx: ActionContext
    ) -> Optional[List[Tuple[str, Dict[str, Any]]]]:
        """Ask the LLM to produce a JSON action plan."""
        try:
            if self._llm is None:
                import sys
                from pathlib import Path
                _root = str(Path(__file__).parent.parent)
                if _root not in sys.path:
                    sys.path.insert(0, _root)
                from core.llm_client import LLMClient
                self._llm = LLMClient()

            catalog = registry.list_all()
            anomaly_summary = "; ".join(
                a.get("message", "") for a in ctx.anomalies[:3]
            )
            kpi_summary = ", ".join(
                f"{k['name']}={k.get('value')}" for k in ctx.kpis[:4]
            )

            system = (
                "You are an action planner for a data platform. "
                "Given a user instruction and context, return a JSON array of actions to execute. "
                'Format: [{"action": "<name>", "params": {<key>: <value>}}]. '
                "Available actions: " + json.dumps([a["name"] for a in catalog]) + ". "
                "Only include actions that are clearly requested. "
                "If an email is needed, extract the 'to' address from the instruction. "
                "Return ONLY the JSON array, no other text."
            )
            user = (
                f"Source: {ctx.source_name}\n"
                f"KPIs: {kpi_summary}\n"
                f"Anomalies: {anomaly_summary}\n"
                f"User instruction: {instruction}"
            )

            resp = self._llm.chat(
                system=system,
                user=user,
                max_tokens=256,
                temperature=0.1,
                json_mode=True,
            )

            raw = resp.content.strip()
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                return None

            plan = []
            for item in parsed:
                name = item.get("action", "")
                params = item.get("params", {})
                if registry.get(name):
                    plan.append((name, params))
            return plan if plan else None

        except Exception as e:
            logger.debug(f"LLM planning failed (using rule-based fallback): {e}")
            return None
