"""JWT authentication middleware for the /webhook endpoint. Implemented in Phase 3b."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


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
        ...
