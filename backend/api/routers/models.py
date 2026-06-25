"""
Router de modelos — lista modelos disponíveis nos provedores de LLM.

OpenCode Zen expõe /models via endpoint OpenAI-compatible.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import httpx

from ..config import settings
from core.model_config import active_model

logger = logging.getLogger(__name__)
router = APIRouter()

# Lista estática de fallback — modelos gratuitos conhecidos do OpenCode Zen.
# Atualizada em: https://opencode.ai/docs/zen
ZEN_FREE_MODELS: List[Dict[str, Any]] = [
    {"id": "opencode/deepseek-v4-flash-free", "name": "DeepSeek V4 Flash Free", "is_free": True},
    {"id": "opencode/mimo-v2.5-free", "name": "MiMo V2.5 Free", "is_free": True},
    {"id": "opencode/north-mini-code-free", "name": "North Mini Code Free", "is_free": True},
    {"id": "opencode/nemotron-3-ultra-free", "name": "Nemotron 3 Ultra Free", "is_free": True},
    {"id": "opencode/big-pickle", "name": "Big Pickle", "is_free": True},
    {"id": "opencode/nemotron-3-super-free", "name": "Nemotron 3 Super Free", "is_free": True},
]

ZEN_PAID_MODELS: List[Dict[str, Any]] = [
    {"id": "opencode/qwen3.5-plus", "name": "Qwen 3.5 Plus", "is_free": False},
    {"id": "opencode/qwen3.6-plus", "name": "Qwen 3.6 Plus", "is_free": False},
    {"id": "opencode/gpt-5.5", "name": "GPT 5.5", "is_free": False},
    {"id": "opencode/gpt-5.5-pro", "name": "GPT 5.5 Pro", "is_free": False},
    {"id": "opencode/claude-opus-4-5", "name": "Claude Opus 4.5", "is_free": False},
    {"id": "opencode/claude-sonnet-4-5", "name": "Claude Sonnet 4.5", "is_free": False},
    {"id": "opencode/gemini-3.5-flash", "name": "Gemini 3.5 Flash", "is_free": False},
    {"id": "opencode/glm-5", "name": "GLM 5", "is_free": False},
    {"id": "opencode/kimi-k2.5", "name": "Kimi K2.5", "is_free": False},
    {"id": "opencode/grok-build-0.1", "name": "Grok Build 0.1", "is_free": False},
]

ZEN_DEFAULT_MODELS = ZEN_FREE_MODELS + ZEN_PAID_MODELS

OPENAI_MODELS: List[Dict[str, Any]] = [
    {"id": "gpt-4o", "name": "GPT-4o", "is_free": False},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "is_free": False},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "is_free": False},
    {"id": "text-embedding-3-small", "name": "Text Embedding 3 Small", "is_free": False},
]

ANTHROPIC_MODELS: List[Dict[str, Any]] = [
    {"id": "claude-opus-4-5", "name": "Claude Opus 4.5", "is_free": False},
    {"id": "claude-sonnet-4-5", "name": "Claude Sonnet 4.5", "is_free": False},
    {"id": "claude-haiku-4-5", "name": "Claude Haiku 4.5", "is_free": False},
]

ZAI_MODELS: List[Dict[str, Any]] = [
    {"id": "glm-4.5-flash", "name": "GLM-4.5-Flash", "is_free": True},
    {"id": "glm-4.7-flash", "name": "GLM-4.7-Flash", "is_free": True},
    {"id": "glm-4.5", "name": "GLM-4.5", "is_free": False},
    {"id": "glm-4.5-air", "name": "GLM-4.5-Air", "is_free": False},
    {"id": "glm-4.6", "name": "GLM-4.6", "is_free": False},
    {"id": "glm-4.7", "name": "GLM-4.7", "is_free": False},
    {"id": "glm-5", "name": "GLM-5", "is_free": False},
    {"id": "glm-5.1", "name": "GLM-5.1", "is_free": False},
]


def _normalize_zen_models(payload: Any) -> List[Dict[str, Any]]:
    """Normaliza a resposta do Zen para uma lista de {id, name, is_free}.

    Os modelids retornados pelo Zen não vêm com o prefixo ``opencode/``;
    o endpoint /chat/completions do Zen espera ids no formato ``opencode/<model-id>``.
    """
    if isinstance(payload, dict):
        items = payload.get("data", [])
    elif isinstance(payload, list):
        items = payload
    else:
        items = []

    free_ids = {m["id"] for m in ZEN_FREE_MODELS}
    free_ids |= {m["id"].split("/")[-1] for m in ZEN_FREE_MODELS}

    result: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            raw_id = item
            model_id = raw_id if raw_id.startswith("opencode/") else f"opencode/{raw_id}"
            name = raw_id.split("/")[-1].replace("-", " ").title()
            result.append({
                "id": model_id,
                "name": name,
                "is_free": "-free" in raw_id.lower() or raw_id in free_ids,
            })
        elif isinstance(item, dict):
            raw_id = item.get("id") or item.get("model") or item.get("name")
            name = item.get("name") or item.get("description") or raw_id
            if not raw_id:
                continue
            model_id = raw_id if raw_id.startswith("opencode/") else f"opencode/{raw_id}"
            is_free = (
                item.get("is_free")
                or "-free" in str(raw_id).lower()
                or raw_id in free_ids
            )
            result.append({
                "id": model_id,
                "name": name,
                "is_free": bool(is_free),
            })
    return result


@router.get("/models")
async def list_models(
    provider: str = Query("opencode", enum=["opencode", "openai", "anthropic", "zai"]),
    refresh: bool = Query(False, description="Ignora cache e busca lista atualizada no Zen"),
):
    """
    Lista modelos disponíveis para o provider escolhido.

    Para OpenCode Zen, consulta o endpoint /models em tempo real.
    Se a chave não estiver configurada ou o Zen estiver indisponível,
    retorna a lista estática de fallback.
    """
    if provider == "opencode":
        api_key = settings.OPENCODE_API_KEY
        if not api_key:
            return {
                "provider": "opencode",
                "source": "fallback",
                "message": "OPENCODE_API_KEY não configurada",
                "models": ZEN_DEFAULT_MODELS,
            }

        base_url = settings.OPENCODE_BASE_URL.rstrip("/")
        url = f"{base_url}/models"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"OpenCode Zen /models retornou {e.response.status_code}: {e.response.text}")
            return {
                "provider": "opencode",
                "source": "fallback",
                "error": f"HTTP {e.response.status_code}",
                "models": ZEN_DEFAULT_MODELS,
            }
        except Exception as e:
            logger.warning(f"Falha ao consultar modelos do Zen: {e}")
            return {
                "provider": "opencode",
                "source": "fallback",
                "error": str(e),
                "models": ZEN_DEFAULT_MODELS,
            }

        models = _normalize_zen_models(data)
        return {
            "provider": "opencode",
            "source": "live",
            "count": len(models),
            "models": models,
        }

    if provider == "openai":
        return {
            "provider": "openai",
            "source": "static",
            "models": OPENAI_MODELS,
        }

    if provider == "anthropic":
        return {
            "provider": "anthropic",
            "source": "static",
            "models": ANTHROPIC_MODELS,
        }

    if provider == "zai":
        return {
            "provider": "zai",
            "source": "static",
            "models": ZAI_MODELS,
        }

    raise HTTPException(status_code=400, detail=f"Provider não suportado: {provider}")


class ActiveModelRequest(BaseModel):
    model: str


@router.get("/active-model")
async def get_active_model():
    """Retorna o modelo ativo global (se houver)."""
    return {
        "provider": settings.LLM_PROVIDER,
        "active_model": active_model.get(),
    }


@router.post("/active-model")
async def set_active_model(request: ActiveModelRequest):
    """Define o modelo ativo global."""
    active_model.set(request.model)
    return {
        "active_model": active_model.get(),
        "message": "Modelo ativo atualizado.",
    }
