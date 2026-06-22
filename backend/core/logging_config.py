"""
Structured logging configuration.

Outputs JSON in production (ENVIRONMENT=production) for ingestion
by log aggregators (Datadog, Grafana Loki, CloudWatch).
Falls back to human-readable format in development.

Usage:
    from core.logging_config import setup_logging
    setup_logging()   # call once at startup

Per-request trace IDs are injected via TraceMiddleware (see api/middleware.py).
Access the current trace ID anywhere:
    from core.logging_config import get_trace_id
    trace_id = get_trace_id()
"""

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# Context variable for per-request trace ID
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    return _trace_id_var.get() or "-"


def set_trace_id(trace_id: str) -> None:
    _trace_id_var.set(trace_id)


def new_trace_id() -> str:
    tid = str(uuid.uuid4())[:8]
    set_trace_id(tid)
    return tid


class _JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "trace_id": get_trace_id(),
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


class _DevFormatter(logging.Formatter):
    _COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelname, "")
        trace = get_trace_id()
        prefix = f"{color}[{record.levelname[0]}]{self._RESET}"
        return (
            f"{prefix} {record.name} [{trace}] {record.getMessage()}"
            + (f"\n{self.formatException(record.exc_info)}" if record.exc_info else "")
        )


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure root logger.
    Call once at application startup (before any logging occurs).
    """
    env = os.getenv("ENVIRONMENT", "development")
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    numeric = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if env == "production":
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(_DevFormatter())

    root = logging.getLogger()
    root.setLevel(numeric)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("httpcore", "httpx", "uvicorn.access", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        f"Logging configured — level={log_level}, format={'json' if env == 'production' else 'dev'}"
    )
