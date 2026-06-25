"""
Armazenamento do modelo ativo selecionado pelo usuário.

Persiste em JSON em DATA_DIR/active_model.json para sobreviver a reinícios.
É usado pelo LLMClient para sobrescrever o modelo default do provider.
"""

import json
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ActiveModelStore:
    """Armazena o modelo ativo global."""

    def __init__(self) -> None:
        data_dir = Path(os.getenv("DATA_DIR", "../dados"))
        self._path = data_dir / "active_model.json"
        self._active_model: Optional[str] = None
        self._load()

    def get(self) -> Optional[str]:
        return self._active_model

    def set(self, model: Optional[str]) -> None:
        self._active_model = model
        self._save()
        logger.info(f"Active model set to: {model}")

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._active_model = data.get("model") or None
        except Exception as e:
            logger.warning(f"Failed to load active model: {e}")

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps({"model": self._active_model}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to save active model: {e}")


active_model = ActiveModelStore()
