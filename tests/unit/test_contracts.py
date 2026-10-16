from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from engine.clock import LiveClock, ScenarioClock
from engine.schemas import Assignment, Event, Provenance, Shelter, WeatherObservation, require_available

T = datetime(2024, 7, 2, 10, tzinfo=timezone.utc)
WALL = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)


def provenance(**overrides):
    return dict(source="simulated", provider="test-generator", event_time=T,
                available_at=T, recorded_at=WALL) | overrides


def record(**overrides):
    return dict(id="e1", run_id="test-run", provenance=provenance()) | overrides


def test_replay_requires_original_identity_and_playback_time():
    with pytest.raises(ValidationError):
        Provenance(**provenance(source="replay"))
    p = Provenance(**provenance(source="replay", event_name="Flood 2024", replayed_at=WALL))
    assert "2024-07-02" in p.display_label and "not live" in p.display_label
    assert p.model_dump(mode="json")["replayed_at"] is not None


@pytest.mark.parametrize("changes", [
    {"source": "historical"}, {"event_time": T.replace(tzinfo=None)},
    {"available_at": T - timedelta(seconds=1)}, {"replayed_at": WALL},
    {"source": "live", "recorded_at": T - timedelta(seconds=1)},
    {"source": "replay", "event_name": "flood", "replayed_at": T - timedelta(days=1)},
    {"source": "replay", "event_name": "flood", "replayed_at": WALL + timedelta(days=1)},
])
def test_invalid_provenance_rejected(changes):
    with pytest.raises(ValidationError):
        Provenance(**provenance(**changes))


def test_labels_and_extra_fields():
    assert Provenance(**provenance()).display_label == "SIMULATION"
    assert Provenance(**provenance(source="live")).display_label == "LIVE"
    with pytest.raises(ValidationError):
        Provenance(**provenance(typo="ignored?"))


def test_clock_is_deterministic_and_rejects_backward_time():
    clock = ScenarioClock(T)
    assert clock.now() == T
    assert clock.advance(timedelta(minutes=10)) == T + timedelta(minutes=10)
    with pytest.raises(ValueError):
        clock.advance(timedelta(seconds=-1))
    with pytest.raises(ValueError):
        ScenarioClock(T.replace(tzinfo=None))
    assert LiveClock().now().utcoffset() == timedelta(0)


def test_late_report_cannot_leak_into_earlier_decision():
    event = Event(**record(provenance=provenance(available_at=T + timedelta(minutes=5))),
                  kind="report", entity_id="r1")
    with pytest.raises(ValueError, match="not available"):
        require_available(event, T)
    assert require_available(event, T + timedelta(minutes=5)) == event


def test_forecast_future_validity_is_not_future_knowledge():
    weather = WeatherObservation(**record(), location={"latitude": 27.2, "longitude": 94.1},
                                 measurement="forecast", precipitation_mm=15,
                                 interval_minutes=60, valid_at=T + timedelta(hours=3))
    assert require_available(weather, T) == weather
    with pytest.raises(ValidationError):
        WeatherObservation(**(weather.model_dump() | {"measurement": "observed"}))


def test_shelter_and_assignment_validation():
    with pytest.raises(ValidationError):
        Shelter(**record(), name="A", location={"latitude": 27, "longitude": 94},
                capacity=10, occupied=11)
    with pytest.raises(ValidationError):
        Assignment(**record(), settlement_id="s1", team_id="t1", route_segment_ids=[],
                   starts_at=T, ends_at=T, status="proposed")
