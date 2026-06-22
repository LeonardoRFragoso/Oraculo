"""
Sprint 6 — Agent Actions: Base classes

Every action follows the same pattern:
    1. validate(context)  → raises ValueError if params missing
    2. execute(context)   → performs the action, returns ActionResult
    3. dry_run(context)   → explains what WOULD happen without doing it

Actions are self-describing: name, description, required_params, optional_params.
The ActionPlanner uses these descriptions to decide which action(s) to invoke.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ActionStatus(str, Enum):
    SUCCESS   = "success"
    FAILED    = "failed"
    SKIPPED   = "skipped"
    DRY_RUN   = "dry_run"


@dataclass
class ActionContext:
    """
    Runtime context passed to every action.

    Contains the trigger (insight/anomaly/user request),
    structured data results, and free-form parameters.
    """
    trigger: str                          # "anomaly" | "user" | "schedule"
    source_id: str
    source_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    kpis: List[Dict[str, Any]] = field(default_factory=list)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    sql_results: Optional[Dict[str, Any]] = None
    user_instruction: Optional[str] = None
    dry_run: bool = False


@dataclass
class ActionResult:
    action_name: str
    status: ActionStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    artifact: Optional[Any] = None       # file path, URL, etc.
    executed_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "artifact": str(self.artifact) if self.artifact else None,
            "executed_at": self.executed_at,
        }


class Action(ABC):
    """Base class for all Oracle Actions."""

    #: Short machine-readable identifier used in routing
    name: str = "base_action"

    #: Human-readable description shown to the LLM planner
    description: str = "Base action — override in subclass"

    #: Params the action MUST receive to execute
    required_params: List[str] = []

    #: Params the action CAN use but are not mandatory
    optional_params: List[str] = []

    def validate(self, ctx: ActionContext) -> None:
        """Raise ValueError if required params are missing."""
        missing = [p for p in self.required_params if p not in ctx.params]
        if missing:
            raise ValueError(
                f"Action '{self.name}' missing required params: {missing}"
            )

    @abstractmethod
    def execute(self, ctx: ActionContext) -> ActionResult:
        """Perform the action. Must be idempotent where possible."""

    def dry_run_description(self, ctx: ActionContext) -> str:
        """Return a human-readable description of what WOULD happen."""
        return f"Would execute '{self.name}' with params: {ctx.params}"

    def run(self, ctx: ActionContext) -> ActionResult:
        """Public entrypoint: validate → execute or dry_run."""
        try:
            self.validate(ctx)
        except ValueError as e:
            return ActionResult(
                action_name=self.name,
                status=ActionStatus.FAILED,
                message=str(e),
            )
        if ctx.dry_run:
            return ActionResult(
                action_name=self.name,
                status=ActionStatus.DRY_RUN,
                message=self.dry_run_description(ctx),
                details={"params": ctx.params},
            )
        try:
            result = self.execute(ctx)
            logger.info(f"Action '{self.name}' → {result.status.value}: {result.message}")
            return result
        except Exception as e:
            logger.error(f"Action '{self.name}' failed: {e}", exc_info=True)
            return ActionResult(
                action_name=self.name,
                status=ActionStatus.FAILED,
                message=str(e),
            )
