"""Unit tests for the multi-factor risk scoring engine (Phase 3)."""
import pytest

from engine.warnings.schemas import WarningFactors
from engine.warnings.scorer import (
    calculate_rain_score,
    calculate_saturation_score,
    calculate_terrain_vulnerability,
    compute_risk_score,
)


def test_rain_score_monotonicity_and_bounds():
    """Verify rain score increases with rainfall and stays in [0.0, 1.0]."""
    score_zero = calculate_rain_score(0.0, 0.0, 0.0, 0.0)
    assert score_zero == 0.0

    score_light = calculate_rain_score(2.0, 5.0, 8.0, 2.0)
    score_moderate = calculate_rain_score(15.0, 30.0, 45.0, 10.0)
    score_severe = calculate_rain_score(35.0, 60.0, 100.0, 40.0)

    assert 0.0 < score_light < score_moderate < score_severe <= 1.0


def test_terrain_vulnerability_physics():
    """Verify low-lying, flat terrain near river has higher vulnerability."""
    # Riverbank low basin: elevation 85m, slope 0.2 deg, distance 100m
    vuln_high = calculate_terrain_vulnerability(85.0, 0.2, 100.0)

    # Upland slope away from river: elevation 115m, slope 3.0 deg, distance 3500m
    vuln_low = calculate_terrain_vulnerability(115.0, 3.0, 3500.0)

    assert vuln_high > vuln_low
    assert 0.0 <= vuln_low < vuln_high <= 1.0


def test_saturation_score_bounds():
    """Verify API saturation increases linearly up to cap."""
    assert calculate_saturation_score(0.0) == 0.0
    assert calculate_saturation_score(60.0) == 0.5
    assert calculate_saturation_score(120.0) == 1.0
    assert calculate_saturation_score(200.0) == 1.0


def test_confirmed_closed_always_critical():
    """Requirement: Confirmed road closure must strictly produce 100.0 risk score."""
    factors = WarningFactors(
        recent_rain_1h_mm=0.0,
        recent_rain_3h_mm=0.0,
        recent_rain_6h_mm=0.0,
        forecast_rain_3h_mm=0.0,
        ground_saturation_api_mm=0.0,
        elevation_m=110.0,
        slope_degrees=3.0,
        distance_to_river_m=4000.0,
        active_reports_count=0,
        is_confirmed_closed=True,
    )
    score, severity = compute_risk_score(factors)
    assert score == 100.0
    assert severity == "critical"


def test_rain_surge_escalates_severity_tier():
    """Verify escalating rainfall shifts severity tier from advisory to high/critical."""
    factors_calm = WarningFactors(
        recent_rain_1h_mm=0.0,
        recent_rain_3h_mm=0.0,
        recent_rain_6h_mm=0.0,
        forecast_rain_3h_mm=0.0,
        ground_saturation_api_mm=10.0,
        elevation_m=94.0,
        slope_degrees=0.8,
        distance_to_river_m=400.0,
        active_reports_count=0,
        is_confirmed_closed=False,
    )
    score_calm, sev_calm = compute_risk_score(factors_calm)
    assert sev_calm in ("advisory", "moderate")

    factors_surge = WarningFactors(
        recent_rain_1h_mm=32.0,
        recent_rain_3h_mm=55.0,
        recent_rain_6h_mm=85.0,
        forecast_rain_3h_mm=25.0,
        ground_saturation_api_mm=80.0,
        elevation_m=94.0,
        slope_degrees=0.8,
        distance_to_river_m=400.0,
        active_reports_count=2,
        is_confirmed_closed=False,
    )
    score_surge, sev_surge = compute_risk_score(factors_surge)
    assert score_surge > score_calm
    assert sev_surge in ("high", "critical")
