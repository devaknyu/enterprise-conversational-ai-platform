"""Password reset business service. Implemented in Phase 3d."""

import structlog

from app.core.exceptions import IntegrationError, PasswordResetError, UserNotFoundError
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import PasswordResetResult
from app.services.business.base import BaseService
from app.services.business.session_service import SessionService


class PasswordService(BaseService):
    """Handles password reset flows via Active Directory integration.

    Validates that the user exists, delegates the reset to the AD client,
    records the action in SessionService for audit, and returns a typed result.
    Never calls Active Directory directly — always through the injected client.
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
        self.logger.info("password_reset_initiated", user_id=user_id, session_id=session_id)

        try:
            result = await self.ad_client.reset_password(user_id)
        except UserNotFoundError:
            self.logger.warning("password_reset_user_not_found", user_id=user_id, session_id=session_id)
            raise
        except IntegrationError as exc:
            self.logger.error(
                "password_reset_integration_failure",
                user_id=user_id,
                session_id=session_id,
                error=str(exc),
            )
            raise PasswordResetError(f"Password reset failed for {user_id}: {exc}") from exc

        await self.session_service.record_action(
            session_id=session_id,
            action="password_reset_initiated",
            metadata={"user_id": user_id, "ticket_reference": result.ticket_reference},
        )
        self.logger.info(
            "password_reset_complete",
            user_id=user_id,
            session_id=session_id,
            ticket_reference=result.ticket_reference,
        )
        return result
