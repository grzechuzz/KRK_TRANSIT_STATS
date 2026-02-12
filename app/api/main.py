from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exceptions import setup_exception_handlers
from app.api.middleware import setup_middleware
from app.api.response import MsgspecJSONResponse
from app.api.stats import router
from app.common.db.connection import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_engine()
    yield
    get_engine().dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="MPK Kraków stats API",
        version="0.1.0",
        description="Public API for Kraków public transport delay statistics",
        default_response_class=MsgspecJSONResponse,
        lifespan=lifespan,
    )

    setup_middleware(app)
    setup_exception_handlers(app)

    app.include_router(router, prefix="/v1")

    return app


mpk_app = create_app()
