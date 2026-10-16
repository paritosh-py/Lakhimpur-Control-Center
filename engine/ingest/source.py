"""Common source-adapter interface (Phase 2, Task 1).

Every data source — live feed, historical replay, seeded scenario —
implements SourceAdapter so the engine sees a single stream of
timestamped records.  Source-specific behaviour lives in subclasses;
the engine never branches on source type.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Sequence

from engine.clock import Clock, LiveClock, ScenarioClock, require_aware


class SourceMode(str, Enum):
    LIVE = "live"
    REPLAY = "replay"
    SCENARIO = "scenario"


@dataclass(frozen=True)
class SourceRecord:
    """Uniform envelope emitted by every adapter."""
    kind: str                       # "weather", "report", "closure", "resource_change"
    entity_id: str                  # settlement/segment/shelter ID
    event_time: datetime            # when this happened in the event timeline
    available_at: datetime          # when the system could act on it
    payload: dict[str, Any]         # source-specific data
    source: str                     # "live" | "replay" | "simulated"
    provider: str
    event_name: str | None = None   # only for replay
    replayed_at: datetime | None = None  # only for replay


class SourceAdapter(abc.ABC):
    """Contract that every data source must satisfy."""

    @abc.abstractmethod
    def mode(self) -> SourceMode:
        """Which mode this adapter represents."""

    @abc.abstractmethod
    def clock(self) -> Clock:
        """The clock governing this source's timeline."""

    @abc.abstractmethod
    def step(self) -> Sequence[SourceRecord]:
        """Advance one time step and return new records.

        Returns an empty sequence when the source has no more data.
        """

    @abc.abstractmethod
    def reset(self) -> None:
        """Return to the initial state, discarding all progress."""

    @abc.abstractmethod
    def is_exhausted(self) -> bool:
        """True when there are no more steps to yield."""

    @abc.abstractmethod
    def display_label(self) -> str:
        """Human-readable banner text for the UI."""

    @abc.abstractmethod
    def current_time(self) -> datetime:
        """The current event-timeline time."""

    def provenance_kwargs(self, event_time: datetime) -> dict:
        """Build base provenance fields for Pydantic schema validation."""
        now_utc = datetime.now(timezone.utc)
        base = {
            "event_time": event_time,
            "available_at": event_time,
            "recorded_at": now_utc,
            "provider": "source-adapter",
        }
        if self.mode() == SourceMode.REPLAY:
            base["source"] = "replay"
            base["replayed_at"] = now_utc
        elif self.mode() == SourceMode.SCENARIO:
            base["source"] = "simulated"
        else:
            base["source"] = "live"
        return base


class LiveWeatherAdapter(SourceAdapter):
    """Wraps the cached live weather snapshot as a source adapter.

    Each step returns one hour of weather observations across all
    settlement grid cells.  In true live mode this would poll the
    upstream API; for the hackathon it reads the cached GFS snapshot
    with stale-detection.
    """

    def __init__(self, weather_data: dict, *, stale_after_minutes: int = 360):
        self._data = weather_data
        self._records = weather_data["records"]
        self._provider = weather_data["provider"]
        self._stale_minutes = stale_after_minutes
        self._fetched = datetime.fromisoformat(weather_data["retrieved_at"])
        self._index = 0
        self._clock = LiveClock()

    def mode(self) -> SourceMode:
        return SourceMode.LIVE

    def clock(self) -> Clock:
        return self._clock

    def step(self) -> Sequence[SourceRecord]:
        if self._index >= len(self._records):
            return []
        rec = self._records[self._index]
        self._index += 1
        valid_at = datetime.fromisoformat(rec["valid_at"])
        return [SourceRecord(
            kind="weather",
            entity_id=f"grid-{self._data['latitude']:.2f}-{self._data['longitude']:.2f}",
            event_time=valid_at,
            available_at=self._fetched,
            payload={"precipitation_mm": rec["precipitation_mm"],
                     "interval_minutes": rec["interval_minutes"],
                     "measurement": rec["measurement"]},
            source="live",
            provider=self._provider,
        )]

    def reset(self) -> None:
        self._index = 0

    def is_exhausted(self) -> bool:
        return self._index >= len(self._records)

    def is_stale(self) -> bool:
        age = datetime.now(timezone.utc) - self._fetched
        return age > timedelta(minutes=self._stale_minutes)

    def display_label(self) -> str:
        stale = " [STALE]" if self.is_stale() else ""
        return f"LIVE{stale}"

    def current_time(self) -> datetime:
        return self._clock.now()


class ReplayWeatherAdapter(SourceAdapter):
    """Plays back historical ERA5 weather hour-by-hour.

    Each step advances the scenario clock by one hour and yields
    weather records for that hour.  Labels are always source=replay
    with original event timestamps preserved.
    """

    def __init__(self, weather_data: dict, event_name: str,
                 start: datetime, step_delta: timedelta = timedelta(hours=1)):
        self._data = weather_data
        self._locations = weather_data.get('locations', [weather_data])
        self._times = sorted({require_aware(datetime.fromisoformat(r['valid_at']))
                              for loc in self._locations for r in loc['records']})
        self._event_name = event_name
        self._step_delta = step_delta
        self._start = require_aware(start)
        self._clock = ScenarioClock(start)
        self._index = 0

    def mode(self) -> SourceMode:
        return SourceMode.REPLAY

    def clock(self) -> Clock:
        return self._clock

    def step(self) -> Sequence[SourceRecord]:
        if self._index >= len(self._times):
            return []
        valid_at = self._times[self._index]
        self._clock = ScenarioClock(valid_at)
        result = []
        for loc in self._locations:
            rec = next((r for r in loc['records'] if datetime.fromisoformat(r['valid_at']) == valid_at), None)
            if rec is None: continue
            entity = loc.get('settlement_id', f"grid-{loc['latitude']:.2f}-{loc['longitude']:.2f}")
            result.append(SourceRecord(
                kind='weather', entity_id=entity, event_time=valid_at, available_at=valid_at,
                payload={'precipitation_mm': rec['precipitation_mm'], 'interval_minutes': rec['interval_minutes'],
                         'measurement': 'reanalysis', 'settlement_ids': [entity],
                         'grid': [loc['latitude'], loc['longitude']],
                         'original_available_at': rec.get('original_available_at'),
                         'retrieved_at': loc.get('retrieved_at'),
                         'availability_basis': 'Retrospective playback release at validity time; original operational availability unknown'},
                source='replay', provider=loc['provider'], event_name=self._event_name,
                replayed_at=LiveClock().now()))
        self._index += 1
        return result

    def reset(self) -> None:
        self._index = 0
        self._clock = ScenarioClock(self._start)

    def is_exhausted(self) -> bool:
        return self._index >= len(self._times)

    def display_label(self) -> str:
        return (f"REPLAY: {self._event_name}; "
                f"event dated {self._start.date()}; not live")

    def current_time(self) -> datetime:
        return self._clock.now()
