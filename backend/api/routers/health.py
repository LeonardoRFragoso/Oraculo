"""
Health check endpoints — real status for all subsystems.
"""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import logging
from fastapi import APIRouter
from ..config import settings

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logger = logging.getLogger(__name__)
router = APIRouter()
_start_time = time.time()


def _check_llm() -> Dict[str, Any]:
    anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-"))
    openai_key = bool(os.getenv("OPENAI_API_KEY", "").startswith("sk-"))
    opencode_key = bool(os.getenv("OPENCODE_API_KEY", ""))
    zai_key = bool(os.getenv("ZAI_API_KEY", ""))
    provider_pref = os.getenv("LLM_PROVIDER", "auto")

    if provider_pref == "anthropic" and anthropic_key:
        provider = "anthropic"
    elif provider_pref == "openai" and openai_key:
        provider = "openai"
    elif provider_pref == "opencode" and opencode_key:
        provider = "opencode"
    elif provider_pref == "zai" and zai_key:
        provider = "zai"
    elif anthropic_key:
        provider = "anthropic"
    elif openai_key:
        provider = "openai"
    elif opencode_key:
        provider = "opencode"
    elif zai_key:
        provider = "zai"
    else:
        provider = None

    return {
        "available": provider is not None and provider != "none",
        "provider": provider or "none",
        "anthropic_key_set": anthropic_key,
        "openai_key_set": openai_key,
        "opencode_key_set": opencode_key,
        "zai_key_set": zai_key,
    }


def _check_vector_store() -> Dict[str, Any]:
    try:
        data_dir = Path(settings.DATA_DIR) if hasattr(settings, "DATA_DIR") else Path("../dados")
        vs_dir = data_dir / "vector_store"
        indices = list(vs_dir.glob("*/faiss_index.bin")) if vs_dir.exists() else []
        return {"available": True, "backend": "faiss", "indexed_sources": len(indices)}
    except Exception as e:
        return {"available": False, "error": str(e)}


def _check_database() -> Dict[str, Any]:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        data_dir = os.getenv("DATA_DIR", "../dados")
        sqlite_path = Path(data_dir) / "oraculo.db"
        return {
            "available": sqlite_path.exists(),
            "backend": "sqlite",
            "path": str(sqlite_path),
        }
    backend = "postgresql" if "postgresql" in db_url or "postgres" in db_url else "other"
    return {"available": True, "backend": backend}


def _check_catalog() -> Dict[str, Any]:
    try:
        from catalog.registry import DataSourceRegistry
        reg = DataSourceRegistry()
        sources = reg.list()
        connected = [s for s in sources if s.status in ("connected", "profiled", "analyzed")]
        return {
            "available": True,
            "total_sources": len(sources),
            "connected_sources": len(connected),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """Comprehensive health check — returns status of all subsystems."""
    uptime_s = round(time.time() - _start_time)

    llm = _check_llm()
    vector = _check_vector_store()
    db = _check_database()
    catalog = _check_catalog()

    auth_ok = bool(settings.SECRET_KEY)

    checks = {
        "llm": llm["available"],
        "vector_store": vector["available"],
        "database": db["available"],
        "catalog": catalog["available"],
        "auth_configured": auth_ok,
    }
    all_ok = all(checks.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "version": "4.0.0",
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_s,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "details": {
            "llm": llm,
            "vector_store": vector,
            "database": db,
            "catalog": catalog,
            "auth": {"secret_key_set": auth_ok, "require_auth": settings.REQUIRE_AUTH},
        },
    }


@router.get("/ping")
async def ping():
    """Liveness probe — lightweight, no subsystem checks."""
    return {"status": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
