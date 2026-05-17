from __future__ import annotations

import sys
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
