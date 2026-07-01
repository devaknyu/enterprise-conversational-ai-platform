"""Abstract interface for VPN gateway integration."""

from abc import ABC, abstractmethod


class BaseVPNClient(ABC):
    """Contract for all VPN gateway client implementations."""

    @abstractmethod
    async def get_connection_status(self, user_id: str) -> dict:
        """Retrieve the current VPN connection status for a user.

        Args:
            user_id: Employee UPN to look up in the VPN gateway.

        Returns:
            Dict with 'connected' (bool), 'last_connected' (str ISO8601),
            'client_version' (str), 'assigned_ip' (str).

        Raises:
            VPNServiceError: If the gateway is unreachable after retries.
        """
        ...

    @abstractmethod
    async def run_diagnostics(self, user_id: str) -> dict:
        """Run connection diagnostics for the given user.

        Args:
            user_id: Employee UPN.

        Returns:
            Dict with 'checks' (list of check results), 'issues' (list of str),
            'recommended_actions' (list of str).

        Raises:
            VPNServiceError: If diagnostics fail after retries.
        """
        ...
