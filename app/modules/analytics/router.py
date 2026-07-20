from fastapi import APIRouter, Depends, Query

from app.database.models.user import User
from app.modules.auth.dependencies import (
    get_current_user,
)
from app.modules.analytics.service import AnalyticsService
from app.schemas.response import APIResponse

router = APIRouter()
service = AnalyticsService()


@router.get(
    "/",
    response_model=APIResponse,
    summary="Get analytics overview",
)
async def get_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(get_current_user),
):
    result = await service.get_analytics(days)
    return APIResponse(
        message="Analytics retrieved",
        data=result.model_dump(),
    )


@router.get(
    "/overview",
    response_model=APIResponse,
    summary="Get analytics overview only",
)
async def get_overview(
    admin: User = Depends(get_current_user),
):
    result = await service.get_analytics(30)
    return APIResponse(
        message="Overview retrieved",
        data=result.overview.model_dump(),
    )


@router.get(
    "/agents",
    response_model=APIResponse,
    summary="Get agent performance analytics",
)
async def get_agent_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(get_current_user),
):
    result = await service.get_analytics(days)
    return APIResponse(
        message="Agent analytics retrieved",
        data={
            "agents": [
                a.model_dump() for a in result.agent_breakdown
            ]
        },
    )


@router.get(
    "/intents",
    response_model=APIResponse,
    summary="Get intent distribution analytics",
)
async def get_intent_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(get_current_user),
):
    result = await service.get_analytics(days)
    return APIResponse(
        message="Intent analytics retrieved",
        data={
            "intents": [
                i.model_dump()
                for i in result.intent_breakdown
            ]
        },
    )
