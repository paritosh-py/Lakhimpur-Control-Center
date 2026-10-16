"""Read-only Phase 1 datasets. Missing data is an explicit 503."""
import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException

from engine.config import ROOT, load_district

router = APIRouter(prefix="/api")
PROCESSED = ROOT / "data/processed"


def load_dataset(filename: str, directory: Path = PROCESSED):
    try:
        return json.loads((directory / filename).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(503, detail=f"Dataset {filename} has not been acquired and built")
    except (ValueError, OSError):
        raise HTTPException(503, detail=f"Dataset {filename} is unreadable; rebuild and validate it")


@router.get("/geography/basecamp")
def get_basecamp():
    dist = load_district()
    if not dist.basecamp:
        raise HTTPException(404, detail="Basecamp not configured")
    return dist.basecamp.model_dump()


@router.get("/geography/summary")
def summary():
    data = load_dataset("geography_summary.json")
    dist = load_district()
    if dist.basecamp:
        data["basecamp"] = dist.basecamp.model_dump()
    return data



@router.get("/geography/{layer}")
def geography(layer: Literal["boundary", "roads", "settlements", "shelters", "waterways"]):
    return load_dataset(layer + ".geojson")


@router.get("/sources")
def sources():
    return load_dataset("source_manifest.json")


@router.get("/weather/{mode}")
def weather(mode: Literal["live", "historical"]):
    return load_dataset("weather_live.json" if mode == "live" else "weather_reanalysis_2024.json")


@router.get("/weather/{mode}/settlements")
def settlement_weather(mode: Literal["live", "historical"]):
    return load_dataset(f"weather_settlements_{mode}.json")
