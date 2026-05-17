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
  { key: 'num_general_doctors', label: '一般醫師數 (General Doctors)', min: 1, step: 1 },
  { key: 'num_senior_doctors', label: '資深醫師數 (Senior Doctors)', min: 0, step: 1 },
  { key: 'num_doctors_night', label: '夜班醫師數', min: 1, step: 1 },
  { key: 'num_nurses', label: '護理師數', min: 0, step: 1 },
  { key: 'num_ct', label: 'CT 資源數', min: 0, step: 1 },
  { key: 'num_xray', label: 'Xray 資源數', min: 0, step: 1 },
  { key: 'num_lab', label: 'Lab 資源數', min: 0, step: 1 },
  { key: 'num_ultrasound', label: 'Ultrasound 資源數', min: 0, step: 1 },
  { key: 'simulation_time', label: '模擬分鐘數', min: 60, step: 60 },
  { key: 'exam_probability', label: '需檢查比例', min: 0, max: 1, step: 0.05 },
  { key: 'arrival_rate_multiplier', label: '到診倍率', min: 0.1, max: 3, step: 0.05 },
  { key: 'random_seed', label: '隨機種子', min: 0, step: 1 },
];

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
          這組表單現在對齊論文模型：NHPP 到診、SBP/ALT/IFP 排程、日夜醫師班表與四種檢查資源。
        </p>
      </div>

      <div className="form-grid">
        {FIELD_CONFIG.map((field) => (
          <label key={field.key} className="field-group">
            <span className="field-label">{field.label}</span>
            {field.type === 'select' ? (
              <select
                className="field-input"
                value={values[field.key]}
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
                value={values[field.key]}
                disabled={disabled}
                onChange={(event) => {
                  const nextValue = ['exam_probability', 'arrival_rate_multiplier'].includes(field.key)
                    ? Number(event.target.value)
                    : Number.parseInt(event.target.value || '0', 10);
                  onFieldChange(field.key, Number.isNaN(nextValue) ? field.min ?? 0 : nextValue);
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
