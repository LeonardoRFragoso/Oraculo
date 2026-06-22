"""
Sprint 6 — Action Registry

Central registry of all available Oracle Actions.
Actions register themselves on import.
The ActionPlanner queries this registry for the catalog of actions.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from actions.base import Action

logger = logging.getLogger(__name__)


class ActionRegistry:
    """Thread-safe, singleton-friendly action registry."""

    def __init__(self) -> None:
        self._actions: Dict[str, Action] = {}

    def register(self, action: Action) -> None:
        self._actions[action.name] = action
        logger.debug(f"Action registered: {action.name}")

    def get(self, name: str) -> Optional[Action]:
        return self._actions.get(name)

    def list_all(self) -> List[Dict]:
        return [
            {
                "name": a.name,
                "description": a.description,
                "required_params": a.required_params,
                "optional_params": a.optional_params,
            }
            for a in self._actions.values()
        ]

    def names(self) -> List[str]:
        return list(self._actions.keys())


# Module-level singleton — import this everywhere
registry = ActionRegistry()
