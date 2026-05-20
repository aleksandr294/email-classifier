import typing
from contextlib import asynccontextmanager

import fastapi

from api.v1 import router as router_v1
from components.core.logger import setup_logging


@asynccontextmanager
async def configure_app(app: fastapi.FastAPI) -> typing.AsyncGenerator[fastapi.FastAPI, None]:
    setup_logging()
    yield


app = fastapi.FastAPI(docs_url="/api/docs", redoc_url="/api/redoc", lifespan=configure_app)

router_v1.configure(app)
