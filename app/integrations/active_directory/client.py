"""Real Active Directory integration client. Implemented in Phase 3c."""

import structlog

from app.integrations.base import BaseIntegration
from app.integrations.active_directory.base import BaseActiveDirectoryClient
from app.models.user import PasswordResetResult, UserProfile


class ActiveDirectoryClient(BaseIntegration, BaseActiveDirectoryClient):
    """Production Active Directory client using the AD REST API.

    Uses httpx with tenacity retry logic (inherited from BaseIntegration).
    Activated when USE_MOCK_INTEGRATIONS=false in production.
    Requires AD_BASE_URL and AD_SERVICE_ACCOUNT environment variables.
    """

    def __init__(self, base_url: str, service_account: str, logger: structlog.BoundLogger) -> None:
        BaseIntegration.__init__(self, base_url=base_url, logger=logger)
        self.service_account = service_account

    async def reset_password(self, user_id: str) -> PasswordResetResult:
        """Reset password via the AD REST API with retry logic."""
        ...

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Retrieve user profile via the AD REST API with retry logic."""
        ...
