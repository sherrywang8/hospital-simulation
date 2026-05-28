from __future__ import annotations

import csv
import io
import math
import random
from typing import Any

import simpy

from .defaults import (
    EVENT_ADMIT,
    EVENT_BOARDING,
    DEFAULT_CT_DURATION,
    DEFAULT_CT_EXAM_PROBABILITY,
    DEFAULT_CT_REPORT_DELAY,
    DEFAULT_FOLLOW_UP_CONSULT_MAX,
    DEFAULT_FOLLOW_UP_CONSULT_MEAN,
    DEFAULT_FOLLOW_UP_CONSULT_MIN,
    DEFAULT_LAB_DURATION,
    DEFAULT_LAB_EXAM_PROBABILITY,
    DEFAULT_LAB_REPORT_DELAY,
    DEFAULT_LEVEL3_SHARE,
    DEFAULT_LEVEL4_SHARE,
    DEFAULT_MEDICATION_MIN,
    DEFAULT_MEDICATION_MAX,
    DEFAULT_MEDICATION_MODE,
    DEFAULT_TRIAGE_MAX,
    DEFAULT_TRIAGE_MIN,
    DEFAULT_TRIAGE_MODE,
    DEFAULT_ULTRASOUND_DURATION,
    DEFAULT_ULTRASOUND_EXAM_PROBABILITY,
    DEFAULT_ULTRASOUND_REPORT_DELAY,
    DEFAULT_XRAY_DURATION,
    DEFAULT_XRAY_EXAM_PROBABILITY,
    DEFAULT_XRAY_REPORT_DELAY,
    EVENT_DISCHARGE,
    EVENT_END_CT,
    EVENT_END_INITIAL,
    EVENT_END_LAB,
    EVENT_END_RETURN,
    EVENT_END_TRIAGE,
    EVENT_END_ULTRASOUND,
    EVENT_END_XRAY,
    EVENT_QUEUE_EXAM,
    EVENT_QUEUE_INITIAL,
    EVENT_QUEUE_RETURN,
    EVENT_QUEUE_TRIAGE,
    EVENT_OBSERVATION,
    EVENT_REPORT_READY_CT,
    EVENT_REPORT_READY_LAB,
    EVENT_REPORT_READY_ULTRASOUND,
    EVENT_REPORT_READY_XRAY,
    EVENT_START_CT,
    EVENT_START_INITIAL,
    EVENT_START_LAB,
    EVENT_START_RETURN,
    EVENT_START_TRIAGE,
    EVENT_START_ULTRASOUND,
    EVENT_START_XRAY,
    PAPER_ARRIVAL_RATES_BY_DAY,
    TW_SHARE_L1,
    TW_SHARE_L2,
    TW_SHARE_L3,
    TW_SHARE_L4,
    TW_SHARE_L5,
)
from .hospital_env import Hospital
from .models import (
    DoctorConsultationRequest,
    PatientRecord,
    SimulationParameters,
    SimulationResult,
    SimulationSummary,
    enrich_event_log,
    extract_all_logs,
    extract_patient_summaries,
    mean_or_zero,
    percentile,
)


EXAM_SEQUENCE = (
    {
        "key": "ct",
        "capacity_field": "num_ct",
        "probability": DEFAULT_CT_EXAM_PROBABILITY,
        "resource_attr": "ct_scanner",
        "resource_name": "CT",
        "busy_key": "ct",
        "duration": DEFAULT_CT_DURATION,
        "report_delay": DEFAULT_CT_REPORT_DELAY,
        "start_event": EVENT_START_CT,
        "end_event": EVENT_END_CT,
        "report_event": EVENT_REPORT_READY_CT,
    },
    {
        "key": "xray",
        "capacity_field": "num_xray",
        "probability": DEFAULT_XRAY_EXAM_PROBABILITY,
        "resource_attr": "xray",
        "resource_name": "Xray",
        "busy_key": "xray",
        "duration": DEFAULT_XRAY_DURATION,
        "report_delay": DEFAULT_XRAY_REPORT_DELAY,
        "start_event": EVENT_START_XRAY,
        "end_event": EVENT_END_XRAY,
        "report_event": EVENT_REPORT_READY_XRAY,
    },
    {
        "key": "lab",
        "capacity_field": "num_lab",
        "probability": DEFAULT_LAB_EXAM_PROBABILITY,
        "resource_attr": "lab",
        "resource_name": "Lab",
        "busy_key": "lab",
        "duration": DEFAULT_LAB_DURATION,
        "report_delay": DEFAULT_LAB_REPORT_DELAY,
        "start_event": EVENT_START_LAB,
        "end_event": EVENT_END_LAB,
        "report_event": EVENT_REPORT_READY_LAB,
    },
    {
        "key": "ultrasound",
        "capacity_field": "num_ultrasound",
        "probability": DEFAULT_ULTRASOUND_EXAM_PROBABILITY,
        "resource_attr": "ultrasound",
        "resource_name": "Ultrasound",
        "busy_key": "ultrasound",
        "duration": DEFAULT_ULTRASOUND_DURATION,
        "report_delay": DEFAULT_ULTRASOUND_REPORT_DELAY,
        "start_event": EVENT_START_ULTRASOUND,
        "end_event": EVENT_END_ULTRASOUND,
        "report_event": EVENT_REPORT_READY_ULTRASOUND,
    },
)

PAPER_TRIAGE_LEVELS = ("Level III", "Level IV")
TTAS_TRIAGE_LEVELS = ("Level I", "Level II", "Level III", "Level IV", "Level V")


def sample_truncated_exponential(
    rng: random.Random,
    *,
    mean: float,
    minimum: float,
    maximum: float,
) -> float:
    rate = 1.0 / mean
    lower_cdf = 1.0 - math.exp(-rate * minimum)
    upper_cdf = 1.0 - math.exp(-rate * maximum)
    draw = rng.uniform(lower_cdf, upper_cdf)
    return -math.log1p(-draw) / rate


def sample_poisson(rng: random.Random, rate: float) -> int:
    if rate <= 0:
        return 0

    threshold = math.exp(-rate)
    count = 0
    product = 1.0

    while product > threshold:
        count += 1
        product *= rng.random()

    return count - 1


def get_arrival_rate(hour_start: float, parameters: SimulationParameters) -> float:
    day_index = int(hour_start // 1440) % 7
    hour_index = int((hour_start % 1440) // 60)
    return PAPER_ARRIVAL_RATES_BY_DAY[day_index][hour_index] * parameters.arrival_rate_multiplier


def sample_initial_triage_level(
    parameters: SimulationParameters,
    rng: random.Random,
) -> str:
    if parameters.use_taiwan_ttas:
        return rng.choices(
            TTAS_TRIAGE_LEVELS,
            weights=[TW_SHARE_L1, TW_SHARE_L2, TW_SHARE_L3, TW_SHARE_L4, TW_SHARE_L5],
            k=1,
        )[0]

    return rng.choices(
        PAPER_TRIAGE_LEVELS,
        weights=[DEFAULT_LEVEL3_SHARE, DEFAULT_LEVEL4_SHARE],
        k=1,
    )[0]


def sample_initial_consult_duration(
    *,
    triage_level: str,
    is_general: bool,
    rng: random.Random,
) -> float:
    if triage_level in ("Level I", "Level II"):
        if is_general:
            return rng.triangular(8, 30, 20)
        return rng.triangular(5, 25, 15)

    if triage_level == "Level III":
        if is_general:
            return rng.triangular(10, 35, 25)
        return rng.triangular(5, 30, 20)

    if triage_level in ("Level IV", "Level V"):
        if is_general:
            return rng.triangular(20, 45, 35)
        return rng.triangular(15, 40, 30)

    raise ValueError(f"Unsupported triage level: {triage_level}")


def select_exam_plan(parameters: SimulationParameters, rng: random.Random) -> list[dict[str, Any]]:
    if rng.random() >= parameters.exam_probability:
        return []

    available_exams = [
        exam
        for exam in EXAM_SEQUENCE
        if getattr(parameters, exam["capacity_field"]) > 0
    ]
    if not available_exams:
        return []

    selected = [
        exam
        for exam in available_exams
        if rng.random() < float(exam["probability"])
    ]
    if not selected:
        selected = [max(available_exams, key=lambda exam: float(exam["probability"]))]

    return selected


def maybe_finish_simulation(completion_state: dict[str, Any]) -> None:
    if (
        completion_state["arrivals_completed"]
        and completion_state["active_patients"] == 0
        and not completion_state["done_event"].triggered
    ):
        completion_state["done_event"].succeed()


def request_doctor_consultation(
    env: simpy.Environment,
    patient: PatientRecord,
    hospital: Hospital,
    stage: str,
    duration: float | None,
) -> Any:
    queue_event = EVENT_QUEUE_INITIAL if stage == "initial" else EVENT_QUEUE_RETURN
    patient.record_event(env.now, queue_event)
    request = DoctorConsultationRequest(
        patient=patient,
        stage=stage,
        queued_at=env.now,
        duration=duration,
        completion_event=env.event(),
    )
    hospital.enqueue_doctor_request(request)
    yield request.completion_event


def perform_triage(
    env: simpy.Environment,
    patient: PatientRecord,
    hospital: Hospital,
    rng: random.Random,
) -> Any:
    # 變更：改用統一的 nurses
    if hospital.nurses is None:
        return

    patient.record_event(env.now, EVENT_QUEUE_TRIAGE)
    with hospital.nurses.request() as req:
        yield req
        patient.record_event(env.now, EVENT_START_TRIAGE, "Nurse")
        duration = rng.triangular(DEFAULT_TRIAGE_MIN, DEFAULT_TRIAGE_MAX, DEFAULT_TRIAGE_MODE)
        yield env.timeout(duration)
        hospital.record_busy_time("nurses", duration) # 變更：紀錄到 nurses
        patient.record_event(env.now, EVENT_END_TRIAGE, "Nurse")

def perform_nursing_task(
    env: simpy.Environment,
    patient: PatientRecord,
    hospital: Hospital,
    task_name: str,
    duration: float,
) -> Any:
    # 變更：改用統一的 nurses
    if hospital.nurses is None:
        return

    patient.record_event(env.now, f"等待 ({task_name})")
    with hospital.nurses.request() as req:
        yield req
        patient.record_event(env.now, f"開始 ({task_name})", "Nurse")
        yield env.timeout(duration)
        hospital.record_busy_time("nurses", duration) # 變更：紀錄到 nurses
        patient.record_event(env.now, f"結束 ({task_name})", "Nurse")


def select_nursing_tasks(patient: PatientRecord, rng: random.Random) -> list[tuple[str, float]]:
    light_pool = [
        ("給藥/打針", 5.0),
        ("傷口護理 (Wound Care)", 3.7),
    ]
    moderate_pool = [("管路放置 (Foley/NG)", 5.7)]
    major_pool = [("協助侵入性處置 (CVC/LP)", 6.8)]

    if patient.initial_triage_level in ("Level I", "Level II"):
        treatment_pool = light_pool + moderate_pool + major_pool
        task_count_weights = [35, 40, 25]
    elif patient.initial_triage_level == "Level III":
        treatment_pool = light_pool + moderate_pool
        task_count_weights = [45, 35, 20]
    else:
        treatment_pool = light_pool
        task_count_weights = [60, 30, 10]

    num_tasks = rng.choices([1, 2, 3], weights=task_count_weights)[0]
    return rng.sample(treatment_pool, k=min(num_tasks, len(treatment_pool)))


def needs_final_reassessment(
    *,
    nursing_tasks: list[tuple[str, float]],
    exam_plan: list[dict[str, Any]],
) -> bool:
    return bool(nursing_tasks or exam_plan)


def perform_final_nursing_wrap_up(
    env: simpy.Environment,
    patient: PatientRecord,
    hospital: Hospital,
    disposition_event: str,
    rng: random.Random,
) -> Any:
    if disposition_event == EVENT_ADMIT:
        task_name = "護理紀錄與交班"
        duration = rng.uniform(2.0, 4.0)
    else:
        task_name = "護理紀錄與衛教"
        duration = rng.uniform(2.0, 4.0)

    yield from perform_nursing_task(env, patient, hospital, task_name, duration)


def determine_disposition(
    patient: PatientRecord,
    nursing_tasks: list[tuple[str, float]],
    rng: random.Random,
) -> tuple[str, float]:
    task_names = {task_name for task_name, _duration in nursing_tasks}
    has_major = "協助侵入性處置 (CVC/LP)" in task_names
    has_moderate = "管路放置 (Foley/NG)" in task_names
    has_medication = "給藥/打針" in task_names

    if has_major:
        return EVENT_ADMIT, rng.uniform(120.0, 480.0)
    if has_moderate and patient.initial_triage_level in ("Level I", "Level II", "Level III"):
        return EVENT_ADMIT, rng.uniform(60.0, 240.0)
    if has_medication:
        return EVENT_OBSERVATION, rng.uniform(30.0, 90.0)
    return EVENT_DISCHARGE, rng.uniform(5.0, 15.0)

def perform_exam(
    env: simpy.Environment,
    patient: PatientRecord,
    hospital: Hospital,
    exam: dict[str, Any],
) -> Any:
    resource = getattr(hospital, exam["resource_attr"])
    if resource is None:
        return env.now

    with resource.request() as req:
        yield req
        patient.record_event(env.now, exam["start_event"], exam["resource_name"])
        duration = float(exam["duration"])
        yield env.timeout(duration)
        hospital.record_busy_time(str(exam["busy_key"]), duration)
        patient.record_event(env.now, exam["end_event"], exam["resource_name"])

    return env.now + float(exam["report_delay"])


def doctor_worker(
    env: simpy.Environment,
    doctor_index: int,
    hospital: Hospital,
    parameters: SimulationParameters,
    rng: random.Random,
) -> Any:
    is_general = doctor_index <= parameters.num_general_doctors
    doctor_type = "General" if is_general else "Senior"
    type_index = doctor_index if is_general else doctor_index - parameters.num_general_doctors
    doctor_name = f"{doctor_type}Doctor_{type_index}"

    while True:
        if not parameters.is_doctor_active(doctor_index, env.now):
            yield env.timeout(parameters.minutes_until_doctor_status_change(doctor_index, env.now))
            continue

        request = hospital.pop_next_doctor_request(env.now, doctor_is_senior=not is_general)
        if request is None:
            wait_for = parameters.minutes_until_doctor_status_change(doctor_index, env.now)
            yield simpy.AnyOf(
                env,
                [hospital.doctor_queue_event, env.timeout(wait_for)],
            )
            continue

        if request.stage == "initial":
            start_event = EVENT_START_INITIAL
            end_event = EVENT_END_INITIAL
            duration = sample_initial_consult_duration(
                triage_level=request.patient.initial_triage_level,
                is_general=is_general,
                rng=rng,
            )
        else:
            start_event = EVENT_START_RETURN
            end_event = EVENT_END_RETURN
            duration = request.duration  # type: ignore[assignment]

        request.patient.record_event(env.now, start_event, doctor_name)
        yield env.timeout(duration)
        hospital.record_busy_time("doctors", duration)
        request.patient.record_event(env.now, end_event, doctor_name)

        if not request.completion_event.triggered:
            request.completion_event.succeed(env.now)


def patient_flow(
    env: simpy.Environment,
    patient: PatientRecord,
    hospital: Hospital,
    parameters: SimulationParameters,
    patient_rng: random.Random,
    completion_state: dict[str, Any],
) -> Any:
    try:
        yield from perform_triage(env, patient, hospital, patient_rng)
        yield from request_doctor_consultation(env, patient, hospital, "initial", None)

        nursing_tasks: list[tuple[str, float]] = []
        if patient_rng.random() < parameters.medication_probability:
            nursing_tasks = select_nursing_tasks(patient, patient_rng)
            for task_name, base_time in nursing_tasks:
                task_duration = patient_rng.uniform(base_time * 0.5, base_time * 1.5)
                yield from perform_nursing_task(env, patient, hospital, task_name, task_duration)

        exam_plan = select_exam_plan(parameters, patient_rng)
        if exam_plan:
            patient.record_event(env.now, EVENT_QUEUE_EXAM)
            report_readiness: list[tuple[float, str, str]] = []

            for exam in exam_plan:
                ready_at = yield from perform_exam(env, patient, hospital, exam)
                report_readiness.append((ready_at, str(exam["report_event"]), str(exam["resource_name"])))

            report_readiness.sort(key=lambda item: (item[0], item[1]))
            for ready_at, report_event, resource_name in report_readiness:
                if env.now < ready_at:
                    yield env.timeout(ready_at - env.now)
                patient.record_event(env.now, report_event, resource_name)

        if needs_final_reassessment(nursing_tasks=nursing_tasks, exam_plan=exam_plan):
            patient.triage_level = "複診"
            follow_up_duration = sample_truncated_exponential(
                patient_rng,
                mean=DEFAULT_FOLLOW_UP_CONSULT_MEAN,
                minimum=DEFAULT_FOLLOW_UP_CONSULT_MIN,
                maximum=DEFAULT_FOLLOW_UP_CONSULT_MAX,
            )
            yield from request_doctor_consultation(
                env,
                patient,
                hospital,
                "follow_up",
                follow_up_duration,
            )

        disposition_event, holding_time = determine_disposition(patient, nursing_tasks, patient_rng)
        if disposition_event == EVENT_ADMIT:
            patient.record_event(env.now, EVENT_BOARDING)
            yield env.timeout(holding_time)
            yield from perform_final_nursing_wrap_up(
                env, patient, hospital, disposition_event, patient_rng
            )
            patient.record_event(env.now, EVENT_ADMIT)
        elif disposition_event == EVENT_OBSERVATION:
            patient.record_event(env.now, EVENT_OBSERVATION)
            yield env.timeout(holding_time)
            yield from perform_final_nursing_wrap_up(
                env, patient, hospital, disposition_event, patient_rng
            )
            patient.record_event(env.now, EVENT_DISCHARGE)
        else:
            yield env.timeout(holding_time)
            yield from perform_final_nursing_wrap_up(
                env, patient, hospital, disposition_event, patient_rng
            )
            patient.record_event(env.now, EVENT_DISCHARGE)
        
    finally:
        completion_state["active_patients"] -= 1
        maybe_finish_simulation(completion_state)

def patient_arrival(
    env: simpy.Environment,
    hospital: Hospital,
    parameters: SimulationParameters,
    patient_list: list[PatientRecord],
    arrival_rng: random.Random,
    completion_state: dict[str, Any],
) -> Any:
    patient_id = 1
    simulation_horizon = int(parameters.simulation_time)

    for hour_start in range(0, simulation_horizon, 60):
        interval_minutes = min(60, simulation_horizon - hour_start)
        hourly_rate = get_arrival_rate(hour_start, parameters) * (interval_minutes / 60.0)
        arrivals = sample_poisson(arrival_rng, hourly_rate)
        arrival_times = sorted(
            hour_start + arrival_rng.uniform(0, interval_minutes)
            for _ in range(arrivals)
        )

        for arrival_time in arrival_times:
            if arrival_time > env.now:
                yield env.timeout(arrival_time - env.now)

            triage_level = sample_initial_triage_level(parameters, arrival_rng)
            patient = PatientRecord(
                patient_id=f"P{patient_id:04d}",
                triage_level=triage_level,
                arrival_time=env.now,
            )
            patient_list.append(patient)
            completion_state["active_patients"] += 1
            patient_rng = random.Random(arrival_rng.randrange(2**63))
            env.process(patient_flow(env, patient, hospital, parameters, patient_rng, completion_state))
            patient_id += 1

        interval_end = hour_start + interval_minutes
        if env.now < interval_end:
            yield env.timeout(interval_end - env.now)

    completion_state["arrivals_completed"] = True
    maybe_finish_simulation(completion_state)


def build_summary(
    parameters: SimulationParameters,
    hospital: Hospital,
    event_log: list[dict[str, Any]],
    patient_summary: list[dict[str, Any]],
    completed_at: float,
) -> SimulationSummary:
    waiting_times = [float(item["waiting_time"]) for item in patient_summary]
    time_in_system_values = [float(item["time_in_system"]) for item in patient_summary]
    service_times = [float(item["service_time"]) for item in patient_summary]

    utilization_capacity = {
        "doctors": parameters.doctor_capacity_minutes(completed_at),
        # 變更：改用新的動態排班加總方法
        "nurses": parameters.nurse_capacity_minutes(completed_at),
        "ct": parameters.num_ct * completed_at,
        "xray": parameters.num_xray * completed_at,
        "lab": parameters.num_lab * completed_at,
        "ultrasound": parameters.num_ultrasound * completed_at,
    }

    resource_utilization = {}
    for resource_name, busy_minutes in hospital.busy_time.items():
        denominator = utilization_capacity.get(resource_name, 0.0)
        utilization = 0.0 if denominator <= 0 else round(busy_minutes / denominator, 4)
        resource_utilization[resource_name] = utilization

    return SimulationSummary(
        total_patients=len(patient_summary),
        total_events=len(event_log),
        average_waiting_time=mean_or_zero(waiting_times),
        p95_waiting_time=percentile(waiting_times, 95),
        average_time_in_system=mean_or_zero(time_in_system_values),
        average_service_time=mean_or_zero(service_times),
        resource_utilization=resource_utilization,
    )


def run_simulation(parameters: SimulationParameters | None = None) -> SimulationResult:
    params = parameters or SimulationParameters()
    arrival_rng = random.Random(params.random_seed)

    env = simpy.Environment()
    hospital = Hospital(env, params)
    all_patients: list[PatientRecord] = []
    completion_state = {
        "active_patients": 0,
        "arrivals_completed": False,
        "done_event": env.event(),
    }

    doctor_rng = random.Random(params.random_seed + 42 if params.random_seed is not None else None)
    for doctor_index in range(1, params.max_doctors + 1):
        env.process(doctor_worker(env, doctor_index, hospital, params, doctor_rng))

    env.process(patient_arrival(env, hospital, params, all_patients, arrival_rng, completion_state))
    env.run(until=completion_state["done_event"])

    raw_logs = extract_all_logs(all_patients)
    patient_summary = extract_patient_summaries(all_patients)
    enriched_event_log = enrich_event_log(raw_logs, patient_summary)
    summary = build_summary(params, hospital, enriched_event_log, patient_summary, env.now)

    return SimulationResult(
        parameters=params,
        summary=summary,
        event_log=enriched_event_log,
        patient_summary=patient_summary,
    )


def _records_to_csv_bytes(records: list[dict[str, Any]]) -> bytes:
    if not records:
        return b""

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8-sig")


def build_strategy_comparison_rows(
    parameters: SimulationParameters,
    *,
    cached_results: dict[str, SimulationResult] | None = None,
) -> list[dict[str, Any]]:
    comparison_rows: list[dict[str, Any]] = []
    cached = cached_results or {}

    for strategy in ("SBP", "IFP", "ALT"):
        result = cached.get(strategy)
        if result is None:
            strategy_parameters = SimulationParameters(
                **{
                    **parameters.to_dict(),
                    "scheduling_strategy": strategy,
                }
            )
            result = run_simulation(strategy_parameters)

        summary = result.summary
        comparison_rows.append(
            {
                "排程策略 (Strategy)": strategy,
                "病人總數 (Total Patients)": summary.total_patients,
                "平均初診等待時間 (Avg Waiting Min)": round(summary.average_waiting_time, 2),
                "P95初診等待時間 (P95 Waiting Min)": round(summary.p95_waiting_time, 2),
                "平均總在院時間 (Avg LoS Min)": round(summary.average_time_in_system, 2),
                "平均醫療服務時間 (Avg Service Min)": round(summary.average_service_time, 2),
                "醫師總利用率 (Doctor Utilization)": (
                    f"{round(summary.resource_utilization.get('doctors', 0) * 100, 2):.2f}%"
                ),
                "護理師總利用率 (Nurse Utilization)": (
                    f"{round(summary.resource_utilization.get('nurses', 0) * 100, 2):.2f}%"
                ),
            }
        )

    return comparison_rows


def export_strategy_comparison_csv(
    parameters: SimulationParameters,
    *,
    cached_results: dict[str, SimulationResult] | None = None,
) -> bytes:
    return _records_to_csv_bytes(
        build_strategy_comparison_rows(parameters, cached_results=cached_results)
    )


def export_result(result: SimulationResult, artifact_name: str) -> bytes | dict[str, Any]:
    if artifact_name == "result.json":
        return result.to_dict()
    if artifact_name == "event_log.json":
        return {"event_log": result.event_log}
    if artifact_name == "patient_summary.json":
        return {"patient_summary": result.patient_summary}
    if artifact_name == "event_log.csv":
        return _records_to_csv_bytes(result.event_log)
    if artifact_name == "patient_summary.csv":
        return _records_to_csv_bytes(result.patient_summary)
    if artifact_name == "strategy_comparison_report.csv":
        return export_strategy_comparison_csv(
            result.parameters,
            cached_results={result.parameters.scheduling_strategy: result},
        )
    raise ValueError(f"Unsupported artifact type: {artifact_name}")
    EVENT_OBSERVATION,
