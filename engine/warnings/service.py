"""Warning Engine Service (Phase 3).

Coordinates data loading, multi-factor scoring, evidence card generation,
and stateful dynamic re-ranking for all settlements and road segments.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from engine.config import ROOT
from engine.ingest.run import RunState
from engine.warnings.evidence import build_evidence_card
from engine.warnings.ranker import WarningRanker
from engine.warnings.schemas import (
    EvidenceCard,
    RankedWarning,
    WarningFactors,
    WarningSummaryResponse,
)
from engine.warnings.scorer import compute_risk_score

DATA_PROCESSED = ROOT / "data" / "processed"


class WarningEngine:
    """Core domain service for flood risk warnings and explainable evidence cards."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_PROCESSED
        self.ranker = WarningRanker()
        self._cards: dict[str, EvidenceCard] = {}
        self._settlements: list[dict[str, Any]] = []
        self._roads: list[dict[str, Any]] = []
        self._initialized = False

    def _ensure_loaded(self) -> None:
        """Loads spatial features from processed GeoJSON files if not already loaded."""
        if self._initialized:
            return

        settlements_file = self.data_dir / "settlements.geojson"
        if settlements_file.exists():
            with open(settlements_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._settlements = [feat["properties"] for feat in data.get("features", [])]

        roads_file = self.data_dir / "roads.geojson"
        if roads_file.exists():
            with open(roads_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._roads = [feat["properties"] for feat in data.get("features", [])]

        self._initialized = True

    def evaluate(
        self,
        run_state: RunState | None = None,
        rain_1h_override: float | None = None,
        additional_closed_roads: set[str] | None = None,
        additional_reports: dict[str, int] | None = None,
    ) -> tuple[list[RankedWarning], WarningSummaryResponse]:
        """Evaluates all settlements and primary study roads, returning ranked warnings."""
        self._ensure_loaded()

        # Determine decision time and source mode
        if run_state and run_state.is_active:
            raw_mode = run_state.mode.value if run_state.mode else "simulated"
            source_mode = "simulated" if raw_mode == "scenario" else raw_mode
            current_time = run_state.current_time or datetime.now(timezone.utc)
            run_id = run_state.run_id
        else:
            source_mode = "live"
            current_time = datetime.now(timezone.utc)
            run_id = None

        closed_roads: set[str] = set()
        active_reports: dict[str, int] = {}
        recent_rain_1h = 0.0
        recent_rain_3h = 0.0
        recent_rain_6h = 0.0
        forecast_rain_3h = 0.0
        newest_obs_time = current_time

        # Extract information from run history if active
        if run_state and run_state.is_active:
            # Look through past records in run state
            for step_res in getattr(run_state, "_history", []):
                for rec in step_res.records:
                    if rec.kind == "weather":
                        precip = rec.payload.get("precipitation_mm", 0.0)
                        if precip is not None:
                            recent_rain_1h = float(precip)
                            recent_rain_3h += float(precip) * 0.4
                            recent_rain_6h += float(precip) * 0.2
                            newest_obs_time = rec.available_at
                    elif rec.kind == "report":
                        if rec.payload.get("reported_status") == "closed":
                            road_id = rec.payload.get("road_id")
                            if road_id:
                                closed_roads.add(road_id)
                        settlement_id = rec.payload.get("settlement_id")
                        if settlement_id:
                            active_reports[settlement_id] = active_reports.get(settlement_id, 0) + 1

        # Apply any explicit overrides (e.g., for testing B3 live re-ranking)
        if rain_1h_override is not None:
            recent_rain_1h = float(rain_1h_override)
            recent_rain_3h = max(recent_rain_3h, recent_rain_1h * 1.8)
            recent_rain_6h = max(recent_rain_6h, recent_rain_1h * 2.5)

        if additional_closed_roads:
            closed_roads.update(additional_closed_roads)

        if additional_reports:
            for k, v in additional_reports.items():
                active_reports[k] = active_reports.get(k, 0) + v

        # Ground saturation (API): approximate from recent cumulative rain
        ground_saturation = min(120.0, recent_rain_6h * 1.5 + recent_rain_1h * 2.0)

        all_cards: list[EvidenceCard] = []

        # 1. Evaluate Settlements (16 study settlements)
        for s in self._settlements:
            s_id = s.get("id", "")
            s_name = s.get("name", s_id)
            elev = float(s.get("elevation_m", 98.0))
            slope = float(s.get("slope_degrees", 1.0))
            dist_river = float(s.get("distance_to_river_m", 2500.0))
            nearest_seg = s.get("nearest_segment_id")

            # Is the access road to this settlement closed?
            access_closed = nearest_seg in closed_roads if nearest_seg else False
            rep_count = active_reports.get(s_id, 0)

            # Local rain with slight elevation modulation
            local_rain_1h = max(0.0, recent_rain_1h * (1.0 + (100.0 - elev) * 0.005))
            local_rain_3h = max(0.0, recent_rain_3h * (1.0 + (100.0 - elev) * 0.005))

            factors = WarningFactors(
                recent_rain_1h_mm=round(local_rain_1h, 1),
                recent_rain_3h_mm=round(local_rain_3h, 1),
                recent_rain_6h_mm=round(recent_rain_6h, 1),
                forecast_rain_3h_mm=round(forecast_rain_3h, 1),
                ground_saturation_api_mm=round(ground_saturation, 1),
                elevation_m=round(elev, 1),
                slope_degrees=round(slope, 2),
                distance_to_river_m=round(dist_river, 1),
                active_reports_count=rep_count,
                is_confirmed_closed=access_closed,
            )

            score, severity = compute_risk_score(factors)
            card = build_evidence_card(
                entity_id=s_id,
                entity_type="settlement",
                entity_name=s_name,
                risk_score=score,
                severity=severity,
                factors=factors,
                source_mode=source_mode,  # type: ignore[arg-type]
                newest_observation_time=newest_obs_time,
                current_decision_time=current_time,
            )
            all_cards.append(card)
            self._cards[s_id] = card

        # 2. Evaluate Road Segments
        # Include all closed roads plus the most vulnerable roads
        roads_to_evaluate = [r for r in self._roads if r.get("id") in closed_roads or float(r.get("distance_to_river_m", 9999.0)) < 800.0]
        # Always sample at least top vulnerable roads
        if not roads_to_evaluate:
            roads_to_evaluate = sorted(self._roads, key=lambda r: float(r.get("distance_to_river_m", 9999.0)))[:25]

        for r in roads_to_evaluate:
            r_id = r.get("id", "")
            r_name = r.get("name") or f"Road {r.get('osm_way_id', r_id)}"
            elev = float(r.get("elevation_m", 98.0))
            slope = float(r.get("slope_degrees", 1.0))
            dist_river = float(r.get("distance_to_river_m", 2500.0))
            is_closed = r_id in closed_roads

            factors = WarningFactors(
                recent_rain_1h_mm=round(recent_rain_1h, 1),
                recent_rain_3h_mm=round(recent_rain_3h, 1),
                recent_rain_6h_mm=round(recent_rain_6h, 1),
                forecast_rain_3h_mm=round(forecast_rain_3h, 1),
                ground_saturation_api_mm=round(ground_saturation, 1),
                elevation_m=round(elev, 1),
                slope_degrees=round(slope, 2),
                distance_to_river_m=round(dist_river, 1),
                active_reports_count=1 if is_closed else 0,
                is_confirmed_closed=is_closed,
            )

            score, severity = compute_risk_score(factors)
            card = build_evidence_card(
                entity_id=r_id,
                entity_type="road_segment",
                entity_name=r_name,
                risk_score=score,
                severity=severity,
                factors=factors,
                source_mode=source_mode,  # type: ignore[arg-type]
                newest_observation_time=newest_obs_time,
                current_decision_time=current_time,
            )
            all_cards.append(card)
            self._cards[r_id] = card

        # Rank all generated evidence cards
        ranked_warnings, summary = self.ranker.rank_cards(
            cards=all_cards,
            run_id=run_id,
            source_mode=source_mode,
            decision_time=current_time,
        )

        # Attach live rank and delta info onto cached Evidence Cards
        ranked_by_id = {rw.entity_id: rw for rw in ranked_warnings}
        for entity_id, card in list(self._cards.items()):
            if entity_id in ranked_by_id:
                rw = ranked_by_id[entity_id]
                self._cards[entity_id] = card.model_copy(update={
                    "rank": rw.rank,
                    "rank_delta": rw.rank_delta,
                    "rerank_reason": rw.rerank_reason,
                })

        return ranked_warnings, summary

    def get_card(self, entity_id: str) -> EvidenceCard | None:
        """Returns the full Evidence Card for a specific entity ID."""
        return self._cards.get(entity_id)

    def reset(self) -> None:
        """Resets the warning engine and ranker history."""
        self.ranker.reset()
        self._cards.clear()


# Shared engine singleton
_warning_engine = WarningEngine()


def get_warning_engine() -> WarningEngine:
    """Returns the shared warning engine singleton."""
    return _warning_engine
