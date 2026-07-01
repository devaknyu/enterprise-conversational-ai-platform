"""Mock Active Directory client for development and testing. Implemented in Phase 3c."""

import asyncio
import random
from datetime import datetime, timezone

import structlog

from app.core.exceptions import IntegrationError, UserNotFoundError
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import PasswordResetResult, UserProfile

_MOCK_USERS: dict[str, UserProfile] = {
    "john.doe@acme.com": UserProfile(
        user_id="john.doe@acme.com",
        employee_id="EMP001",
        display_name="John Doe",
        email="john.doe@acme.com",
        department="Engineering",
        manager="jane.smith@acme.com",
        phone="+1-555-0100",
        location="NYC",
        account_status="active",
    ),
    "jane.smith@acme.com": UserProfile(
        user_id="jane.smith@acme.com",
        employee_id="EMP002",
        display_name="Jane Smith",
        email="jane.smith@acme.com",
        department="IT Operations",
        manager="cto@acme.com",
        phone="+1-555-0200",
        location="NYC",
        account_status="active",
    ),
    "bob.jones@acme.com": UserProfile(
        user_id="bob.jones@acme.com",
        employee_id="EMP003",
        display_name="Bob Jones",
        email="bob.jones@acme.com",
        department="Finance",
        manager="jane.smith@acme.com",
        phone="+1-555-0300",
        location="Chicago",
        account_status="locked",
    ),
}


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

    async def _simulate_call(self, operation: str) -> None:
        """Inject configurable latency and a random transient failure."""
        delay = random.uniform(self.latency_min_ms, self.latency_max_ms) / 1000
        await asyncio.sleep(delay)
        if random.random() < self.error_rate:
            self.logger.warning("mock_error_injected", operation=operation)
            raise IntegrationError(
                f"AD service unavailable (simulated failure in {operation})"
            )

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Simulate user profile retrieval with latency and configurable error rate."""
        await self._simulate_call("get_user_profile")
        if user_id not in _MOCK_USERS:
            raise UserNotFoundError(f"User not found: {user_id}")
        profile = _MOCK_USERS[user_id]
        self.logger.info(
            "ad_get_user_profile", user_id=user_id, account_status=profile.account_status
        )
        return profile

    async def reset_password(self, user_id: str) -> PasswordResetResult:
        """Simulate a password reset with latency and configurable error rate."""
        await self._simulate_call("reset_password")
        if user_id not in _MOCK_USERS:
            raise UserNotFoundError(f"User not found: {user_id}")
        result = PasswordResetResult(
            success=True,
            user_id=user_id,
            delivery_method="email",
            estimated_delivery_minutes=5,
            ticket_reference=f"CHG{random.randint(1000000, 9999999)}",
            reset_at=datetime.now(timezone.utc),
        )
        self.logger.info("ad_reset_password", user_id=user_id, ticket_reference=result.ticket_reference)
        return result
