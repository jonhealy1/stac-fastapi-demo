"""Item crud client."""
import json
from typing import Union, Optional, List
from bson.json_util import dumps
import attr
from datetime import datetime
from pydantic import ValidationError
from stac_fastapi.types.search import BaseSearchPostRequest

from stac_fastapi.demo.config import MongoSettings
from fastapi import HTTPException
from stac_fastapi.types.core import BaseCoreClient
from stac_fastapi.types.stac import Collection, Collections, Item, ItemCollection

NumType = Union[float, int]


@attr.s
class CoreCrudClient(BaseCoreClient):
    """Client for core endpoints defined by stac."""
    settings = MongoSettings()
    client = settings.create_client
    item_table = client.stac.stac_item
    collection_table = client.stac.stac_collection

    def all_collections(self, **kwargs) -> Collections:
        """Read all collections from the database."""
        collections = self.collection_table.find()
        collections = [json.loads(dumps(collection)) for collection in collections]
        return collections

    def get_collection(self, collection_id: str, **kwargs) -> Collection:
        """Get collection by id."""
        collection = self.collection_table.find_one({"id": collection_id})
        return json.loads(dumps(collection))

    def item_collection(
        self, collection_id: str, limit: int = 10, token: str = None, **kwargs
    ) -> ItemCollection:
        """Read an item collection from the database."""
        collection_children = (
            self.item_table.find({"collection": collection_id})
        )
        items = [json.loads(dumps(item)) for item in collection_children]

        return {
            "type": "FeatureCollection",
            "features": items
        }

    def get_item(self, item_id: str, collection_id: str, **kwargs) -> Item:
        """Get item by item id, collection id."""
        item = self.item_table.find_one({"id": item_id, "collection": collection_id})
        return json.loads(dumps(item))

    def get_search(
        self,
        collections: Optional[List[str]] = None,
        ids: Optional[List[str]] = None,
        bbox: Optional[List[NumType]] = None,
        datetime: Optional[Union[str, datetime]] = None,
        limit: Optional[int] = 10,
        query: Optional[str] = None,
        token: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sortby: Optional[str] = None,
        **kwargs,
    ) -> ItemCollection:
        """GET search catalog."""
        base_args = {
            "collections": collections,
            "ids": ids,
            "bbox": bbox,
            "limit": limit,
            "token": token,
            "query": json.loads(query) if query else query,
        }
        pass

    def post_search(
        self, search_request: BaseSearchPostRequest, **kwargs
    ) -> ItemCollection:
        """POST search catalog."""
        base_url = str(kwargs["request"].base_url)
        queries = {}

        if search_request.intersects:
            intersect_filter = {
                "geometry": {
                    "$geoIntersects": {
                        "$geometry": {
                            "type": search_request.intersects.type,
                            "coordinates": search_request.intersects.coordinates,
                        }
                    }
                }
            }
            queries.update(**intersect_filter)

        if search_request.query:
            if type(search_request.query) == str:
                search_request.query = json.loads(search_request.query)
            for (field_name, expr) in search_request.query.items():
                field = "properties." + field_name
                for (op, value) in expr.items():
                    key_filter = {field: {f"${op}": value}}
                    queries.update(**key_filter)

        results = (self.item_table.find(queries).limit(search_request.limit))

        items = [json.loads(dumps(item)) for item in results]

        return ItemCollection(
            type="FeatureCollection",
            features=items
        )
