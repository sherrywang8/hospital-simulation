from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from simulation_core.defaults import (
    DEFAULT_ARRIVAL_RATE_MULTIPLIER,
    DEFAULT_EXAM_PROBABILITY,
    DEFAULT_NUM_CT,
    DEFAULT_NUM_DOCTORS_NIGHT,
    DEFAULT_NUM_GENERAL_DOCTORS,
    DEFAULT_NUM_LAB,
    DEFAULT_NUM_NURSES,
    DEFAULT_NUM_SENIOR_DOCTORS,
    DEFAULT_NUM_SENIOR_DOCTORS_NIGHT,
    DEFAULT_NUM_ULTRASOUND,
    DEFAULT_NUM_XRAY,
    DEFAULT_RANDOM_SEED,
    DEFAULT_SCHEDULING_STRATEGY,
    DEFAULT_SIMULATION_TIME,
)


class SimulationParamsRequest(BaseModel):
    scheduling_strategy: Literal["IFP", "ALT", "SBP"] = Field(default=DEFAULT_SCHEDULING_STRATEGY)
    num_general_doctors: int = Field(default=DEFAULT_NUM_GENERAL_DOCTORS, ge=1, le=32)
    num_senior_doctors: int = Field(default=DEFAULT_NUM_SENIOR_DOCTORS, ge=0, le=32)
    num_doctors_night: int = Field(default=DEFAULT_NUM_DOCTORS_NIGHT, ge=1, le=32)
    num_senior_doctors_night: int = Field(default=DEFAULT_NUM_SENIOR_DOCTORS_NIGHT, ge=0, le=32)
    num_nurses: int = Field(default=DEFAULT_NUM_NURSES, ge=0, le=32)
    num_ct: int = Field(default=DEFAULT_NUM_CT, ge=0, le=16)
    num_xray: int = Field(default=DEFAULT_NUM_XRAY, ge=0, le=16)
    num_lab: int = Field(default=DEFAULT_NUM_LAB, ge=0, le=32)
    num_ultrasound: int = Field(default=DEFAULT_NUM_ULTRASOUND, ge=0, le=16)
    simulation_time: int = Field(default=DEFAULT_SIMULATION_TIME, ge=60, le=60 * 24 * 30)
    exam_probability: float = Field(default=DEFAULT_EXAM_PROBABILITY, ge=0.0, le=1.0)
    arrival_rate_multiplier: float = Field(default=DEFAULT_ARRIVAL_RATE_MULTIPLIER, ge=0.1, le=3.0)
    use_taiwan_ttas: bool = Field(default=False)
    random_seed: int | None = Field(default=DEFAULT_RANDOM_SEED)

    @model_validator(mode="after")
    def _validate_night_composition(self) -> "SimulationParamsRequest":
        if self.num_senior_doctors_night > self.num_doctors_night:
            raise ValueError("num_senior_doctors_night 不能超過 num_doctors_night")
        if self.num_senior_doctors_night > self.num_senior_doctors:
            raise ValueError("num_senior_doctors_night 不能超過總資深醫師人數 num_senior_doctors")
        return self


class ScenarioResponse(BaseModel):
    slug: str
    title: str
    description: str
    sample_result_slug: str
    parameters: SimulationParamsRequest


class SimulationSummaryResponse(BaseModel):
    total_patients: int
    total_events: int
    average_waiting_time: float
    p95_waiting_time: float
    average_time_in_system: float
    average_service_time: float
    resource_utilization: dict[str, float]


class SimulationRecordResponse(BaseModel):
    simulation_id: str
    status: Literal["queued", "completed", "failed"]
    created_at: datetime
    parameters: SimulationParamsRequest
    artifacts: dict[str, str] = Field(default_factory=dict)
    summary: SimulationSummaryResponse | None = None
    error_message: str | None = None
    result_url: str | None = None


class SimulationResultResponse(SimulationRecordResponse):
    event_log: list[dict[str, Any]] = Field(default_factory=list)
    patient_summary: list[dict[str, Any]] = Field(default_factory=list)
