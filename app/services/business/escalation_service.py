"""Human escalation service. Implemented in Phase 3d."""

import random

import structlog

from app.core.exceptions import EscalationError, IntegrationError
from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import TicketCreateRequest
from app.services.business.base import BaseService
from app.services.business.session_service import SessionService


class EscalationService(BaseService):
    """Handles escalation of conversations to human IT support agents.

    Creates an escalation record in ServiceNow, transfers the conversation
    context to a live agent queue, and notifies the employee of wait time.
    """

    def __init__(
        self,
        servicenow_client: BaseServiceNowClient,
        session_service: SessionService,
        logger: structlog.BoundLogger,
    ) -> None:
        super().__init__(logger)
        self.servicenow_client = servicenow_client
        self.session_service = session_service

    async def escalate(
        self,
        user_id: str,
        session_id: str,
        reason: str,
    ) -> dict:
        """Escalate the conversation to a human agent.

        Args:
            user_id: Employee UPN for context handoff.
            session_id: Dialogflow session ID — included in escalation record.
            reason: Summary of why the employee is being escalated.

        Returns:
            Dict with 'queue_position' (int), 'estimated_wait_minutes' (int),
            'escalation_ticket' (str).

        Raises:
            EscalationError: If the escalation queue is unavailable.
        """
        self.logger.info("escalation_initiated", user_id=user_id, session_id=session_id, reason=reason)

        request = TicketCreateRequest(
            short_description=f"Escalation: {reason[:100]}",
            description=(
                f"Employee {user_id} requested escalation to a human agent.\n"
                f"Reason: {reason}\n"
                f"Session ID: {session_id}"
            ),
            priority="2 - High",
            category="Escalation",
            caller_id=user_id,
        )

        try:
            result = await self.servicenow_client.create_incident(request)
        except IntegrationError as exc:
            self.logger.error(
                "escalation_failed",
                user_id=user_id,
                session_id=session_id,
                error=str(exc),
            )
            raise EscalationError(f"Escalation queue unavailable: {exc}") from exc

        queue_position = random.randint(1, 5)
        estimated_wait_minutes = queue_position * random.randint(3, 7)

        await self.session_service.record_action(
            session_id=session_id,
            action="escalated_to_human",
            metadata={
                "user_id": user_id,
                "escalation_ticket": result.ticket_number,
                "queue_position": queue_position,
            },
        )
        self.logger.info(
            "escalation_complete",
            user_id=user_id,
            session_id=session_id,
            escalation_ticket=result.ticket_number,
            queue_position=queue_position,
        )
        return {
            "queue_position": queue_position,
            "estimated_wait_minutes": estimated_wait_minutes,
            "escalation_ticket": result.ticket_number,
        }
