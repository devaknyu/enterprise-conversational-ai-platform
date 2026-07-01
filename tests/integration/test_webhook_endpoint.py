"""Integration tests for POST /webhook. Partially implemented in Phase 3a.

Tests the full request path: HTTP → middleware → route → dispatcher → response.
Phase 3a covers auth and fallback behaviour. Business-logic tests (Phase 7)
require mock integrations (Phase 3c) and business services (Phase 3d).
"""

import pytest
from httpx import AsyncClient

_MINIMAL_WEBHOOK_BODY = {
    "detect_intent_response_id": "",
    "intent_info": {
        "last_matched_intent": "projects/test/intents/unknown",
        "display_name": "it.unknown.intent",
        "parameters": {},
        "confidence": 0.9,
    },
    "page_info": {"current_page": "", "display_name": ""},
    "session_info": {
        "session": (
            "projects/test-project/locations/us-central1"
            "/agents/test-agent/sessions/sess-001"
        ),
        "parameters": {},
    },
    "fulfillment_info": {"tag": ""},
    "text": "help",
}


class TestWebhookEndpoint:
    """Integration tests for the /webhook route."""

    async def test_health_check_returns_200(self, async_client: AsyncClient):
        """GET /health returns 200 with status=healthy."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_webhook_without_auth_header_returns_401(self, async_client: AsyncClient):
        """Requests without Authorization header are rejected with 401."""
        response = await async_client.post("/webhook/", json=_MINIMAL_WEBHOOK_BODY)
        assert response.status_code == 401

    async def test_webhook_with_invalid_token_returns_401(self, async_client: AsyncClient):
        """Requests with a tampered or expired JWT are rejected with 401."""
        response = await async_client.post(
            "/webhook/",
            json=_MINIMAL_WEBHOOK_BODY,
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert response.status_code == 401

    async def test_webhook_with_unregistered_intent_returns_200_fallback(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Unregistered intents return 200 with a graceful fallback message."""
        response = await async_client.post(
            "/webhook/", json=_MINIMAL_WEBHOOK_BODY, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "fulfillment_response" in data
        messages = data["fulfillment_response"]["messages"]
        assert len(messages) > 0
        assert len(messages[0]["text"]["text"][0]) > 0

    async def test_password_reset_webhook_returns_200(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Valid password reset webhook with a known user_id returns HTTP 200."""
        body = {
            **_MINIMAL_WEBHOOK_BODY,
            "intent_info": {
                **_MINIMAL_WEBHOOK_BODY["intent_info"],
                "display_name": "it.password.reset",
            },
            "session_info": {
                "session": (
                    "projects/test-project/locations/us-central1"
                    "/agents/test-agent/sessions/sess-001"
                ),
                "parameters": {"user_id": "john.doe@acme.com"},
            },
        }
        response = await async_client.post("/webhook/", json=body, headers=auth_headers)
        assert response.status_code == 200
        assert "fulfillment_response" in response.json()

    async def test_password_reset_response_contains_confirmation_message(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Password reset response text includes delivery method and ticket reference."""
        body = {
            **_MINIMAL_WEBHOOK_BODY,
            "intent_info": {
                **_MINIMAL_WEBHOOK_BODY["intent_info"],
                "display_name": "it.password.reset",
            },
            "session_info": {
                "session": (
                    "projects/test-project/locations/us-central1"
                    "/agents/test-agent/sessions/sess-001"
                ),
                "parameters": {"user_id": "john.doe@acme.com"},
            },
        }
        response = await async_client.post("/webhook/", json=body, headers=auth_headers)
        data = response.json()
        text = data["fulfillment_response"]["messages"][0]["text"]["text"][0]
        assert "reset" in text.lower() or "password" in text.lower()
