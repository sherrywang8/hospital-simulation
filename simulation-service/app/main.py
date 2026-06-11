from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.settings import load_settings
from app.services.artifact_store import LocalArtifactStore
from app.services.simulation_store import SimulationStore


def create_app(
    *,
    artifact_root: Path | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    settings = load_settings()
    resolved_artifact_root = artifact_root or settings.artifact_root
    resolved_cors_origins = cors_origins or settings.cors_origins
    allow_credentials = "*" not in resolved_cors_origins

    app = FastAPI(
        title="ED Simulation Service",
        description="FastAPI service for the React + SimPy emergency department simulator.",
        version="0.1.0",
    )
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "message": "ED Simulation Service is running"
        }
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.artifact_store = LocalArtifactStore(resolved_artifact_root)
    app.state.simulation_store = SimulationStore()
    app.include_router(router)
    return app


app = create_app()
