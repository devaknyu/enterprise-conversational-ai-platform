"""Request/response logging middleware. Implemented in Phase 3a."""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every incoming request and outgoing response with structured context.

    Assigns a unique request_id to each request, logs method, path, and
    status code. Binds request_id to structlog context vars so all log
    events within a request automatically include it.
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Log request/response and bind request_id to log context.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            The route response, unchanged.
        """
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id

        logger = structlog.get_logger(__name__)
        logger.info("request_received", method=request.method, path=request.url.path)

        response = await call_next(request)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response
