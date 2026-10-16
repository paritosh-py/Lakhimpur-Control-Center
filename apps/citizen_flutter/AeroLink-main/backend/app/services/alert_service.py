from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from pymongo.collection import Collection
from pymongo.results import UpdateResult

from app.core.constants import AlertStatus
from app.database.collections import ALERTS_COLLECTION
from app.database.mongodb import mongodb
from app.models.alert import AlertDocument
from app.services.incident_service import incident_service
from app.services.node_service import node_service
from app.services.priority_service import priority_service


class AlertService:
    """
    Handles AeroLink alert generation and lifecycle operations.
    """

    def _get_collection(self) -> Collection[AlertDocument]:
        """
        Returns the alerts MongoDB collection.
        """

        if mongodb.database is None:
            raise RuntimeError("MongoDB database is not connected.")

        return cast(
            Collection[AlertDocument],
            mongodb.database[ALERTS_COLLECTION],
        )

    def generate_alert(
        self,
        incident_id: str,
    ) -> AlertDocument:
        """
        Generates an alert for an existing incident.
        """

        incident = incident_service.get_incident(incident_id)

        if incident is None:
            raise ValueError(f"Incident '{incident_id}' was not found.")

        collection = self._get_collection()

        existing_alert = collection.find_one({"incident_id": incident_id})

        if existing_alert is not None:
            raise ValueError(f"Alert for incident '{incident_id}' already exists.")

        reporting_node = None

        if incident["reporting_node_id"] is not None:
            reporting_node = node_service.get_node(incident["reporting_node_id"])

        priority_result = priority_service.calculate_priority(
            incident,
            reporting_node,
        )

        now = datetime.now(UTC)

        alert_id = f"AL-ALT-{uuid4().hex[:8].upper()}"

        alert_document: AlertDocument = {
            "alert_id": alert_id,
            "incident_id": incident_id,
            "priority_score": priority_result.total_score,
            "priority_level": priority_result.priority_level,
            "severity_score": priority_result.severity_score,
            "incident_type_score": (priority_result.incident_type_score),
            "network_score": priority_result.network_score,
            "status": AlertStatus.GENERATED,
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
        }

        _ = collection.insert_one(alert_document)

        return alert_document

    def get_alert(
        self,
        alert_id: str,
    ) -> AlertDocument | None:
        """
        Retrieves an alert by its AeroLink alert ID.
        """

        collection = self._get_collection()

        return collection.find_one({"alert_id": alert_id})

    def get_all_alerts(
        self,
    ) -> list[AlertDocument]:
        """
        Retrieves all AeroLink alerts.
        """

        collection = self._get_collection()

        return list(collection.find())

    def update_status(
        self,
        alert_id: str,
        status: AlertStatus,
    ) -> AlertDocument | None:
        """
        Updates the lifecycle status of an AeroLink alert.
        """

        collection = self._get_collection()

        now = datetime.now(UTC)

        update_fields = {
            "status": status,
            "updated_at": now,
        }

        if status == AlertStatus.RESOLVED:
            update_fields["resolved_at"] = now

        update_result: UpdateResult = collection.update_one(
            {"alert_id": alert_id},
            {"$set": update_fields},
        )

        if update_result.matched_count == 0:
            return None

        return self.get_alert(alert_id)


alert_service = AlertService()
