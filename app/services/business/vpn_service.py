"""VPN diagnostic and remediation service. Implemented in Phase 3d."""

import structlog

from app.integrations.vpn.base import BaseVPNClient
from app.services.business.base import BaseService
from app.services.business.session_service import SessionService


class VPNService(BaseService):
    """Handles VPN troubleshooting diagnostics and guided remediation.

    Queries the VPN gateway for connection status, applies diagnostic
    rules, and returns a structured remediation plan for the employee.
    """

    def __init__(
        self,
        vpn_client: BaseVPNClient,
        session_service: SessionService,
        logger: structlog.BoundLogger,
    ) -> None:
        super().__init__(logger)
        self.vpn_client = vpn_client
        self.session_service = session_service

    async def diagnose(
        self,
        user_id: str,
        session_id: str,
        symptoms: list[str],
    ) -> dict:
        """Run VPN diagnostics for the given user and reported symptoms.

        Args:
            user_id: Employee UPN for looking up VPN profile and history.
            session_id: Dialogflow session ID for audit trail.
            symptoms: List of symptom strings from Dialogflow entity extraction.

        Returns:
            Dict with 'diagnosis' (str), 'steps' (list[str]), 'escalate' (bool).

        Raises:
            VPNServiceError: If VPN gateway is unreachable after retries.
        """
        self.logger.info(
            "vpn_diagnosis_started",
            user_id=user_id,
            session_id=session_id,
            symptom_count=len(symptoms),
        )

        # VPNServiceError propagates — caller (handler) decides the user-facing response
        status = await self.vpn_client.get_connection_status(user_id)
        diagnostics = await self.vpn_client.run_diagnostics(user_id)

        connected: bool = status["connected"]
        issues: list[str] = diagnostics["issues"]
        steps: list[str] = diagnostics["recommended_actions"]
        escalate: bool = len(issues) > 0

        if connected:
            diagnosis = "VPN connection is active. No issues detected."
        else:
            diagnosis = f"VPN tunnel failure detected. {len(issues)} issue(s) found."

        await self.session_service.record_action(
            session_id=session_id,
            action="vpn_diagnosis_run",
            metadata={
                "user_id": user_id,
                "connected": connected,
                "issue_count": len(issues),
                "escalate": escalate,
            },
        )
        self.logger.info(
            "vpn_diagnosis_complete",
            user_id=user_id,
            session_id=session_id,
            connected=connected,
            issue_count=len(issues),
            escalate=escalate,
        )
        return {"diagnosis": diagnosis, "steps": steps, "escalate": escalate}
