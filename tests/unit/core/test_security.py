"""Unit tests for JWT security utilities. Implemented in Phase 3b."""

import pytest


class TestJWTSecurity:
    """Unit tests for create_webhook_token() and decode_webhook_token()."""

    def test_create_token_returns_string(self):
        """create_webhook_token() returns a non-empty string."""
        pass

    def test_decode_valid_token_returns_payload(self):
        """decode_webhook_token() returns the payload for a valid token."""
        pass

    def test_decode_expired_token_raises_authentication_error(self):
        """An expired token raises AuthenticationError."""
        pass

    def test_decode_tampered_token_raises_authentication_error(self):
        """A token with modified payload raises AuthenticationError (sig invalid)."""
        pass

    def test_decode_wrong_secret_raises_authentication_error(self):
        """A token decoded with the wrong secret raises AuthenticationError."""
        pass
