"""
Tests for the plan-based LLM access control system.

Covers:
- plan_config: model access per plan
- LLMClient: plan-aware model selection
- Models router: filtering by plan
- Auth: JWT contains plan, admin can update plan
- Quota: tracking and reset
"""

import pytest
import sys
from pathlib import Path

# Ensure backend root on sys.path
_BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(_BACKEND))


# ── plan_config tests ────────────────────────────────────────────────────────

class TestPlanConfig:
    def test_free_plan_has_only_free_models(self):
        from core.plan_config import PLAN_MODELS
        free = PLAN_MODELS["free"]
        # Free plan should not have openai or anthropic models
        assert free["openai"] == []
        assert free["anthropic"] == []

    def test_enterprise_has_all_providers(self):
        from core.plan_config import PLAN_MODELS
        ent = PLAN_MODELS["enterprise"]
        assert len(ent["openai"]) > 0
        assert len(ent["anthropic"]) > 0
        assert len(ent["zai"]) > 0
        assert len(ent["opencode"]) > 0

    def test_premium_superset_of_free(self):
        from core.plan_config import PLAN_MODELS
        for provider in ["zai", "opencode"]:
            free_set = set(PLAN_MODELS["free"][provider])
            premium_set = set(PLAN_MODELS["premium"][provider])
            assert free_set.issubset(premium_set), f"Premium should include all free models for {provider}"

    def test_is_model_allowed(self):
        from core.plan_config import is_model_allowed
        assert is_model_allowed("free", "zai", "glm-4.5-flash") is True
        assert is_model_allowed("free", "zai", "glm-4.5") is False
        assert is_model_allowed("premium", "zai", "glm-4.5") is True
        assert is_model_allowed("free", "openai", "gpt-4o") is False
        assert is_model_allowed("enterprise", "openai", "gpt-4o") is True

    def test_get_quota(self):
        from core.plan_config import get_quota
        assert get_quota("free") == 100
        assert get_quota("premium") == 2000
        assert get_quota("enterprise") == 10000

    def test_get_available_providers(self):
        from core.plan_config import get_available_providers
        free_providers = get_available_providers("free")
        assert "zai" in free_providers
        assert "opencode" in free_providers
        assert "openai" not in free_providers
        assert "anthropic" not in free_providers

        ent_providers = get_available_providers("enterprise")
        assert "openai" in ent_providers
        assert "anthropic" in ent_providers


# ── LLMClient plan-aware tests ───────────────────────────────────────────────

class TestLLMClientPlanAware:
    def test_infer_provider_from_model(self):
        from core.llm_client import LLMClient
        assert LLMClient._infer_provider_from_model("glm-4.5-flash") == "zai"
        assert LLMClient._infer_provider_from_model("opencode/deepseek-v4-flash-free") == "opencode"
        assert LLMClient._infer_provider_from_model("claude-haiku-4-5") == "anthropic"
        assert LLMClient._infer_provider_from_model("gpt-4o") == "openai"

    def test_free_user_cannot_use_paid_model(self):
        from core.llm_client import LLMClient
        client = LLMClient(user_plan="free", user_model="gpt-4o")
        # Model should NOT be gpt-4o since free plan doesn't allow it
        assert client._model_override != "gpt-4o"

    def test_enterprise_user_can_use_paid_model(self):
        from core.llm_client import LLMClient
        client = LLMClient(user_plan="enterprise", user_model="gpt-4o")
        assert client._model_override == "gpt-4o"

    def test_free_user_model_falls_back_to_allowed(self):
        from core.llm_client import LLMClient
        client = LLMClient(user_plan="free", user_model="glm-4.5")
        # glm-4.5 is not free, should fall back to an allowed model
        assert client._model_override != "glm-4.5"


# ── Auth JWT plan tests ──────────────────────────────────────────────────────

class TestAuthPlan:
    def test_admin_has_enterprise_plan(self, auth_service):
        user = auth_service.get_user("admin")
        assert user is not None
        assert user.get("plan") == "enterprise"

    def test_new_user_gets_free_plan(self, auth_service):
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = auth_service.register_user(
            username=username,
            email=f"{username}@test.com",
            password="testpass123",
        )
        assert user.get("plan") == "free"
        # Cleanup
        auth_service.delete_user(username)

    def test_jwt_contains_plan(self, auth_service):
        token = auth_service.create_access_token(
            data={"sub": "admin", "user_id": "test-id", "plan": "premium"}
        )
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload.get("plan") == "premium"

    def test_update_user_plan(self, auth_service):
        import uuid
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        auth_service.register_user(
            username=username,
            email=f"{username}@test.com",
            password="testpass123",
        )
        updated = auth_service.update_user(username, {"plan": "premium", "llm_quota_monthly": 2000})
        assert updated["plan"] == "premium"
        assert updated["llm_quota_monthly"] == 2000
        auth_service.delete_user(username)


# ── Models router tests ──────────────────────────────────────────────────────

class TestModelsRouter:
    @pytest.mark.asyncio
    async def test_models_filtered_by_plan(self, app_client):
        """Models endpoint should return plan field and filtered models."""
        # Login as admin (enterprise plan)
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query Z.AI models — plan field should be present
        resp = await app_client.get("/api/models?provider=zai", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
        assert "models" in data
        # In test env (REQUIRE_AUTH=false), middleware doesn't run so plan defaults to "free"
        # The important assertion is that models are filtered (free plan has fewer models)
        if data["plan"] == "free":
            # Free plan: only 2 Z.AI models (glm-4.5-flash, glm-4.7-flash)
            assert len(data["models"]) == 2
        else:
            # Enterprise: all 8 Z.AI models
            assert len(data["models"]) > 2

    @pytest.mark.asyncio
    async def test_providers_endpoint(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await app_client.get("/api/models/providers", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
        assert "providers" in data
        assert isinstance(data["providers"], list)

    @pytest.mark.asyncio
    async def test_quota_endpoint(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await app_client.get("/api/quota", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
        assert "used" in data
        assert "monthly" in data
        assert "remaining" in data

    @pytest.mark.asyncio
    async def test_active_model_per_user(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Set active model
        resp = await app_client.post(
            "/api/active-model",
            json={"model": "glm-4.5-flash", "provider": "zai"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_model"] == "glm-4.5-flash"

        # Verify it's saved
        resp = await app_client.get("/api/active-model", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_model"] == "glm-4.5-flash"

    @pytest.mark.asyncio
    async def test_set_model_not_allowed_for_plan(self, app_client):
        """Setting a model not allowed for the user's plan should return 403."""
        # Register a free user
        import uuid
        username = f"freeuser_{uuid.uuid4().hex[:8]}"
        await app_client.post(
            "/api/auth/register",
            json={"username": username, "email": f"{username}@test.com", "password": "testpass123"},
        )
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": username, "password": "testpass123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to set a premium-only model
        resp = await app_client.post(
            "/api/active-model",
            json={"model": "gpt-4o", "provider": "openai"},
            headers=headers,
        )
        assert resp.status_code == 403


# ── Admin plan management tests ──────────────────────────────────────────────

class TestAdminPlanManagement:
    @pytest.mark.asyncio
    async def test_admin_can_update_plan(self, app_client):
        # Login as admin
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Register a user
        import uuid
        username = f"admtest_{uuid.uuid4().hex[:8]}"
        await app_client.post(
            "/api/auth/register",
            json={"username": username, "email": f"{username}@test.com", "password": "testpass123"},
        )

        # Update plan to premium
        resp = await app_client.put(
            f"/api/auth/users/{username}/plan",
            json={"plan": "premium"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "premium"
        assert data["llm_quota_monthly"] == 2000

    @pytest.mark.asyncio
    async def test_non_admin_cannot_update_plan(self, app_client):
        # Register and login as regular user
        import uuid
        username = f"nonadm_{uuid.uuid4().hex[:8]}"
        await app_client.post(
            "/api/auth/register",
            json={"username": username, "email": f"{username}@test.com", "password": "testpass123"},
        )
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": username, "password": "testpass123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to update own plan
        resp = await app_client.put(
            f"/api/auth/users/{username}/plan",
            json={"plan": "enterprise"},
            headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_plan_rejected(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await app_client.put(
            "/api/auth/users/admin/plan",
            json={"plan": "ultra"},
            headers=headers,
        )
        assert resp.status_code == 400
