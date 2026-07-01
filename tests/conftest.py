"""Shared test fixtures for the Enterprise IT Support Assistant test suite.

All fixtures used across multiple test files live here.
Test-specific fixtures stay in their respective test files.

Follows the pytest-convention skill: DI overrides, not module-level patch.
Implemented in Phase 3a — stubs here, filled in as services are built.
"""

import pytest
import structlog
from httpx import AsyncClient, ASGITransport

from app.config import Settings


# ---------------------------------------------------------------------------
# Settings Override
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Overridden settings for the test environment.

    Uses mock integrations, deterministic secrets, zero mock latency,
    and the free LLM backend (gemini_api). No GCP credentials required
    to run the test suite.
    """
    return Settings(
        app_env="development",
        jwt_secret_key="test-secret-key-minimum-32-characters-long",
        jwt_algorithm="HS256",
        jwt_expiry_minutes=60,
        webhook_shared_secret="test-webhook-secret-1234",
        llm_backend="gemini_api",
        gemini_api_key="test-key-not-real",
        gemini_model="gemini-2.0-flash",
        embedding_backend="local",
        embedding_model_local="all-MiniLM-L6-v2",
        google_cloud_project="test-project",
        use_mock_integrations=True,
        mock_error_rate=0.0,          # Disable random errors — test errors explicitly
        mock_latency_ms_min=0,        # Zero latency for test speed
        mock_latency_ms_max=0,
        chroma_persist_dir="./tests/fixtures/chroma_test_db",
        chroma_collection_name="test_knowledge_base",
    )


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

@pytest.fixture
def test_logger() -> structlog.BoundLogger:
    """Configured structlog logger for test use."""
    return structlog.get_logger("test")


# ---------------------------------------------------------------------------
# Test Data Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_user_id() -> str:
    """Active user available in MockActiveDirectoryClient."""
    return "john.doe@acme.com"


@pytest.fixture
def unknown_user_id() -> str:
    """User ID not present in MockActiveDirectoryClient."""
    return "unknown.user@acme.com"


@pytest.fixture
def locked_user_id() -> str:
    """Locked account user in MockActiveDirectoryClient (error path)."""
    return "bob.jones@acme.com"


@pytest.fixture
def valid_session_id() -> str:
    """Realistic Dialogflow CX session ID."""
    return "projects/test-project/locations/us-central1/agents/test-agent/sessions/sess-001"


@pytest.fixture
def valid_ticket_id() -> str:
    """Ticket number available in MockServiceNowClient."""
    return "INC0001234"
