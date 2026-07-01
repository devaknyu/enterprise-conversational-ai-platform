"""Abstract interface for ServiceNow integration."""

from abc import ABC, abstractmethod

from app.models.ticket import IncidentResult, TicketCreateRequest


class BaseServiceNowClient(ABC):
    """Contract for all ServiceNow client implementations."""

    @abstractmethod
    async def create_incident(self, request: TicketCreateRequest) -> IncidentResult:
        """Create a new IT support incident in ServiceNow.

        Args:
            request: Incident parameters (description, priority, caller_id).

        Returns:
            IncidentResult with assigned ticket number, state, and created timestamp.

        Raises:
            TicketCreationError: If incident creation fails after retries.
        """
        ...

    @abstractmethod
    async def get_incident(self, ticket_number: str) -> IncidentResult:
        """Retrieve the current status of a ServiceNow incident.

        Args:
            ticket_number: Incident number (e.g. INC0001234).

        Returns:
            IncidentResult with current state, priority, and assignment.

        Raises:
            TicketNotFoundError: If ticket_number does not exist.
            IntegrationError: If ServiceNow is unreachable after retries.
        """
        ...
