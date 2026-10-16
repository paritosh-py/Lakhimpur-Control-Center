"""Evidence Card Generator (Phase 3).

Implements Requirement B4:
Every warning must include an Evidence Card containing:
- why: plain-language explanation of primary drivers
- confidence: high / medium / low
- confidence_reason: why the system has that confidence
- data_age_seconds: age of the newest input data
- lead_time_hours: estimated hours until onset/access loss
- uncertainty_disclosure: explicit distinction of modeled vs verified facts
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from engine.warnings.schemas import EvidenceCard, WarningFactors


def generate_why_explanation(
    entity_name: str,
    entity_type: str,
    factors: WarningFactors,
    score: float,
) -> str:
    """Generates plain-language 'Why' breakdown describing primary drivers."""
    if factors.is_confirmed_closed:
        return (
            f"Confirmed impassable. Physical road closure verified on {entity_name}. "
            f"Segment is impassable to all civilian and standard transport."
        )

    parts: list[str] = []

    # Rain component
    rain_desc: str | None = None
    if factors.recent_rain_1h_mm >= 25.0:
        rain_desc = f"Intense cloudburst rain of {factors.recent_rain_1h_mm:.1f} mm/h ({factors.recent_rain_3h_mm:.1f} mm / 3h)"
    elif factors.recent_rain_1h_mm >= 10.0:
        rain_desc = f"Heavy rainfall of {factors.recent_rain_1h_mm:.1f} mm/h ({factors.recent_rain_3h_mm:.1f} mm / 3h)"
    elif factors.recent_rain_3h_mm >= 15.0:
        rain_desc = f"Cumulative rainfall buildup of {factors.recent_rain_3h_mm:.1f} mm over 3h"
    elif factors.forecast_rain_3h_mm >= 15.0:
        rain_desc = f"Incoming forecast of {factors.forecast_rain_3h_mm:.1f} mm rain over next 3 hours"

    # Terrain vulnerability
    terrain_notes: list[str] = []
    if factors.distance_to_river_m < 500.0:
        terrain_notes.append(f"within {int(factors.distance_to_river_m)}m of active river channel")
    elif factors.distance_to_river_m < 1500.0:
        terrain_notes.append(f"{int(factors.distance_to_river_m)}m from river channel")

    if factors.elevation_m < 95.0:
        terrain_notes.append(f"low-lying basin (elevation {factors.elevation_m:.1f}m, slope {factors.slope_degrees:.1f}°)")
    elif factors.slope_degrees < 1.0:
        terrain_notes.append(f"flat alluvial terrain (slope {factors.slope_degrees:.1f}°)")

    if rain_desc:
        parts.append(rain_desc)
        if terrain_notes:
            parts.append(" on " + ", ".join(terrain_notes))
    elif terrain_notes:
        parts.append(f"Baseline conditions for {entity_name} across " + ", ".join(terrain_notes))
    else:
        parts.append(f"Normal baseline conditions for {entity_name} (elevation {factors.elevation_m:.1f}m, river dist {int(factors.distance_to_river_m)}m)")

    # Saturation
    if factors.ground_saturation_api_mm >= 60.0:
        parts.append(f". Soil saturation is high ({factors.ground_saturation_api_mm:.0f}mm API)")

    # Incident reports
    if factors.active_reports_count > 0:
        parts.append(f". Corroborated by {factors.active_reports_count} active field incident report(s)")

    return "".join(parts).strip()


def determine_confidence(
    factors: WarningFactors,
    source_mode: str,
) -> tuple[Literal["low", "medium", "high"], str]:
    """Evaluates confidence level and plain-language confidence reason."""
    if factors.is_confirmed_closed:
        return "high", "High: Confirmed road closure verified by official operational report."

    if factors.active_reports_count >= 2 and factors.recent_rain_1h_mm > 10.0:
        return (
            "high",
            f"High: Corroborated by {factors.active_reports_count} local incident reports "
            f"and matching atmospheric rainfall observations."
        )

    if factors.active_reports_count == 1:
        return (
            "medium",
            "Medium: Model atmospheric rain matches 1 citizen field report; additional ground verification pending."
        )

    if source_mode == "replay":
        return (
            "high",
            "High: Historical reanalysis (ERA5) with calibrated local Copernicus 90m DSM terrain."
        )

    if factors.recent_rain_1h_mm > 0.0 or factors.ground_saturation_api_mm > 20.0:
        return (
            "medium",
            "Medium: Derived from atmospheric model forecast and 90m DSM terrain; physical road passability unverified by ground scouts."
        )

    return (
        "low",
        "Low: Quiescent conditions; based on default terrain attributes with no active precipitation."
    )


def estimate_lead_time_hours(factors: WarningFactors, score: float) -> float | None:
    """Estimates time in hours before physical access failure."""
    if factors.is_confirmed_closed:
        return 0.0

    if score < 25.0:
        return None

    if factors.recent_rain_1h_mm >= 25.0 and factors.distance_to_river_m < 500.0:
        return 0.5  # Rapid flash inundation within 30 mins
    elif factors.recent_rain_1h_mm >= 15.0 or factors.distance_to_river_m < 1000.0:
        return 1.5
    elif factors.forecast_rain_3h_mm >= 15.0:
        return 2.5
    else:
        return 4.0


def build_evidence_card(
    entity_id: str,
    entity_type: Literal["settlement", "road_segment"],
    entity_name: str,
    risk_score: float,
    severity: Literal["advisory", "moderate", "high", "critical"],
    factors: WarningFactors,
    source_mode: Literal["live", "replay", "simulated"],
    newest_observation_time: datetime,
    current_decision_time: datetime,
) -> EvidenceCard:
    """Builds a complete Evidence Card conforming to Requirement B4."""
    why = generate_why_explanation(entity_name, entity_type, factors, risk_score)
    confidence, confidence_reason = determine_confidence(factors, source_mode)
    lead_time = estimate_lead_time_hours(factors, risk_score)

    # Compute data age
    if current_decision_time >= newest_observation_time:
        age_seconds = (current_decision_time - newest_observation_time).total_seconds()
    else:
        age_seconds = 0.0

    uncertainty_disclosure = (
        "Copernicus DSM terrain elevation and OpenStreetMap river geometries are verified spatial baselines. "
        "Rainfall values reflect numerical atmospheric model data. Last-mile ditch capacity and culvert "
        "blockages are unmeasured and may alter local water accumulation."
    )

    return EvidenceCard(
        entity_id=entity_id,
        entity_type=entity_type,
        entity_name=entity_name,
        risk_score=risk_score,
        severity=severity,
        why=why,
        confidence=confidence,
        confidence_reason=confidence_reason,
        data_age_seconds=max(0.0, age_seconds),
        lead_time_hours=lead_time,
        uncertainty_disclosure=uncertainty_disclosure,
        factors=factors,
        source_mode=source_mode,
        generated_at=current_decision_time,
    )
