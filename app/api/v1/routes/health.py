from datetime import datetime

from fastapi import APIRouter

from app.schemas.response import APIResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=APIResponse,
)
async def health():

    return APIResponse(
        success=True,
        message="Backend is healthy",
        data={
            "timestamp": datetime.utcnow(),
            "status": "UP",
        },
    )