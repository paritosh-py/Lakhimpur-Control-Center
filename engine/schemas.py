"""Version-one contracts. Domain behavior belongs in later phases."""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from engine.clock import require_aware

Identifier = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^\S+$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Provenance(Contract):
    source: Literal["live", "replay", "simulated"]
    provider: Annotated[str, Field(min_length=1)]
    event_time: AwareDatetime
    available_at: AwareDatetime
    recorded_at: AwareDatetime
    event_name: str | None = Field(default=None, min_length=1)
    replayed_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_timeline(self):
        if self.available_at < self.event_time:
            raise ValueError("available_at cannot precede event_time; forecasts use valid_at")
        if self.source == "replay":
            if not self.event_name or self.replayed_at is None:
                raise ValueError("Replay requires event_name and replayed_at")
            if self.replayed_at < self.available_at or self.recorded_at < self.replayed_at:
                raise ValueError("Replay recording must follow original availability and playback")
        elif self.replayed_at is not None:
            raise ValueError("Only replay records may carry replayed_at")
        if self.source == "live" and self.recorded_at < self.available_at:
            raise ValueError("Live recording cannot precede availability")
        return self

    @property
    def display_label(self) -> str:
        if self.source == "replay":
            return f"REPLAY: {self.event_name}; event dated {self.event_time.date()}; not live"
        return "SIMULATION" if self.source == "simulated" else "LIVE"


class Record(Contract):
    id: Identifier
    run_id: Identifier
    provenance: Provenance


class Location(Contract):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Settlement(Record):
    name: str = Field(min_length=1)
    location: Location
    population: int | None = Field(default=None, ge=0)


class RoadSegment(Record):
    from_node: Identifier
    to_node: Identifier
    length_m: float = Field(gt=0)
    travel_minutes: float = Field(gt=0)
    status: Literal["unknown", "open", "at_risk", "confirmed_closed"] = "unknown"


class Shelter(Record):
    name: str = Field(min_length=1)
    location: Location
    capacity: int = Field(ge=0)
    occupied: int = Field(ge=0)

    @model_validator(mode="after")
    def capacity_check(self):
        if self.occupied > self.capacity:
            raise ValueError("Shelter occupancy exceeds capacity")
        return self


class Report(Record):
    raw_text: str = Field(min_length=1, max_length=2000)
    transport: Literal["internet", "esp_now"]
    sender_location: Location | None = None
    settlement_id: Identifier | None = None
    road_id: Identifier | None = None
    people_count: int | None = Field(default=None, ge=0)


class Resource(Record):
    kind: Literal["team", "vehicle", "boat"]
    location: Location
    capacity: int = Field(ge=0)
    status: Literal["free", "assigned", "en_route", "on_task", "unavailable"]


class Assignment(Record):
    settlement_id: Identifier
    team_id: Identifier
    vehicle_id: Identifier | None = None
    shelter_id: Identifier | None = None
    route_segment_ids: tuple[Identifier, ...]
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    status: Literal["proposed", "accepted", "en_route", "arrived", "completed", "impossible"]

    @model_validator(mode="after")
    def positive_window(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Assignment must have a positive reservation window")
        return self


class WeatherObservation(Record):
    location: Location
    measurement: Literal["observed", "forecast", "reanalysis"]
    precipitation_mm: float = Field(ge=0)
    interval_minutes: int = Field(gt=0)
    valid_at: AwareDatetime

    @model_validator(mode="after")
    def valid_time(self):
        if self.measurement != "forecast" and self.valid_at != self.provenance.event_time:
            raise ValueError("Observation/reanalysis valid_at must equal event_time")
        if self.measurement == "forecast" and self.valid_at < self.provenance.event_time:
            raise ValueError("Forecast validity cannot precede issue time")
        return self


class Event(Record):
    kind: Literal["weather", "report", "closure", "resource_change", "assignment_update"]
    entity_id: Identifier


def require_available(record: Record, decision_time: datetime) -> Record:
    """Future forecast validity is allowed; future availability is not."""
    decision_time = require_aware(decision_time)
    if record.provenance.available_at > decision_time:
        raise ValueError("Record was not available at decision time")
    return record
