"""The only module allowed to read the system clock."""
from datetime import datetime, timedelta, timezone
from typing import Protocol


def require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    return value.astimezone(timezone.utc)


class Clock(Protocol):
    def now(self) -> datetime: ...


class LiveClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class ScenarioClock:
    """Explicit event time for both replay and simulation; never wall-time driven."""

    def __init__(self, start: datetime):
        self._time = require_aware(start)

    def now(self) -> datetime:
        return self._time

    def advance(self, delta: timedelta) -> datetime:
        if delta.total_seconds() < 0:
            raise ValueError("Scenario clock cannot move backwards; create a new run")
        self._time += delta
        return self._time
