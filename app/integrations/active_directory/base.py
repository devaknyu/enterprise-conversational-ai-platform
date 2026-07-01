"""Abstract interface for Active Directory integration.

Both ActiveDirectoryClient (real) and MockActiveDirectoryClient (mock)
implement this contract. Business services (PasswordService) depend only
on this abstract class — they never import the concrete implementations.
"""

from abc import ABC, abstractmethod

from app.models.user import PasswordResetResult, UserProfile


class BaseActiveDirectoryClient(ABC):
    """Contract for all Active Directory client implementations."""

    @abstractmethod
    async def reset_password(self, user_id: str) -> PasswordResetResult:
        """Initiate a password reset for the given user.

        Args:
            user_id: Employee UPN (e.g. john.doe@acme.com) or employee ID.

        Returns:
            PasswordResetResult with delivery method and ticket reference.

        Raises:
            UserNotFoundError: If user_id is not found in the directory.
            IntegrationError: If the AD service is unavailable after retries.
        """
        ...

    @abstractmethod
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """Retrieve employee profile from Active Directory.

        Args:
            user_id: Employee UPN or employee ID.

        Returns:
            UserProfile with display name, department, manager, phone.

        Raises:
            UserNotFoundError: If user_id is not found.
            IntegrationError: If the AD service is unavailable after retries.
        """
        ...
