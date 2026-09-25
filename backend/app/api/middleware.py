"""Request id + access log + no-store caching for API responses (api-contract §1)."""

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.errors import ErrorCode, error_body
from app.core.logging import request_id_var

logger = logging.getLogger("app.access")

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")  # echo only harmless client ids


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # last resort: the envelope, the request id, never a stack trace
            logger.exception("Unhandled error")
            response = JSONResponse(
                status_code=500,
                content=error_body(ErrorCode.INTERNAL_ERROR, "Something went wrong."),
            )
        response.headers[REQUEST_ID_HEADER] = request_id
        if request.url.path.startswith("/api/"):
            # Session-bound data must never be cached by the browser or a proxy.
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        request_id_var.reset(token)
        return response
