"""
smtp_schema.py - Pydantic schemas for SMTP pool management API endpoints.
Passwords are write-only and never returned in responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


# ============================================================
# Request Schemas
# ============================================================

class SMTPAccountCreate(BaseModel):
    """Schema for creating a new SMTP account."""
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable label")
    email: str = Field(..., description="Sender email address")
    password: str = Field(..., min_length=1, description="SMTP password (will be encrypted)")
    host: str = Field(..., description="SMTP server host")
    port: int = Field(default=587, description="SMTP server port")
    use_tls: bool = Field(default=False, description="Use direct TLS (port 465)")
    use_starttls: bool = Field(default=True, description="Use STARTTLS (port 587)")
    daily_limit: int = Field(default=500, ge=1, description="Max emails per day")
    hourly_limit: int = Field(default=50, ge=1, description="Max emails per hour")
    priority: int = Field(default=5, ge=1, le=100, description="Priority weight for weighted strategy")
    warmup_enabled: bool = Field(default=False, description="Enable warm-up mode")
    warmup_daily_increment: int = Field(default=20, ge=1, description="Emails added per day during warm-up")
    provider: Optional[str] = Field(default="custom", description="Provider: gmail, outlook, brevo, ses, mailgun, custom")


class SMTPAccountUpdate(BaseModel):
    """Schema for updating an SMTP account. All fields are optional."""
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    password: Optional[str] = Field(None, description="Leave blank to keep current password")
    host: Optional[str] = None
    port: Optional[int] = None
    use_tls: Optional[bool] = None
    use_starttls: Optional[bool] = None
    daily_limit: Optional[int] = Field(None, ge=1)
    hourly_limit: Optional[int] = Field(None, ge=1)
    priority: Optional[int] = Field(None, ge=1, le=100)
    warmup_enabled: Optional[bool] = None
    warmup_daily_increment: Optional[int] = Field(None, ge=1)
    provider: Optional[str] = None


class SMTPTestRequest(BaseModel):
    """Schema for testing an SMTP connection."""
    # Either provide an existing account ID, or inline credentials
    id: Optional[int] = Field(None, description="Test an existing account by ID")
    host: Optional[str] = None
    port: Optional[int] = None
    email: Optional[str] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = False
    use_starttls: Optional[bool] = True


# ============================================================
# Response Schemas
# ============================================================

class SMTPAccountResponse(BaseModel):
    """
    Response schema for SMTP account.
    Password is NEVER returned — shows a masked placeholder.
    """
    id: int
    name: str
    email: str
    host: str
    port: int
    use_tls: bool
    use_starttls: bool
    daily_limit: int
    hourly_limit: int
    sent_today: int
    sent_this_hour: int
    last_sent_at: Optional[datetime] = None
    status: str
    priority: int
    failure_count: int
    total_sent: int
    total_failed: int
    warmup_enabled: bool
    warmup_start_date: Optional[date] = None
    warmup_daily_increment: int
    provider: Optional[str] = None

    # Computed fields
    remaining_daily: int = 0
    remaining_hourly: int = 0
    success_rate: float = 0.0

    # Masked password placeholder
    password: str = "••••••••"

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SMTPAccountStats(BaseModel):
    """Aggregate statistics for the entire SMTP pool."""
    total_accounts: int = 0
    active_accounts: int = 0
    paused_accounts: int = 0
    blocked_accounts: int = 0
    disabled_accounts: int = 0
    total_sent_today: int = 0
    total_remaining_today: int = 0
    total_daily_capacity: int = 0
    accounts_at_limit: int = 0


class SMTPTestResponse(BaseModel):
    """Response schema for SMTP connection test."""
    success: bool
    message: str
    latency_ms: Optional[float] = None
