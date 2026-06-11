from __future__ import annotations

import csv
from statistics import mean, stdev
from pathlib import Path

from simulation_core.models import SimulationParameters
from simulation_core.simulation import run_simulation


TARGET_LEVEL3 = 30.0
TARGET_LEVEL4 = 120.0

# 小版測試建議先用 3 個 seed；確認沒問題後再改成 list(range(7, 17))
SEEDS = [7, 8, 9]
# SEEDS = list(range(7, 17))  # 7~16，共 10 次，正式一點再打開

# 粗略搜尋範圍
K3_VALUES = range(0, 31, 2)     # 0, 2, 4, ... 30
K4_VALUES = range(0, 121, 10)   # 0, 10, 20, ... 120
# 若要跑比較細，再改成：
# K4_VALUES = range(0, 121, 5)

# 醫師人力敏感度分析：每個情境覆寫醫師人力參數，其餘維持同一組設定
DOCTOR_STAFFING_SCENARIOS = [
    {
        "scenario_name": "baseline",
        "num_general_doctors": 5,
        "num_senior_doctors": 3,
        "num_doctors_night": 5,
        "num_senior_doctors_night": 2,
    },
    {
        "scenario_name": "add_1_day_general_doctor",
        "num_general_doctors": 6,
        "num_senior_doctors": 3,
        "num_doctors_night": 5,
        "num_senior_doctors_night": 2,
    },
    {
        "scenario_name": "add_1_night_doctor",
        "num_general_doctors": 5,
        "num_senior_doctors": 3,
        "num_doctors_night": 6,
        "num_senior_doctors_night": 2,
    },
    {
        "scenario_name": "add_1_day_general_and_1_night_doctor",
        "num_general_doctors": 6,
        "num_senior_doctors": 3,
        "num_doctors_night": 6,
        "num_senior_doctors_night": 2,
    },
]


def calculate_level_metrics(result):
    """
    從 patient_summary 計算 Level III / Level IV 等待時間與服務水準。
    waiting_time = 初診等待時間。
    service_level = 未超過目標等待時間的比例。
    """
    rows = result.patient_summary

    level3_waits = [
        float(row["waiting_time"])
        for row in rows
        if row["triage_level"] == "Level III"
    ]

    level4_waits = [
        float(row["waiting_time"])
        for row in rows
        if row["triage_level"] == "Level IV"
    ]

    def service_level(waits, target):
        if not waits:
            return 0.0
        success_count = sum(1 for wait in waits if wait <= target)
        return success_count / len(waits)

    return {
        "level3_avg_wait": mean(level3_waits) if level3_waits else 0.0,
        "level4_avg_wait": mean(level4_waits) if level4_waits else 0.0,
        "level3_service_level": service_level(level3_waits, TARGET_LEVEL3),
        "level4_service_level": service_level(level4_waits, TARGET_LEVEL4),
        "level3_count": len(level3_waits),
        "level4_count": len(level4_waits),
    }


def evaluate_k_pair(k3: float, k4: float, scenario: dict):
    """
    同一組 k3 / k4 跑多個 seed，降低隨機波動。
    scenario 提供該情境的 scenario_name 與醫師人力覆寫參數。
    """
    scenario_name = scenario["scenario_name"]

    avg_waits = []
    p95_waits = []
    avg_los = []
    doctor_utils = []
    nurse_utils = []
    level3_service_levels = []
    level4_service_levels = []
    level3_avg_waits = []
    level4_avg_waits = []

    for seed in SEEDS:
        params = SimulationParameters(
            scheduling_strategy="SBP",
            target_time_level3=TARGET_LEVEL3,
            target_time_level4=TARGET_LEVEL4,
            k_level3=float(k3),
            k_level4=float(k4),
            use_taiwan_ttas=True,
            random_seed=seed,

            num_general_doctors=scenario["num_general_doctors"],
            num_senior_doctors=scenario["num_senior_doctors"],
            num_doctors_night=scenario["num_doctors_night"],
            num_senior_doctors_night=scenario["num_senior_doctors_night"],
        )

        result = run_simulation(params)
        summary = result.summary
        level_metrics = calculate_level_metrics(result)

        avg_waits.append(float(summary.average_waiting_time))
        p95_waits.append(float(summary.p95_waiting_time))
        avg_los.append(float(summary.average_time_in_system))
        doctor_utils.append(float(summary.resource_utilization.get("doctors", 0.0)))
        nurse_utils.append(float(summary.resource_utilization.get("nurses", 0.0)))

        level3_service_levels.append(level_metrics["level3_service_level"])
        level4_service_levels.append(level_metrics["level4_service_level"])
        level3_avg_waits.append(level_metrics["level3_avg_wait"])
        level4_avg_waits.append(level_metrics["level4_avg_wait"])

    return {
        "scenario_name": scenario_name,
        "k_level3": k3,
        "k_level4": k4,
        "replications": len(SEEDS),
        "avg_waiting_time": round(mean(avg_waits), 4),
        "p95_waiting_time": round(mean(p95_waits), 4),
        "avg_time_in_system": round(mean(avg_los), 4),
        "level3_avg_wait": round(mean(level3_avg_waits), 4),
        "level4_avg_wait": round(mean(level4_avg_waits), 4),
        "level3_service_level": round(mean(level3_service_levels), 4),
        "level4_service_level": round(mean(level4_service_levels), 4),
        "doctor_utilization": round(mean(doctor_utils), 4),
        "nurse_utilization": round(mean(nurse_utils), 4),
        "avg_waiting_time_sd": round(stdev(avg_waits), 4) if len(avg_waits) > 1 else 0.0,
    }


def main():
    rows = []

    total = len(DOCTOR_STAFFING_SCENARIOS) * len(K3_VALUES) * len(K4_VALUES)
    current = 0

    for scenario in DOCTOR_STAFFING_SCENARIOS:
        scenario_name = scenario["scenario_name"]

        for k3 in K3_VALUES:
            for k4 in K4_VALUES:
                current += 1
                print(
                    f"[{current}/{total}] "
                    f"Running scenario={scenario_name}, k3={k3}, k4={k4}..."
                )

                row = evaluate_k_pair(float(k3), float(k4), scenario)
                rows.append(row)

    rows.sort(key=lambda row: (row["scenario_name"], row["avg_waiting_time"]))

    output_path = Path("sbp_grid_search_results.csv")
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Results saved to {output_path}")

    for scenario in DOCTOR_STAFFING_SCENARIOS:
        scenario_name = scenario["scenario_name"]
        scenario_rows = [row for row in rows if row["scenario_name"] == scenario_name]

        print(f"\nTop 10 results for scenario '{scenario_name}':")
        for row in scenario_rows[:10]:
            print(row)


if __name__ == "__main__":
    main()