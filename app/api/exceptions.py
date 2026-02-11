import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled error on {request.method} {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
