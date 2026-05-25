import { formatDuration, formatInteger } from '../../../lib/formatters.js';

const METRICS = [
  {
    key: 'total_patients',
    label: '病人總數',
    format: formatInteger,
    deltaFormat: formatInteger,
    lowerIsBetter: null,
  },
  {
    key: 'total_events',
    label: '事件總數',
    format: formatInteger,
    deltaFormat: formatInteger,
    lowerIsBetter: null,
  },
  {
    key: 'average_waiting_time',
    label: '平均初診等待',
    format: formatDuration,
    deltaFormat: formatDuration,
    lowerIsBetter: true,
  },
  {
    key: 'p95_waiting_time',
    label: 'P95 初診等待',
    format: formatDuration,
    deltaFormat: formatDuration,
    lowerIsBetter: true,
  },
  {
    key: 'average_time_in_system',
    label: '平均在院時間',
    format: formatDuration,
    deltaFormat: formatDuration,
    lowerIsBetter: true,
  },
  {
    key: 'average_service_time',
    label: '平均初診後流程時間',
    format: formatDuration,
    deltaFormat: formatDuration,
    lowerIsBetter: true,
  },
];

const RESOURCE_PARAM_KEYS = [
  'num_general_doctors',
  'num_senior_doctors',
  'num_doctors_night',
  'num_senior_doctors_night',
  'num_nurses',
  'num_ct',
  'num_xray',
  'num_lab',
  'num_ultrasound',
  'simulation_time',
  'exam_probability',
  'arrival_rate_multiplier',
  'use_taiwan_ttas',
  'random_seed',
];

const PARAM_LABELS = {
  num_general_doctors: '一般醫師',
  num_senior_doctors: '資深醫師',
  num_doctors_night: '夜班醫師',
  num_senior_doctors_night: '夜班資深醫師',
  num_nurses: '檢傷護理師',
  num_ct: 'CT',
  num_xray: 'X-ray',
  num_lab: 'Lab',
  num_ultrasound: 'Ultrasound',
  simulation_time: '模擬時長',
  exam_probability: '檢查機率',
  arrival_rate_multiplier: '到診倍率',
  use_taiwan_ttas: 'TTAS 模式',
  random_seed: '隨機種子',
};

const getNumericValue = (summary, key) => {
  const value = Number(summary?.[key]);
  return Number.isFinite(value) ? value : 0;
};

const getDeltaTone = (delta, lowerIsBetter) => {
  if (delta === 0 || lowerIsBetter === null) {
    return 'neutral';
  }

  return lowerIsBetter ? (delta < 0 ? 'better' : 'worse') : delta > 0 ? 'better' : 'worse';
};

const formatDelta = (delta, metric) => {
  if (delta === 0) {
    return '與 baseline 相同';
  }

  const prefix = delta > 0 ? '+' : '-';
  return `${prefix}${metric.deltaFormat(Math.abs(delta))}`;
};

const findParameterMismatches = (currentParameters, baselineParameters) => {
  if (!currentParameters || !baselineParameters) {
    return [];
  }

  return RESOURCE_PARAM_KEYS.filter((key) => {
    const a = currentParameters[key];
    const b = baselineParameters[key];
    return a !== b;
  });
};

function ComparisonSummary({
  currentResult,
  currentParameters,
  baselineResult,
  baselineParameters,
  baselineLabel,
  isCustomBaseline,
}) {
  const currentSummary = currentResult?.summary;
  const baselineSummary = baselineResult?.summary;

  if (!currentSummary || !baselineSummary) {
    return null;
  }

  const mismatches = isCustomBaseline
    ? findParameterMismatches(currentParameters, baselineParameters)
    : [];

  const strategyChanged =
    isCustomBaseline &&
    currentParameters?.scheduling_strategy &&
    baselineParameters?.scheduling_strategy &&
    currentParameters.scheduling_strategy !== baselineParameters.scheduling_strategy;

  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="panel-eyebrow">Comparison</p>
          <h2 className="panel-title">比較結果</h2>
        </div>
        <p className="panel-copy">
          {isCustomBaseline
            ? `目前以「${baselineLabel}」作為比較基準，建議只切換「排程策略」以進行公平對決。`
            : `目前顯示即時模擬與 ${baselineLabel} 樣本結果的差異。鎖定自訂基準後可在相同資源下比較 SBP / IFP / ALT。`}
        </p>
      </div>

      {isCustomBaseline && mismatches.length > 0 ? (
        <div className="comparison-warning" role="alert">
          <strong>⚠️ 警告：目前的資源參數與基準線不同！</strong>
          <span>
            這將導致比較結果失真，請確保僅切換「排程策略」以進行公平對決。
          </span>
          <ul className="comparison-warning-list">
            {mismatches.map((key) => (
              <li key={key}>
                {PARAM_LABELS[key] || key}：基準 = {String(baselineParameters[key])}，目前 ={' '}
                {String(currentParameters[key])}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {isCustomBaseline && strategyChanged && mismatches.length === 0 ? (
        <div className="comparison-info" role="status">
          ✅ 資源參數一致，僅切換策略：{baselineParameters.scheduling_strategy} →{' '}
          {currentParameters.scheduling_strategy}，可視為公平對決。
        </div>
      ) : null}

      <div className="comparison-table" role="table" aria-label="模擬結果比較">
        <div className="comparison-header" role="row">
          <span>指標</span>
          <span>目前結果</span>
          <span>Baseline</span>
          <span>差異</span>
        </div>

        {METRICS.map((metric) => {
          const currentValue = getNumericValue(currentSummary, metric.key);
          const baselineValue = getNumericValue(baselineSummary, metric.key);
          const delta = currentValue - baselineValue;
          const deltaTone = getDeltaTone(delta, metric.lowerIsBetter);

          return (
            <div key={metric.key} className="comparison-row" role="row">
              <div className="comparison-metric">
                <strong>{metric.label}</strong>
              </div>
              <div className="comparison-value">{metric.format(currentValue)}</div>
              <div className="comparison-value comparison-baseline">{metric.format(baselineValue)}</div>
              <div className={`comparison-delta tone-${deltaTone}`}>{formatDelta(delta, metric)}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default ComparisonSummary;
