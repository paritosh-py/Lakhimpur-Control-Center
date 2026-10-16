from collections.abc import Mapping

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import get_settings

settings = get_settings()


class MongoDB:
    """
    Manages the MongoDB connection for the AeroLink backend.
    """

    def __init__(self) -> None:
        self.client: MongoClient[Mapping[str, object]] | None = None
        self.database: Database[Mapping[str, object]] | None = None

    def connect(self) -> None:
        """
        Creates a connection to MongoDB.
        """

        if not settings.MONGODB_URI:
            raise ValueError("MONGODB_URI is not configured.")

        self.client = MongoClient(settings.MONGODB_URI)

        self.database = self.client[settings.MONGODB_DATABASE]

        # Verify the database connection
        _ = self.client.admin.command("ping")

        print("Connected to MongoDB successfully.")

    def close(self) -> None:
        """
        Closes the MongoDB connection.
        """

        if self.client:
            self.client.close()

            self.client = None
            self.database = None

            print("MongoDB connection closed.")


mongodb = MongoDB()
