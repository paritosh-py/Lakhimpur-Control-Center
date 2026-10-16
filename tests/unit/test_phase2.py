"""Phase 2 unit tests: source adapters, scenario generator, run state."""
from datetime import datetime, timedelta, timezone

import pytest

from engine.clock import ScenarioClock
from engine.ingest.source import (
    LiveWeatherAdapter,
    ReplayWeatherAdapter,
    SourceMode,
    SourceRecord,
)
from engine.ingest.run import RunState
from data.generators.flood_scenario import (
    ScenarioAdapter,
    ScenarioConfig,
    EventTimeline,
    generate_event,
    generate_event_batch,
    split_events,
    _rain_at_hour,
    _compute_flood_prob,
    SegmentState,
)

T = datetime(2024, 7, 2, 0, tzinfo=timezone.utc)
WALL = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)


def _fake_weather(n_records: int = 24) -> dict:
    """Build minimal weather data for adapter tests."""
    return {
        "provider": "test-provider",
        "latitude": 27.2,
        "longitude": 94.1,
        "retrieved_at": WALL.isoformat(),
        "records": [
            {"valid_at": (T + timedelta(hours=i)).isoformat(),
             "precipitation_mm": i * 0.5,
             "interval_minutes": 60,
             "measurement": "forecast"}
            for i in range(n_records)
        ],
    }


def _fake_edges(n: int = 10) -> list[dict]:
    return [
        {"id": f"seg-{i}", "elevation_m": 90 + i * 2, "slope_degrees": 0.5 + i * 0.2,
         "distance_to_river_m": 500 + i * 300, "length_m": 100 + i * 10,
         "road_type": "primary", "from_node": f"n{i}", "to_node": f"n{i+1}"}
        for i in range(n)
    ]


def _fake_settlements(n: int = 3) -> list[dict]:
    return [
        {"id": f"sett-{i}", "name": f"Village {i}", "coordinates": [94.1 + i * 0.01, 27.2 + i * 0.01],
         "elevation_m": 95 + i, "distance_to_river_m": 1000 + i * 500,
         "graph_node_id": f"n{i}", "nearest_segment_id": f"seg-{i}"}
        for i in range(n)
    ]


def _fake_shelters(n: int = 2) -> list[dict]:
    return [
        {"id": f"shel-{i}", "name": f"Shelter {i}", "published_capacity": 30 + i * 10,
         "coordinates": [94.1 + i * 0.01, 27.2 + i * 0.01]}
        for i in range(n)
    ]


# ── Source adapter tests ──────────────────────────────────────────────

class TestLiveWeatherAdapter:
    def test_mode_and_label(self):
        adapter = LiveWeatherAdapter(_fake_weather())
        assert adapter.mode() == SourceMode.LIVE
        assert "LIVE" in adapter.display_label()

    def test_steps_yield_records_then_exhaust(self):
        weather = _fake_weather(5)
        adapter = LiveWeatherAdapter(weather)
        assert not adapter.is_exhausted()
        all_records = []
        while not adapter.is_exhausted():
            all_records.extend(adapter.step())
        assert len(all_records) == 5
        assert adapter.is_exhausted()
        assert adapter.step() == []

    def test_reset_replays_from_start(self):
        adapter = LiveWeatherAdapter(_fake_weather(3))
        adapter.step()
        adapter.step()
        adapter.reset()
        assert not adapter.is_exhausted()
        records = adapter.step()
        assert len(records) == 1
        assert records[0].payload["precipitation_mm"] == 0.0

    def test_stale_detection(self):
        adapter = LiveWeatherAdapter(_fake_weather(), stale_after_minutes=0)
        assert adapter.is_stale()
        adapter2 = LiveWeatherAdapter(_fake_weather(), stale_after_minutes=999999)
        assert not adapter2.is_stale()


class TestReplayWeatherAdapter:
    def test_mode_and_label(self):
        adapter = ReplayWeatherAdapter(
            _fake_weather(), "Test flood 2024", T)
        assert adapter.mode() == SourceMode.REPLAY
        assert "REPLAY" in adapter.display_label()
        assert "not live" in adapter.display_label()

    def test_replay_labels_are_correct(self):
        adapter = ReplayWeatherAdapter(
            _fake_weather(3), "Test flood 2024", T)
        records = adapter.step()
        assert records[0].source == "replay"
        assert records[0].event_name == "Test flood 2024"
        assert records[0].replayed_at is not None

    def test_clock_advances_with_steps(self):
        adapter = ReplayWeatherAdapter(
            _fake_weather(3), "Test flood 2024", T, step_delta=timedelta(hours=1))
        assert adapter.current_time() == T
        adapter.step()
        assert adapter.current_time() == T
        adapter.step()
        assert adapter.current_time() == T + timedelta(hours=1)

    def test_reset_rewinds_clock(self):
        adapter = ReplayWeatherAdapter(
            _fake_weather(3), "Test flood 2024", T)
        adapter.step()
        adapter.step()
        adapter.reset()
        assert adapter.current_time() == T
        assert not adapter.is_exhausted()


# ── Run state tests ───────────────────────────────────────────────────

class TestRunState:
    def test_start_and_status(self):
        rs = RunState()
        assert not rs.is_active
        adapter = LiveWeatherAdapter(_fake_weather(3))
        run_id = rs.start(adapter)
        assert rs.is_active
        assert rs.run_id == run_id
        status = rs.status()
        assert status["is_active"]
        assert status["mode"] == "live"

    def test_step_increments(self):
        rs = RunState()
        rs.start(LiveWeatherAdapter(_fake_weather(3)))
        result = rs.step()
        assert result.step_index == 1
        result2 = rs.step()
        assert result2.step_index == 2

    def test_reset_gives_new_run_id(self):
        rs = RunState()
        rs.start(LiveWeatherAdapter(_fake_weather(3)))
        old_id = rs.run_id
        rs.step()
        new_id = rs.reset()
        assert new_id != old_id
        assert rs.step_index == 0

    def test_step_without_start_raises(self):
        rs = RunState()
        with pytest.raises(RuntimeError, match="No active source"):
            rs.step()

    def test_step_when_exhausted_raises(self):
        rs = RunState()
        rs.start(LiveWeatherAdapter(_fake_weather(1)))
        rs.step()
        with pytest.raises(RuntimeError, match="exhausted"):
            rs.step()

    def test_stop_clears_state(self):
        rs = RunState()
        rs.start(LiveWeatherAdapter(_fake_weather(3)))
        rs.stop()
        assert not rs.is_active
        assert rs.run_id == ""


# ── Scenario generator tests ─────────────────────────────────────────

class TestScenarioGenerator:
    def test_same_seed_produces_identical_events(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        config = ScenarioConfig(
            event_id="test-1", seed=42, start_time=T, duration_hours=24)
        e1 = generate_event(config, edges, setts, shelters)
        e2 = generate_event(config, edges, setts, shelters)
        assert len(e1.observable_records) == len(e2.observable_records)
        assert e1.closures_generated == e2.closures_generated
        for r1, r2 in zip(e1.observable_records, e2.observable_records):
            assert r1.kind == r2.kind
            assert r1.entity_id == r2.entity_id
            assert r1.event_time == r2.event_time

    def test_different_seeds_produce_different_events(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        c1 = ScenarioConfig(event_id="test-1", seed=42, start_time=T, duration_hours=24)
        c2 = ScenarioConfig(event_id="test-2", seed=99, start_time=T, duration_hours=24)
        e1 = generate_event(c1, edges, setts, shelters)
        e2 = generate_event(c2, edges, setts, shelters)
        # At least some records should differ
        diffs = sum(1 for r1, r2 in zip(e1.observable_records, e2.observable_records)
                    if r1.payload != r2.payload)
        assert diffs > 0

    def test_observable_records_never_contain_truth(self):
        edges, setts, shelters = _fake_edges(20), _fake_settlements(5), _fake_shelters(3)
        config = ScenarioConfig(
            event_id="truth-test", seed=42, start_time=T,
            duration_hours=48, peak_rain_mm_h=35.0)
        event = generate_event(config, edges, setts, shelters)
        for rec in event.observable_records:
            assert rec.source == "simulated"
            assert "ground_truth" not in str(rec.payload)
            assert "truth" not in rec.kind.lower()

    def test_ground_truth_is_separate(self):
        edges, setts, shelters = _fake_edges(20), _fake_settlements(5), _fake_shelters(3)
        config = ScenarioConfig(
            event_id="sep-test", seed=42, start_time=T,
            duration_hours=48, peak_rain_mm_h=35.0)
        event = generate_event(config, edges, setts, shelters)
        # Ground truth should have at least the final snapshot
        assert len(event.ground_truth) >= 1
        assert event.ground_truth[-1]["kind"] == "final_snapshot"

    def test_all_records_labeled_simulated(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        config = ScenarioConfig(
            event_id="label-test", seed=42, start_time=T, duration_hours=24)
        event = generate_event(config, edges, setts, shelters)
        for rec in event.observable_records:
            assert rec.source == "simulated"
            assert rec.provider == "scenario-generator"

    def test_chronology_within_event(self):
        """Records should not have event_time after available_at."""
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        config = ScenarioConfig(
            event_id="chrono-test", seed=42, start_time=T, duration_hours=48)
        event = generate_event(config, edges, setts, shelters)
        for rec in event.observable_records:
            assert rec.event_time <= rec.available_at or rec.kind == "report"
            # Stale reports may have event_time < available_at — that's correct


class TestEventBatchAndSplits:
    def test_batch_generates_correct_count(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        events = generate_event_batch(edges, setts, shelters, num_events=10, base_seed=100)
        assert len(events) == 10

    def test_splits_are_deterministic_by_event_id(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        events = generate_event_batch(edges, setts, shelters, num_events=20, base_seed=100)
        splits = split_events(events)
        assert len(splits["train"]) == 12      # 60%
        assert len(splits["calibration"]) == 3  # 15%
        assert len(splits["held_out"]) == 5     # 25%
        # No overlap
        train_ids = {e.config.event_id for e in splits["train"]}
        cal_ids = {e.config.event_id for e in splits["calibration"]}
        held_ids = {e.config.event_id for e in splits["held_out"]}
        assert train_ids.isdisjoint(cal_ids)
        assert train_ids.isdisjoint(held_ids)
        assert cal_ids.isdisjoint(held_ids)

    def test_splits_never_random(self):
        """Same input → same splits."""
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        e1 = generate_event_batch(edges, setts, shelters, num_events=20, base_seed=100)
        e2 = generate_event_batch(edges, setts, shelters, num_events=20, base_seed=100)
        s1 = split_events(e1)
        s2 = split_events(e2)
        assert [e.config.event_id for e in s1["train"]] == [e.config.event_id for e in s2["train"]]
        assert [e.config.event_id for e in s1["held_out"]] == [e.config.event_id for e in s2["held_out"]]


class TestRainProfile:
    def test_rain_peaks_during_sustain_phase(self):
        config = ScenarioConfig(
            event_id="rain", seed=1, start_time=T,
            buildup_hours=12, sustain_hours=8, decay_hours=12,
            peak_rain_mm_h=30.0)
        buildup_rain = _rain_at_hour(6, config)
        peak_rain = _rain_at_hour(14, config)  # mid-sustain
        decay_rain = _rain_at_hour(26, config)
        tail_rain = _rain_at_hour(40, config)
        assert peak_rain > buildup_rain
        assert peak_rain > decay_rain
        assert decay_rain > tail_rain

    def test_rain_zero_outside_bounds(self):
        config = ScenarioConfig(
            event_id="rain", seed=1, start_time=T, duration_hours=48)
        assert _rain_at_hour(-1, config) == 0.0
        assert _rain_at_hour(200, config) == 0.0


class TestScenarioAdapter:
    def test_adapter_plays_back_timeline(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        config = ScenarioConfig(
            event_id="adapter-test", seed=42, start_time=T, duration_hours=12)
        event = generate_event(config, edges, setts, shelters)
        adapter = ScenarioAdapter(event)
        assert adapter.mode() == SourceMode.SCENARIO
        assert "SIMULATION" in adapter.display_label()
        assert adapter.current_time() == T

        all_records = []
        while not adapter.is_exhausted():
            all_records.extend(adapter.step())
        assert len(all_records) > 0
        assert adapter.is_exhausted()

    def test_adapter_reset(self):
        edges, setts, shelters = _fake_edges(), _fake_settlements(), _fake_shelters()
        config = ScenarioConfig(
            event_id="reset-test", seed=42, start_time=T, duration_hours=6)
        event = generate_event(config, edges, setts, shelters)
        adapter = ScenarioAdapter(event)
        adapter.step()
        adapter.step()
        adapter.reset()
        assert adapter.current_time() == T
        assert not adapter.is_exhausted()


class TestFloodModel:
    def test_high_risk_segment(self):
        """Low elevation, close to river, flat terrain, heavy rain → high prob."""
        from random import Random
        seg = SegmentState(
            segment_id="risky",
            elevation_m=20.0, slope_degrees=0.5,
            distance_to_river_m=200.0, length_m=100.0,
            road_type="primary", rain_accum_6h=120.0)
        prob = _compute_flood_prob(seg, Random(42))
        assert prob > 0.7

    def test_low_risk_segment(self):
        """High elevation, far from river, steep terrain, no rain → low prob."""
        from random import Random
        seg = SegmentState(
            segment_id="safe",
            elevation_m=180.0, slope_degrees=8.0,
            distance_to_river_m=9000.0, length_m=100.0,
            road_type="primary", rain_accum_6h=0.0)
        prob = _compute_flood_prob(seg, Random(42))
        assert prob < 0.3
