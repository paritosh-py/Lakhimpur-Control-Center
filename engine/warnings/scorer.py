"""Multi-factor risk scoring engine for settlements and roads (Phase 3).

Implements Requirement B2:
Combines rainfall (recent + forecast), ground saturation (API),
terrain (elevation, slope, river proximity), and field/closure reports
into an explainable, normalized risk score (0 to 100).
"""
from __future__ import annotations

import math
from typing import Any, Literal

from engine.warnings.schemas import WarningFactors


def calculate_rain_score(
    rain_1h: float,
    rain_3h: float,
    rain_6h: float,
    forecast_3h: float,
) -> float:
    """Calculates normalized rain hazard index [0.0, 1.0].
    
    Calibration thresholds for Brahmaputra/Lakhimpur basin:
    - 35 mm/h: Cloudburst / flash flood intensity
    - 60 mm / 3h: Severe drainage overtopping
    - 100 mm / 6h: Regional inundation threshold
    - 40 mm / 3h forecast: Imminent surge
    """
    comp_1h = min(1.0, rain_1h / 35.0)
    comp_3h = min(1.0, rain_3h / 60.0)
    comp_6h = min(1.0, rain_6h / 100.0)
    comp_fc = min(1.0, forecast_3h / 40.0)
    
    return min(1.0, 0.40 * comp_1h + 0.30 * comp_3h + 0.15 * comp_6h + 0.15 * comp_fc)


def calculate_terrain_vulnerability(
    elevation_m: float,
    slope_degrees: float,
    distance_to_river_m: float,
) -> float:
    """Calculates terrain susceptibility index [0.0, 1.0].
    
    - Elevation: 80m (riverbed lowest) to 110m (higher terrace)
    - Slope: < 0.8 deg flat basin accumulates water; > 2.5 deg drains quickly
    - River distance: < 200m extreme floodway; > 3000m outside direct breach zone
    """
    # Lower elevation is higher vulnerability
    v_elev = max(0.0, min(1.0, (110.0 - elevation_m) / 30.0))
    # Flatter terrain is higher water retention
    v_slope = max(0.0, min(1.0, (2.5 - slope_degrees) / 2.5))
    # Closer to river channel is higher vulnerability
    v_river = max(0.0, min(1.0, (3000.0 - distance_to_river_m) / 2800.0))
    
    return 0.40 * v_elev + 0.25 * v_slope + 0.35 * v_river


def calculate_saturation_score(api_mm: float) -> float:
    """Calculates Antecedent Precipitation Index saturation [0.0, 1.0].
    
    120mm cumulative saturation represents near-zero infiltration capacity.
    """
    return min(1.0, max(0.0, api_mm / 120.0))


def compute_risk_score(factors: WarningFactors) -> tuple[float, Literal["advisory", "moderate", "high", "critical"]]:
    """Computes composite multi-factor risk score [0.0, 100.0] and severity tier.
    
    If confirmed closed, score is strictly 100.0 (CRITICAL).
    """
    if factors.is_confirmed_closed:
        return 100.0, "critical"

    s_rain = calculate_rain_score(
        factors.recent_rain_1h_mm,
        factors.recent_rain_3h_mm,
        factors.recent_rain_6h_mm,
        factors.forecast_rain_3h_mm,
    )
    s_sat = calculate_saturation_score(factors.ground_saturation_api_mm)
    v_terrain = calculate_terrain_vulnerability(
        factors.elevation_m,
        factors.slope_degrees,
        factors.distance_to_river_m,
    )
    
    # Reports component: citizen reports or nearby access alerts
    s_reports = min(1.0, factors.active_reports_count * 0.25)

    # Core interaction: atmospheric rain hazard modulated by physical terrain vulnerability
    base_hazard = 0.65 * s_rain + 0.35 * s_sat
    terrain_amplified = base_hazard * (0.35 + 0.65 * v_terrain)
    
    combined = 0.80 * terrain_amplified + 0.20 * s_reports
    score = round(min(100.0, max(0.0, combined * 100.0)), 1)

    if score >= 75.0:
        severity = "critical"
    elif score >= 50.0:
        severity = "high"
    elif score >= 25.0:
        severity = "moderate"
    else:
        severity = "advisory"

    return score, severity
