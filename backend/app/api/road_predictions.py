"""Read-only adapter for the teammate's saved-weather model. Never changes road status."""
import os
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from engine.clock import LiveClock
from backend.app.api.geography import load_dataset

router = APIRouter(prefix="/api/ml", tags=["Team road estimates"])


class Prediction(BaseModel):
    model_config = ConfigDict(strict=True)
    road_id: str = Field(min_length=1, max_length=200)
    probability_unusable: float = Field(ge=0, le=1, allow_inf_nan=False)
    risk_level: Literal["LOW", "MODERATE", "HIGH"]
    road_status: str = Field(min_length=1, max_length=100)
    data_quality_status: str = Field(min_length=1, max_length=100)


class Snapshot(BaseModel):
    model_config = ConfigDict(strict=True)
    model_version: Literal["lightgbm_v2_candidate"]
    mode: Literal["snapshot_demo"]
    eta_minutes: Literal[30, 60, 120]
    road_count: int = Field(ge=0, le=10000)
    predictions: list[Prediction] = Field(max_length=10000)

    @model_validator(mode="after")
    def consistent(self):
        ids = [p.road_id for p in self.predictions]
        if len(ids) != self.road_count or len(set(ids)) != len(ids):
            raise ValueError("Invalid road count or duplicate road IDs")
        for p in self.predictions:
            expected = "HIGH" if p.probability_unusable >= .7 else "MODERATE" if p.probability_unusable >= .4 else "LOW"
            if p.risk_level != expected:
                raise ValueError("Risk band differs from the agreed display thresholds")
        return self


async def fetch_snapshot(eta: int) -> Snapshot:
    base = os.environ.get("ROAD_MODEL_BASE_URL", "http://10.10.0.169:8002").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=4), trust_env=False) as client:
            result = await client.get(base + "/ml/roads/simple", params={"eta": eta})
            result.raise_for_status()
            snapshot = Snapshot.model_validate(result.json())
        if snapshot.eta_minutes != eta:
            raise ValueError("Upstream ETA mismatch")
        return snapshot
    except httpx.RequestError as exc:
        raise HTTPException(503, "Road model unavailable. Check the model laptop and Wi-Fi, then retry.") from exc
    except (httpx.HTTPStatusError, ValidationError, ValueError) as exc:
        raise HTTPException(502, "Road model returned an invalid response. No estimates have been substituted.") from exc


@router.get("/roads")
async def road_predictions(response: Response, eta: int = 60):
    if eta not in (30, 60, 120):
        raise HTTPException(422, "ETA must be 30, 60 or 120 minutes")
    snapshot = await fetch_snapshot(eta)
    roads = load_dataset("roads.geojson")["features"]
    predictions = {p.road_id: p for p in snapshot.predictions}
    ids = {r["properties"]["id"] for r in roads}
    joined = []
    for feature in roads:
        props = feature["properties"]
        prediction = predictions.get(props["id"])
        joined.append({
            "road_id": props["id"], "name": props.get("name") or "Unnamed road",
            "road_type": props.get("road_type"), "length_m": props.get("length_m"),
            "recorded_road_status": props.get("status") or "unknown",
            "prediction": prediction.model_dump() if prediction else None,
        })
    response.headers["Cache-Control"] = "no-store"
    return {
        "model_version": snapshot.model_version, "mode": snapshot.mode,
        "eta_minutes": snapshot.eta_minutes, "source": "simulated",
        "fetched_at": LiveClock().now(), "weather_metadata_source": "model_owner_supplied",
        "weather_retrieved_at": os.environ.get("ROAD_MODEL_WEATHER_RETRIEVED_AT", "2026-10-10T10:27:51.083909Z"),
        "rainfall_completion_example": "2026-10-10T10:00:00Z",
        "road_count": len(joined), "prediction_count": snapshot.road_count,
        "matched_count": len(ids & predictions.keys()), "unmatched_prediction_count": len(predictions.keys() - ids),
        "roads": joined,
    }
