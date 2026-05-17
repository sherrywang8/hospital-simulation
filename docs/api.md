# API

## Endpoints

### `GET /api/v1/health`

Returns a lightweight health payload:

```json
{ "status": "ok" }
```

### `GET /api/v1/scenarios`

Returns the curated scenario list used by both the frontend and the CLI sample generator.

### `POST /api/v1/simulations`

Accepts:

```json
{
  "scheduling_strategy": "SBP",
  "num_doctors": 5,
  "num_doctors_night": 3,
  "num_nurses": 3,
  "num_ct": 1,
  "num_xray": 1,
  "num_lab": 1,
  "num_ultrasound": 1,
  "simulation_time": 720,
  "exam_probability": 0.6,
  "arrival_rate_multiplier": 1.0,
  "random_seed": 7
}
```

Returns a completed simulation payload with:

- `simulation_id`
- `status`
- `created_at`
- `parameters`
- `summary`
- `artifacts`
- `event_log`
- `patient_summary`

### `GET /api/v1/simulations/{simulation_id}`

Returns metadata and artifact URLs without re-running the simulation.

### `GET /api/v1/simulations/{simulation_id}/result`

Returns the stored full simulation payload.

### `GET /api/v1/simulations/{simulation_id}/artifacts/{artifact_name}`

Downloads one of:

- `result.json`
- `event_log.json`
- `patient_summary.json`
- `event_log.csv`
- `patient_summary.csv`
