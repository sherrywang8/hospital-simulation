import MetricCard from '../../../components/MetricCard.jsx';
import {
  formatDateTime,
  formatDuration,
  formatInteger,
  formatPercent,
} from '../../../lib/formatters.js';

const RESOURCE_LABELS = {
  doctors: '醫師',
  nurses: '護理師', // 👈 新增這個，對應後端合併後的三班制護理師
  ct: 'CT',
  xray: 'Xray',
  lab: 'Lab',
  ultrasound: 'Ultrasound',
};

function ResultSummary({ result, sourceLabel }) {
  const summary = result?.summary;

  if (!summary) {
    return null;
  }

  const artifacts = Object.entries(result.artifacts || {});
  const metrics = [
    { label: '病人總數', value: formatInteger(summary.total_patients) },
    { label: '事件總數', value: formatInteger(summary.total_events) },
    {
      label: '平均初診等待',
      value: formatDuration(summary.average_waiting_time),
      note: '到院 -> 開始初診',
    },
    {
      label: 'P95 初診等待',
      value: formatDuration(summary.p95_waiting_time),
      note: '95% 病人不會超過此值',
    },
    {
      label: '平均在院時間',
      value: formatDuration(summary.average_time_in_system),
      note: '到院 -> 離院',
    },
    {
      label: '平均初診後流程時間',
      value: formatDuration(summary.average_service_time),
      note: '開始初診 -> 離院',
    },
  ];

  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="panel-eyebrow">Results</p>
          <h2 className="panel-title">模擬摘要</h2>
        </div>
        <p className="panel-copy">
          來源：{sourceLabel}，建立時間 {formatDateTime(result.created_at)}。P95 初診等待代表 95%
          病人的初診等待時間都不會超過這個值。
        </p>
      </div>

      <div className="summary-grid">
        {metrics.map((metric) => (
          <MetricCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            note={metric.note}
          />
        ))}
      </div>

      <div className="summary-explainer">
        <p className="summary-explainer-title">指標說明</p>
        <p className="summary-explainer-item">
          <strong>P95 初診等待：</strong>
          第 95 百分位初診等待時間。若 P95 = 42 分，代表 95% 病人的初診等待都在 42 分鐘內。
        </p>
        <p className="summary-explainer-item">
          <strong>平均初診等待：</strong>
          病人從到院到開始初診前，平均需要等待多久。
        </p>
        <p className="summary-explainer-item">
          <strong>平均在院時間：</strong>
          病人從到院到離院的總停留時間。
        </p>
        <p className="summary-explainer-item">
          <strong>平均初診後流程時間：</strong>
          病人從開始初診到離院之間，包含檢查、等報告、複診與離院流程的平均時間。
        </p>
      </div>

      <div className="utilization-wrap">
        {Object.entries(summary.resource_utilization || {}).map(([resource, value]) => (
          <div key={resource} className="utilization-row">
            <span className="utilization-label">{RESOURCE_LABELS[resource] || resource}</span>
            <div className="utilization-bar">
              <span className="utilization-fill" style={{ width: `${Math.min(value * 100, 100)}%` }} />
            </div>
            <span className="utilization-value">{formatPercent(value)}</span>
          </div>
        ))}
      </div>

      {artifacts.length > 0 ? (
        <div className="artifact-row">
          {artifacts.map(([label, url]) => (
            <a key={label} className="artifact-link" href={url} target="_blank" rel="noreferrer">
              {label}
            </a>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export default ResultSummary;
