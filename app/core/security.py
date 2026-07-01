"""JWT utilities for Dialogflow → FastAPI webhook authentication.

Provides encode/decode helpers used by WebhookAuthMiddleware and
the generate_jwt.py dev helper script. All JWT operations use HS256
with the shared JWT_SECRET_KEY from settings.

See adr/004-jwt-webhook-auth.md for the full rationale.
"""

from datetime import datetime, timezone


def create_webhook_token(secret: str, expiry_minutes: int = 60) -> str:
    """Create a signed HS256 JWT for use as a Dialogflow webhook bearer token.

    Args:
        secret: The HMAC signing secret (JWT_SECRET_KEY from settings).
        expiry_minutes: Token lifetime in minutes. Default 60.

    Returns:
        Signed JWT string suitable for use in Authorization: Bearer <token>.
    """
    ...


def decode_webhook_token(token: str, secret: str) -> dict:
    """Decode and validate a webhook JWT.

    Validates signature and expiry claim. Raises AuthenticationError on
    any validation failure — callers must not swallow this exception.

    Args:
        token: Raw JWT string extracted from the Authorization header.
        secret: The HMAC signing secret (JWT_SECRET_KEY from settings).

    Returns:
        Decoded JWT payload as a dict.

    Raises:
        AuthenticationError: If the token is missing, expired, or has an
            invalid signature.
    """
    ...
