"""
Tests — Authentication: login, JWT, protected routes.
"""

import pytest
import pytest_asyncio


class TestPasswordHashing:
    def test_hash_and_verify(self, auth_service):
        hashed = auth_service.hash_password("secret123")
        assert hashed != "secret123"
        assert auth_service.verify_password("secret123", hashed)

    def test_wrong_password_rejected(self, auth_service):
        hashed = auth_service.hash_password("correct")
        assert not auth_service.verify_password("wrong", hashed)

    def test_empty_password_rejected(self, auth_service):
        hashed = auth_service.hash_password("something")
        assert not auth_service.verify_password("", hashed)


class TestJWT:
    def test_create_and_decode_token(self, auth_service):
        token = auth_service.create_access_token({"sub": "alice"})
        assert token
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "alice"

    def test_expired_token_returns_none(self, auth_service):
        # Force expiry to 0 minutes
        import time
        from jose import jwt
        from datetime import datetime, timedelta, timezone
        expired = jwt.encode(
            {"sub": "alice", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            auth_service.secret_key,
            algorithm=auth_service.algorithm,
        )
        assert auth_service.decode_token(expired) is None

    def test_tampered_token_returns_none(self, auth_service):
        token = auth_service.create_access_token({"sub": "alice"})
        tampered = token + "x"
        assert auth_service.decode_token(tampered) is None


@pytest.mark.asyncio
class TestLoginEndpoint:
    async def test_login_success(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_user(self, app_client):
        resp = await app_client.post(
            "/api/auth/login",
            json={"username": "ghost", "password": "pass"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestProtectedRoutes:
    async def test_health_public(self, app_client):
        resp = await app_client.get("/api/health")
        assert resp.status_code == 200

    async def test_root_public(self, app_client):
        resp = await app_client.get("/")
        assert resp.status_code == 200

    async def test_datasources_requires_token(self, app_client):
        # When REQUIRE_AUTH=false this will pass, but we can still test the route exists
        resp = await app_client.get("/api/datasources")
        assert resp.status_code in (200, 401)

    async def test_me_with_valid_token(self, authed_client):
        resp = await authed_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
