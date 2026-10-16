from app.core.constants import IncidentType, PriorityLevel
from app.models.alert import AlertDocument
from app.models.incident import IncidentDocument
from app.services.alert_service import alert_service
from app.services.spatial_service import spatial_service


class ResponseService:
    """
    Generates actionable AeroLink response recommendations.
    """

    def get_incident_response(
        self,
        incident_id: str,
    ) -> (
        tuple[
            IncidentDocument,
            AlertDocument,
            str,
            str | None,
            str,
            str,
            str,
        ]
        | None
    ):
        """
        Builds a complete response recommendation for an incident.
        """

        alert = self._get_alert_for_incident(incident_id)

        if alert is None:
            return None

        network_context = spatial_service.get_incident_network_context(incident_id)

        if network_context is None:
            return None

        (
            incident,
            _nearby_nodes,
            nearest_online_node,
            network_risk,
        ) = network_context

        nearest_online_node_id: str | None = None

        if nearest_online_node is not None:
            nearest_online_node_id = nearest_online_node[0]["node_id"]

        action = self._get_recommended_action(incident["incident_type"])

        urgency = self._get_urgency(alert["priority_level"])

        communication_strategy = self._get_communication_strategy(network_risk)

        return (
            incident,
            alert,
            network_risk,
            nearest_online_node_id,
            action,
            urgency,
            communication_strategy,
        )

    @staticmethod
    def _get_recommended_action(
        incident_type: IncidentType,
    ) -> str:
        """
        Maps incident type to a primary response action.
        """

        actions = {
            IncidentType.MEDICAL: "medical_response",
            IncidentType.FIRE: "fire_and_emergency_response",
            IncidentType.ACCIDENT: "rescue_and_traffic_response",
            IncidentType.NATURAL_HAZARD: "disaster_response",
            IncidentType.SECURITY: "security_response",
            IncidentType.OTHER: "field_assessment",
        }

        return actions[incident_type]

    @staticmethod
    def _get_urgency(
        priority_level: PriorityLevel,
    ) -> str:
        """
        Maps priority level to response urgency.
        """

        urgencies = {
            PriorityLevel.CRITICAL: "immediate",
            PriorityLevel.HIGH: "urgent",
            PriorityLevel.MEDIUM: "prioritized",
            PriorityLevel.LOW: "routine",
        }

        return urgencies[priority_level]

    @staticmethod
    def _get_communication_strategy(
        network_risk: str,
    ) -> str:
        """
        Determines the recommended communication strategy.
        """

        strategies = {
            "low": "primary_route_available",
            "medium": "monitor_network_route",
            "high": "use_redundant_communication",
            "critical": ("fallback_emergency_communication"),
        }

        return strategies[network_risk]

    @staticmethod
    def _get_alert_for_incident(
        incident_id: str,
    ) -> AlertDocument | None:
        """
        Retrieves the generated alert associated with an incident.
        """

        alerts = alert_service.get_all_alerts()

        for alert in alerts:
            if alert["incident_id"] == incident_id:
                return alert

        return None


response_service = ResponseService()
