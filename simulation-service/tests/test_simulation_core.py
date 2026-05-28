from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation_core import SimulationParameters, export_result, run_simulation
from simulation_core.defaults import (
    EVENT_ADMIT,
    EVENT_ARRIVAL,
    EVENT_DISCHARGE,
    EVENT_END_RETURN,
    EVENT_END_TRIAGE,
    EVENT_QUEUE_EXAM,
    EVENT_QUEUE_TRIAGE,
    EVENT_QUEUE_RETURN,
    EVENT_START_RETURN,
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

    assert parameters.doctor_capacity_at(0) == 5
    assert parameters.doctor_capacity_at(7 * 60) == 8
    assert parameters.doctor_capacity_at(22 * 60) == 5
    assert parameters.doctor_capacity_minutes(24 * 60) == 9900.0


def test_export_result_supports_json_and_csv():
    result = run_simulation(SimulationParameters(simulation_time=180, random_seed=7))

    json_payload = export_result(result, "result.json")
    csv_payload = export_result(result, "event_log.csv")
    comparison_payload = export_result(result, "strategy_comparison_report.csv")

    assert isinstance(json_payload, dict)
    assert "summary" in json_payload
    assert isinstance(csv_payload, bytes)
    assert csv_payload.startswith(b"\xef\xbb\xbf")
    assert isinstance(comparison_payload, bytes)
    decoded_comparison = comparison_payload.decode("utf-8-sig")
    assert "排程策略 (Strategy)" in decoded_comparison.splitlines()[0]
    assert "護理師總利用率 (Nurse Utilization)" in decoded_comparison.splitlines()[0]
    assert "SBP" in decoded_comparison
    assert "IFP" in decoded_comparison
    assert "ALT" in decoded_comparison


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
        SimulationParameters(
            simulation_time=180,
            random_seed=7,
            num_nurses_day=1,
            num_nurses_evening=1,
            num_nurses_night=1,
        )
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


def test_patient_summary_uses_final_terminal_event_after_follow_up():
    patient = PatientRecord("P9001", "Level III", 0.0)
    patient.record_event(10.0, EVENT_START_INITIAL, "Doctor")
    patient.record_event(20.0, EVENT_QUEUE_RETURN)
    patient.triage_level = "複診"
    patient.record_event(25.0, EVENT_START_RETURN, "Doctor")
    patient.record_event(35.0, EVENT_END_RETURN, "Doctor")
    patient.record_event(40.0, "開始 (給藥/打針)", "Nurse")
    patient.record_event(45.0, EVENT_DISCHARGE)

    summary = patient.build_patient_summary()

    assert summary["follow_up_waiting_time"] == 5.0
    assert summary["departure_clock"] == 45.0
    assert summary["service_time"] == 35.0
    assert summary["time_in_system"] == 45.0


def test_nursing_tasks_happen_before_follow_up():
    result = run_simulation(
        SimulationParameters(
            simulation_time=240,
            random_seed=7,
            medication_probability=1.0,
            exam_probability=1.0,
        )
    )

    found_patient_with_both = False
    events_by_patient: dict[str, list[dict[str, object]]] = {}
    for item in result.event_log:
        events_by_patient.setdefault(str(item["patient_id"]), []).append(item)

    for patient_events in events_by_patient.values():
        event_types = [str(item["event_type"]) for item in patient_events]
        nursing_indices = [
            index
            for index, event_type in enumerate(event_types)
            if event_type.startswith("開始 (")
            and event_type not in {"開始 (護理紀錄與衛教)", "開始 (護理紀錄與交班)"}
        ]
        if not nursing_indices or EVENT_START_RETURN not in event_types:
            continue

        found_patient_with_both = True
        assert max(nursing_indices) < event_types.index(EVENT_START_RETURN)

    assert found_patient_with_both


def test_major_nursing_interventions_end_in_admission():
    patient = PatientRecord("P9002", "Level II", 0.0)
    patient.record_event(8.0, EVENT_START_INITIAL, "Doctor")
    patient.record_event(18.0, EVENT_QUEUE_RETURN)
    patient.triage_level = "複診"
    patient.record_event(20.0, EVENT_START_RETURN, "Doctor")
    patient.record_event(32.0, EVENT_END_RETURN, "Doctor")
    patient.record_event(35.0, EVENT_ADMIT)

    summary = patient.build_patient_summary()

    assert summary["departure_clock"] == 35.0


def test_every_patient_has_final_nursing_wrap_up_before_terminal_event():
    result = run_simulation(
        SimulationParameters(
            simulation_time=240,
            random_seed=7,
            medication_probability=1.0,
            exam_probability=1.0,
        )
    )

    events_by_patient: dict[str, list[dict[str, object]]] = {}
    for item in result.event_log:
        events_by_patient.setdefault(str(item["patient_id"]), []).append(item)

    for patient_events in events_by_patient.values():
        event_types = [str(item["event_type"]) for item in patient_events]
        terminal_index = max(
            index
            for index, event_type in enumerate(event_types)
            if event_type in {EVENT_DISCHARGE, EVENT_ADMIT}
        )
        wrap_up_indices = [
            index
            for index, event_type in enumerate(event_types)
            if event_type in {"結束 (護理紀錄與衛教)", "結束 (護理紀錄與交班)"}
        ]

        assert wrap_up_indices
        assert max(wrap_up_indices) < terminal_index


def test_final_nursing_education_does_not_happen_before_exam_or_follow_up():
    result = run_simulation(
        SimulationParameters(
            simulation_time=240,
            random_seed=7,
            medication_probability=1.0,
            exam_probability=1.0,
        )
    )

    events_by_patient: dict[str, list[dict[str, object]]] = {}
    for item in result.event_log:
        events_by_patient.setdefault(str(item["patient_id"]), []).append(item)

    for patient_events in events_by_patient.values():
        event_types = [str(item["event_type"]) for item in patient_events]
        if "開始 (護理紀錄與衛教)" not in event_types:
            continue

        education_index = event_types.index("開始 (護理紀錄與衛教)")
        if EVENT_QUEUE_EXAM in event_types:
            assert education_index > event_types.index(EVENT_QUEUE_EXAM)
        if EVENT_START_RETURN in event_types:
            assert education_index > event_types.index(EVENT_START_RETURN)
