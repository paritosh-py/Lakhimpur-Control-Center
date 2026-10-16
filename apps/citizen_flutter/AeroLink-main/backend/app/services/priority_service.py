from dataclasses import dataclass
from typing import ClassVar

from app.core.constants import (
    IncidentSeverity,
    IncidentType,
    NodeStatus,
    PriorityLevel,
)
from app.models.incident import IncidentDocument
from app.models.node import NodeDocument


@dataclass(frozen=True)
class PriorityResult:
    """
    Result produced by the AeroLink Priority Engine.
    """

    severity_score: int
    incident_type_score: int
    network_score: int
    total_score: int
    priority_level: PriorityLevel


class PriorityService:
    """
    Calculates an explainable priority score for AeroLink incidents.
    """

    _SEVERITY_SCORES: ClassVar[dict[IncidentSeverity, int]] = {
        IncidentSeverity.LOW: 12,
        IncidentSeverity.MEDIUM: 25,
        IncidentSeverity.HIGH: 38,
        IncidentSeverity.CRITICAL: 50,
    }

    _INCIDENT_TYPE_SCORES: ClassVar[dict[IncidentType, int]] = {
        IncidentType.MEDICAL: 25,
        IncidentType.FIRE: 25,
        IncidentType.ACCIDENT: 18,
        IncidentType.NATURAL_HAZARD: 22,
        IncidentType.SECURITY: 15,
        IncidentType.OTHER: 8,
    }

    def calculate_priority(
        self,
        incident: IncidentDocument,
        reporting_node: NodeDocument | None,
    ) -> PriorityResult:
        """
        Calculates the priority score for an incident.
        """

        severity_score = self._SEVERITY_SCORES[incident["severity"]]

        incident_type_score = self._INCIDENT_TYPE_SCORES[incident["incident_type"]]

        network_score = self._calculate_network_score(reporting_node)

        total_score = severity_score + incident_type_score + network_score

        priority_level = self._get_priority_level(total_score)

        return PriorityResult(
            severity_score=severity_score,
            incident_type_score=incident_type_score,
            network_score=network_score,
            total_score=total_score,
            priority_level=priority_level,
        )

    @staticmethod
    def _calculate_network_score(
        reporting_node: NodeDocument | None,
    ) -> int:
        """
        Calculates the network-risk contribution.
        """

        if reporting_node is None:
            return 12

        if reporting_node["status"] == NodeStatus.OFFLINE:
            return 25

        signal_strength = reporting_node["signal_strength"]

        if signal_strength is None:
            return 12

        if signal_strength < -100:
            return 22

        if signal_strength < -85:
            return 15

        return 5

    @staticmethod
    def _get_priority_level(
        total_score: int,
    ) -> PriorityLevel:
        """
        Converts a priority score into a priority level.
        """

        if total_score >= 75:
            return PriorityLevel.CRITICAL

        if total_score >= 55:
            return PriorityLevel.HIGH

        if total_score >= 30:
            return PriorityLevel.MEDIUM

        return PriorityLevel.LOW


priority_service = PriorityService()
