"""User identity verification service. Implemented in Phase 3b."""

import structlog

from app.core.exceptions import IntegrationError, UserNotFoundError
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import UserProfile
from app.services.business.base import BaseService
from app.services.business.session_service import SessionService


class AuthService(BaseService):
    """Verifies employee identity via Active Directory.

    Centralises all AD user-lookup logic so PasswordService, VPNService,
    and TicketService call verify_user() rather than each importing the AD
    client directly. This means the "does this user exist?" policy lives in
    exactly one place.

    Dependency path: AuthService → BaseActiveDirectoryClient (mock or real,
    swapped via USE_MOCK_INTEGRATIONS env var in DI layer).
    """

    def __init__(
        self,
        ad_client: BaseActiveDirectoryClient,
        session_service: SessionService,
        logger: structlog.BoundLogger,
    ) -> None:
        super().__init__(logger)
        self.ad_client = ad_client
        self.session_service = session_service

    async def verify_user(self, user_id: str, session_id: str) -> UserProfile:
        """Look up an employee in Active Directory and record the check.

        Args:
            user_id: Employee UPN (e.g. john.doe@acme.com).
            session_id: Dialogflow session ID for the audit trail.

        Returns:
            UserProfile for the verified employee.

        Raises:
            UserNotFoundError: If user_id is not in Active Directory.
            IntegrationError: If the AD service is unavailable after retries.
        """
        self.logger.info("verifying_user", user_id=user_id, session_id=session_id)

        try:
            profile = await self.ad_client.get_user_profile(user_id)
        except (UserNotFoundError, IntegrationError):
            self.logger.warning(
                "user_verification_failed", user_id=user_id, session_id=session_id
            )
            raise

        await self.session_service.record_action(
            session_id=session_id,
            action="user_verified",
            metadata={"user_id": user_id, "department": profile.department},
        )

        self.logger.info(
            "user_verified",
            user_id=user_id,
            session_id=session_id,
            department=profile.department,
        )
        return profile
