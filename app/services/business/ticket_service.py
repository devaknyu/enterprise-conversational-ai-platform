"""IT ticket business service. Implemented in Phase 3d."""

import structlog

from app.services.business.base import BaseService
from app.models.ticket import TicketCreateRequest, IncidentResult


class TicketService(BaseService):
    """Handles ServiceNow IT ticket creation and status queries.

    Delegates all ServiceNow operations to the injected client.
    Applies priority defaults and records actions in SessionService.
    """

    def __init__(
        self,
        servicenow_client: object,
        session_service: object,
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
        ...

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
        ...
