"""Abstract base class for all business services."""

from abc import ABC
import structlog


class BaseService(ABC):
    """Abstract base for all business services.

    Provides a pre-bound structured logger. Every subclass receives
    a logger with the service class name automatically bound as context,
    so all log events from that service carry a 'service' field.

    Subclasses must call super().__init__(logger) in their constructors.
    """

    def __init__(self, logger: structlog.BoundLogger) -> None:
        self.logger = logger.bind(service=self.__class__.__name__)
