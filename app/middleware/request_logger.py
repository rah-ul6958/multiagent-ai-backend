import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next
    ):
        request_id = request.headers.get(
            "X-Request-ID", str(uuid.uuid4())
        )
        start_time = time.time()

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host
                if request.client
                else None,
            },
        )

        response = await call_next(request)

        process_time = round(
            (time.time() - start_time) * 1000, 2
        )

        logger.info(
            f"Request completed: {request.method} {request.url.path} {response.status_code} {process_time}ms",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": process_time,
            },
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = (
            str(process_time)
        )

        return response
