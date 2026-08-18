"""
conftest.py – Shared fixtures for backend tests.
"""
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src import app
from src.db.main import AsyncSessionLocal
from src.db.models import User


# ---------------------------------------------------------------------------
# FastAPI test client fixture
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to the FastAPI app with ASGITransport."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helpers – create test users and produce auth headers
# ---------------------------------------------------------------------------
def generate_user_data():
    uid_str = uuid.uuid4().hex[:6]
    return {
        "first_name": "Test",
        "last_name": "User",
        "username": f"u{uid_str}",
        "email": f"test_{uid_str}@example.com",
        "password": "Password123",
    }


@pytest_asyncio.fixture()
async def test_user_data():
    return generate_user_data()


@pytest_asyncio.fixture()
async def registered_user(client: AsyncClient, test_user_data):
    """Registers a user and marks them as verified for authenticated test flows."""
    resp = await client.post("/auth/signup", json=test_user_data)
    assert resp.status_code == 200, f"Signup failed: {resp.text}"

    async with AsyncSessionLocal() as session:
        result = await session.exec(select(User).where(User.email == test_user_data["email"]))
        user = result.first()
        if user:
            user.is_verified = True
            session.add(user)
            await session.commit()
            await session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def auth_headers(client: AsyncClient, test_user_data, registered_user) -> dict:
    """Returns Bearer auth headers for the registered test user."""
    resp = await client.post(
        "/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
