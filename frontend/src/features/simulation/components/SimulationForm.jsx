const FIELD_CONFIG = [
  {
    key: 'scheduling_strategy',
    label: '排程策略',
    type: 'select',
    options: [
      { value: 'SBP', label: 'SBP' },
      { value: 'ALT', label: 'ALT' },
      { value: 'IFP', label: 'IFP' },
    ],
  },

  // === SBP 最佳化參數 ===
  { key: 'target_time_level3', label: 'Level III 目標等待時間', min: 0, max: 240, step: 1 },
  { key: 'target_time_level4', label: 'Level IV 目標等待時間', min: 0, max: 480, step: 1 },
  { key: 'k_level3', label: 'Level III 提前優先分鐘數 k3', min: 0, max: 120, step: 0.1 },
  { key: 'k_level4', label: 'Level IV 提前優先分鐘數 k4', min: 0, max: 240, step: 0.1 },
  // =======================

  { key: 'num_general_doctors', label: '日班一般醫師數 (Day · General)', min: 1, step: 1 },
  { key: 'num_senior_doctors', label: '日班資深醫師數 (Day · Senior)', min: 0, step: 1 },
  { key: 'num_doctors_night', label: '夜班醫師總數', min: 1, step: 1 },
  { key: 'num_senior_doctors_night', label: '夜班資深醫師數 (其餘為一般)', min: 0, step: 1 },

  // === 三班制護理師設定 ===
  { key: 'num_nurses_day', label: '護理師 白班 (Day)', min: 1, step: 1 },
  { key: 'num_nurses_evening', label: '護理師 小夜班 (Evening)', min: 1, step: 1 },
  { key: 'num_nurses_night', label: '護理師 大夜班 (Night)', min: 1, step: 1 },
  // ======================

  { key: 'medication_probability', label: '給藥/打針機率', min: 0, max: 1, step: 0.05 },
  { key: 'num_ct', label: 'CT 資源數', min: 0, step: 1 },
  { key: 'num_xray', label: 'Xray 資源數', min: 0, step: 1 },
  { key: 'num_lab', label: 'Lab 資源數', min: 0, step: 1 },
  { key: 'num_ultrasound', label: 'Ultrasound 資源數', min: 0, step: 1 },
  { key: 'simulation_time', label: '模擬分鐘數', min: 60, step: 60 },
  { key: 'exam_probability', label: '需檢查比例', min: 0, max: 1, step: 0.05 },
  { key: 'arrival_rate_multiplier', label: '到診倍率', min: 0.1, max: 3, step: 0.05 },
  { key: 'random_seed', label: '隨機種子', min: 0, step: 1 },
];

const FLOAT_FIELDS = [
  'exam_probability',
  'arrival_rate_multiplier',
  'medication_probability',
  'target_time_level3',
  'target_time_level4',
  'k_level3',
  'k_level4',
];

function parseFieldValue(field, rawValue) {
  const nextValue = FLOAT_FIELDS.includes(field.key)
    ? Number(rawValue)
    : Number.parseInt(rawValue || '0', 10);

  return Number.isNaN(nextValue) ? field.min ?? 0 : nextValue;
}

function SimulationForm({
  values,
  onFieldChange,
  onSubmit,
  disabled,
  apiAvailable,
}) {
  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="panel-eyebrow">Simulation</p>
          <h2 className="panel-title">即時模擬參數</h2>
        </div>
        <p className="panel-copy">
          這組表單目前支援 NHPP 到診、SBP/ALT/IFP 排程、醫師日夜班表、護理師三班制、
          四種檢查資源，以及 SBP 的 Level III / IV 提前優先閾值設定。
        </p>
      </div>

      <div className="form-grid">
        {FIELD_CONFIG.map((field) => (
          <label key={field.key} className="field-group">
            <span className="field-label">{field.label}</span>

            {field.type === 'select' ? (
              <select
                className="field-input"
                value={values[field.key] ?? ''}
                disabled={disabled}
                onChange={(event) => onFieldChange(field.key, event.target.value)}
              >
                {field.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="field-input"
                type="number"
                min={field.min}
                max={field.max}
                step={field.step}
                value={values[field.key] ?? field.min ?? 0}
                disabled={disabled}
                onChange={(event) => {
                  const nextValue = parseFieldValue(field, event.target.value);
                  onFieldChange(field.key, nextValue);
                }}
              />
            )}
          </label>
        ))}
      </div>

      <div className="form-actions">
        <button className="primary-button" type="button" onClick={onSubmit} disabled={disabled}>
          {disabled ? '模擬執行中...' : '執行模擬'}
        </button>

        <span className="form-hint">
          {apiAvailable ? '已連到 FastAPI 服務。' : '目前使用樣本模式，執行會退回情境結果。'}
        </span>
      </div>
    </section>
  );
}

export default SimulationForm;