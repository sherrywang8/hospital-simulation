from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .defaults import (
    DEFAULT_ARRIVAL_RATE_MULTIPLIER,
    DEFAULT_EXAM_PROBABILITY,
    DEFAULT_K_LEVEL3,
    DEFAULT_K_LEVEL4,
    DEFAULT_NUM_CT,
    DEFAULT_NUM_DOCTORS_NIGHT,
    DEFAULT_NUM_GENERAL_DOCTORS,
    DEFAULT_NUM_SENIOR_DOCTORS_NIGHT,
    DEFAULT_NUM_LAB,
    DEFAULT_NUM_NURSES_DAY,       # 新增
    DEFAULT_NUM_NURSES_EVENING,   # 新增
    DEFAULT_NUM_NURSES_NIGHT,     # 新增
    DEFAULT_MEDICATION_PROBABILITY,
    DEFAULT_NUM_SENIOR_DOCTORS,
    DEFAULT_NUM_ULTRASOUND,
    DEFAULT_NUM_XRAY,
    DEFAULT_RANDOM_SEED,
    DEFAULT_SCHEDULING_STRATEGY,
    DEFAULT_SIMULATION_TIME,
    DEFAULT_TARGET_TIME_LEVEL3,
    DEFAULT_TARGET_TIME_LEVEL4,
    EVENT_ARRIVAL,
    EVENT_DISCHARGE,
    EVENT_END_RETURN,
    EVENT_QUEUE_RETURN,
    EVENT_START_INITIAL,
    EVENT_START_RETURN,
)


def _next_shift_boundary(current_time: float) -> float:
    minute_of_day = current_time % 1440
    day_start = current_time - minute_of_day
    for boundary in (7 * 60, 15 * 60, 22 * 60):
        if boundary > minute_of_day + 1e-9:
            return day_start + boundary
    return day_start + 1440 + 7 * 60


@dataclass(slots=True)
class SimulationParameters:
    scheduling_strategy: str = DEFAULT_SCHEDULING_STRATEGY
    num_general_doctors: int = DEFAULT_NUM_GENERAL_DOCTORS
    num_senior_doctors: int = DEFAULT_NUM_SENIOR_DOCTORS
    num_doctors_night: int = DEFAULT_NUM_DOCTORS_NIGHT
    num_senior_doctors_night: int = DEFAULT_NUM_SENIOR_DOCTORS_NIGHT
    num_nurses_day: int = DEFAULT_NUM_NURSES_DAY
    num_nurses_evening: int = DEFAULT_NUM_NURSES_EVENING
    num_nurses_night: int = DEFAULT_NUM_NURSES_NIGHT
    medication_probability: float = DEFAULT_MEDICATION_PROBABILITY
    num_ct: int = DEFAULT_NUM_CT
    num_xray: int = DEFAULT_NUM_XRAY
    num_lab: int = DEFAULT_NUM_LAB
    num_ultrasound: int = DEFAULT_NUM_ULTRASOUND
    simulation_time: int = DEFAULT_SIMULATION_TIME
    exam_probability: float = DEFAULT_EXAM_PROBABILITY
    arrival_rate_multiplier: float = DEFAULT_ARRIVAL_RATE_MULTIPLIER
    use_taiwan_ttas: bool = False
    target_time_level3: float = DEFAULT_TARGET_TIME_LEVEL3
    target_time_level4: float = DEFAULT_TARGET_TIME_LEVEL4
    k_level3: float = DEFAULT_K_LEVEL3
    k_level4: float = DEFAULT_K_LEVEL4
    random_seed: int | None = DEFAULT_RANDOM_SEED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def num_doctors(self) -> int:
        return self.num_general_doctors + self.num_senior_doctors

    @property
    def max_doctors(self) -> int:
        return max(self.num_doctors, self.num_doctors_night)

    @property
    def num_general_doctors_night(self) -> int:
        # 夜班一般醫師 = 夜班總人數 − 夜班資深醫師（下限為 0）
        return max(self.num_doctors_night - self.num_senior_doctors_night, 0)

    def _is_day_shift(self, current_time: float) -> bool:
        minute_of_day = int(current_time) % 1440
        return 7 * 60 <= minute_of_day < 22 * 60

    def doctor_capacity_at(self, current_time: float) -> int:
        if self._is_day_shift(current_time):
            return self.num_doctors
        return self.num_doctors_night

    def is_doctor_active(self, doctor_index: int, current_time: float) -> bool:
        is_general = doctor_index <= self.num_general_doctors
        if is_general:
            type_rank = doctor_index
            day_capacity = self.num_general_doctors
            night_capacity = self.num_general_doctors_night
        else:
            type_rank = doctor_index - self.num_general_doctors
            day_capacity = self.num_senior_doctors
            night_capacity = self.num_senior_doctors_night

        active_capacity = day_capacity if self._is_day_shift(current_time) else night_capacity
        return type_rank <= active_capacity

    def minutes_until_doctor_status_change(self, doctor_index: int, current_time: float) -> float:
        status_now = self.is_doctor_active(doctor_index, current_time)
        next_boundary = _next_shift_boundary(current_time)

        for _ in range(4):
            if self.is_doctor_active(doctor_index, next_boundary) != status_now:
                return max(next_boundary - current_time, 0.01)
            next_boundary = _next_shift_boundary(next_boundary + 0.01)

        return 1440.0

    def doctor_capacity_minutes(self, horizon: float) -> float:
        if horizon <= 0:
            return 0.0

        total = 0.0
        current_time = 0.0
        while current_time < horizon:
            next_boundary = min(_next_shift_boundary(current_time), horizon)
            total += self.doctor_capacity_at(current_time) * (next_boundary - current_time)
            current_time = next_boundary
        return round(total, 4)
    
# 新增：取得當下時間點的護理師編制人數
    def get_nurse_capacity(self, current_time: float) -> int:
        minute_of_day = int(current_time) % 1440
        # 配合 _next_shift_boundary 的時間切分[cite: 3]
        if 7 * 60 <= minute_of_day < 15 * 60:
            return self.num_nurses_day
        elif 15 * 60 <= minute_of_day < 22 * 60:
            return self.num_nurses_evening
        else:
            return self.num_nurses_night

    # 新增：計算模擬期間內護理師的總量能 (分鐘數)，用於計算稼動率
    def nurse_capacity_minutes(self, horizon: float) -> float:
        if horizon <= 0:
            return 0.0
        total = 0.0
        current_time = 0.0
        while current_time < horizon:
            next_boundary = min(_next_shift_boundary(current_time), horizon)
            total += self.get_nurse_capacity(current_time) * (next_boundary - current_time)
            current_time = next_boundary
        return round(total, 4)


@dataclass(slots=True)
class SimulationSummary:
    total_patients: int
    total_events: int
    average_waiting_time: float
    p95_waiting_time: float
    average_time_in_system: float
    average_service_time: float
    resource_utilization: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SimulationResult:
    parameters: SimulationParameters
    summary: SimulationSummary
    event_log: list[dict[str, Any]]
    patient_summary: list[dict[str, Any]]
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(
        self,
        *,
        include_event_log: bool = True,
        include_patient_summary: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "parameters": self.parameters.to_dict(),
            "summary": self.summary.to_dict(),
            "artifacts": dict(self.artifacts),
        }
        if include_event_log:
            payload["event_log"] = self.event_log
        if include_patient_summary:
            payload["patient_summary"] = self.patient_summary
        return payload


@dataclass(slots=True)
class PatientRecord:
    patient_id: str
    triage_level: str
    arrival_time: float
    event_log: list[dict[str, Any]] = field(default_factory=list)
    initial_triage_level: str = field(init=False)

    def __post_init__(self) -> None:
        self.initial_triage_level = self.triage_level
        self.record_event(self.arrival_time, EVENT_ARRIVAL, resource="Triage")

    def record_event(self, current_time: float, event_name: str, resource: str = "") -> None:
        resource_label = resource if resource else "-"
        record = {
            "patient_id": self.patient_id,
            "patient": self.patient_id,
            "triage_level": self.triage_level,
            "arrival_clock": round(self.arrival_time, 2),
            "timestamp": round(current_time, 2),
            "event": event_name,
            "event_type": event_name,
            "resource_used": resource,
            "resource": resource_label,
            "desc": (
                f"{self.patient_id} ({self.triage_level}) - {event_name}"
                if resource_label == "-"
                else f"{self.patient_id} ({self.triage_level}) - {event_name} [{resource_label}]"
            ),
        }
        self.event_log.append(record)

    def build_patient_summary(self) -> dict[str, Any]:
        arrival_clock = float(round(self.arrival_time, 2))
        initial_start_clock: float | None = None
        follow_up_queue_clock: float | None = None
        follow_up_start_clock: float | None = None
        departure_clock: float | None = None

        for log in self.event_log:
            event_name = log.get("event", "")
            event_time = float(log.get("timestamp", self.arrival_time))

            if event_name == EVENT_START_INITIAL and initial_start_clock is None:
                initial_start_clock = event_time
            elif event_name == EVENT_QUEUE_RETURN and follow_up_queue_clock is None:
                follow_up_queue_clock = event_time
            elif event_name == EVENT_START_RETURN and follow_up_start_clock is None:
                follow_up_start_clock = event_time
            elif event_name in {EVENT_END_RETURN, EVENT_DISCHARGE}:
                departure_clock = event_time

        if initial_start_clock is None:
            initial_start_clock = arrival_clock

        if departure_clock is None:
            departure_clock = max(float(log.get("timestamp", 0)) for log in self.event_log)

        waiting_time = max(0.0, initial_start_clock - arrival_clock)
        follow_up_waiting_time = 0.0
        if follow_up_queue_clock is not None and follow_up_start_clock is not None:
            follow_up_waiting_time = max(0.0, follow_up_start_clock - follow_up_queue_clock)

        service_time = max(0.0, departure_clock - initial_start_clock)
        time_in_system = max(0.0, departure_clock - arrival_clock)

        return {
            "patient_id": self.patient_id,
            "triage_level": self.initial_triage_level,
            "arrival_clock": round(arrival_clock, 2),
            "enter_facility_clock": round(initial_start_clock, 2),
            "waiting_time": round(waiting_time, 2),
            "follow_up_waiting_time": round(follow_up_waiting_time, 2),
            "total_waiting_time": round(waiting_time + follow_up_waiting_time, 2),
            "service_time": round(service_time, 2),
            "departure_clock": round(departure_clock, 2),
            "time_in_system": round(time_in_system, 2),
        }


@dataclass(slots=True)
class DoctorConsultationRequest:
    patient: PatientRecord
    stage: Literal["initial", "follow_up"]
    queued_at: float
    duration: float | None
    completion_event: Any


def extract_all_logs(patients: list[PatientRecord]) -> list[dict[str, Any]]:
    all_logs: list[dict[str, Any]] = []
    for patient in patients:
        all_logs.extend(patient.event_log)
    return sorted(all_logs, key=lambda item: float(item.get("timestamp", 0.0)))


def extract_patient_summaries(patients: list[PatientRecord]) -> list[dict[str, Any]]:
    return [patient.build_patient_summary() for patient in patients]


def enrich_event_log(
    event_log: list[dict[str, Any]],
    patient_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary_by_patient = {
        item["patient_id"]: item
        for item in patient_summaries
    }

    enriched: list[dict[str, Any]] = []
    for item in event_log:
        patient_summary = summary_by_patient.get(item["patient_id"], {})
        merged = dict(item)
        merged.update(
            {
                "enter_facility_clock": patient_summary.get("enter_facility_clock"),
                "waiting_time": patient_summary.get("waiting_time"),
                "follow_up_waiting_time": patient_summary.get("follow_up_waiting_time"),
                "total_waiting_time": patient_summary.get("total_waiting_time"),
                "service_time": patient_summary.get("service_time"),
                "departure_clock": patient_summary.get("departure_clock"),
                "time_in_system": patient_summary.get("time_in_system"),
            }
        )
        enriched.append(merged)
    return enriched


def mean_or_zero(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def percentile(values: list[float], value: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 2)

    rank = (value / 100) * (len(ordered) - 1)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = rank - lower_index
    blended = ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * weight
    return round(blended, 2)
