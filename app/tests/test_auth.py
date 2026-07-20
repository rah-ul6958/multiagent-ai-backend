import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_get_current_admin_user_rejects_non_admin():
    from app.core.exceptions import AuthorizationError
    from app.modules.auth.dependencies import get_current_admin_user

    user = MagicMock(role="user", is_active=True)
    with pytest.raises(AuthorizationError, match="Admin access required"):
        await get_current_admin_user(current_user=user)


@pytest.mark.asyncio
async def test_register_success(client):
    with patch(
        "app.modules.auth.service.AuthService.register"
    ) as mock_register:
        mock_register.return_value = MagicMock(
            model_dump=lambda: {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "token_type": "Bearer",
                "user": {
                    "id": "123",
                    "full_name": "Test User",
                    "email": "test@example.com",
                    "role": "user",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                },
            }
        )

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "invalid-email",
            "password": "password123",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "123",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    with patch(
        "app.modules.auth.service.AuthService.login"
    ) as mock_login:
        mock_login.return_value = MagicMock(
            model_dump=lambda: {
                "access_token": "test_token",
                "refresh_token": "test_refresh",
                "token_type": "Bearer",
                "user": {
                    "id": "123",
                    "full_name": "Test User",
                    "email": "test@example.com",
                    "role": "user",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                },
            }
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    with patch(
        "app.modules.auth.service.AuthService.login"
    ) as mock_login:
        from app.core.exceptions import (
            AuthenticationError,
        )

        mock_login.side_effect = AuthenticationError(
            "Invalid email or password"
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_fields(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_profile_requires_auth(client):
    response = await client.get(
        "/api/v1/auth/profile"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_change_password_requires_auth(client):
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "old",
            "new_password": "newpassword123",
        },
    )
    assert response.status_code == 403
