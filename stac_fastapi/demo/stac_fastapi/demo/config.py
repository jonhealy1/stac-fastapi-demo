"""API configuration."""
import os

from pymongo import GEOSPHERE, MongoClient, errors

from stac_fastapi.types.config import ApiSettings

DOMAIN = os.getenv("MONGO_HOST")
PORT = os.getenv("MONGO_PORT")


class MongoSettings(ApiSettings):
    """API settings."""

    @property
    def create_client(self):
        """Create mongo client."""
        try:
            client = MongoClient(
                host=[str(DOMAIN) + ":" + str(PORT)],
                serverSelectionTimeoutMS=3000,
                username=os.getenv("MONGO_USER"),
                password=os.getenv("MONGO_PASS"),
            )

            # create indices - they are only created if they don't already exist
            item_table = client.stac.stac_item
            item_table.create_index([("bbox", GEOSPHERE), ("properties.datetime", 1)])
            item_table.create_index([("geometry", GEOSPHERE)])
            item_table.create_index([("properties.datetime", 1)])
            item_table.create_index([("properties.created", 1)])
            item_table.create_index([("properties.updated", 1)])
            item_table.create_index([("bbox", GEOSPHERE)])

        except errors.ServerSelectionTimeoutError as err:
            client = None
            print("pymongo ERROR:", err)

        return client
