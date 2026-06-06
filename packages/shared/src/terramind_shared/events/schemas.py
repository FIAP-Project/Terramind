"""Tipos de evento e schemas Pydantic transportados no barramento."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"
    AUTH_FAILED = "auth.failed"
    SATELLITE_READING_RECORDED = "satellite.reading.recorded"
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_RESOLVED = "alert.resolved"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BaseEvent(BaseModel):
    """Envelope base para todos os eventos de domínio."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    occurred_at: datetime = Field(default_factory=_utcnow)
    actor_user_id: str | None = None


# --- Auth ---

class UserRegisteredEvent(BaseEvent):
    event_type: EventType = EventType.USER_REGISTERED
    user_id: str
    email: str
    role: str


class UserLoggedInEvent(BaseEvent):
    event_type: EventType = EventType.USER_LOGGED_IN
    user_id: str
    email: str


class AuthFailedEvent(BaseEvent):
    event_type: EventType = EventType.AUTH_FAILED
    email: str
    reason: str


# --- Satellites ---

class SatelliteReadingRecordedEvent(BaseEvent):
    event_type: EventType = EventType.SATELLITE_READING_RECORDED
    satellite_id: str
    plot_id: str
    satellite_type: str
    value: float
    unit: str
    captured_at: datetime


# --- Alerts ---

class AlertTriggeredEvent(BaseEvent):
    event_type: EventType = EventType.ALERT_TRIGGERED
    alert_id: str
    plot_id: str
    severity: str
    message: str


class AlertResolvedEvent(BaseEvent):
    event_type: EventType = EventType.ALERT_RESOLVED
    alert_id: str
    plot_id: str
