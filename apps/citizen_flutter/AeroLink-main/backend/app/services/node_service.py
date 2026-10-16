from datetime import UTC, datetime
from typing import cast

from pymongo.collection import Collection
from pymongo.results import UpdateResult

from app.core.constants import NodeStatus
from app.database.collections import NODES_COLLECTION
from app.database.mongodb import mongodb
from app.models.node import NodeDocument
from app.schemas.node import NodeCreate, NodeTelemetry


class NodeService:
    """
    Handles AeroLink node database operations and business logic.
    """

    def _get_collection(self) -> Collection[NodeDocument]:
        """
        Returns the nodes MongoDB collection.
        """

        if mongodb.database is None:
            raise RuntimeError("MongoDB database is not connected.")

        return cast(
            Collection[NodeDocument],
            mongodb.database[NODES_COLLECTION],
        )

    def register_node(self, node: NodeCreate) -> NodeDocument:
        """
        Registers a new AeroLink node.
        """

        collection = self._get_collection()

        existing_node = collection.find_one({"node_id": node.node_id})

        if existing_node is not None:
            raise ValueError(f"Node with ID '{node.node_id}' already exists.")

        now = datetime.now(UTC)

        node_document: NodeDocument = {
            "node_id": node.node_id,
            "node_name": node.node_name,
            "node_type": node.node_type,
            "location": {
                "latitude": node.location.latitude,
                "longitude": node.location.longitude,
            },
            "status": NodeStatus.INACTIVE,
            "battery_level": None,
            "signal_strength": None,
            "last_seen": None,
            "created_at": now,
            "updated_at": now,
        }

        _ = collection.insert_one(node_document)

        return node_document

    def get_node(self, node_id: str) -> NodeDocument | None:
        """
        Retrieves a node by its AeroLink node ID.
        """

        collection = self._get_collection()

        return collection.find_one({"node_id": node_id})

    def get_all_nodes(self) -> list[NodeDocument]:
        """
        Retrieves all registered AeroLink nodes.
        """

        collection = self._get_collection()

        return list(collection.find())

    def update_telemetry(
        self,
        node_id: str,
        telemetry: NodeTelemetry,
    ) -> NodeDocument | None:
        """
        Updates the latest telemetry received from an AeroLink node.
        """

        collection = self._get_collection()

        now = datetime.now(UTC)

        update_result: UpdateResult = collection.update_one(
            {"node_id": node_id},
            {
                "$set": {
                    "battery_level": telemetry.battery_level,
                    "signal_strength": telemetry.signal_strength,
                    "status": telemetry.status,
                    "last_seen": now,
                    "updated_at": now,
                }
            },
        )

        if update_result.matched_count == 0:
            return None

        return self.get_node(node_id)


node_service = NodeService()
