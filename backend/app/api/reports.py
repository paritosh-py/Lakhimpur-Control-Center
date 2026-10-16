"""API routes for citizen ground reports, Gemini AI prioritization, and device repetition tracking."""
import math
from typing import Literal
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/reports", tags=["citizen reports"])

IncidentType = Literal[
    "rescue_sos",
    "road_closure",
    "flood_rising",
    "medical",
    "hazard",
    "general",
    "other",
]


class ReportInput(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    # Identifiers
    message_id: str | None = None
    device_id: str | None = Field(default="DEV-ANONYMOUS", max_length=100)
    sender_name: str | None = Field(default=None, max_length=100)
    sender_phone: str | None = Field(default=None, max_length=30)

    # Incident Details
    incident_type: str = "general"
    settlement_id: str | None = None
    settlement_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Quantitative & Observation fields
    people_affected: int = Field(default=1, ge=0, le=50000)
    severity_level: str | None = None
    water_depth_cm: float | None = Field(default=None, ge=0, le=5000)
    water_trend: Literal["rising", "falling", "stable", "unknown"] | None = "unknown"
    road_status: Literal["blocked", "partially_blocked", "open", "unknown"] | None = "unknown"

    # Descriptions & Conditions
    description: str = Field(default="", max_length=2000)
    conditions: list[str] = Field(default_factory=list)
    timestamp: str | None = None

    @classmethod
    def model_validate_json_or_dict(cls, data: dict):
        # Handle field aliases and AeroLink legacy keys
        if isinstance(data, dict):
            if "additionalDetails" in data and not data.get("description"):
                data["description"] = data["additionalDetails"]
            if "peopleAffected" in data and "people_affected" not in data:
                data["people_affected"] = data["peopleAffected"]
            if "deviceId" in data and "device_id" not in data:
                data["device_id"] = data["deviceId"]
            if "type" in data and ("incident_type" not in data or data.get("incident_type") == "general"):
                val = str(data["type"]).lower()
                data["incident_type"] = "rescue_sos" if val == "sos" else val
            if "roadStatus" in data and "road_status" not in data:
                data["road_status"] = data["roadStatus"]
            if "waterDepthCm" in data and "water_depth_cm" not in data:
                data["water_depth_cm"] = data["waterDepthCm"]
            if "waterTrend" in data and "water_trend" not in data:
                data["water_trend"] = data["waterTrend"]
        return data

    from pydantic import model_validator

    @model_validator(mode="before")
    @classmethod
    def remap_legacy_and_camelcase(cls, data):
        if isinstance(data, dict):
            if "additionalDetails" in data and not data.get("description"):
                data["description"] = data["additionalDetails"]
            if "peopleAffected" in data and "people_affected" not in data:
                data["people_affected"] = data["peopleAffected"]
            if "deviceId" in data and "device_id" not in data:
                data["device_id"] = data["deviceId"]
            if "senderName" in data and "sender_name" not in data:
                data["sender_name"] = data["senderName"]
            if "senderPhone" in data and "sender_phone" not in data:
                data["sender_phone"] = data["senderPhone"]
            if "incidentType" in data and ("incident_type" not in data or data.get("incident_type") == "general"):
                data["incident_type"] = data["incidentType"]
            if "settlementId" in data and "settlement_id" not in data:
                data["settlement_id"] = data["settlementId"]
            if "settlementName" in data and "settlement_name" not in data:
                data["settlement_name"] = data["settlementName"]
            if "type" in data and ("incident_type" not in data or data.get("incident_type") == "general"):
                val = str(data["type"]).lower()
                data["incident_type"] = "rescue_sos" if val == "sos" else val
            if "roadStatus" in data and "road_status" not in data:
                data["road_status"] = data["roadStatus"]
            if "waterDepthCm" in data and "water_depth_cm" not in data:
                data["water_depth_cm"] = data["waterDepthCm"]
            if "waterTrend" in data and "water_trend" not in data:
                data["water_trend"] = data["waterTrend"]
        return data


class StatusUpdateInput(BaseModel):
    status: Literal["new", "verified", "actioned", "dismissed", "closed", "resolved"]
    note: str = Field(default="", max_length=500)


import json
from engine.config import ROOT


def _snap_nearest_settlement(request: Request, lat: float | None, lon: float | None) -> tuple[str | None, str | None]:
    """Snap coordinates to closest study settlement in Lakhimpur."""
    if lat is None or lon is None:
        return None, None
    try:
        geo_path = ROOT / "data/processed/settlements.geojson"
        if not geo_path.exists():
            return None, None
        data = json.loads(geo_path.read_text(encoding="utf-8"))
        features = data.get("features", [])
        best_id = None
        best_name = None
        min_dist = float("inf")
        for f in features:
            coords = f.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                s_lon, s_lat = coords[0], coords[1]
                dist = math.hypot(lat - s_lat, lon - s_lon)
                if dist < min_dist:
                    min_dist = dist
                    best_id = f.get("properties", {}).get("id")
                    best_name = f.get("properties", {}).get("name")
        return best_id, best_name
    except Exception:
        return None, None


@router.post("")
async def submit_report(payload: ReportInput, request: Request, context: str = "live"):
    """Ingest a citizen report, evaluate with Gemini AI, detect repeat device, and persist."""
    data = payload.model_dump()
    device_id = data.get("device_id") or "DEV-ANONYMOUS"

    # Location snapping if settlement_id is absent
    if not data.get("settlement_id") and data.get("latitude") and data.get("longitude"):
        s_id, s_name = _snap_nearest_settlement(request, data["latitude"], data["longitude"])
        if s_id:
            data["settlement_id"] = s_id
            if not data.get("settlement_name"):
                data["settlement_name"] = s_name

    # Validate against existing settlement if provided
    if data.get("settlement_id"):
        geo_path = ROOT / "data/processed/settlements.geojson"
        if geo_path.exists():
            try:
                features = json.loads(geo_path.read_text(encoding="utf-8")).get("features", [])
                for f in features:
                    if f.get("properties", {}).get("id") == data["settlement_id"]:
                        data["settlement_name"] = f.get("properties", {}).get("name")
                        coords = f.get("geometry", {}).get("coordinates", [])
                        if len(coords) >= 2:
                            if not data.get("longitude"):
                                data["longitude"] = coords[0]
                            if not data.get("latitude"):
                                data["latitude"] = coords[1]
                        break
            except Exception:
                pass

    store = request.app.state.reports
    prior_count = store.count_prior_device_reports(context, device_id)

    # Gemini AI Triage
    triage_service = getattr(request.app.state, "triage", None)
    if triage_service:
        triage_result = await triage_service.triage_report(data, prior_count=prior_count)
    else:
        from backend.app.services.reports import GeminiTriageService
        triage_result = GeminiTriageService().fallback_triage(data, prior_count=prior_count)

    # Save to SQLite
    saved = store.save_report(data, triage_result, context=context)
    return saved


@router.get("")
def list_reports(request: Request, context: str = "live"):
    """List all reports for the given context, with repeat-device annotations."""
    store = request.app.state.reports
    reports = store.list_reports(context=context)
    return {
        "context": context,
        "count": len(reports),
        "reports": reports,
    }


@router.get("/stats")
def report_stats(request: Request, context: str = "live"):
    """Return summary statistics of citizen reports."""
    store = request.app.state.reports
    return store.stats(context=context)


@router.get("/devices/{device_id}")
def get_device_history(device_id: str, request: Request, context: str = "live"):
    """Return all historical reports from a given device."""
    store = request.app.state.reports
    history = store.get_device_history(device_id, context=context)
    return {
        "device_id": device_id,
        "context": context,
        "count": len(history),
        "reports": history,
    }


@router.get("/{report_id}")
def get_single_report(report_id: str, request: Request, context: str = "live"):
    """Fetch status and details of a single report by report ID or message ID."""
    store = request.app.state.reports
    report = store.get_report(report_id, context=context)
    if not report:
        with store.transaction() as db:
            row = db.execute(
                "SELECT id FROM citizen_reports WHERE (message_id = ? OR id = ?) AND context = ?",
                (report_id, report_id, context),
            ).fetchone()
            if row:
                report = store.get_report(row["id"], context=context)
    if not report:
        raise HTTPException(404, "Report not found in this context")
    return report


@router.post("/{report_id}/status")
def update_report_status(report_id: str, payload: StatusUpdateInput, request: Request, context: str = "live"):
    """Update operator status of a report."""
    store = request.app.state.reports
    updated = store.update_status(report_id, payload.status, payload.note, context=context)
    if not updated:
        raise HTTPException(404, "Report not found in this context")
    return updated

