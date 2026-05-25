from __future__ import annotations

import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app.main import create_app


def make_artifact_root() -> Path:
    base = PROJECT_ROOT / ".test-artifacts"
    base.mkdir(parents=True, exist_ok=True)
    target = base / uuid4().hex
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_healthcheck():
    artifact_root = make_artifact_root()
    try:
        client = TestClient(create_app(artifact_root=artifact_root))

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    finally:
        shutil.rmtree(artifact_root, ignore_errors=True)


def test_create_simulation_returns_result():
    artifact_root = make_artifact_root()
    try:
        client = TestClient(create_app(artifact_root=artifact_root))

        response = client.post(
            "/api/v1/simulations",
            json={
                "scheduling_strategy": "SBP",
                "num_general_doctors": 3,
                "num_senior_doctors": 2,
                "num_doctors_night": 3,
                "num_nurses": 3,
                "num_ct": 1,
                "num_xray": 1,
                "num_lab": 1,
                "num_ultrasound": 1,
                "simulation_time": 180,
                "exam_probability": 0.6,
                "arrival_rate_multiplier": 1.0,
                "use_taiwan_ttas": True,
                "random_seed": 7,
            },
        )

        payload = response.json()

        assert response.status_code == 200
        assert payload["status"] == "completed"
        assert payload["summary"]["total_patients"] > 0
        assert payload["summary"]["resource_utilization"]["nurses"] >= 0
        assert payload["summary"]["resource_utilization"]["ultrasound"] >= 0
        assert payload["parameters"]["use_taiwan_ttas"] is True
        assert payload["event_log"]
        assert "event_log.csv" in payload["artifacts"]
        assert "patient_summary.csv" in payload["artifacts"]
    finally:
        shutil.rmtree(artifact_root, ignore_errors=True)


def test_create_simulation_exports_json_and_csv_artifacts():
    artifact_root = make_artifact_root()
    try:
        client = TestClient(create_app(artifact_root=artifact_root))

        response = client.post(
            "/api/v1/simulations",
            json={
                "scheduling_strategy": "SBP",
                "num_general_doctors": 3,
                "num_senior_doctors": 2,
                "num_doctors_night": 3,
                "num_nurses": 3,
                "num_ct": 1,
                "num_xray": 1,
                "num_lab": 1,
                "num_ultrasound": 1,
                "simulation_time": 180,
                "exam_probability": 0.6,
                "arrival_rate_multiplier": 1.0,
                "use_taiwan_ttas": True,
                "random_seed": 7,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        simulation_id = payload["simulation_id"]

        json_response = client.get(f"/api/v1/simulations/{simulation_id}/artifacts/event_log.json")
        csv_response = client.get(f"/api/v1/simulations/{simulation_id}/artifacts/event_log.csv")
        summary_csv_response = client.get(
            f"/api/v1/simulations/{simulation_id}/artifacts/patient_summary.csv"
        )

        assert json_response.status_code == 200
        assert json_response.json()["event_log"]
        assert csv_response.status_code == 200
        assert csv_response.content.startswith(b"\xef\xbb\xbf")
        assert "event_type" in csv_response.content.decode("utf-8-sig").splitlines()[0]
        assert summary_csv_response.status_code == 200
        assert "patient_id" in summary_csv_response.content.decode("utf-8-sig").splitlines()[0]
    finally:
        shutil.rmtree(artifact_root, ignore_errors=True)


def test_create_app_reads_artifact_root_from_env(monkeypatch: pytest.MonkeyPatch):
    artifact_root = make_artifact_root()
    try:
        monkeypatch.setenv("SIMULATION_ARTIFACT_ROOT", str(artifact_root))

        app = create_app()

        assert app.state.artifact_store.base_path == artifact_root
    finally:
        shutil.rmtree(artifact_root, ignore_errors=True)
