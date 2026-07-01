"""Pydantic models for user and password reset domain objects."""

from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    """Employee profile retrieved from Active Directory."""

    user_id: str
    employee_id: str
    display_name: str
    email: str
    department: str
    manager: str
    phone: str
    location: str
    account_status: str


class PasswordResetResult(BaseModel):
    """Result of a password reset operation."""

    success: bool
    user_id: str
    delivery_method: str
    estimated_delivery_minutes: int
    ticket_reference: str
    reset_at: datetime
