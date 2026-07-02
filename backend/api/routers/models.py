"""
Router de modelos — lista modelos disponíveis nos provedores de LLM.

OpenCode Zen expõe /models via endpoint OpenAI-compatible.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
import httpx

from ..config import settings
from core.model_config import active_model
from core.plan_config import (
    get_allowed_models,
    is_model_allowed,
    get_available_providers,
    PLAN_LABELS,
)

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


def _filter_by_plan(models: List[Dict[str, Any]], plan: str, provider: str) -> List[Dict[str, Any]]:
    """Filter model list to only those allowed for the user's plan."""
    allowed_ids = set(get_allowed_models(plan, provider))
    return [m for m in models if m["id"] in allowed_ids]


@router.get("/models")
async def list_models(
    request: Request,
    provider: str = Query("opencode", enum=["opencode", "openai", "anthropic", "zai"]),
    refresh: bool = Query(False, description="Ignora cache e busca lista atualizada no Zen"),
):
    """
    Lista modelos disponíveis para o provider escolhido, filtrados pelo plano do usuário.

    Para OpenCode Zen, consulta o endpoint /models em tempo real.
    Se a chave não estiver configurada ou o Zen estiver indisponível,
    retorna a lista estática de fallback.
    """
    user_plan = getattr(request.state, "user_plan", "free")

    if provider == "opencode":
        api_key = settings.OPENCODE_API_KEY
        if not api_key:
            all_models = ZEN_DEFAULT_MODELS
            source = "fallback"
            message = "OPENCODE_API_KEY não configurada"
        else:
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
                all_models = _normalize_zen_models(data)
                source = "live"
                message = None
            except httpx.HTTPStatusError as e:
                logger.warning(f"OpenCode Zen /models retornou {e.response.status_code}: {e.response.text}")
                all_models = ZEN_DEFAULT_MODELS
                source = "fallback"
                message = f"HTTP {e.response.status_code}"
            except Exception as e:
                logger.warning(f"Falha ao consultar modelos do Zen: {e}")
                all_models = ZEN_DEFAULT_MODELS
                source = "fallback"
                message = str(e)

        filtered = _filter_by_plan(all_models, user_plan, provider)
        result = {"provider": "opencode", "source": source, "plan": user_plan, "count": len(filtered), "models": filtered}
        if message:
            result["message"] = message
        return result

    if provider == "openai":
        filtered = _filter_by_plan(OPENAI_MODELS, user_plan, provider)
        return {"provider": "openai", "source": "static", "plan": user_plan, "count": len(filtered), "models": filtered}

    if provider == "anthropic":
        filtered = _filter_by_plan(ANTHROPIC_MODELS, user_plan, provider)
        return {"provider": "anthropic", "source": "static", "plan": user_plan, "count": len(filtered), "models": filtered}

    if provider == "zai":
        filtered = _filter_by_plan(ZAI_MODELS, user_plan, provider)
        return {"provider": "zai", "source": "static", "plan": user_plan, "count": len(filtered), "models": filtered}

    raise HTTPException(status_code=400, detail=f"Provider não suportado: {provider}")


@router.get("/models/providers")
async def list_providers(request: Request):
    """Lista providers disponíveis para o plano do usuário."""
    user_plan = getattr(request.state, "user_plan", "free")
    available = get_available_providers(user_plan)
    return {
        "plan": user_plan,
        "plan_label": PLAN_LABELS.get(user_plan, user_plan),
        "providers": available,
    }


class ActiveModelRequest(BaseModel):
    model: str
    provider: Optional[str] = None


@router.get("/active-model")
async def get_active_model(request: Request):
    """Retorna o modelo ativo do usuário (ou global como fallback)."""
    user_id = getattr(request.state, "user_id", None)
    user_plan = getattr(request.state, "user_plan", "free")

    # Try user-specific preference first, fall back to global
    user_model = None
    user_provider = None
    if user_id:
        try:
            from db.engine import AsyncSessionLocal
            from db.models import UserPreferenceModel
            from sqlalchemy import select
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
                )
                pref = result.scalar_one_or_none()
                if pref:
                    user_model = pref.active_model
                    user_provider = pref.active_provider
        except Exception as e:
            logger.debug(f"Could not load user preference: {e}")

    return {
        "provider": user_provider or settings.LLM_PROVIDER,
        "active_model": user_model or active_model.get(),
        "plan": user_plan,
        "scope": "user" if user_model else "global",
    }


@router.post("/active-model")
async def set_active_model(request: Request, body: ActiveModelRequest):
    """Define o modelo ativo do usuário, validando permissão do plano."""
    user_id = getattr(request.state, "user_id", None)
    user_plan = getattr(request.state, "user_plan", "free")
    provider = body.provider or "auto"

    # Determine which provider the model belongs to
    if provider == "auto":
        # Infer provider from model id prefix
        if body.model.startswith("opencode/"):
            provider = "opencode"
        elif body.model.startswith("glm-"):
            provider = "zai"
        elif body.model.startswith("claude-"):
            provider = "anthropic"
        elif body.model.startswith("gpt-"):
            provider = "openai"
        else:
            provider = "zai"  # default

    # Validate model is allowed for user's plan
    if not is_model_allowed(user_plan, provider, body.model):
        raise HTTPException(
            status_code=403,
            detail=f"Modelo '{body.model}' não disponível no plano '{user_plan}'. Faça upgrade para acessar.",
        )

    # Save to user preference if user_id available
    if user_id:
        try:
            from db.engine import AsyncSessionLocal
            from db.models import UserPreferenceModel
            from sqlalchemy import select
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
                )
                pref = result.scalar_one_or_none()
                if pref:
                    pref.active_model = body.model
                    pref.active_provider = provider
                else:
                    pref = UserPreferenceModel(
                        user_id=user_id,
                        active_model=body.model,
                        active_provider=provider,
                    )
                    session.add(pref)
                await session.commit()
            logger.info(f"User {user_id} set active model: {body.model} (provider={provider})")
            return {
                "active_model": body.model,
                "provider": provider,
                "plan": user_plan,
                "scope": "user",
                "message": "Modelo ativo atualizado.",
            }
        except Exception as e:
            logger.warning(f"Failed to save user preference, falling back to global: {e}")

    # Fallback: set global
    active_model.set(body.model)
    return {
        "active_model": active_model.get(),
        "provider": provider,
        "plan": user_plan,
        "scope": "global",
        "message": "Modelo ativo atualizado (global).",
    }


@router.get("/quota")
async def get_quota(request: Request):
    """Retorna o status de quota de LLM do usuário."""
    from core.quota import get_quota_status
    from core.plan_config import PLAN_LABELS

    user_id = getattr(request.state, "user_id", None)
    user_plan = getattr(request.state, "user_plan", "free")

    status = await get_quota_status(user_id) if user_id else {"used": 0, "monthly": 100, "remaining": 100}

    return {
        "plan": user_plan,
        "plan_label": PLAN_LABELS.get(user_plan, user_plan),
        **status,
    }
