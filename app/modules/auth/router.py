from fastapi import APIRouter, Depends

from app.core.config import settings
from app.modules.auth.dependencies import (
    get_current_admin_user,
    get_current_user,
)
from app.modules.auth.repository import UserRepository
from app.modules.auth.schema import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SeedAdminRequest,
    UpdateProfileRequest,
)
from app.modules.auth.security import hash_password
from app.modules.auth.service import AuthService
from app.schemas.response import APIResponse
from app.database.models.user import User

router = APIRouter()
service = AuthService()
user_repository = UserRepository()


@router.post(
    "/register",
    response_model=APIResponse,
    summary="Register a new user",
)
async def register(data: RegisterRequest):
    result = await service.register(data)
    payload = (
        result.model_dump()
        if hasattr(result, "model_dump")
        else result
    )
    return APIResponse(
        message="Registration successful",
        data=payload,
    )


@router.post(
    "/login",
    response_model=APIResponse,
    summary="Login with credentials",
)
async def login(data: LoginRequest):
    result = await service.login(data)
    payload = (
        result.model_dump()
        if hasattr(result, "model_dump")
        else result
    )
    return APIResponse(
        message="Login successful",
        data=payload,
    )


@router.post(
    "/refresh",
    response_model=APIResponse,
    summary="Refresh access token",
)
async def refresh_token(data: RefreshTokenRequest):
    result = await service.refresh_token(data.refresh_token)
    payload = (
        result.model_dump()
        if hasattr(result, "model_dump")
        else result
    )
    return APIResponse(
        message="Token refreshed",
        data=payload,
    )


@router.get(
    "/profile",
    response_model=APIResponse,
    summary="Get current user profile",
)
async def get_profile(current_user: User = Depends(get_current_user)):
    result = await service.get_profile(str(current_user.id))
    return APIResponse(
        message="Profile retrieved",
        data=result.model_dump(),
    )


@router.put(
    "/profile",
    response_model=APIResponse,
    summary="Update current user profile",
)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
):
    result = await service.update_profile(
        str(current_user.id), data
    )
    return APIResponse(
        message="Profile updated",
        data=result.model_dump(),
    )


@router.post(
    "/change-password",
    response_model=APIResponse,
    summary="Change password",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    result = await service.change_password(
        str(current_user.id), data
    )
    return APIResponse(message=result["message"])


@router.post(
    "/forgot-password",
    response_model=APIResponse,
    summary="Request password reset",
)
async def forgot_password(data: ForgotPasswordRequest):
    result = await service.forgot_password(data)
    return APIResponse(message=result["message"])


@router.post(
    "/reset-password",
    response_model=APIResponse,
    summary="Reset password with token",
)
async def reset_password(data: ResetPasswordRequest):
    result = await service.reset_password(data)
    return APIResponse(message=result["message"])


if settings.DEBUG:
    @router.post(
        "/seed-admin",
        response_model=APIResponse,
        summary="Create or promote a development admin user",
    )
    async def seed_admin(data: SeedAdminRequest):
        existing_user = await user_repository.get_by_email(data.email)
        if existing_user:
            existing_user.role = "admin"
            existing_user.password_hash = hash_password(data.password)
            existing_user.is_active = True
            updated_user = await existing_user.save()
            return APIResponse(
                message="Admin user updated",
                data={
                    "email": updated_user.email,
                    "role": updated_user.role,
                },
            )

        admin_user = User(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role="admin",
            is_active=True,
        )
        await admin_user.insert()
        return APIResponse(
            message="Admin user created",
            data={"email": admin_user.email, "role": admin_user.role},
        )


@router.get(
    "/users",
    response_model=APIResponse,
    summary="List all users (admin only)",
)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_current_admin_user),
):
    users = await service.list_users(skip, limit)
    return APIResponse(
        message="Users retrieved",
        data={"users": [u.model_dump() for u in users]},
    )


@router.post(
    "/users/{user_id}/deactivate",
    response_model=APIResponse,
    summary="Deactivate user (admin only)",
)
async def deactivate_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
):
    result = await service.deactivate_user(user_id)
    return APIResponse(
        message="User deactivated",
        data=result.model_dump(),
    )


@router.post(
    "/users/{user_id}/activate",
    response_model=APIResponse,
    summary="Activate user (admin only)",
)
async def activate_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
):
    result = await service.activate_user(user_id)
    return APIResponse(
        message="User activated",
        data=result.model_dump(),
    )
