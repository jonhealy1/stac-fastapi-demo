"""transactions extension client."""

import logging
from datetime import datetime

import attr
from stac_pydantic.shared import DATETIME_RFC339

from stac_fastapi.demo.config import MongoSettings
from stac_fastapi.demo.session import Session
from stac_fastapi.types import stac as stac_types
from stac_fastapi.types.core import BaseTransactionsClient
from stac_fastapi.types.links import CollectionLinks, ItemLinks

logger = logging.getLogger(__name__)


@attr.s
class TransactionsClient(BaseTransactionsClient):
    """Transactions extension specific CRUD operations."""

    session: Session = attr.ib(default=attr.Factory(Session.create_from_env))
    settings = MongoSettings()
    client = settings.create_client
    item_table = client.stac.stac_item
    collection_table = client.stac.stac_collection

    def create_item(self, model: stac_types.Item, **kwargs):
        """Create item."""
        base_url = str(kwargs["request"].base_url)
        item_links = ItemLinks(
            collection_id=model["collection"], item_id=model["id"], base_url=base_url
        ).create_links()
        model["links"] = item_links
        with self.client.start_session(causal_consistency=True) as session:
            now = datetime.utcnow().strftime(DATETIME_RFC339)
            if "created" not in model["properties"]:
                model["properties"]["created"] = str(now)
            self.item_table.insert_one(model, session=session)
            return model

    def create_collection(self, model: stac_types.Collection, **kwargs):
        """Create collection."""
        base_url = str(kwargs["request"].base_url)
        collection_links = CollectionLinks(
            collection_id=model["id"], base_url=base_url
        ).create_links()
        model["links"] = collection_links

        with self.client.start_session(causal_consistency=True) as session:
            self.collection_table.insert_one(model, session=session)

    def update_item(self, model: stac_types.Item, **kwargs):
        """Update item."""
        base_url = str(kwargs["request"].base_url)

        with self.client.start_session(causal_consistency=True) as session:
            self.delete_item(
                item_id=model["id"], collection_id=model["collection"], session=session
            )
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
        with self.client.start_session(causal_consistency=True) as session:
            self.item_table.delete_one(
                {"id": item_id, "collection": collection_id}, session=session
            )

    def delete_collection(self, collection_id: str, **kwargs):
        """Delete collection."""
        with self.client.start_session(causal_consistency=True) as session:
            self.collection_table.delete_one({"id": collection_id}, session=session)
