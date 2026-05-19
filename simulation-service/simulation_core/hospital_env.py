from __future__ import annotations

from collections import deque

import simpy

from .models import DoctorConsultationRequest, SimulationParameters
from .scheduler import pop_next_request


def _build_optional_resource(env: simpy.Environment, capacity: int) -> simpy.Resource | None:
    if capacity <= 0:
        return None
    return simpy.Resource(env, capacity=capacity)


class Hospital:
    def __init__(self, env: simpy.Environment, parameters: SimulationParameters):
        self.env = env
        self.parameters = parameters

        self.nurses = _build_optional_resource(env, parameters.num_nurses)
        self.ct_scanner = _build_optional_resource(env, parameters.num_ct)
        self.xray = _build_optional_resource(env, parameters.num_xray)
        self.lab = _build_optional_resource(env, parameters.num_lab)
        self.ultrasound = _build_optional_resource(env, parameters.num_ultrasound)

        self.level1_initial_queue: deque[DoctorConsultationRequest] = deque()
        self.level2_initial_queue: deque[DoctorConsultationRequest] = deque()
        self.level3_initial_queue: deque[DoctorConsultationRequest] = deque()
        self.level4_initial_queue: deque[DoctorConsultationRequest] = deque()
        self.level5_initial_queue: deque[DoctorConsultationRequest] = deque()
        self.follow_up_queue: deque[DoctorConsultationRequest] = deque()
        self.last_doctor_group: str | None = None
        self.doctor_queue_event = env.event()

        self.busy_time: dict[str, float] = {
            "doctors": 0.0,
            "nurses": 0.0,
            "ct": 0.0,
            "xray": 0.0,
            "lab": 0.0,
            "ultrasound": 0.0,
        }

    def enqueue_doctor_request(self, request: DoctorConsultationRequest) -> None:
        if request.stage == "follow_up":
            self.follow_up_queue.append(request)
        elif request.patient.initial_triage_level == "Level I":
            self.level1_initial_queue.append(request)
        elif request.patient.initial_triage_level == "Level II":
            self.level2_initial_queue.append(request)
        elif request.patient.initial_triage_level == "Level III":
            self.level3_initial_queue.append(request)
        elif request.patient.initial_triage_level == "Level V":
            self.level5_initial_queue.append(request)
        else:
            self.level4_initial_queue.append(request)
        self._notify_doctor_queue()

    def pop_next_doctor_request(
        self,
        current_time: float,
        *,
        doctor_is_senior: bool,
    ) -> DoctorConsultationRequest | None:
        request, next_group = pop_next_request(
            self.level1_initial_queue,
            self.level2_initial_queue,
            self.level3_initial_queue,
            self.level4_initial_queue,
            self.level5_initial_queue,
            self.follow_up_queue,
            current_time,
            self.parameters,
            self.last_doctor_group,
            doctor_is_senior,
        )
        if next_group is not None:
            self.last_doctor_group = next_group
        return request

    def record_busy_time(self, resource_name: str, minutes: float) -> None:
        self.busy_time[resource_name] = round(self.busy_time.get(resource_name, 0.0) + minutes, 4)

    def _notify_doctor_queue(self) -> None:
        if not self.doctor_queue_event.triggered:
            self.doctor_queue_event.succeed()
        self.doctor_queue_event = self.env.event()
