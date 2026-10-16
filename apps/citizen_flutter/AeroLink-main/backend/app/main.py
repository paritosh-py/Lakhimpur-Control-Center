from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.alerts import router as alerts_router
from app.api.health import router as health_router
from app.api.incident import router as incidents_router
from app.api.network import router as network_router
from app.api.nodes import router as nodes_router
from app.api.response import router as response_router
from app.api.websocket import router as websocket_router
from app.core.config import get_settings
from app.core.constants import API_V1_PREFIX
from app.database.mongodb import mongodb

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages application startup and shutdown tasks.
    """

    mongodb.connect()

    yield

    mongodb.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API for AeroLink emergency communication, "
        "incident management, and intelligent response coordination."
    ),
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(
    health_router,
    prefix=API_V1_PREFIX,
)


app.include_router(
    nodes_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    incidents_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    alerts_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    network_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    response_router,
    prefix=API_V1_PREFIX,
)

app.include_router(
    websocket_router,
    prefix=API_V1_PREFIX,
)


@app.get("/")
def root() -> dict[str, str]:
    """
    Returns basic AeroLink backend information.
    """

    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/favicon.ico")
async def favicon() -> FileResponse:
    return FileResponse("app/static/favicon.ico")
