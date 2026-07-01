"""Password reset business service. Implemented in Phase 3d."""

import structlog

from app.services.business.base import BaseService
from app.models.user import PasswordResetResult


class PasswordService(BaseService):
    """Handles password reset flows via Active Directory integration.

    Validates that the user exists, delegates the reset to the AD client,
    records the action in SessionService for audit, and returns a typed result.
    Never calls Active Directory directly — always through the injected client.
    """

    def __init__(
        self,
        ad_client: object,
        session_service: object,
        logger: structlog.BoundLogger,
    ) -> None:
        super().__init__(logger)
        self.ad_client = ad_client
        self.session_service = session_service

    async def initiate_reset(
        self,
        user_id: str,
        session_id: str,
    ) -> PasswordResetResult:
        """Initiate a password reset for the given user.

        Args:
            user_id: Employee UPN (e.g. john.doe@acme.com) from Dialogflow.
            session_id: Dialogflow session ID for audit trail.

        Returns:
            PasswordResetResult with delivery method and ticket reference.

        Raises:
            UserNotFoundError: If user_id does not exist in Active Directory.
            PasswordResetError: If the reset operation fails after retries.
        """
        ...
