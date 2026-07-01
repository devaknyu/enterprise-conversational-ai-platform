"""Custom exception hierarchy for the Enterprise IT Support Assistant.

All application exceptions inherit from AppBaseError. Services raise only
typed exceptions from this module — never raw Exception or ValueError.
Route handlers catch these and map them to appropriate HTTP responses or
Dialogflow fallback messages.
"""


class AppBaseError(Exception):
    """Root exception for all application errors."""


# ---------------------------------------------------------------------------
# Domain Errors — raised by business services
# ---------------------------------------------------------------------------

class UserNotFoundError(AppBaseError):
    """Raised when a user cannot be found in Active Directory or internal records."""


class PasswordResetError(AppBaseError):
    """Raised when a password reset operation fails after all retries."""


class TicketCreationError(AppBaseError):
    """Raised when ServiceNow incident creation fails."""


class TicketNotFoundError(AppBaseError):
    """Raised when a requested ticket does not exist in ServiceNow."""


class VPNServiceError(AppBaseError):
    """Raised when VPN diagnostic or remediation fails."""


class EscalationError(AppBaseError):
    """Raised when escalation to a human agent fails."""


# ---------------------------------------------------------------------------
# Infrastructure Errors — raised by integration clients
# ---------------------------------------------------------------------------

class IntegrationError(AppBaseError):
    """Raised when an external integration call fails after retries."""


class ServiceUnavailableError(AppBaseError):
    """Raised when a required downstream service cannot be reached."""


class RAGRetrievalError(AppBaseError):
    """Raised when ChromaDB similarity search fails."""


class LLMError(AppBaseError):
    """Raised when the Gemini API call fails (either backend)."""


class EmbeddingError(AppBaseError):
    """Raised when embedding generation fails (either backend)."""


# ---------------------------------------------------------------------------
# Auth / Security Errors
# ---------------------------------------------------------------------------

class AuthenticationError(AppBaseError):
    """Raised when JWT validation fails (missing, expired, or tampered token)."""


class AuthorizationError(AppBaseError):
    """Raised when a valid user lacks permission for a requested action."""


# ---------------------------------------------------------------------------
# Webhook / Dispatcher Errors
# ---------------------------------------------------------------------------

class IntentNotFoundError(AppBaseError):
    """Raised when no handler is registered for the incoming Dialogflow intent."""


class MissingParameterError(AppBaseError):
    """Raised when a required Dialogflow session parameter is absent."""
