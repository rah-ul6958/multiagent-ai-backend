import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models.user import User


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    response = await client.get(
        "/api/v1/chat/sessions"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_search_requires_auth(client):
    response = await client.get(
        "/api/v1/chat/search", params={"q": "test"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_delete_requires_auth(client):
    response = await client.delete(
        "/api/v1/chat/sessions/test_id"
    )
    assert response.status_code == 403


def _make_fake_user():
    user = MagicMock(spec=User)
    user.id = "test_user_id"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.role = "user"
    user.is_active = True
    return user


@pytest.mark.asyncio
async def test_chat_list_sessions(client):
    from app.modules.chat.router import router as chat_router
    from app.modules.auth.dependencies import get_current_user

    fake_user = _make_fake_user()
    app = client._transport.app
    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        with patch(
            "app.modules.chat.service.ChatService.list_sessions"
        ) as mock_list:
            mock_list.return_value = MagicMock(
                model_dump=lambda: {
                    "sessions": [],
                    "total": 0,
                }
            )

            response = await client.get(
                "/api/v1/chat/sessions"
            )

            assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_get_history(client):
    from app.modules.auth.dependencies import get_current_user

    fake_user = _make_fake_user()
    app = client._transport.app
    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        with patch(
            "app.modules.chat.service.ChatService.get_chat_history"
        ) as mock_history:
            mock_history.return_value = MagicMock(
                model_dump=lambda: {
                    "session": {
                        "id": "123",
                        "title": "Test",
                        "status": "active",
                        "agent_type": None,
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                        "message_count": 0,
                    },
                    "messages": [],
                }
            )

            response = await client.get(
                "/api/v1/chat/sessions/test_id"
            )

            assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
