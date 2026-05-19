from __future__ import annotations

from collections import deque
from typing import Literal

from .models import DoctorConsultationRequest, SimulationParameters

DoctorQueueGroup = Literal["initial", "follow_up"]


def is_initial_request_urgent(
    request: DoctorConsultationRequest,
    current_time: float,
    parameters: SimulationParameters,
) -> bool:
    wait_time = current_time - request.patient.arrival_time

    if request.patient.initial_triage_level == "Level III":
        return wait_time >= parameters.target_time_level3 - parameters.k_level3

    return wait_time >= parameters.target_time_level4 - parameters.k_level4


def pop_next_request(
    level1_queue: deque[DoctorConsultationRequest],
    level2_queue: deque[DoctorConsultationRequest],
    level3_queue: deque[DoctorConsultationRequest],
    level4_queue: deque[DoctorConsultationRequest],
    level5_queue: deque[DoctorConsultationRequest],
    follow_up_queue: deque[DoctorConsultationRequest],
    current_time: float,
    parameters: SimulationParameters,
    last_group: DoctorQueueGroup | None,
    doctor_is_senior: bool,
) -> tuple[DoctorConsultationRequest | None, DoctorQueueGroup | None]:
    urgent_request = _pop_absolute_priority(level1_queue, level2_queue, doctor_is_senior)
    if urgent_request is not None:
        return urgent_request, None

    strategy = parameters.scheduling_strategy.upper()

    if strategy == "IFP":
        request, group = _pop_initial_first(level3_queue, level4_queue, follow_up_queue)
    elif strategy == "ALT":
        request, group = _pop_alternating(level3_queue, level4_queue, follow_up_queue, last_group)
    else:
        request, group = _pop_slack_based(
            level3_queue,
            level4_queue,
            follow_up_queue,
            current_time,
            parameters,
        )

    if request is not None:
        return request, group

    if level5_queue:
        return level5_queue.popleft(), None

    return None, None


def _pop_absolute_priority(
    level1_queue: deque[DoctorConsultationRequest],
    level2_queue: deque[DoctorConsultationRequest],
    doctor_is_senior: bool,
) -> DoctorConsultationRequest | None:
    if doctor_is_senior and level1_queue:
        return level1_queue.popleft()
    if level2_queue:
        return level2_queue.popleft()
    return None


def _pop_initial_first(
    level3_queue: deque[DoctorConsultationRequest],
    level4_queue: deque[DoctorConsultationRequest],
    follow_up_queue: deque[DoctorConsultationRequest],
) -> tuple[DoctorConsultationRequest | None, DoctorQueueGroup | None]:
    if level3_queue:
        return level3_queue.popleft(), "initial"
    if level4_queue:
        return level4_queue.popleft(), "initial"
    if follow_up_queue:
        return follow_up_queue.popleft(), "follow_up"
    return None, None


def _pop_alternating(
    level3_queue: deque[DoctorConsultationRequest],
    level4_queue: deque[DoctorConsultationRequest],
    follow_up_queue: deque[DoctorConsultationRequest],
    last_group: DoctorQueueGroup | None,
) -> tuple[DoctorConsultationRequest | None, DoctorQueueGroup | None]:
    initial_available = bool(level3_queue or level4_queue)
    follow_up_available = bool(follow_up_queue)

    if initial_available and follow_up_available:
        preferred_group: DoctorQueueGroup = "follow_up" if last_group == "initial" else "initial"
        request = _pop_from_group(level3_queue, level4_queue, follow_up_queue, preferred_group)
        if request is not None:
            return request, preferred_group

        fallback_group: DoctorQueueGroup = "initial" if preferred_group == "follow_up" else "follow_up"
        request = _pop_from_group(level3_queue, level4_queue, follow_up_queue, fallback_group)
        if request is not None:
            return request, fallback_group

    if initial_available:
        return _pop_from_group(level3_queue, level4_queue, follow_up_queue, "initial"), "initial"

    if follow_up_available:
        return _pop_from_group(level3_queue, level4_queue, follow_up_queue, "follow_up"), "follow_up"

    return None, None


def _pop_slack_based(
    level3_queue: deque[DoctorConsultationRequest],
    level4_queue: deque[DoctorConsultationRequest],
    follow_up_queue: deque[DoctorConsultationRequest],
    current_time: float,
    parameters: SimulationParameters,
) -> tuple[DoctorConsultationRequest | None, DoctorQueueGroup | None]:
    if level3_queue and is_initial_request_urgent(level3_queue[0], current_time, parameters):
        return level3_queue.popleft(), "initial"

    if level4_queue and is_initial_request_urgent(level4_queue[0], current_time, parameters):
        return level4_queue.popleft(), "initial"

    if follow_up_queue:
        return follow_up_queue.popleft(), "follow_up"

    if level3_queue:
        return level3_queue.popleft(), "initial"

    if level4_queue:
        return level4_queue.popleft(), "initial"

    return None, None


def _pop_from_group(
    level3_queue: deque[DoctorConsultationRequest],
    level4_queue: deque[DoctorConsultationRequest],
    follow_up_queue: deque[DoctorConsultationRequest],
    group: DoctorQueueGroup,
) -> DoctorConsultationRequest | None:
    if group == "follow_up":
        return follow_up_queue.popleft() if follow_up_queue else None

    if level3_queue:
        return level3_queue.popleft()
    if level4_queue:
        return level4_queue.popleft()
    return None
