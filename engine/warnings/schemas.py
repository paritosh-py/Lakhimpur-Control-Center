"""Schemas for the Explainable Warning Engine & Evidence Cards (Phase 3).

Satisfies Requirements B2, B3, and B4:
- B2: Multi-factor flood risk score per settlement and road segment.
- B3: Changing input re-ranks settlements with plain-language reason.
- B4: Every warning includes an Evidence Card (why, confidence + reason, data age).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class WarningFactors(BaseModel):
    """Detailed numeric breakdown of all contributing physical factors."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    recent_rain_1h_mm: float = Field(ge=0.0, description="1-hour precipitation in mm")
    recent_rain_3h_mm: float = Field(ge=0.0, description="3-hour cumulative precipitation in mm")
    recent_rain_6h_mm: float = Field(ge=0.0, description="6-hour cumulative precipitation in mm")
    forecast_rain_3h_mm: float = Field(ge=0.0, description="Upcoming 3-hour forecast precipitation in mm")
    ground_saturation_api_mm: float = Field(ge=0.0, description="Antecedent Precipitation Index saturation in mm")
    elevation_m: float = Field(description="Surface elevation above sea level in meters (Copernicus DSM)")
    slope_degrees: float = Field(ge=0.0, description="Local terrain surface slope in degrees")
    distance_to_river_m: float = Field(ge=0.0, description="Distance to nearest mapped river channel in meters")
    active_reports_count: int = Field(ge=0, description="Number of field incident reports in vicinity")
    is_confirmed_closed: bool = Field(default=False, description="Whether entity or access road is confirmed closed")


class EvidenceCard(BaseModel):
    """Explainable evidence card required by Requirement B4 for every warning."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1, description="Unique ID of settlement or road segment")
    entity_type: Literal["settlement", "road_segment"]
    entity_name: str = Field(min_length=1, description="Human readable name")
    risk_score: float = Field(ge=0.0, le=100.0, description="Normalized risk score from 0 to 100")
    severity: Literal["advisory", "moderate", "high", "critical"]
    why: str = Field(min_length=5, description="Plain-language explanation of primary risk drivers")
    confidence: Literal["low", "medium", "high"] = Field(description="Confidence rating in alert")
    confidence_reason: str = Field(min_length=5, description="Transparent explanation for confidence score")
    data_age_seconds: float = Field(ge=0.0, description="Seconds since newest contributing observation was issued")
    lead_time_hours: float | None = Field(default=None, ge=0.0, description="Estimated hours before impact onset")
    uncertainty_disclosure: str = Field(min_length=5, description="Explicit disclosure of modeled vs verified facts")
    factors: WarningFactors
    source_mode: Literal["live", "replay", "simulated", "scenario"]
    generated_at: AwareDatetime
    rank: int | None = Field(default=None, description="Current rank order")
    rank_delta: int | None = Field(default=None, description="Change in rank")
    rerank_reason: str | None = Field(default=None, description="Plain-language reason for rank shift")


class RankedWarning(BaseModel):
    """Summary record for list displays and re-ranking tables (Requirement B3)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    rank: int = Field(ge=1, description="Current rank order (1 = highest risk)")
    entity_id: str
    entity_type: Literal["settlement", "road_segment"]
    entity_name: str
    risk_score: float = Field(ge=0.0, le=100.0)
    severity: Literal["advisory", "moderate", "high", "critical"]
    primary_driver: str = Field(description="Short summary of top contributing factor")
    previous_rank: int | None = Field(default=None, description="Rank in previous evaluation step")
    rank_delta: int = Field(default=0, description="Change in rank (+2 means moved up 2 spots in risk)")
    rerank_reason: str | None = Field(default=None, description="Plain-language reason for rank shift")


class WarningSummaryResponse(BaseModel):
    """District-wide aggregated warning overview."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str | None
    source_mode: Literal["live", "replay", "simulated", "scenario"]
    evaluated_at: AwareDatetime
    total_settlements_evaluated: int
    total_roads_evaluated: int
    severity_counts: dict[str, int]
    highest_risk_settlement: RankedWarning | None
    highest_risk_road: RankedWarning | None
    active_warnings: list[RankedWarning]
