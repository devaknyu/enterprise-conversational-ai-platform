"""Mock Active Directory client for development and testing. Implemented in Phase 3c."""

import structlog

from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import PasswordResetResult, UserProfile


class MockActiveDirectoryClient(BaseActiveDirectoryClient):
    """Mock Active Directory client with realistic latency and error simulation.

    Activated when USE_MOCK_INTEGRATIONS=true (default in development).
    Returns realistic-shaped response models using the MOCK_USERS dataset.

    Available test users:
        john.doe@acme.com  — active account (happy path)
        jane.smith@acme.com — active, manager-level account
        bob.jones@acme.com  — locked account (error path testing)
    """

    def __init__(
        self,
        error_rate: float = 0.05,
        latency_min_ms: int = 100,
        latency_max_ms: int = 300,
    ) -> None:
        self.error_rate = error_rate
        self.latency_min_ms = latency_min_ms
        self.latency_max_ms = latency_max_ms
        self.logger = structlog.get_logger(__name__).bind(client="MockActiveDirectoryClient")

    async def reset_password(self, user_id: str) -> PasswordResetResult:
        """Simulate a password reset with latency and configurable error rate."""
        ...

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Simulate user profile retrieval with latency and configurable error rate."""
        ...
