"""
Testes para o endpoint de modelos.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from api.routers import models as models_router


@pytest.fixture
def models_app():
    """FastAPI mínimo apenas com o router de modelos."""
    app = FastAPI()
    app.include_router(models_router.router, prefix="/api")
    return app


@pytest.mark.asyncio
async def test_list_opencode_models_fallback(models_app, monkeypatch):
    """Sem OPENCODE_API_KEY, o endpoint retorna a lista estática de fallback."""
    monkeypatch.setattr(models_router.settings, "OPENCODE_API_KEY", "")
    async with AsyncClient(
        transport=ASGITransport(app=models_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/models?provider=opencode")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "opencode"
    assert data["source"] == "fallback"
    assert len(data["models"]) > 0
    assert any(m["is_free"] for m in data["models"])
    assert all(m["id"].startswith("opencode/") for m in data["models"])


@pytest.mark.asyncio
async def test_list_openai_models_static(models_app):
    async with AsyncClient(
        transport=ASGITransport(app=models_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/models?provider=openai")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openai"
    assert data["source"] == "static"
    assert any(m["id"] == "gpt-4o" for m in data["models"])


@pytest.mark.asyncio
async def test_list_anthropic_models_static(models_app):
    async with AsyncClient(
        transport=ASGITransport(app=models_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/models?provider=anthropic")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "anthropic"
    assert data["source"] == "static"
    assert any(m["id"] == "claude-haiku-4-5" for m in data["models"])


@pytest.mark.asyncio
async def test_list_zai_models_static(models_app):
    async with AsyncClient(
        transport=ASGITransport(app=models_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/models?provider=zai")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "zai"
    assert data["source"] == "static"
    assert any(m["id"] == "glm-4.5-flash" and m["is_free"] for m in data["models"])
    assert any(m["id"] == "glm-5" and not m["is_free"] for m in data["models"])
