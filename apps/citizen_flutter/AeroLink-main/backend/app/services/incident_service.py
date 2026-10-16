from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from pymongo.collection import Collection
from pymongo.results import UpdateResult

from app.core.constants import IncidentStatus
from app.database.collections import INCIDENTS_COLLECTION
from app.database.mongodb import mongodb
from app.models.incident import IncidentDocument
from app.schemas.incident import (
    IncidentCreate,
    IncidentStatusUpdate,
)


class IncidentService:
    """
    Handles AeroLink incident database operations and business logic.
    """

    def _get_collection(self) -> Collection[IncidentDocument]:
        """
        Returns the incidents MongoDB collection.
        """

        if mongodb.database is None:
            raise RuntimeError("MongoDB database is not connected.")

        return cast(
            Collection[IncidentDocument],
            mongodb.database[INCIDENTS_COLLECTION],
        )

    def create_incident(
        self,
        incident: IncidentCreate,
    ) -> IncidentDocument:
        """
        Creates a new AeroLink incident.
        """

        collection = self._get_collection()

        now = datetime.now(UTC)

        incident_id = f"AL-INC-{uuid4().hex[:8].upper()}"

        incident_document: IncidentDocument = {
            "incident_id": incident_id,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "description": incident.description,
            "location": {
                "latitude": incident.location.latitude,
                "longitude": incident.location.longitude,
            },
            "reporting_node_id": incident.reporting_node_id,
            "status": IncidentStatus.REPORTED,
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
        }

        _ = collection.insert_one(incident_document)

        return incident_document

    def get_incident(
        self,
        incident_id: str,
    ) -> IncidentDocument | None:
        """
        Retrieves an incident by its AeroLink incident ID.
        """

        collection = self._get_collection()

        return collection.find_one({"incident_id": incident_id})

    def get_all_incidents(
        self,
    ) -> list[IncidentDocument]:
        """
        Retrieves all AeroLink incidents.
        """

        collection = self._get_collection()

        return list(collection.find())

    def update_status(
        self,
        incident_id: str,
        status_update: IncidentStatusUpdate,
    ) -> IncidentDocument | None:
        """
        Updates the lifecycle status of an incident.
        """

        collection = self._get_collection()

        now = datetime.now(UTC)

        update_fields = {
            "status": status_update.status,
            "updated_at": now,
        }

        if status_update.status == IncidentStatus.RESOLVED:
            update_fields["resolved_at"] = now

        update_result: UpdateResult = collection.update_one(
            {"incident_id": incident_id},
            {"$set": update_fields},
        )

        if update_result.matched_count == 0:
            return None

        return self.get_incident(incident_id)


incident_service = IncidentService()
