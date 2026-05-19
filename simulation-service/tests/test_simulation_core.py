from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation_core import SimulationParameters, export_result, run_simulation
from simulation_core.defaults import (
    EVENT_ARRIVAL,
    EVENT_END_TRIAGE,
    EVENT_QUEUE_TRIAGE,
    EVENT_START_INITIAL,
    EVENT_START_TRIAGE,
)
from simulation_core.models import DoctorConsultationRequest, PatientRecord
from simulation_core.scheduler import pop_next_request


def test_run_simulation_returns_records():
    result = run_simulation(SimulationParameters(simulation_time=180, random_seed=7))

    assert result.summary.total_patients > 0
    assert result.summary.total_events == len(result.event_log)
    assert result.event_log[0]["event_type"] == EVENT_ARRIVAL
    assert "waiting_time" in result.patient_summary[0]
    assert "follow_up_waiting_time" in result.patient_summary[0]


def test_doctor_shift_schedule_matches_paper():
    parameters = SimulationParameters()

    assert parameters.doctor_capacity_at(0) == 3
    assert parameters.doctor_capacity_at(7 * 60) == 5
    assert parameters.doctor_capacity_at(22 * 60) == 3
    assert parameters.doctor_capacity_minutes(24 * 60) == 6120.0


def test_export_result_supports_json_and_csv():
    result = run_simulation(SimulationParameters(simulation_time=180, random_seed=7))

    json_payload = export_result(result, "result.json")
    csv_payload = export_result(result, "event_log.csv")

    assert isinstance(json_payload, dict)
    assert "summary" in json_payload
    assert isinstance(csv_payload, bytes)
    assert csv_payload.startswith(b"\xef\xbb\xbf")


def test_patient_cohort_stays_stable_across_strategies():
    sbp = run_simulation(
        SimulationParameters(simulation_time=720, random_seed=7, scheduling_strategy="SBP")
    )
    alt = run_simulation(
        SimulationParameters(simulation_time=720, random_seed=7, scheduling_strategy="ALT")
    )

    sbp_cohort = [
        (item["patient_id"], item["triage_level"], item["arrival_clock"])
        for item in sbp.patient_summary
    ]
    alt_cohort = [
        (item["patient_id"], item["triage_level"], item["arrival_clock"])
        for item in alt.patient_summary
    ]

    assert sbp_cohort == alt_cohort


def test_paper_mode_only_generates_level3_and_level4():
    result = run_simulation(
        SimulationParameters(
            simulation_time=720,
            random_seed=7,
            scheduling_strategy="SBP",
            use_taiwan_ttas=False,
        )
    )

    triage_levels = {item["triage_level"] for item in result.patient_summary}

    assert triage_levels <= {"Level III", "Level IV"}


def test_ttas_mode_generates_all_five_levels_with_high_volume():
    result = run_simulation(
        SimulationParameters(
            simulation_time=1440,
            random_seed=7,
            exam_probability=0.0,
            arrival_rate_multiplier=3.0,
            use_taiwan_ttas=True,
        )
    )

    triage_levels = {item["triage_level"] for item in result.patient_summary}

    assert triage_levels == {"Level I", "Level II", "Level III", "Level IV", "Level V"}


def test_scheduler_blocks_general_doctor_when_only_level1_waits():
    level1_queue = deque(
        [
            DoctorConsultationRequest(
                patient=PatientRecord("P0001", "Level I", 0.0),
                stage="initial",
                queued_at=0.0,
                duration=None,
                completion_event=None,
            )
        ]
    )

    request, group = pop_next_request(
        level1_queue,
        deque(),
        deque(),
        deque(),
        deque(),
        deque(),
        current_time=10.0,
        parameters=SimulationParameters(use_taiwan_ttas=True),
        last_group=None,
        doctor_is_senior=False,
    )

    assert request is None
    assert group is None


def test_scheduler_prefers_level1_and_level2_before_algorithm_zone():
    level1_queue = deque(
        [
            DoctorConsultationRequest(
                patient=PatientRecord("P0001", "Level I", 0.0),
                stage="initial",
                queued_at=0.0,
                duration=None,
                completion_event=None,
            )
        ]
    )
    level2_queue = deque(
        [
            DoctorConsultationRequest(
                patient=PatientRecord("P0002", "Level II", 1.0),
                stage="initial",
                queued_at=1.0,
                duration=None,
                completion_event=None,
            )
        ]
    )
    level3_queue = deque(
        [
            DoctorConsultationRequest(
                patient=PatientRecord("P0003", "Level III", 2.0),
                stage="initial",
                queued_at=2.0,
                duration=None,
                completion_event=None,
            )
        ]
    )

    senior_request, senior_group = pop_next_request(
        level1_queue,
        level2_queue,
        level3_queue,
        deque(),
        deque(),
        deque(),
        current_time=10.0,
        parameters=SimulationParameters(use_taiwan_ttas=True),
        last_group=None,
        doctor_is_senior=True,
    )
    general_request, general_group = pop_next_request(
        level1_queue,
        level2_queue,
        level3_queue,
        deque(),
        deque(),
        deque(),
        current_time=10.0,
        parameters=SimulationParameters(use_taiwan_ttas=True),
        last_group=None,
        doctor_is_senior=False,
    )

    assert senior_request is not None
    assert senior_request.patient.initial_triage_level == "Level I"
    assert senior_group is None
    assert general_request is not None
    assert general_request.patient.initial_triage_level == "Level II"
    assert general_group is None
    assert level3_queue


def test_scheduler_only_serves_level5_after_higher_queues_clear():
    level5_queue = deque(
        [
            DoctorConsultationRequest(
                patient=PatientRecord("P0005", "Level V", 0.0),
                stage="initial",
                queued_at=0.0,
                duration=None,
                completion_event=None,
            )
        ]
    )
    follow_up_queue = deque(
        [
            DoctorConsultationRequest(
                patient=PatientRecord("P0006", "Level III", 0.0),
                stage="follow_up",
                queued_at=0.0,
                duration=10.0,
                completion_event=None,
            )
        ]
    )

    request, group = pop_next_request(
        deque(),
        deque(),
        deque(),
        deque(),
        level5_queue,
        follow_up_queue,
        current_time=10.0,
        parameters=SimulationParameters(use_taiwan_ttas=True, scheduling_strategy="SBP"),
        last_group=None,
        doctor_is_senior=True,
    )

    assert request is not None
    assert request.stage == "follow_up"
    assert group == "follow_up"
    assert level5_queue


def test_triage_events_happen_before_initial_consult():
    result = run_simulation(
        SimulationParameters(simulation_time=180, random_seed=7, num_nurses=1)
    )

    events_by_patient = {}
    for item in result.event_log:
        events_by_patient.setdefault(item["patient_id"], []).append(item)

    assert result.summary.resource_utilization["nurses"] >= 0

    for patient_events in events_by_patient.values():
        event_types = [item["event_type"] for item in patient_events]
        if EVENT_START_INITIAL not in event_types:
            continue

        queue_index = event_types.index(EVENT_QUEUE_TRIAGE)
        start_triage_index = event_types.index(EVENT_START_TRIAGE)
        end_triage_index = event_types.index(EVENT_END_TRIAGE)
        start_initial_index = event_types.index(EVENT_START_INITIAL)

        assert queue_index < start_triage_index < end_triage_index < start_initial_index
