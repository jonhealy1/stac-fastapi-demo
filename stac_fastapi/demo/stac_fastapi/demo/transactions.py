"""transactions extension client."""

import logging
from datetime import datetime

import attr
from stac_pydantic.shared import DATETIME_RFC339

from stac_fastapi.demo.config import MongoSettings
from stac_fastapi.types import stac as stac_types
from stac_fastapi.types.core import BaseTransactionsClient

logger = logging.getLogger(__name__)


@attr.s
class TransactionsClient(BaseTransactionsClient):
    """Transactions extension specific CRUD operations."""
    settings = MongoSettings()
    client = settings.create_client
    item_table = client.stac.stac_item
    collection_table = client.stac.stac_collection

    def create_item(self, model: stac_types.Item, **kwargs):
        """Create item."""
        self.item_table.insert_one(model)
        return "success"

    def create_collection(self, model: stac_types.Collection, **kwargs):
        """Create collection."""
        self.collection_table.insert_one(model)
        return "success"

    def update_item(self, model: stac_types.Item, **kwargs):
        """Update item."""
        self.delete_item(item_id=model["id"], collection_id=model["collection"])
        now = datetime.utcnow().strftime(DATETIME_RFC339)
        model["properties"]["updated"] = str(now)
        self.create_item(model, **kwargs)
        return model

    def update_collection(self, model: stac_types.Collection, **kwargs):
        """Update collection."""
        self.delete_collection(model["id"])
        self.create_collection(model, **kwargs)

    def delete_item(self, item_id: str, collection_id: str, **kwargs):
        """Delete item."""
        self.item_table.delete_one({"id": item_id, "collection": collection_id})

    def delete_collection(self, collection_id: str, **kwargs):
        """Delete collection."""
        self.collection_table.delete_one({"id": collection_id})
