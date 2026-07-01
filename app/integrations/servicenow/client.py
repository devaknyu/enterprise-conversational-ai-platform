"""Real ServiceNow integration client. Implemented in Phase 3c."""

import structlog

from app.integrations.base import BaseIntegration
from app.integrations.servicenow.base import BaseServiceNowClient
from app.models.ticket import IncidentResult, TicketCreateRequest


class ServiceNowClient(BaseIntegration, BaseServiceNowClient):
    """Production ServiceNow client using the Table API.

    Uses httpx with tenacity retry logic (inherited from BaseIntegration).
    Activated when USE_MOCK_INTEGRATIONS=false in production.
    Requires SERVICENOW_BASE_URL, SERVICENOW_USERNAME, SERVICENOW_PASSWORD.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        logger: structlog.BoundLogger,
    ) -> None:
        BaseIntegration.__init__(self, base_url=base_url, logger=logger)
        self.username = username
        self.password = password

    async def create_incident(self, request: TicketCreateRequest) -> IncidentResult:
        """Create incident via ServiceNow Table API with retry logic."""
        ...

    async def get_incident(self, ticket_number: str) -> IncidentResult:
        """Get incident status via ServiceNow Table API with retry logic."""
        ...
