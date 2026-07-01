"""JWT authentication middleware for the /webhook endpoint. Implemented in Phase 3a."""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_webhook_token

_EXCLUDED_PATHS = frozenset({"/health", "/ready"})

_logger = structlog.get_logger(__name__)


class WebhookAuthMiddleware(BaseHTTPMiddleware):
    """Validates JWT Bearer tokens on all /webhook requests.

    Extracts Authorization: Bearer <token> header, decodes the JWT using
    JWT_SECRET_KEY, and rejects with HTTP 401 if missing, expired, or invalid.

    /health and /ready endpoints are excluded from JWT validation so Cloud Run
    health checks pass without authentication.

    See adr/004-jwt-webhook-auth.md for the full rationale.
    """

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Validate JWT on /webhook requests; pass through all others.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler in the chain.

        Returns:
            HTTP 401 JSONResponse if auth fails; otherwise the route response.
        """
        if request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            _logger.warning("auth_missing", path=request.url.path)
            return JSONResponse({"detail": "Missing authentication"}, status_code=401)

        token = auth_header[len("Bearer "):]
        settings = get_settings()
        try:
            decode_webhook_token(token, settings.jwt_secret_key)
        except AuthenticationError:
            _logger.warning("auth_failed", path=request.url.path)
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        return await call_next(request)
