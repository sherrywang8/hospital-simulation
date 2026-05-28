from __future__ import annotations

import mimetypes

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.schemas.simulation import (
    ScenarioResponse,
    SimulationParamsRequest,
    SimulationRecordResponse,
    SimulationResultResponse,
    SimulationSummaryResponse,
)
from app.services.artifact_store import LocalArtifactStore
from app.services.simulation_store import SimulationRecord, SimulationStore
from simulation_core.defaults import DEFAULT_SCENARIOS
from simulation_core.models import SimulationParameters
from simulation_core.simulation import export_result, run_simulation

router = APIRouter(prefix="/api/v1", tags=["simulation"])


def _build_record_response(record: SimulationRecord) -> SimulationRecordResponse:
    summary = None
    if record.result is not None:
        summary = SimulationSummaryResponse(**record.result.summary.to_dict())

    return SimulationRecordResponse(
        simulation_id=record.simulation_id,
        status=record.status,
        created_at=record.created_at,
        parameters=SimulationParamsRequest(**record.parameters.to_dict()),
        artifacts=record.artifacts,
        summary=summary,
        error_message=record.error_message,
        result_url=f"/api/v1/simulations/{record.simulation_id}/result",
    )


def _build_result_response(record: SimulationRecord) -> SimulationResultResponse:
    if record.result is None:
        raise HTTPException(status_code=404, detail="Simulation result is not ready.")

    base_payload = _build_record_response(record).model_dump()
    base_payload["event_log"] = record.result.event_log
    base_payload["patient_summary"] = record.result.patient_summary
    return SimulationResultResponse(**base_payload)


def _artifact_urls(simulation_id: str) -> dict[str, str]:
    return {
        "result.json": f"/api/v1/simulations/{simulation_id}/artifacts/result.json",
        "event_log.json": f"/api/v1/simulations/{simulation_id}/artifacts/event_log.json",
        "patient_summary.json": f"/api/v1/simulations/{simulation_id}/artifacts/patient_summary.json",
        "event_log.csv": f"/api/v1/simulations/{simulation_id}/artifacts/event_log.csv",
        "patient_summary.csv": f"/api/v1/simulations/{simulation_id}/artifacts/patient_summary.csv",
        "strategy_comparison_report.csv": (
            f"/api/v1/simulations/{simulation_id}/artifacts/strategy_comparison_report.csv"
        ),
    }


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/scenarios", response_model=list[ScenarioResponse])
def list_scenarios() -> list[ScenarioResponse]:
    return [ScenarioResponse(**item) for item in DEFAULT_SCENARIOS]


@router.post("/simulations", response_model=SimulationResultResponse)
def create_simulation(
    payload: SimulationParamsRequest,
    request: Request,
) -> SimulationResultResponse:
    store: SimulationStore = request.app.state.simulation_store
    artifact_store: LocalArtifactStore = request.app.state.artifact_store

    parameters = SimulationParameters(**payload.model_dump())
    record = store.create(parameters)

    try:
        result = run_simulation(parameters)
        artifacts = _artifact_urls(record.simulation_id)
        result.artifacts.update(artifacts)
        for artifact_name in artifacts:
            artifact_store.save(record.simulation_id, artifact_name, export_result(result, artifact_name))
        completed = store.complete(record.simulation_id, result, artifacts)
        return _build_result_response(completed)
    except Exception as exc:
        store.fail(record.simulation_id, str(exc))
        raise HTTPException(status_code=500, detail="Simulation failed to complete.") from exc


@router.get("/simulations/{simulation_id}", response_model=SimulationRecordResponse)
def get_simulation(simulation_id: str, request: Request) -> SimulationRecordResponse:
    store: SimulationStore = request.app.state.simulation_store
    record = store.get(simulation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Simulation not found.")
    return _build_record_response(record)


@router.get("/simulations/{simulation_id}/result", response_model=SimulationResultResponse)
def get_simulation_result(simulation_id: str, request: Request) -> SimulationResultResponse:
    store: SimulationStore = request.app.state.simulation_store
    record = store.get(simulation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Simulation not found.")
    if record.result is None:
        raise HTTPException(status_code=404, detail="Simulation result is not ready.")
    return _build_result_response(record)


@router.get("/simulations/{simulation_id}/artifacts/{artifact_name}")
def get_artifact(simulation_id: str, artifact_name: str, request: Request) -> FileResponse:
    store: SimulationStore = request.app.state.simulation_store
    artifact_store: LocalArtifactStore = request.app.state.artifact_store
    record = store.get(simulation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Simulation not found.")

    target_path = artifact_store.resolve(simulation_id, artifact_name)
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found.")

    media_type, _encoding = mimetypes.guess_type(target_path.name)
    return FileResponse(target_path, media_type=media_type or "application/octet-stream")
