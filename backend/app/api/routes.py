"""API router for model-driven arrival-time routing and Google Maps style navigation."""
import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from engine.routing.route_planner import RoutePlanner
from backend.app.api.road_predictions import fetch_snapshot

router = APIRouter(prefix="/api/routes", tags=["Routing and Navigation"])

_planner_instance: RoutePlanner | None = None


def get_planner() -> RoutePlanner:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = RoutePlanner()
    return _planner_instance


_predictions_cache: dict[str, Any] = {"time": 0.0, "data": {}}


async def get_model_predictions_by_eta() -> dict[int, dict[str, dict[str, Any]]]:
    """Attempts to fetch model predictions for ETA horizons (30, 60, 120) concurrently with in-memory TTL caching."""
    import time
    now = time.time()
    # Cache predictions for 45 seconds since they are from a saved weather snapshot
    if _predictions_cache["time"] and (now - _predictions_cache["time"] < 45.0) and _predictions_cache["data"]:
        return _predictions_cache["data"]

    preds_by_eta: dict[int, dict[str, dict[str, Any]]] = {}

    async def fetch_one(eta: int):
        try:
            snapshot = await asyncio.wait_for(fetch_snapshot(eta), timeout=3.5)
            preds_by_eta[eta] = {p.road_id: p.model_dump() for p in snapshot.predictions}
        except Exception:
            # Model service unavailable or timeout; fallback gracefully
            preds_by_eta[eta] = {}

    await asyncio.gather(fetch_one(30), fetch_one(60), fetch_one(120), return_exceptions=True)
    if any(len(v) > 0 for v in preds_by_eta.values()):
        _predictions_cache["time"] = now
        _predictions_cache["data"] = preds_by_eta
    return preds_by_eta


@router.get("/plan")
async def plan_route(
    settlement_id: str = Query(..., description="Target settlement ID"),
    team_id: str | None = Query(None, description="Optional team ID"),
    request: Request = None,
):
    planner = get_planner()
    try:
        preds = await get_model_predictions_by_eta()
        model_available = any(len(v) > 0 for v in preds.values())
        
        plan = planner.plan_mission(
            settlement_id=settlement_id,
            predictions_by_eta=preds if model_available else None,
            confirmed_closures=None,
        )
        plan["model_status"] = "connected" if model_available else "offline_fallback"
        return plan
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail=f"Routing calculation failed: {exc}") from exc


@router.get("/active")
async def active_mission(request: Request, context: str = "live"):
    """Returns the mission route for the active assignment, allowing single-phone operation without tokens."""
    planner = get_planner()
    team_store = request.app.state.teams
    state = team_store.list(context)

    # Find active assignment if present
    active_tasks = [t for t in state["assignments"] if t["status"] not in ("completed", "cancelled")]
    task = None
    team = None
    if active_tasks:
        task = active_tasks[0]
        team = next((t for t in state["teams"] if t["id"] == task["team_id"]), None)
        target_settlement_id = task["settlement_id"]
    else:
        # Default to first study settlement so route, map, and navigation are immediately live
        target_settlement_id = planner.settlements_data["features"][0]["properties"]["id"]

    preds = await get_model_predictions_by_eta()
    model_available = any(len(v) > 0 for v in preds.values())

    plan = planner.plan_mission(
        settlement_id=target_settlement_id,
        predictions_by_eta=preds if model_available else None,
    )
    plan["has_active_assignment"] = bool(task)
    plan["active_task"] = task
    plan["assigned_team"] = team
    plan["model_status"] = "connected" if model_available else "offline_fallback"
    plan["settlements"] = [
        {"id": f["properties"]["id"], "name": f["properties"]["name"]}
        for f in planner.settlements_data["features"]
    ]
    return plan

