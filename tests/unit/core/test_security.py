"""Unit tests for JWT security utilities. Implemented in Phase 3a."""

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import create_webhook_token, decode_webhook_token

_SECRET = "test-secret-key-minimum-32-characters-long"
_WRONG_SECRET = "wrong-secret-key-minimum-32-characters-xxx"


class TestJWTSecurity:
    """Unit tests for create_webhook_token() and decode_webhook_token()."""

    def test_create_token_returns_string(self):
        """create_webhook_token() returns a non-empty JWT string."""
        token = create_webhook_token(_SECRET)
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # header.payload.signature

    def test_decode_valid_token_returns_payload(self):
        """decode_webhook_token() returns the payload for a valid token."""
        token = create_webhook_token(_SECRET, expiry_minutes=60)
        payload = decode_webhook_token(token, _SECRET)
        assert payload["iss"] == "enterprise-it-assistant"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_expired_token_raises_authentication_error(self):
        """An expired token raises AuthenticationError."""
        token = create_webhook_token(_SECRET, expiry_minutes=-1)
        with pytest.raises(AuthenticationError):
            decode_webhook_token(token, _SECRET)

    def test_decode_tampered_token_raises_authentication_error(self):
        """A token with a modified signature raises AuthenticationError."""
        token = create_webhook_token(_SECRET)
        parts = token.split(".")
        # Alter a character in the middle of the signature (avoids base64url
        # padding-bit-only changes that leave the decoded bytes identical).
        mid = len(parts[-1]) // 2
        mid_char = parts[-1][mid]
        replacement = "B" if mid_char != "B" else "C"
        parts[-1] = parts[-1][:mid] + replacement + parts[-1][mid + 1:]
        tampered = ".".join(parts)
        with pytest.raises(AuthenticationError):
            decode_webhook_token(tampered, _SECRET)

    def test_decode_wrong_secret_raises_authentication_error(self):
        """A token decoded with the wrong secret raises AuthenticationError."""
        token = create_webhook_token(_SECRET)
        with pytest.raises(AuthenticationError):
            decode_webhook_token(token, _WRONG_SECRET)
