from math import asin, cos, radians, sin, sqrt
from typing import ClassVar

from app.core.constants import NodeStatus
from app.models.incident import IncidentDocument
from app.models.node import NodeDocument
from app.services.incident_service import incident_service
from app.services.node_service import node_service


class SpatialService:
    """
    Provides geographic calculations for AeroLink.
    """

    EARTH_RADIUS_METERS: ClassVar[float] = 6_371_000

    @staticmethod
    def calculate_distance_meters(
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
    ) -> float:
        """
        Calculates the geographic distance between two coordinates
        using the Haversine formula.
        """

        latitude_1_rad = radians(latitude_1)
        longitude_1_rad = radians(longitude_1)
        latitude_2_rad = radians(latitude_2)
        longitude_2_rad = radians(longitude_2)

        latitude_difference = latitude_2_rad - latitude_1_rad

        longitude_difference = longitude_2_rad - longitude_1_rad

        haversine_value = (
            sin(latitude_difference / 2) ** 2
            + cos(latitude_1_rad)
            * cos(latitude_2_rad)
            * sin(longitude_difference / 2) ** 2
        )

        angular_distance = 2 * asin(sqrt(haversine_value))

        return SpatialService.EARTH_RADIUS_METERS * angular_distance

    @staticmethod
    def _calculate_network_risk(
        nearby_nodes: list[tuple[NodeDocument, float]],
        nearest_online_node: (tuple[NodeDocument, float] | None),
    ) -> str:
        """
        Evaluates communication risk around an incident.
        """

        if not nearby_nodes:
            return "critical"

        if nearest_online_node is None:
            return "high"

        nearest_distance = nearest_online_node[1]

        if nearest_distance <= 500:
            return "low"

        if nearest_distance <= 2_000:
            return "medium"

        return "high"

    def get_nearby_nodes(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 5_000,
    ) -> list[tuple[NodeDocument, float]]:
        """
        Returns nodes within the specified radius,
        sorted by distance.
        """

        nodes = node_service.get_all_nodes()

        nearby_nodes: list[tuple[NodeDocument, float]] = []

        for node in nodes:
            distance = self.calculate_distance_meters(
                latitude,
                longitude,
                node["location"]["latitude"],
                node["location"]["longitude"],
            )

            if distance <= radius_meters:
                nearby_nodes.append((node, distance))

        nearby_nodes.sort(key=lambda item: item[1])

        return nearby_nodes

    def get_network_overview(
        self,
    ) -> dict[str, int | float | None]:
        """
        Calculates a summary of the AeroLink network state.
        """

        nodes = node_service.get_all_nodes()

        total_nodes = len(nodes)

        online_nodes = sum(1 for node in nodes if node["status"] == NodeStatus.ONLINE)

        offline_nodes = sum(1 for node in nodes if node["status"] == NodeStatus.OFFLINE)

        inactive_nodes = sum(
            1 for node in nodes if node["status"] == NodeStatus.INACTIVE
        )

        signal_strengths = [
            node["signal_strength"]
            for node in nodes
            if node["signal_strength"] is not None
        ]

        average_signal_strength: float | None = None

        if signal_strengths:
            average_signal_strength = sum(signal_strengths) / len(signal_strengths)

        return {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "inactive_nodes": inactive_nodes,
            "average_signal_strength": average_signal_strength,
        }

    def get_incident_network_context(
        self,
        incident_id: str,
        radius_meters: float = 5_000,
    ) -> (
        tuple[
            IncidentDocument,
            list[tuple[NodeDocument, float]],
            tuple[NodeDocument, float] | None,
            str,
        ]
        | None
    ):
        """
        Builds network context around an AeroLink incident.
        """

        incident = incident_service.get_incident(incident_id)

        if incident is None:
            return None

        latitude = incident["location"]["latitude"]
        longitude = incident["location"]["longitude"]

        nearby_nodes = self.get_nearby_nodes(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
        )

        nearest_online_node: tuple[NodeDocument, float] | None = next(
            (
                node_with_distance
                for node_with_distance in nearby_nodes
                if (node_with_distance[0]["status"] == NodeStatus.ONLINE)
            ),
            None,
        )

        network_risk = self._calculate_network_risk(
            nearby_nodes,
            nearest_online_node,
        )

        return (
            incident,
            nearby_nodes,
            nearest_online_node,
            network_risk,
        )


spatial_service = SpatialService()
