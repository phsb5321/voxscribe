"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.bootstrap import bootstrap


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap the application on startup."""
    bootstrap()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Audio Transcriber",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Import and include routes
    from app.adapters.inbound.web.routes import router

    app.include_router(router)

    return app
