from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation_core.defaults import DEFAULT_SCENARIOS, VALID_SCHEDULING_STRATEGIES
from simulation_core.models import SimulationParameters
from simulation_core.simulation import export_result, run_simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ED simulation and export artifacts.")
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT.parent / "data" / "samples"),
        help="Directory used to store exported simulation artifacts.",
    )
    parser.add_argument(
        "--scenario",
        choices=[scenario["slug"] for scenario in DEFAULT_SCENARIOS],
        default="weekly-baseline",
        help="Preset scenario to run.",
    )
    parser.add_argument("--scheduling-strategy", choices=list(VALID_SCHEDULING_STRATEGIES))
    parser.add_argument("--num-general-doctors", type=int)
    parser.add_argument("--num-senior-doctors", type=int)
    parser.add_argument("--num-doctors-night", type=int)
    parser.add_argument("--num-senior-doctors-night", type=int)
    parser.add_argument("--num-nurses-day", type=int)
    parser.add_argument("--num-nurses-evening", type=int)
    parser.add_argument("--num-nurses-night", type=int)
    parser.add_argument("--num-ct", type=int)
    parser.add_argument("--num-xray", type=int)
    parser.add_argument("--num-lab", type=int)
    parser.add_argument("--num-ultrasound", type=int)
    parser.add_argument("--simulation-time", type=int)
    parser.add_argument("--exam-probability", type=float)
    parser.add_argument("--arrival-rate-multiplier", type=float)
    parser.add_argument("--use-taiwan-ttas", action="store_true")
    parser.add_argument("--random-seed", type=int)
    return parser.parse_args()


def resolve_parameters(args: argparse.Namespace) -> SimulationParameters:
    preset = next(item for item in DEFAULT_SCENARIOS if item["slug"] == args.scenario)
    payload = dict(preset["parameters"])

    overrides = {
        "scheduling_strategy": args.scheduling_strategy,
        "num_general_doctors": args.num_general_doctors,
        "num_senior_doctors": args.num_senior_doctors,
        "num_doctors_night": args.num_doctors_night,
        "num_senior_doctors_night": args.num_senior_doctors_night,
        "num_nurses_day": args.num_nurses_day,
        "num_nurses_evening": args.num_nurses_evening,
        "num_nurses_night": args.num_nurses_night,
        "num_ct": args.num_ct,
        "num_xray": args.num_xray,
        "num_lab": args.num_lab,
        "num_ultrasound": args.num_ultrasound,
        "simulation_time": args.simulation_time,
        "exam_probability": args.exam_probability,
        "arrival_rate_multiplier": args.arrival_rate_multiplier,
        "use_taiwan_ttas": args.use_taiwan_ttas,
        "random_seed": args.random_seed,
    }
    for key, value in overrides.items():
        if value is not None:
            payload[key] = value

    return SimulationParameters(**payload)


def write_payload(output_path: Path, payload: bytes | dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        output_path.write_bytes(payload)
    else:
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def main() -> int:
    args = parse_args()
    parameters = resolve_parameters(args)
    result = run_simulation(parameters)

    output_dir = Path(args.output_dir).resolve()
    scenario_dir = output_dir / args.scenario
    scenario_dir.mkdir(parents=True, exist_ok=True)

    artifacts = [
        "result.json",
        "event_log.json",
        "patient_summary.json",
        "event_log.csv",
        "patient_summary.csv",
        "strategy_comparison_report.csv",
    ]
    for artifact_name in artifacts:
        write_payload(scenario_dir / artifact_name, export_result(result, artifact_name))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
