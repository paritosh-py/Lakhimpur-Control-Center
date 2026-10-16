"""Unit tests for Evidence Card generator conforming to Requirement B4."""
from datetime import datetime, timezone

import pytest

from engine.warnings.evidence import build_evidence_card
from engine.warnings.schemas import WarningFactors
from engine.warnings.scorer import compute_risk_score


def test_evidence_card_complete_fields():
    """Requirement B4: Every warning must contain why, confidence, age, lead time, and disclosures."""
    now = datetime.now(timezone.utc)
    factors = WarningFactors(
        recent_rain_1h_mm=28.5,
        recent_rain_3h_mm=48.0,
        recent_rain_6h_mm=72.0,
        forecast_rain_3h_mm=20.0,
        ground_saturation_api_mm=75.0,
        elevation_m=92.5,
        slope_degrees=0.7,
        distance_to_river_m=280.0,
        active_reports_count=2,
        is_confirmed_closed=False,
    )
    score, severity = compute_risk_score(factors)

    card = build_evidence_card(
        entity_id="geonames-12523887",
        entity_type="settlement",
        entity_name="Kadam",
        risk_score=score,
        severity=severity,
        factors=factors,
        source_mode="simulated",
        newest_observation_time=now,
        current_decision_time=now,
    )

    # Verify all Requirement B4 fields exist and are non-empty
    assert card.entity_id == "geonames-12523887"
    assert card.entity_name == "Kadam"
    assert card.risk_score == score
    assert len(card.why) > 10
    assert "28.5 mm/h" in card.why or "rain" in card.why.lower()
    assert card.confidence in ("low", "medium", "high")
    assert len(card.confidence_reason) > 5
    assert card.data_age_seconds >= 0.0
    assert card.lead_time_hours is not None
    assert "Copernicus" in card.uncertainty_disclosure
    assert card.source_mode == "simulated"


def test_evidence_card_confirmed_closure_high_confidence():
    """Confirmed closures must produce high confidence and 0.0h lead time."""
    now = datetime.now(timezone.utc)
    factors = WarningFactors(
        recent_rain_1h_mm=0.0,
        recent_rain_3h_mm=0.0,
        recent_rain_6h_mm=0.0,
        forecast_rain_3h_mm=0.0,
        ground_saturation_api_mm=0.0,
        elevation_m=98.0,
        slope_degrees=1.0,
        distance_to_river_m=1200.0,
        active_reports_count=1,
        is_confirmed_closed=True,
    )

    card = build_evidence_card(
        entity_id="osm-1092487157-27-28",
        entity_type="road_segment",
        entity_name="NT Road",
        risk_score=100.0,
        severity="critical",
        factors=factors,
        source_mode="live",
        newest_observation_time=now,
        current_decision_time=now,
    )

    assert card.risk_score == 100.0
    assert card.severity == "critical"
    assert card.confidence == "high"
    assert card.lead_time_hours == 0.0
    assert "Confirmed impassable" in card.why
