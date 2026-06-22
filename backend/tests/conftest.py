"""
pytest fixtures — shared across all test modules.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure backend root on sys.path
_BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(_BACKEND))

# ── Environment overrides for testing ──────────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("REQUIRE_AUTH", "false")   # most tests opt-in per scenario
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest.fixture(scope="session")
def tmp_data_dir() -> Generator[Path, None, None]:
    """Temporary data directory — deleted after test session."""
    with tempfile.TemporaryDirectory(prefix="oraculo_test_") as d:
        p = Path(d)
        (p / "catalog").mkdir()
        (p / "alerts").mkdir()
        (p / "reports").mkdir()
        (p / "graphs").mkdir()
        (p / "vector_store").mkdir()
        os.environ["DATA_DIR"] = str(p)
        yield p


@pytest.fixture(scope="session")
def sample_csv(tmp_data_dir: Path) -> Path:
    """Write a minimal CSV file and return its path."""
    path = tmp_data_dir / "test_sales.csv"
    path.write_text(
        "id,customer,product,amount,date\n"
        "1,Alice,Widget,100.0,2024-01-01\n"
        "2,Bob,Gadget,250.5,2024-01-02\n"
        "3,Alice,Widget,75.0,2024-01-03\n"
        "4,Carol,Gadget,300.0,2024-01-04\n"
        "5,Bob,Widget,50.0,2024-01-05\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture(scope="session")
def sample_excel(tmp_data_dir: Path) -> Path:
    """Write a minimal Excel file and return its path."""
    import pandas as pd
    path = tmp_data_dir / "test_hr.xlsx"
    df = pd.DataFrame({
        "employee_id": [1, 2, 3],
        "name": ["Ana", "Bruno", "Carlos"],
        "salary": [5000, 7000, 4500],
        "department": ["HR", "Engineering", "HR"],
    })
    df.to_excel(path, index=False)
    return path


@pytest.fixture(scope="session")
def auth_service():
    from api.auth_service import AuthService
    return AuthService(users_file=":memory:")   # in-memory path won't persist


@pytest_asyncio.fixture(scope="session")
async def app_client(tmp_data_dir):
    """AsyncClient wrapping the FastAPI app — no auth required."""
    from api.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def auth_token(app_client):
    """Obtain a valid JWT token for the default admin user."""
    resp = await app_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def authed_client(app_client, auth_token):
    """Client with Authorization header preset."""
    app_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    yield app_client
    # Remove header after test
    app_client.headers.pop("Authorization", None)
