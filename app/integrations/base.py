"""Base class for all real (non-mock) external API integration clients.

Provides shared httpx AsyncClient setup, timeout configuration, and
a tenacity retry decorator factory. All real integration clients inherit
from this — never implement retry logic in individual clients.

Mock clients do NOT inherit from BaseIntegration (they don't make HTTP calls).
They implement only the domain-specific abstract base (e.g. BaseServiceNowClient).
"""

import logging

import httpx
import structlog
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import IntegrationError


class BaseIntegration:
    """Base class for all real external API clients.

    Provides:
    - Shared httpx.AsyncClient with timeout configuration
    - Tenacity retry decorator factory with exponential backoff and jitter
    - Structured error logging on retry attempts and final failures
    - _get() and _post() helpers that convert HTTP errors to IntegrationError

    Subclasses set their base_url and optionally override DEFAULT_TIMEOUT
    and MAX_RETRIES. They call _get()/_post() for all HTTP operations.
    """

    DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
    MAX_RETRIES = 3
    RETRY_MIN_WAIT = 1
    RETRY_MAX_WAIT = 10

    def __init__(self, base_url: str, logger: structlog.BoundLogger) -> None:
        self.base_url = base_url
        self.logger = logger.bind(integration=self.__class__.__name__)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=self.DEFAULT_TIMEOUT,
        )

    async def __aenter__(self) -> "BaseIntegration":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    def _retryable(self) -> object:
        """Return a tenacity retry decorator for transient HTTP errors.

        Retries on TransportError and TimeoutException with exponential
        backoff. Logs each retry attempt at WARNING level.

        Returns:
            Configured tenacity retry decorator.
        """
        return retry(
            stop=stop_after_attempt(self.MAX_RETRIES),
            wait=wait_exponential(
                multiplier=1,
                min=self.RETRY_MIN_WAIT,
                max=self.RETRY_MAX_WAIT,
            ),
            retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
            reraise=True,
        )

    async def _get(self, path: str, **kwargs: object) -> dict:
        """Execute a GET request and return the JSON response body.

        Args:
            path: URL path relative to base_url.
            **kwargs: Additional arguments passed to httpx.AsyncClient.get().

        Returns:
            Parsed JSON response as a dict.

        Raises:
            IntegrationError: On HTTP error status or network failure.
        """
        try:
            response = await self._client.get(path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error("http_error", path=path, status=e.response.status_code)
            raise IntegrationError(f"HTTP {e.response.status_code} from {path}") from e
        except httpx.RequestError as e:
            self.logger.error("request_error", path=path, error=str(e))
            raise IntegrationError(f"Request failed: {path}") from e

    async def _post(self, path: str, payload: dict, **kwargs: object) -> dict:
        """Execute a POST request with a JSON body and return the response.

        Args:
            path: URL path relative to base_url.
            payload: Request body serialized to JSON.
            **kwargs: Additional arguments passed to httpx.AsyncClient.post().

        Returns:
            Parsed JSON response as a dict.

        Raises:
            IntegrationError: On HTTP error status or network failure.
        """
        try:
            response = await self._client.post(path, json=payload, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error("http_error", path=path, status=e.response.status_code)
            raise IntegrationError(f"HTTP {e.response.status_code} from {path}") from e
        except httpx.RequestError as e:
            self.logger.error("request_error", path=path, error=str(e))
            raise IntegrationError(f"Request failed: {path}") from e
