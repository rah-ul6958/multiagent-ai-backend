import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_database():
    with patch(
        "app.database.mongodb.get_database"
    ) as mock:
        mock_db = AsyncMock()
        mock.return_value = mock_db
        yield mock_db


@pytest_asyncio.fixture
async def mock_user():
    user = AsyncMock()
    user.id = "test_user_id"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.role = "user"
    user.is_active = True
    user.password_hash = "hashed_password"
    return user


@pytest_asyncio.fixture
async def mock_admin_user():
    user = AsyncMock()
    user.id = "admin_user_id"
    user.email = "admin@example.com"
    user.full_name = "Admin User"
    user.role = "admin"
    user.is_active = True
    user.password_hash = "hashed_password"
    return user
