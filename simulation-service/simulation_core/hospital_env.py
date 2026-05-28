from __future__ import annotations

from collections import deque

import simpy

# 注意這裡多引入了 _next_shift_boundary，給動態排班計算時間用
from .models import DoctorConsultationRequest, SimulationParameters, _next_shift_boundary
from .scheduler import pop_next_request


def _build_optional_resource(env: simpy.Environment, capacity: int) -> simpy.Resource | None:
    if capacity <= 0:
        return None
    return simpy.Resource(env, capacity=capacity)
#測試

class Hospital:
    def __init__(self, env: simpy.Environment, parameters: SimulationParameters):
        self.env = env
        self.parameters = parameters

        # 1. 找出三班制中的最大人數作為 Resource 的硬體容量上限
        max_nurses = max(
            parameters.num_nurses_day, 
            parameters.num_nurses_evening, 
            parameters.num_nurses_night
        )
        self.nurses = _build_optional_resource(env, max_nurses)
        
        # 2. 啟動護理師動態排班管理員
        if self.nurses is not None:
            self.env.process(self._manage_nurse_shifts(max_nurses))

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
            "nurses": 0.0,  # 3. 將原本兩個護理師統計合併為一個
            "ct": 0.0,
            "xray": 0.0,
            "lab": 0.0,
            "ultrasound": 0.0,
        }

    def _manage_nurse_shifts(self, max_nurses: int):
        """透過預佔名額(Dummy requests)來動態控制各班別的護理師人數"""
        dummy_requests = []
        
        while True:
            current_cap = self.parameters.get_nurse_capacity(self.env.now)
            to_block = max_nurses - current_cap  # 計算這個班別需要「封鎖」幾個座位

            # 釋放名額 (例如從大夜 8 人交班給白班 16 人)
            while len(dummy_requests) > to_block:
                req = dummy_requests.pop()
                self.nurses.release(req)

            # 封鎖名額 (例如從小夜 16 人交班給大夜 8 人)
            while len(dummy_requests) < to_block:
                req = self.nurses.request()
                yield req  # 會等當下正在忙的護理師結束手邊工作才真正離線
                dummy_requests.append(req)

            # 睡覺等待直到下一次交接班的時間點
            now = self.env.now
            next_boundary = _next_shift_boundary(now)
            if next_boundary > now:
                yield self.env.timeout(next_boundary - now)
            else:
                yield self.env.timeout(0.01) # 防止卡死

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