from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from simulation_core.models import SimulationParameters, SimulationResult


SimulationStatus = Literal["queued", "completed", "failed"]


@dataclass(slots=True)
class SimulationRecord:
    simulation_id: str
    status: SimulationStatus
    created_at: datetime
    parameters: SimulationParameters
    result: SimulationResult | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None


class SimulationStore:
    def __init__(self) -> None:
        self._records: dict[str, SimulationRecord] = {}
        self._lock = Lock()

    def create(self, parameters: SimulationParameters) -> SimulationRecord:
        record = SimulationRecord(
            simulation_id=str(uuid4()),
            status="queued",
            created_at=datetime.now(timezone.utc),
            parameters=parameters,
        )
        with self._lock:
            self._records[record.simulation_id] = record
        return record

    def complete(
        self,
        simulation_id: str,
        result: SimulationResult,
        artifacts: dict[str, str],
    ) -> SimulationRecord:
        with self._lock:
            record = self._records[simulation_id]
            record.status = "completed"
            record.result = result
            record.artifacts = artifacts
            return record

    def fail(self, simulation_id: str, message: str) -> SimulationRecord:
        with self._lock:
            record = self._records[simulation_id]
            record.status = "failed"
            record.error_message = message
            return record

    def get(self, simulation_id: str) -> SimulationRecord | None:
        with self._lock:
            return self._records.get(simulation_id)
