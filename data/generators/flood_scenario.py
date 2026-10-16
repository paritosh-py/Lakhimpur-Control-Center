"""Seeded synthetic flood-scenario generator (Phase 2, Task 4).

Generates reproducible event sequences on the real Lakhimpur road
graph.  The flood model is simplified and explicitly simulated:

    rainfall accumulation + low elevation + waterway proximity
    → road flood probability → closure, reports, resource strain

All generated data is labeled source="simulated".  When paired with
real historical weather (ERA5 replay), closures remain labeled
"simulated" because no real closure labels exist.

Design decisions (docs/DECISIONS.md):
  - Target ~40 events for train/cal/held-out splits
  - Flood model: logistic function of weighted risk factors
  - In-memory generation, serialisable to JSON for caching
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from engine.clock import ScenarioClock, require_aware
from engine.ingest.source import SourceAdapter, SourceMode, SourceRecord


# ---------------------------------------------------------------------------
# Configuration defaults (overridable via scenario definition files)
# ---------------------------------------------------------------------------

DEFAULT_DURATION_HOURS = 72          # 3-day event
DEFAULT_STEP_HOURS = 1               # hourly steps
DEFAULT_NUM_EVENTS = 40              # train/cal/held-out splits
RAIN_INTENSITY_RANGE = (5.0, 45.0)   # mm/h peak range
RAIN_BUILDUP_HOURS = (6, 24)         # hours to peak
RAIN_SUSTAIN_HOURS = (4, 18)         # hours at/near peak
RAIN_DECAY_HOURS = (6, 24)           # hours to subside

# Flood risk weights (normalised internally)
W_RAIN_ACCUM = 0.35    # cumulative rainfall over 6 hours
W_ELEVATION = 0.25     # lower elevation = higher risk
W_RIVER_DIST = 0.25    # closer to river = higher risk
W_SLOPE = 0.15         # flatter terrain = higher risk (water pools)

# Thresholds
CLOSURE_PROB_THRESHOLD = 0.55   # above this, road may close
REPORT_PROB_PER_STEP = 0.15     # chance of a citizen report per settlement per step
STALE_REPORT_PROB = 0.08        # chance a report arrives late (stale)
CONFLICTING_REPORT_PROB = 0.10  # chance a report contradicts ground truth


@dataclass(frozen=True)
class ScenarioConfig:
    """Parameters for a single generated flood event."""
    event_id: str
    seed: int
    start_time: datetime
    duration_hours: int = DEFAULT_DURATION_HOURS
    step_hours: int = DEFAULT_STEP_HOURS
    peak_rain_mm_h: float = 20.0
    buildup_hours: int = 12
    sustain_hours: int = 8
    decay_hours: int = 12
    # Simulated resources
    num_teams: int = 3
    num_vehicles: int = 4
    num_boats: int = 2
    shelter_capacity_factor: float = 0.7  # fraction of published capacity available


@dataclass
class SegmentState:
    """Mutable state tracking a road segment during simulation."""
    segment_id: str
    elevation_m: float
    slope_degrees: float
    distance_to_river_m: float
    length_m: float
    road_type: str
    rain_accum_6h: float = 0.0         # rolling 6h accumulation
    flood_probability: float = 0.0
    is_closed: bool = False
    closed_at: datetime | None = None
    closure_source: str | None = None   # "ground_truth" for hidden truth


@dataclass
class SettlementState:
    """Mutable state tracking a settlement during simulation."""
    settlement_id: str
    name: str
    elevation_m: float
    distance_to_river_m: float
    graph_node_id: str
    population_simulated: int = 0       # assigned during generation
    needs_rescue: bool = False
    needs_rescue_since: datetime | None = None


@dataclass
class ShelterState:
    """Mutable state tracking a shelter during simulation."""
    shelter_id: str
    name: str
    capacity: int           # simulated available capacity
    occupied: int = 0
    is_operational: bool = True


@dataclass
class EventTimeline:
    """Complete generated event with observable inputs and hidden truth."""
    config: ScenarioConfig
    # Observable: what the engine is allowed to see
    observable_records: list[SourceRecord] = field(default_factory=list)
    # Hidden truth: ground truth for evaluation (never fed to engine)
    ground_truth: list[dict[str, Any]] = field(default_factory=list)
    # Metadata
    total_steps: int = 0
    closures_generated: int = 0
    reports_generated: int = 0
    conflicts_generated: int = 0


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ez = math.exp(x)
    return ez / (1.0 + ez)


def _rain_at_hour(hour: int, config: ScenarioConfig) -> float:
    """Generate rainfall intensity at a given hour using a bell-curve profile."""
    buildup_end = config.buildup_hours
    sustain_end = buildup_end + config.sustain_hours
    decay_end = sustain_end + config.decay_hours
    peak = config.peak_rain_mm_h

    if hour < 0 or hour >= config.duration_hours:
        return 0.0
    if hour < buildup_end:
        # Smooth buildup (sine curve)
        progress = hour / max(buildup_end, 1)
        return peak * math.sin(progress * math.pi / 2) ** 2
    elif hour < sustain_end:
        # Sustain near peak with small fluctuation
        return peak * (0.85 + 0.15 * math.sin(hour * 0.7))
    elif hour < decay_end:
        # Smooth decay
        progress = (hour - sustain_end) / max(config.decay_hours, 1)
        return peak * math.cos(progress * math.pi / 2) ** 2
    else:
        # Tail drizzle
        return peak * 0.05 * max(0, 1 - (hour - decay_end) / 12)


def _compute_flood_prob(seg: SegmentState, rng: random.Random) -> float:
    """Compute flood probability from risk factors.

    Uses a logistic model on normalised, weighted risk factors.
    All factors are normalised to [0, 1] range before combining.
    """
    # Normalise factors
    rain_norm = min(seg.rain_accum_6h / 150.0, 1.0)        # 150mm/6h = saturated
    elev_norm = 1.0 - min(seg.elevation_m / 200.0, 1.0)    # lower = riskier
    river_norm = 1.0 - min(seg.distance_to_river_m / 10000.0, 1.0)  # closer = riskier
    slope_norm = 1.0 - min(seg.slope_degrees / 10.0, 1.0)  # flatter = riskier

    # Weighted combination
    raw = (W_RAIN_ACCUM * rain_norm +
           W_ELEVATION * elev_norm +
           W_RIVER_DIST * river_norm +
           W_SLOPE * slope_norm)

    # Add small random noise for realism
    noise = rng.gauss(0, 0.03)

    # Logistic scaling: maps [0,1] weighted sum to sharper [0,1] probability
    return _sigmoid((raw + noise - 0.4) * 8)


def load_graph(graph_path: Path) -> dict:
    """Load the processed road graph."""
    return json.loads(graph_path.read_text(encoding="utf-8"))


def load_settlements(settlements_path: Path) -> list[dict]:
    """Load processed settlements GeoJSON."""
    data = json.loads(settlements_path.read_text(encoding="utf-8"))
    return [f["properties"] | {"coordinates": f["geometry"]["coordinates"]}
            for f in data["features"]]


def load_shelters(shelters_path: Path) -> list[dict]:
    """Load processed shelters GeoJSON."""
    data = json.loads(shelters_path.read_text(encoding="utf-8"))
    return [f["properties"] | {"coordinates": f["geometry"]["coordinates"]}
            for f in data["features"]]


def _make_config_from_seed(seed: int, base_time: datetime) -> ScenarioConfig:
    """Generate a randomised but reproducible scenario config from a seed."""
    rng = random.Random(seed)
    peak = rng.uniform(*RAIN_INTENSITY_RANGE)
    buildup = rng.randint(*RAIN_BUILDUP_HOURS)
    sustain = rng.randint(*RAIN_SUSTAIN_HOURS)
    decay = rng.randint(*RAIN_DECAY_HOURS)
    duration = buildup + sustain + decay + rng.randint(6, 24)  # tail hours
    offset_hours = rng.randint(0, 48)  # stagger start times across events

    return ScenarioConfig(
        event_id=f"synth-{seed:04d}",
        seed=seed,
        start_time=base_time + timedelta(hours=offset_hours),
        duration_hours=min(duration, 120),  # cap at 5 days
        peak_rain_mm_h=round(peak, 1),
        buildup_hours=buildup,
        sustain_hours=sustain,
        decay_hours=decay,
        num_teams=rng.randint(2, 5),
        num_vehicles=rng.randint(2, 6),
        num_boats=rng.randint(1, 3),
        shelter_capacity_factor=round(rng.uniform(0.4, 0.9), 2),
    )


def generate_event(
    config: ScenarioConfig,
    edges: list[dict],
    settlements: list[dict],
    shelters: list[dict],
) -> EventTimeline:
    """Generate a complete synthetic flood event.

    Returns an EventTimeline with observable records (what the engine
    sees) and ground truth (for evaluation only).
    """
    rng = random.Random(config.seed)
    timeline = EventTimeline(config=config)

    # Initialise segment states
    seg_states: dict[str, SegmentState] = {}
    for edge in edges:
        seg_states[edge["id"]] = SegmentState(
            segment_id=edge["id"],
            elevation_m=edge.get("elevation_m", 100.0),
            slope_degrees=edge.get("slope_degrees", 1.0),
            distance_to_river_m=edge.get("distance_to_river_m", 5000.0),
            length_m=edge.get("length_m", 100.0),
            road_type=edge.get("road_type", "unclassified"),
        )

    # Initialise settlement states with simulated populations
    sett_states: dict[str, SettlementState] = {}
    for s in settlements:
        sett_states[s["id"]] = SettlementState(
            settlement_id=s["id"],
            name=s["name"],
            elevation_m=s.get("elevation_m", 100.0),
            distance_to_river_m=s.get("distance_to_river_m", 5000.0),
            graph_node_id=s.get("graph_node_id", ""),
            population_simulated=rng.randint(200, 5000),
        )

    # Initialise shelter states
    shel_states: dict[str, ShelterState] = {}
    for sh in shelters:
        published = sh.get("published_capacity", 30)
        shel_states[sh["id"]] = ShelterState(
            shelter_id=sh["id"],
            name=sh["name"],
            capacity=int(published * config.shelter_capacity_factor),
        )

    # Rain history for 6h accumulation
    rain_history: list[float] = []

    # Step through the event
    total_steps = config.duration_hours // config.step_hours
    for step_i in range(total_steps):
        hour = step_i * config.step_hours
        event_time = config.start_time + timedelta(hours=hour)

        # 1. Generate rainfall
        base_rain = _rain_at_hour(hour, config)
        # Spatial variation: each segment gets slightly different rain
        for seg_id, seg in seg_states.items():
            local_rain = base_rain * rng.uniform(0.7, 1.3)
            seg.rain_accum_6h = sum(rain_history[-5:]) + local_rain  # last 6 values

        rain_history.append(base_rain)

        # Emit weather observation (one per settlement grid cell)
        seen_grids: set[str] = set()
        for s in settlements:
            coords = s["coordinates"]
            grid_id = f"grid-{coords[1]:.2f}-{coords[0]:.2f}"
            if grid_id in seen_grids:
                continue
            seen_grids.add(grid_id)
            local_rain = base_rain * rng.uniform(0.8, 1.2)
            timeline.observable_records.append(SourceRecord(
                kind="weather",
                entity_id=grid_id,
                event_time=event_time,
                available_at=event_time,
                payload={
                    "precipitation_mm": round(local_rain, 2),
                    "interval_minutes": config.step_hours * 60,
                    "measurement": "simulated",
                    "settlement_ids": [ss['id'] for ss in settlements
                                       if f"grid-{ss['coordinates'][1]:.2f}-{ss['coordinates'][0]:.2f}" == grid_id],
                    "grid": [round(coords[1], 2), round(coords[0], 2)],
                },
                source="simulated",
                provider="scenario-generator",
            ))

        # 2. Compute flood probabilities and closures
        for seg_id, seg in seg_states.items():
            seg.flood_probability = _compute_flood_prob(seg, rng)

            # Ground truth: road actually becomes unusable
            if not seg.is_closed and seg.flood_probability > CLOSURE_PROB_THRESHOLD:
                if rng.random() < seg.flood_probability * 0.4:  # not every high-prob closes
                    seg.is_closed = True
                    seg.closed_at = event_time
                    seg.closure_source = "ground_truth"
                    timeline.closures_generated += 1

                    # Record ground truth (hidden from engine)
                    timeline.ground_truth.append({
                        "kind": "segment_status",
                        "segment_id": seg_id,
                        "status": "closed",
                        "at": event_time.isoformat(),
                        "flood_probability": round(seg.flood_probability, 4),
                        "rain_accum_6h": round(seg.rain_accum_6h, 2),
                    })

            # Recovery: some roads reopen after rain subsides
            elif seg.is_closed and seg.flood_probability < 0.2:
                if rng.random() < 0.15:  # slow recovery
                    seg.is_closed = False
                    seg.closed_at = None
                    timeline.ground_truth.append({
                        "kind": "segment_status",
                        "segment_id": seg_id,
                        "status": "open",
                        "at": event_time.isoformat(),
                        "flood_probability": round(seg.flood_probability, 4),
                    })

        # 3. Generate reports (observable by engine)
        for sett_id, sett in sett_states.items():
            if rng.random() > REPORT_PROB_PER_STEP:
                continue

            # Find nearest segments to this settlement
            nearest_seg_id = None
            for s in settlements:
                if s["id"] == sett_id:
                    nearest_seg_id = s.get("nearest_segment_id")
                    break

            if not nearest_seg_id or nearest_seg_id not in seg_states:
                continue

            seg = seg_states[nearest_seg_id]
            is_stale = rng.random() < STALE_REPORT_PROB
            is_conflicting = rng.random() < CONFLICTING_REPORT_PROB

            # Report content
            actual_closed = seg.is_closed
            reported_closed = actual_closed
            if is_conflicting:
                reported_closed = not actual_closed  # contradicts ground truth
                timeline.conflicts_generated += 1

            report_time = event_time
            if is_stale:
                # Report arrives 2-6 hours late
                report_time = event_time - timedelta(hours=rng.randint(2, 6))

            # Determine sender location (on-site, nearby, or remote)
            location_type = rng.choices(
                ["on_site", "nearby", "not_at_location"],
                weights=[0.6, 0.25, 0.15],
                k=1
            )[0]

            people_count = rng.randint(5, 200) if actual_closed else None

            timeline.observable_records.append(SourceRecord(
                kind="report",
                entity_id=f"report-{sett_id}-{step_i}-{rng.randint(0,9999)}",
                event_time=report_time,
                available_at=event_time,  # arrives at event_time regardless of staleness
                payload={
                    "raw_text": _generate_report_text(
                        sett.name, reported_closed, people_count, is_stale, rng),
                    "settlement_id": sett_id,
                    "road_id": nearest_seg_id,
                    "reported_status": "closed" if reported_closed else "open",
                    "people_count": people_count,
                    "transport": rng.choice(["internet", "esp_now"]),
                    "sender_location_type": location_type,
                    "sender_id": f"synthetic-{sett_id}-{step_i % 3}",
                },
                source="simulated",
                provider="scenario-generator",
            ))
            timeline.reports_generated += 1

        # 4. Generate resource strain events
        closed_count = sum(1 for s in seg_states.values() if s.is_closed)
        if closed_count > len(seg_states) * 0.1:  # >10% roads closed
            for sett_id, sett in sett_states.items():
                if not sett.needs_rescue and rng.random() < 0.05 * closed_count / len(seg_states):
                    sett.needs_rescue = True
                    sett.needs_rescue_since = event_time
                    timeline.observable_records.append(SourceRecord(
                        kind="resource_change",
                        entity_id=sett_id,
                        event_time=event_time,
                        available_at=event_time,
                        payload={
                            "change_type": "need_declared",
                            "settlement_name": sett.name,
                            "population_affected": sett.population_simulated,
                            "needs": ["rescue", "shelter", "supplies"],
                        },
                        source="simulated",
                        provider="scenario-generator",
                    ))

        # Shelter strain
        for sh_id, sh in shel_states.items():
            if sh.is_operational and rng.random() < 0.02 * closed_count / max(len(seg_states), 1):
                new_arrivals = rng.randint(5, 20)
                sh.occupied = min(sh.occupied + new_arrivals, sh.capacity + 10)  # allow overflow
                if sh.occupied > sh.capacity:
                    timeline.observable_records.append(SourceRecord(
                        kind="resource_change",
                        entity_id=sh_id,
                        event_time=event_time,
                        available_at=event_time,
                        payload={
                            "change_type": "shelter_overflow",
                            "shelter_name": sh.name,
                            "capacity": sh.capacity,
                            "occupied": sh.occupied,
                            "overflow": sh.occupied - sh.capacity,
                        },
                        source="simulated",
                        provider="scenario-generator",
                    ))

    # Record final ground truth snapshot
    timeline.ground_truth.append({
        "kind": "final_snapshot",
        "at": (config.start_time + timedelta(hours=config.duration_hours)).isoformat(),
        "segments_closed": sum(1 for s in seg_states.values() if s.is_closed),
        "segments_total": len(seg_states),
        "settlements_needing_rescue": sum(1 for s in sett_states.values() if s.needs_rescue),
        "shelters_over_capacity": sum(1 for s in shel_states.values() if s.occupied > s.capacity),
    })

    timeline.total_steps = total_steps
    return timeline


def _generate_report_text(
    settlement_name: str,
    is_closed: bool,
    people_count: int | None,
    is_stale: bool,
    rng: random.Random,
) -> str:
    """Generate realistic but synthetic report text."""
    templates_closed = [
        f"Road near {settlement_name} is flooded, cannot pass",
        f"Water on road at {settlement_name}, blocked for vehicles",
        f"Bridge near {settlement_name} submerged, road impassable",
        f"{settlement_name} road cut off by floodwater",
        f"Heavy flooding near {settlement_name}, road closed",
    ]
    templates_open = [
        f"Road near {settlement_name} is still passable",
        f"Water receding near {settlement_name}, road clearing",
        f"{settlement_name} road is open but muddy",
        f"Checked road at {settlement_name}, vehicles can pass",
    ]
    if is_closed:
        text = rng.choice(templates_closed)
        if people_count:
            text += f". About {people_count} people need help"
    else:
        text = rng.choice(templates_open)

    if is_stale:
        text += " (sent earlier, delayed)"

    return text


def generate_event_batch(
    edges: list[dict],
    settlements: list[dict],
    shelters: list[dict],
    num_events: int = DEFAULT_NUM_EVENTS,
    base_seed: int = 42,
    base_time: datetime | None = None,
) -> list[EventTimeline]:
    """Generate a batch of synthetic events for training/evaluation.

    Events are split by event ID:
      - First 60% → training
      - Next 15% → calibration
      - Last 25% → held-out evaluation
    """
    if base_time is None:
        base_time = datetime(2024, 6, 25, 0, tzinfo=timezone.utc)

    events = []
    for i in range(num_events):
        seed = base_seed + i
        config = _make_config_from_seed(seed, base_time)
        event = generate_event(config, edges, settlements, shelters)
        events.append(event)

    return events


def split_events(
    events: list[EventTimeline],
) -> dict[str, list[EventTimeline]]:
    """Split events into train/calibration/held-out sets by event ID.

    Never random — deterministic by event order (which is seed-based).
    """
    n = len(events)
    train_end = int(n * 0.6)
    cal_end = int(n * 0.75)
    return {
        "train": events[:train_end],
        "calibration": events[train_end:cal_end],
        "held_out": events[cal_end:],
    }


def save_events(
    events: list[EventTimeline],
    output_dir: Path,
    *,
    include_truth: bool = True,
) -> Path:
    """Serialise events to JSON files in the output directory.

    Observable records and ground truth are in separate files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generator_version": "phase2-v1",
        "num_events": len(events),
        "events": [],
    }

    for event in events:
        eid = event.config.event_id
        obs_file = output_dir / f"{eid}_observable.json"
        obs_data = {
            "event_id": eid,
            "seed": event.config.seed,
            "start_time": event.config.start_time.isoformat(),
            "duration_hours": event.config.duration_hours,
            "total_steps": event.total_steps,
            "closures_generated": event.closures_generated,
            "reports_generated": event.reports_generated,
            "conflicts_generated": event.conflicts_generated,
            "records": [
                {
                    "kind": r.kind,
                    "entity_id": r.entity_id,
                    "event_time": r.event_time.isoformat(),
                    "available_at": r.available_at.isoformat(),
                    "payload": r.payload,
                    "source": r.source,
                    "provider": r.provider,
                    "event_name": r.event_name,
                    "replayed_at": r.replayed_at.isoformat() if r.replayed_at else None,
                }
                for r in event.observable_records
            ],
        }
        obs_file.write_text(json.dumps(obs_data, indent=2), encoding="utf-8")

        if include_truth:
            truth_file = output_dir / f"{eid}_truth.json"
            truth_data = {
                "event_id": eid,
                "WARNING": "GROUND TRUTH — never feed to engine or feature builder",
                "ground_truth": event.ground_truth,
            }
            truth_file.write_text(json.dumps(truth_data, indent=2), encoding="utf-8")

        manifest["events"].append({
            "event_id": eid,
            "seed": event.config.seed,
            "start_time": event.config.start_time.isoformat(),
            "duration_hours": event.config.duration_hours,
            "total_steps": event.total_steps,
            "closures": event.closures_generated,
            "reports": event.reports_generated,
            "conflicts": event.conflicts_generated,
            "observable_file": obs_file.name,
            "truth_file": f"{eid}_truth.json" if include_truth else None,
        })

    manifest_file = output_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_file


class ScenarioAdapter(SourceAdapter):
    """Source adapter that plays back a generated EventTimeline.

    Each step() call yields the next batch of observable records
    for one time step.
    """

    def __init__(self, timeline: EventTimeline):
        self._timeline = timeline
        self._config = timeline.config
        self._clock = ScenarioClock(self._config.start_time)
        self._step_delta = timedelta(hours=self._config.step_hours)
        self._step_index = 0
        self._total_steps = timeline.total_steps
        # Group records by step
        self._records_by_step: list[list[SourceRecord]] = self._group_by_step()

    def _group_by_step(self) -> list[list[SourceRecord]]:
        """Group observable records into per-step buckets."""
        buckets: list[list[SourceRecord]] = [[] for _ in range(self._total_steps)]
        for rec in self._timeline.observable_records:
            step_offset = max(rec.event_time, rec.available_at) - self._config.start_time
            import math
            step_i = max(0, math.ceil(step_offset.total_seconds() / (self._config.step_hours * 3600)))
            if step_i < self._total_steps:
                buckets[step_i].append(rec)
        return buckets

    def mode(self) -> SourceMode:
        return SourceMode.SCENARIO

    def clock(self) -> Clock:
        return self._clock

    def step(self) -> Sequence[SourceRecord]:
        if self._step_index >= self._total_steps:
            return []
        records = self._records_by_step[self._step_index]
        self._clock = ScenarioClock(self._config.start_time + self._step_delta * self._step_index)
        self._step_index += 1
        return records

    def reset(self) -> None:
        self._step_index = 0
        self._clock = ScenarioClock(self._config.start_time)

    def is_exhausted(self) -> bool:
        return self._step_index >= self._total_steps

    def display_label(self) -> str:
        return (f"SIMULATION: {self._config.event_id}; "
                f"seed {self._config.seed}; not live")

    def current_time(self) -> datetime:
        return self._clock.now()
