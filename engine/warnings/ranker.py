"""Prioritization and Dynamic Re-ranking Engine (Phase 3).

Implements Requirement B3:
Changing input re-ranks settlements and road segments with plain-language reason.
Maintains rank history across timeline steps to identify and explain rank shifts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from engine.warnings.schemas import (
    EvidenceCard,
    RankedWarning,
    WarningFactors,
    WarningSummaryResponse,
)


def create_primary_driver_summary(factors: WarningFactors) -> str:
    """Produces a concise 4-8 word tag of the top contributing driver."""
    if factors.is_confirmed_closed:
        return "Confirmed impassable road closure"
    if factors.recent_rain_1h_mm >= 25.0:
        return f"Severe cloudburst ({factors.recent_rain_1h_mm:.1f} mm/h)"
    if factors.distance_to_river_m < 500.0 and factors.recent_rain_3h_mm >= 15.0:
        return f"River proximity ({int(factors.distance_to_river_m)}m) + rain buildup"
    if factors.ground_saturation_api_mm >= 60.0:
        return f"High ground saturation ({factors.ground_saturation_api_mm:.0f}mm API)"
    if factors.elevation_m < 95.0:
        return f"Low-lying basin ({factors.elevation_m:.1f}m)"
    return "Normal baseline conditions"


def explain_rank_shift(
    previous_rank: int,
    new_rank: int,
    old_card: EvidenceCard | None,
    new_card: EvidenceCard,
) -> str:
    """Generates a plain-language reason explaining why an entity re-ranked (Requirement B3)."""
    delta = previous_rank - new_rank  # positive delta means increased in risk (moved towards rank 1)

    if delta == 0:
        return "Rank unchanged."

    direction = "Climbed" if delta > 0 else "Dropped"
    shift_str = f"{direction} {abs(delta)} rank(s) (from #{previous_rank} to #{new_rank})"

    if new_card.factors.is_confirmed_closed and (not old_card or not old_card.factors.is_confirmed_closed):
        return f"{shift_str} directly due to confirmed impassable closure report."

    if old_card is None:
        return f"Initial priority assignment at rank #{new_rank} ({new_card.severity.upper()})."

    # Compare factors
    reasons: list[str] = []
    rain_diff = new_card.factors.recent_rain_1h_mm - old_card.factors.recent_rain_1h_mm
    if rain_diff > 3.0:
        reasons.append(f"+{rain_diff:.1f} mm/h rainfall increase")
    elif rain_diff < -3.0:
        reasons.append(f"{rain_diff:.1f} mm/h rainfall decrease")

    rep_diff = new_card.factors.active_reports_count - old_card.factors.active_reports_count
    if rep_diff > 0:
        reasons.append(f"+{rep_diff} new field incident report(s)")

    if delta > 0:
        if reasons:
            return f"{shift_str} due to " + ", ".join(reasons) + "."
        return f"{shift_str} as local storm accumulation outpaced neighboring areas."
    else:
        if reasons:
            return f"{shift_str} as local rain eased (" + ", ".join(reasons) + ")."
        return f"{shift_str} as upstream corridors experienced more severe storm surges."


class WarningRanker:
    """Maintains stateful history across simulation steps to compute live rank shifts."""

    def __init__(self) -> None:
        self._previous_cards: dict[str, EvidenceCard] = {}
        self._previous_ranks: dict[str, int] = {}

    def rank_cards(
        self,
        cards: Sequence[EvidenceCard],
        run_id: str | None = None,
        source_mode: str = "simulated",
        decision_time: datetime | None = None,
    ) -> tuple[list[RankedWarning], WarningSummaryResponse]:
        """Ranks cards by risk score descending and computes rank shifts with reasons."""
        if decision_time is None:
            decision_time = datetime.now(timezone.utc)

        # Sort descending by risk score, tiebreaking by severity tier, then entity ID
        severity_weight = {"critical": 4, "high": 3, "moderate": 2, "advisory": 1}
        sorted_cards = sorted(
            cards,
            key=lambda c: (c.risk_score, severity_weight.get(c.severity, 0), c.factors.distance_to_river_m * -1),
            reverse=True,
        )

        ranked_warnings: list[RankedWarning] = []
        new_ranks: dict[str, int] = {}
        new_cards_map: dict[str, EvidenceCard] = {}

        severity_counts = {"critical": 0, "high": 0, "moderate": 0, "advisory": 0}
        highest_settlement: RankedWarning | None = None
        highest_road: RankedWarning | None = None

        total_settlements = 0
        total_roads = 0

        for idx, card in enumerate(sorted_cards, start=1):
            entity_id = card.entity_id
            new_ranks[entity_id] = idx
            new_cards_map[entity_id] = card

            if card.entity_type == "settlement":
                total_settlements += 1
            else:
                total_roads += 1

            severity_counts[card.severity] = severity_counts.get(card.severity, 0) + 1

            prev_rank = self._previous_ranks.get(entity_id)
            prev_card = self._previous_cards.get(entity_id)

            if prev_rank is not None:
                delta = prev_rank - idx  # positive = climbed in risk
                rerank_reason = explain_rank_shift(prev_rank, idx, prev_card, card)
            else:
                delta = 0
                rerank_reason = f"Initial assessment at rank #{idx} ({card.severity.upper()})."

            driver = create_primary_driver_summary(card.factors)

            rw = RankedWarning(
                rank=idx,
                entity_id=entity_id,
                entity_type=card.entity_type,
                entity_name=card.entity_name,
                risk_score=card.risk_score,
                severity=card.severity,
                primary_driver=driver,
                previous_rank=prev_rank,
                rank_delta=delta,
                rerank_reason=rerank_reason,
            )
            ranked_warnings.append(rw)

            if card.entity_type == "settlement" and highest_settlement is None:
                highest_settlement = rw
            elif card.entity_type == "road_segment" and highest_road is None:
                highest_road = rw

        # Update historical state
        self._previous_ranks = new_ranks
        self._previous_cards = new_cards_map

        summary = WarningSummaryResponse(
            run_id=run_id,
            source_mode=source_mode,  # type: ignore[arg-type]
            evaluated_at=decision_time,
            total_settlements_evaluated=total_settlements,
            total_roads_evaluated=total_roads,
            severity_counts=severity_counts,
            highest_risk_settlement=highest_settlement,
            highest_risk_road=highest_road,
            active_warnings=ranked_warnings,
        )

        return ranked_warnings, summary

    def reset(self) -> None:
        """Clears rank history (e.g. on scenario reset)."""
        self._previous_cards.clear()
        self._previous_ranks.clear()
