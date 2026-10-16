"""Scenario API endpoints (Phase 2, Task 6).

Provides start/step/reset controls for live, replay, and scenario
modes.  All modes feed the same engine contract via SourceAdapter.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from threading import RLock
from functools import wraps

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from engine.config import ROOT
from engine.ingest.run import RunState
from engine.ingest.source import (
    LiveWeatherAdapter,
    ReplayWeatherAdapter,
    SourceRecord,
)
from data.generators.flood_scenario import (
    ScenarioAdapter,
    ScenarioConfig,
    generate_event,
    load_graph,
    load_settlements,
    load_shelters,
)

router = APIRouter(prefix="/api/scenario")

# Shared run state — in-memory, reset on server restart
_run_state = RunState()
_run_lock = RLock()


def run_locked(fn):
    @wraps(fn)
    def locked(*args, **kwargs):
        with _run_lock:
            return fn(*args, **kwargs)
    return locked


def get_shared_run_state() -> RunState:
    """Returns the active shared run state."""
    return _run_state


PROCESSED = ROOT / "data" / "processed"


class StartRequest(BaseModel):
    mode: Literal["live", "replay", "scenario"]
    seed: int | None = Field(default=42, description="Seed for scenario mode")
    duration_hours: int = Field(default=72, ge=6, le=120)
    peak_rain_mm_h: float = Field(default=25.0, ge=1.0, le=60.0)


class StepResponse(BaseModel):
    run_id: str
    step_index: int
    current_time: str
    num_records: int
    record_kinds: dict[str, int]
    is_exhausted: bool
    display_label: str
    records: list[dict]


def _load_json(filename: str) -> dict:
    path = PROCESSED / filename
    if not path.exists():
        raise HTTPException(503, detail=f"Dataset {filename} not built yet")
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/start")
@run_locked
def start_scenario(req: StartRequest):
    """Start a new source run (live, replay, or scenario)."""
    try:
        if req.mode == "live":
            raise HTTPException(409, detail="Live monitoring is automatic at /api/live/conditions; it cannot be started as a playback run.")

        elif req.mode == "replay":
            weather = _load_json("weather_settlements_historical.json")
            adapter = ReplayWeatherAdapter(
                weather,
                event_name="Assam flood context, June–July 2024",
                start=datetime(2024, 6, 25, 0, tzinfo=timezone.utc),
            )

        elif req.mode == "scenario":
            graph = load_graph(PROCESSED / "graph.json")
            settlements = load_settlements(PROCESSED / "settlements.geojson")
            shelters = load_shelters(PROCESSED / "shelters.geojson")

            config = ScenarioConfig(
                event_id=f"demo-{req.seed}",
                seed=req.seed or 42,
                start_time=datetime(2024, 6, 25, 0, tzinfo=timezone.utc),
                duration_hours=req.duration_hours,
                peak_rain_mm_h=req.peak_rain_mm_h,
            )
            timeline = generate_event(config, graph["edges"], settlements, shelters)
            adapter = ScenarioAdapter(timeline)

        else:
            raise HTTPException(400, detail=f"Unknown mode: {req.mode}")

        run_id = _run_state.start(adapter)
        return {
            "run_id": run_id,
            "mode": req.mode,
            "display_label": _run_state.display_label,
            "status": _run_state.status(),
        }

    except FileNotFoundError as e:
        raise HTTPException(503, detail=f"Required dataset not found: {e}")


@router.post("/step")
@run_locked
def step_scenario():
    """Advance the current run by one time step."""
    if _run_state.mode and _run_state.mode.value == "live":
        raise HTTPException(409, detail="Live monitoring cannot be stepped through time.")
    if not _run_state.is_active:
        raise HTTPException(400, detail="No active run — call /start first")
    if _run_state.is_exhausted:
        raise HTTPException(400, detail="Source is exhausted — /reset or /start a new run")

    result = _run_state.step()

    # Count record types
    kinds: dict[str, int] = {}
    record_dicts = []
    for r in result.records:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1
        record_dicts.append({
            "kind": r.kind,
            "entity_id": r.entity_id,
            "event_time": r.event_time.isoformat(),
            "available_at": r.available_at.isoformat(),
            "source": r.source,
            "provider": r.provider,
            "event_name": r.event_name,
            "replayed_at": r.replayed_at.isoformat() if r.replayed_at else None,
            "payload": r.payload,
        })

    return StepResponse(
        run_id=result.run_id,
        step_index=result.step_index,
        current_time=result.current_time.isoformat(),
        num_records=len(result.records),
        record_kinds=kinds,
        is_exhausted=result.is_exhausted,
        display_label=result.display_label,
        records=record_dicts,
    )


@router.post("/reset")
@run_locked
def reset_scenario():
    """Reset the current run to the beginning."""
    if _run_state.mode and _run_state.mode.value == "live":
        raise HTTPException(409, detail="Live monitoring has no playback reset.")
    if not _run_state.is_active:
        raise HTTPException(400, detail="No active run — call /start first")
    new_run_id = _run_state.reset()
    return {
        "run_id": new_run_id,
        "message": "Run reset to step 0",
        "status": _run_state.status(),
    }


@router.post("/stop")
@run_locked
def stop_scenario():
    """Stop the current run and return to idle."""
    _run_state.stop()
    return {"message": "Run stopped", "status": _run_state.status()}


@router.get("/status")
@run_locked
def scenario_status():
    """Get the current run state."""
    return _run_state.status()


@router.get('/snapshot')
@run_locked
def scenario_snapshot(request: Request):
    if not _run_state.is_active:
        raise HTTPException(409, 'Choose a historical replay or synthetic exercise first.')
    return request.app.state.assessments.replay(_run_state)
