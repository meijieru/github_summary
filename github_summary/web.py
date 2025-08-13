import os
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from github_summary.config import load_config
from github_summary.scheduler import ReportScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for the FastAPI app."""
    config_path = os.getenv("GHSUM_CONFIG_PATH", "config/config.toml")
    cfg = load_config(config_path)
    os.makedirs(cfg.output_dir, exist_ok=True)

    scheduler = ReportScheduler(config_path)
    scheduler.start()
    yield
    scheduler.stop()


def build_web_app(config_path: Optional[str] = None) -> FastAPI:
    """Build the ASGI application that serves static files and runs the scheduler.

    On startup it ensures the output directory exists and starts a background
    scheduler thread. On shutdown it stops it.

    Args:
        config_path: Path to the TOML configuration file. If not provided, the
            GHSUM_CONFIG_PATH environment variable or the default path will be used.

    Returns:
        A configured FastAPI application instance.
    """
    if not config_path:
        config_path = os.getenv("GHSUM_CONFIG_PATH", "config/config.toml")

    app = FastAPI(lifespan=lifespan)

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    # Ensure config_path is a string at this point
    assert config_path is not None, "config_path should not be None at this point"
    cfg = load_config(config_path)
    app.mount("/", StaticFiles(directory=cfg.output_dir, html=False), name="static")

    return app


def main() -> None:
    """CLI entry that runs the ASGI app using Uvicorn."""
    # For uvicorn import-style execution: `uvicorn github_summary.web:main`
    app = build_web_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, workers=1)
