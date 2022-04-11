"""FastAPI application."""
from stac_fastapi.api.app import StacApi
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.extensions.core import (
    ContextExtension,
    SortExtension,
    TransactionExtension,
)
from stac_fastapi.mongo.config import MongoSettings
from stac_fastapi.mongo.core import CoreCrudClient
from stac_fastapi.mongo.extensions import QueryExtension
from stac_fastapi.mongo.session import Session
from stac_fastapi.mongo.transactions import TransactionsClient

settings = MongoSettings()
session = Session.create_from_settings(settings)

extensions = [
    TransactionExtension(client=TransactionsClient(session=session), settings=settings),
    QueryExtension(),
    SortExtension(),
    ContextExtension(),
]

post_request_model = create_post_request_model(extensions)

api = StacApi(
    settings=settings,
    extensions=extensions,
    client=CoreCrudClient(session=session, post_request_model=post_request_model),
    search_get_request_model=create_get_request_model(extensions),
    search_post_request_model=post_request_model,
)
app = api.app


def run():
    """Run app from command line using uvicorn if available."""
    try:
        import uvicorn

        uvicorn.run(
            "stac_fastapi.mongo.app:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level="info",
            reload=settings.reload,
        )
    except ImportError:
        raise RuntimeError("Uvicorn must be installed in order to use command")


if __name__ == "__main__":
    run()