from __future__ import annotations

# Kim (2024) Table 4: Doctor Experience Levels
DEFAULT_NUM_GENERAL_DOCTORS = 3
DEFAULT_NUM_SENIOR_DOCTORS = 2
DEFAULT_NUM_DOCTORS_NIGHT = 3
DEFAULT_NUM_NURSES = 3
DEFAULT_NUM_CT = 1
DEFAULT_NUM_XRAY = 1
DEFAULT_NUM_LAB = 1
DEFAULT_NUM_ULTRASOUND = 1

DEFAULT_EXAM_PROBABILITY = 0.60
DEFAULT_ARRIVAL_RATE_MULTIPLIER = 1.0
DEFAULT_SCHEDULING_STRATEGY = "SBP"
VALID_SCHEDULING_STRATEGIES = ("IFP", "ALT", "SBP")

DEFAULT_TARGET_TIME_LEVEL3 = 30.0
DEFAULT_TARGET_TIME_LEVEL4 = 120.0
DEFAULT_K_LEVEL3 = 13.1
DEFAULT_K_LEVEL4 = 2.1

DEFAULT_LEVEL3_SHARE = 0.25
DEFAULT_LEVEL4_SHARE = 0.75

DEFAULT_INITIAL_CONSULT_MEAN = 9.0
DEFAULT_INITIAL_CONSULT_MIN = 5.0
DEFAULT_INITIAL_CONSULT_MAX = 15.0

DEFAULT_TRIAGE_MIN = 3.0
DEFAULT_TRIAGE_MODE = 7.0
DEFAULT_TRIAGE_MAX = 10.0

DEFAULT_FOLLOW_UP_CONSULT_MEAN = 15.0
DEFAULT_FOLLOW_UP_CONSULT_MIN = 5.0
DEFAULT_FOLLOW_UP_CONSULT_MAX = 25.0

DEFAULT_LAB_EXAM_PROBABILITY = 0.92
DEFAULT_ULTRASOUND_EXAM_PROBABILITY = 0.22
DEFAULT_XRAY_EXAM_PROBABILITY = 0.29
DEFAULT_CT_EXAM_PROBABILITY = 0.55

DEFAULT_LAB_DURATION = 1.19
DEFAULT_ULTRASOUND_DURATION = 6.58
DEFAULT_XRAY_DURATION = 3.99
DEFAULT_CT_DURATION = 2.45

DEFAULT_LAB_REPORT_DELAY = 20.0
DEFAULT_ULTRASOUND_REPORT_DELAY = 0.0
DEFAULT_XRAY_REPORT_DELAY = 30.0
DEFAULT_CT_REPORT_DELAY = 30.0

DEFAULT_SIMULATION_TIME = 60 * 24 * 7
DEFAULT_RANDOM_SEED = 7

# Table 2 from the paper, arranged as Monday-Sunday rows with 24 hourly rates.
PAPER_ARRIVAL_RATES_BY_DAY: tuple[tuple[float, ...], ...] = (
    (
        7.84,
        5.79,
        4.94,
        3.70,
        2.19,
        4.30,
        6.78,
        8.83,
        15.23,
        21.59,
        21.71,
        17.53,
        15.55,
        18.26,
        20.87,
        18.28,
        17.31,
        16.28,
        16.87,
        22.61,
        23.05,
        17.53,
        12.49,
        7.52,
    ),
    (
        7.50,
        5.37,
        4.50,
        3.33,
        1.83,
        3.58,
        6.39,
        8.23,
        14.95,
        21.26,
        21.44,
        17.11,
        15.18,
        17.93,
        20.76,
        18.14,
        17.14,
        16.10,
        16.46,
        22.47,
        22.81,
        17.23,
        12.31,
        7.23,
    ),
    (
        7.51,
        5.38,
        4.51,
        3.34,
        1.81,
        3.59,
        6.40,
        8.17,
        14.93,
        21.24,
        21.43,
        17.12,
        15.17,
        17.94,
        20.77,
        18.15,
        17.15,
        16.11,
        16.44,
        22.46,
        22.80,
        17.24,
        12.30,
        7.21,
    ),
    (
        7.49,
        5.35,
        4.50,
        3.30,
        1.80,
        3.54,
        6.37,
        8.18,
        14.90,
        21.23,
        21.45,
        17.11,
        15.18,
        17.92,
        20.75,
        18.13,
        17.13,
        16.08,
        16.43,
        22.43,
        22.79,
        17.21,
        12.29,
        7.22,
    ),
    (
        7.49,
        5.36,
        4.49,
        3.34,
        1.82,
        3.55,
        6.36,
        8.25,
        14.90,
        21.27,
        21.43,
        17.10,
        15.17,
        17.92,
        20.77,
        18.13,
        17.14,
        16.10,
        16.44,
        22.44,
        22.79,
        17.22,
        12.29,
        7.24,
    ),
    (
        7.13,
        5.07,
        4.31,
        3.11,
        1.68,
        3.21,
        6.08,
        7.98,
        14.49,
        20.64,
        20.65,
        16.59,
        14.73,
        17.43,
        19.97,
        17.33,
        16.47,
        15.38,
        15.97,
        21.64,
        22.44,
        16.75,
        11.83,
        7.03,
    ),
    (
        7.12,
        5.06,
        4.32,
        3.12,
        1.68,
        3.19,
        6.07,
        7.97,
        14.48,
        20.61,
        20.64,
        16.51,
        14.72,
        17.41,
        19.96,
        17.35,
        16.45,
        15.39,
        15.98,
        21.63,
        22.43,
        16.74,
        11.82,
        7.02,
    ),
)

EVENT_ARRIVAL = "抵達急診"
EVENT_QUEUE_TRIAGE = "進入檢傷佇列"
EVENT_START_TRIAGE = "開始檢傷"
EVENT_END_TRIAGE = "結束檢傷"
EVENT_QUEUE_INITIAL = "進入初診佇列"
EVENT_START_INITIAL = "開始初診"
EVENT_END_INITIAL = "結束初診"
EVENT_QUEUE_EXAM = "進入醫療檢查佇列"
EVENT_START_CT = "開始 CT 檢查"
EVENT_END_CT = "結束 CT 檢查"
EVENT_REPORT_READY_CT = "CT 報告可用"
EVENT_START_XRAY = "開始 Xray 檢查"
EVENT_END_XRAY = "結束 Xray 檢查"
EVENT_REPORT_READY_XRAY = "Xray 報告可用"
EVENT_START_LAB = "開始 Lab 檢驗"
EVENT_END_LAB = "結束 Lab 檢驗"
EVENT_REPORT_READY_LAB = "Lab 報告可用"
EVENT_START_ULTRASOUND = "開始超音波檢查"
EVENT_END_ULTRASOUND = "結束超音波檢查"
EVENT_REPORT_READY_ULTRASOUND = "超音波報告可用"
EVENT_QUEUE_RETURN = "進入複診佇列"
EVENT_START_RETURN = "開始複診"
EVENT_END_RETURN = "結束複診"
EVENT_DISCHARGE = "辦理離院"

DEFAULT_SCENARIOS = [
    {
        "slug": "weekly-baseline",
        "title": "Weekly Baseline",
        "description": "論文基準設定的 7 天 NHPP 情境，使用 SBP 與 5/5/3 醫師班表。",
        "sample_result_slug": "weekly-baseline",
        "parameters": {
            "scheduling_strategy": DEFAULT_SCHEDULING_STRATEGY,
            "num_general_doctors": DEFAULT_NUM_GENERAL_DOCTORS,
            "num_senior_doctors": DEFAULT_NUM_SENIOR_DOCTORS,
            "num_doctors_night": DEFAULT_NUM_DOCTORS_NIGHT,
            "num_nurses": DEFAULT_NUM_NURSES,
            "num_ct": DEFAULT_NUM_CT,
            "num_xray": DEFAULT_NUM_XRAY,
            "num_lab": DEFAULT_NUM_LAB,
            "num_ultrasound": DEFAULT_NUM_ULTRASOUND,
            "simulation_time": DEFAULT_SIMULATION_TIME,
            "exam_probability": DEFAULT_EXAM_PROBABILITY,
            "arrival_rate_multiplier": DEFAULT_ARRIVAL_RATE_MULTIPLIER,
            "random_seed": DEFAULT_RANDOM_SEED,
        },
    },
    {
        "slug": "baseline",
        "title": "Baseline",
        "description": "論文基準設定的 12 小時片段，適合快速檢查單日流程。",
        "sample_result_slug": "baseline",
        "parameters": {
            "scheduling_strategy": DEFAULT_SCHEDULING_STRATEGY,
            "num_general_doctors": DEFAULT_NUM_GENERAL_DOCTORS,
            "num_senior_doctors": DEFAULT_NUM_SENIOR_DOCTORS,
            "num_doctors_night": DEFAULT_NUM_DOCTORS_NIGHT,
            "num_nurses": DEFAULT_NUM_NURSES,
            "num_ct": DEFAULT_NUM_CT,
            "num_xray": DEFAULT_NUM_XRAY,
            "num_lab": DEFAULT_NUM_LAB,
            "num_ultrasound": DEFAULT_NUM_ULTRASOUND,
            "simulation_time": 60 * 12,
            "exam_probability": DEFAULT_EXAM_PROBABILITY,
            "arrival_rate_multiplier": DEFAULT_ARRIVAL_RATE_MULTIPLIER,
            "random_seed": DEFAULT_RANDOM_SEED,
        },
    },
    {
        "slug": "surge",
        "title": "Surge Load",
        "description": "把論文的 NHPP 到診率提高 15%，用來觀察高壓需求情境。",
        "sample_result_slug": "surge",
        "parameters": {
            "scheduling_strategy": DEFAULT_SCHEDULING_STRATEGY,
            "num_general_doctors": DEFAULT_NUM_GENERAL_DOCTORS,
            "num_senior_doctors": DEFAULT_NUM_SENIOR_DOCTORS,
            "num_doctors_night": DEFAULT_NUM_DOCTORS_NIGHT,
            "num_nurses": DEFAULT_NUM_NURSES,
            "num_ct": DEFAULT_NUM_CT,
            "num_xray": DEFAULT_NUM_XRAY,
            "num_lab": DEFAULT_NUM_LAB,
            "num_ultrasound": DEFAULT_NUM_ULTRASOUND,
            "simulation_time": 60 * 24,
            "exam_probability": DEFAULT_EXAM_PROBABILITY,
            "arrival_rate_multiplier": 1.15,
            "random_seed": 11,
        },
    },
    {
        "slug": "expanded-staffing",
        "title": "Expanded Staffing",
        "description": "在論文基準上增加醫師班表人力，觀察擴編後的等待改善。",
        "sample_result_slug": "expanded-staffing",
        "parameters": {
            "scheduling_strategy": DEFAULT_SCHEDULING_STRATEGY,
            "num_general_doctors": 4,
            "num_senior_doctors": 2,
            "num_doctors_night": 4,
            "num_nurses": DEFAULT_NUM_NURSES,
            "num_ct": DEFAULT_NUM_CT,
            "num_xray": DEFAULT_NUM_XRAY,
            "num_lab": DEFAULT_NUM_LAB,
            "num_ultrasound": DEFAULT_NUM_ULTRASOUND,
            "simulation_time": 60 * 12,
            "exam_probability": DEFAULT_EXAM_PROBABILITY,
            "arrival_rate_multiplier": DEFAULT_ARRIVAL_RATE_MULTIPLIER,
            "random_seed": 13,
        },
    },
]
