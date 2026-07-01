"""Pydantic models for ServiceNow ticket domain objects."""

from datetime import datetime
from pydantic import BaseModel


class TicketCreateRequest(BaseModel):
    """Parameters for creating a new IT support incident."""

    short_description: str
    description: str
    priority: str = "3 - Moderate"
    category: str = "General"
    caller_id: str


class IncidentResult(BaseModel):
    """Result returned after creating or querying a ServiceNow incident."""

    ticket_number: str
    short_description: str
    state: str
    priority: str
    assigned_to: str
    created_at: datetime
    caller_id: str
