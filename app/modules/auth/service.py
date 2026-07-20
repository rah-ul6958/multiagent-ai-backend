import logging

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
)
from app.database.models.user import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schema import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.modules.auth.security import hash_password, verify_password
from app.shared.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.repository = UserRepository()

    def _user_to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=str(user.id),
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def register(self, data: RegisterRequest) -> TokenResponse:
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already registered")

        user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
        )

        created_user = await self.repository.create(user)
        logger.info(f"User registered: {created_user.email}")

        return TokenResponse(
            access_token=create_access_token(
                str(created_user.id), created_user.role
            ),
            refresh_token=create_refresh_token(str(created_user.id)),
            user=self._user_to_response(created_user),
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repository.get_by_email(data.email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        logger.info(f"User logged in: {user.email}")

        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role),
            refresh_token=create_refresh_token(str(user.id)),
            user=self._user_to_response(user),
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role),
            refresh_token=create_refresh_token(str(user.id)),
            user=self._user_to_response(user),
        )

    async def get_profile(self, user_id: str) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return self._user_to_response(user)

    async def update_profile(
        self, user_id: str, data: UpdateProfileRequest
    ) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.email is not None:
            existing = await self.repository.get_by_email(data.email)
            if existing and str(existing.id) != user_id:
                raise ConflictError("Email already in use")
            user.email = data.email

        updated_user = await self.repository.update(user)
        return self._user_to_response(updated_user)

    async def change_password(
        self, user_id: str, data: ChangePasswordRequest
    ) -> dict:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        if not verify_password(data.current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")

        user.password_hash = hash_password(data.new_password)
        await self.repository.update(user)

        logger.info(f"Password changed for user: {user.email}")
        return {"message": "Password updated successfully"}

    async def forgot_password(self, data: ForgotPasswordRequest) -> dict:
        user = await self.repository.get_by_email(data.email)
        if user:
            logger.info(
                f"Password reset requested for: {data.email}"
            )
        return {
            "message": "If the email exists, a reset link has been sent"
        }

    async def reset_password(
        self, data: ResetPasswordRequest
    ) -> dict:
        payload = decode_token(data.token)
        if payload.get("type") != "reset":
            raise AuthenticationError("Invalid reset token")

        user_id = payload.get("sub")
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user.password_hash = hash_password(data.new_password)
        await self.repository.update(user)

        logger.info(f"Password reset completed for user: {user.email}")
        return {"message": "Password reset successfully"}

    async def list_users(
        self, skip: int = 0, limit: int = 50
    ) -> list[UserResponse]:
        users = await self.repository.list_users(skip, limit)
        return [self._user_to_response(u) for u in users]

    async def deactivate_user(self, user_id: str) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user.is_active = False
        updated_user = await self.repository.update(user)
        logger.info(f"User deactivated: {user.email}")
        return self._user_to_response(updated_user)

    async def activate_user(self, user_id: str) -> UserResponse:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        user.is_active = True
        updated_user = await self.repository.update(user)
        logger.info(f"User activated: {user.email}")
        return self._user_to_response(updated_user)
