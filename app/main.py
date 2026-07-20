import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.database.mongodb import (
    close_database_connection,
    connect_to_database,
    init_beanie_models,
)
from app.middleware.request_logger import (
    RequestLoggerMiddleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    await connect_to_database()

    from app.database.models import (
        AgentLog,
        ChatSession,
        DailyAnalytics,
        DocumentMetadata,
        Feedback,
        Message,
        Ticket,
        User,
    )

    await init_beanie_models(
        document_models=[
            User,
            ChatSession,
            Message,
            DocumentMetadata,
            Feedback,
            Ticket,
            AgentLog,
            DailyAnalytics,
        ]
    )

    logger.info("Application started successfully")
    yield

    logger.info("Shutting down application...")
    await close_database_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready Multi-Agent AI Customer Support System",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, exc: AppException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
):
    request_id = request.headers.get(
        "X-Request-ID", str(uuid.uuid4())
    )
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
        },
    )


@app.middleware("http")
async def add_request_id(
    request: Request, call_next
):
    request_id = request.headers.get(
        "X-Request-ID", str(uuid.uuid4())
    )
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


from app.api.v1.routes.health import (
    router as health_router,
)
from app.websocket.handler import (
    websocket_endpoint,
)
from app.modules.admin.router import (
    router as admin_router,
)
from app.modules.analytics.router import (
    router as analytics_router,
)
from app.modules.auth.router import (
    router as auth_router,
)
from app.modules.chat.router import (
    router as chat_router,
)
from app.modules.knowledge_base.router import (
    router as kb_router,
)

API_PREFIX = settings.API_PREFIX

app.include_router(
    health_router,
    prefix=API_PREFIX,
    tags=["Health"],
)

app.include_router(
    auth_router,
    prefix=f"{API_PREFIX}/auth",
    tags=["Authentication"],
)

app.include_router(
    chat_router,
    prefix=f"{API_PREFIX}/chat",
    tags=["Chat"],
)

app.include_router(
    kb_router,
    prefix=f"{API_PREFIX}/knowledge-base",
    tags=["Knowledge Base"],
)

app.include_router(
    admin_router,
    prefix=f"{API_PREFIX}/admin",
    tags=["Admin"],
)

app.include_router(
    analytics_router,
    prefix=f"{API_PREFIX}/analytics",
    tags=["Analytics"],
)


from fastapi import WebSocket


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket_endpoint(websocket)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "ws": "/ws",
    }
