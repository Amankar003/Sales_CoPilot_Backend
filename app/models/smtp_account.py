"""
smtp_account.py - SMTPAccount model for the multi-SMTP pool system.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date


class SMTPAccount(SQLModel, table=True):
    """Represents an SMTP email account in the sending pool."""

    __tablename__ = "smtp_accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Human-readable label (e.g., "Gmail Main")
    email: str = Field(index=True)  # Sender email address
    password_encrypted: str  # Fernet-encrypted SMTP password

    # Connection settings
    host: str  # SMTP host (e.g., smtp.gmail.com)
    port: int = Field(default=587)
    use_tls: bool = Field(default=False)  # True for port 465 (direct TLS)
    use_starttls: bool = Field(default=True)  # True for port 587 (STARTTLS)

    # Rate limiting
    daily_limit: int = Field(default=500)
    hourly_limit: int = Field(default=50)
    sent_today: int = Field(default=0)
    sent_this_hour: int = Field(default=0)

    # Timestamps for counter resets
    last_sent_at: Optional[datetime] = Field(default=None)
    last_reset_date: Optional[date] = Field(default=None)
    last_hour_reset: Optional[datetime] = Field(default=None)

    # Status management
    status: str = Field(default="active", index=True)  # active, paused, blocked, disabled

    # Priority for weighted strategy (higher = more traffic)
    priority: int = Field(default=5)

    # Failure tracking
    failure_count: int = Field(default=0)  # Consecutive failures since last success

    # Lifetime statistics
    total_sent: int = Field(default=0)
    total_failed: int = Field(default=0)

    # Warm-up configuration
    warmup_enabled: bool = Field(default=False)
    warmup_start_date: Optional[date] = Field(default=None)
    warmup_daily_increment: int = Field(default=20)  # Emails added per day during ramp

    # Provider hint for UI display
    provider: Optional[str] = Field(default="custom")  # gmail, outlook, brevo, ses, mailgun, custom

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
