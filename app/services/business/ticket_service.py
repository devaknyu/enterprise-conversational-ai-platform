"""IT ticket business service. Implemented in Phase 3d."""

import structlog

from app.core.exceptions import IntegrationError, TicketCreationError, TicketNotFoundError
from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import IncidentResult, TicketCreateRequest
from app.services.business.base import BaseService
from app.services.business.session_service import SessionService


class TicketService(BaseService):
    """Handles ServiceNow IT ticket creation and status queries.

    Delegates all ServiceNow operations to the injected client.
    Applies priority defaults and records actions in SessionService.
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

    async def create_ticket(
        self,
        request: TicketCreateRequest,
        session_id: str,
    ) -> IncidentResult:
        """Create a new IT support incident in ServiceNow.

        Args:
            request: Ticket creation parameters (description, priority, caller_id).
            session_id: Dialogflow session ID for audit trail.

        Returns:
            IncidentResult with assigned ticket number and state.

        Raises:
            TicketCreationError: If ServiceNow incident creation fails after retries.
        """
        self.logger.info(
            "ticket_creation_initiated",
            caller_id=request.caller_id,
            session_id=session_id,
            priority=request.priority,
        )

        try:
            result = await self.servicenow_client.create_incident(request)
        except IntegrationError as exc:
            self.logger.error(
                "ticket_creation_failed",
                caller_id=request.caller_id,
                session_id=session_id,
                error=str(exc),
            )
            raise TicketCreationError(f"Ticket creation failed: {exc}") from exc

        await self.session_service.record_action(
            session_id=session_id,
            action="ticket_created",
            metadata={"ticket_number": result.ticket_number, "caller_id": request.caller_id},
        )
        self.logger.info(
            "ticket_created",
            ticket_number=result.ticket_number,
            caller_id=request.caller_id,
            session_id=session_id,
        )
        return result

    async def get_ticket_status(
        self,
        ticket_number: str,
        session_id: str,
    ) -> IncidentResult:
        """Retrieve the current status of an existing ServiceNow incident.

        Args:
            ticket_number: ServiceNow incident number (e.g. INC0001234).
            session_id: Dialogflow session ID for audit trail.

        Returns:
            IncidentResult with current state and assignment.

        Raises:
            TicketNotFoundError: If ticket_number does not exist.
            IntegrationError: If ServiceNow is unreachable after retries.
        """
        self.logger.info("ticket_status_requested", ticket_number=ticket_number, session_id=session_id)

        try:
            result = await self.servicenow_client.get_incident(ticket_number)
        except (TicketNotFoundError, IntegrationError):
            self.logger.warning(
                "ticket_lookup_failed", ticket_number=ticket_number, session_id=session_id
            )
            raise

        await self.session_service.record_action(
            session_id=session_id,
            action="ticket_status_checked",
            metadata={"ticket_number": ticket_number, "state": result.state},
        )
        self.logger.info(
            "ticket_status_retrieved",
            ticket_number=ticket_number,
            state=result.state,
            session_id=session_id,
        )
        return result
