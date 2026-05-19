const EXAM_ROWS = [
  {
    name: 'Lab（檢驗）',
    probability: 0.92,
    duration: 1.19,
    reportDelay: 20.0,
    note: '抽血/檢體；報告約 20 分鐘後可用',
  },
  {
    name: 'X-ray（X 光）',
    probability: 0.29,
    duration: 3.99,
    reportDelay: 30.0,
    note: '影像檢查；報告約 30 分鐘後可用',
  },
  {
    name: 'Ultrasound（超音波）',
    probability: 0.22,
    duration: 6.58,
    reportDelay: 0.0,
    note: '即時判讀，無報告等待時間',
  },
  {
    name: 'CT（電腦斷層）',
    probability: 0.55,
    duration: 2.45,
    reportDelay: 30.0,
    note: '影像檢查；報告約 30 分鐘後可用',
  },
];

const NURSE_ROWS = [
  {
    role: '檢傷護理師（Triage Nurse）',
    distribution: 'Triangular(min=3, mode=7, max=10)',
    expected: '≈ 6.67 min',
    note: '對每位到診病人執行檢傷分級',
  },
];

function MedicalExamReference() {
  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="panel-eyebrow">Paper Reference</p>
          <h2 className="panel-title">檢查設備與護理人員參數</h2>
        </div>
        <p className="panel-copy">
          以下為目前模擬實際採用的設備檢查時間、報告延遲與護理流程時間。檢查/檢驗時間目前以固定常數實作（可由參數覆寫），未來若需改成隨機分配可再擴充。
        </p>
      </div>

      <div className="reference-summary">
        <span className="reference-chip">Kim (2024) Table 4 / 5</span>
        <span className="reference-caption">「檢查機率」= 病人在初診後被開立該項檢查的條件機率。</span>
      </div>

      <div className="table-wrap">
        <h3 className="formula-title" style={{ marginTop: 0 }}>檢查 / 檢驗資源</h3>
        <table className="log-table reference-table">
          <thead>
            <tr>
              <th>項目</th>
              <th>檢查機率</th>
              <th>檢查時間 (分鐘)</th>
              <th>報告延遲 (分鐘)</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            {EXAM_ROWS.map((row) => (
              <tr key={row.name}>
                <td>{row.name}</td>
                <td className="mono-cell">{row.probability.toFixed(2)}</td>
                <td className="mono-cell">{row.duration.toFixed(2)}</td>
                <td className="mono-cell">{row.reportDelay.toFixed(1)}</td>
                <td>{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-wrap" style={{ marginTop: '1rem' }}>
        <h3 className="formula-title">護理人員流程</h3>
        <table className="log-table reference-table">
          <thead>
            <tr>
              <th>角色</th>
              <th>時間分配</th>
              <th>期望值</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            {NURSE_ROWS.map((row) => (
              <tr key={row.role}>
                <td>{row.role}</td>
                <td className="mono-cell">{row.distribution}</td>
                <td className="mono-cell">{row.expected}</td>
                <td>{row.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="reference-cite" style={{ marginTop: '1rem' }}>
        * 數值對應 <code>simulation_core/defaults.py</code> 中的 <code>DEFAULT_LAB_*</code>、<code>DEFAULT_XRAY_*</code>、<code>DEFAULT_ULTRASOUND_*</code>、<code>DEFAULT_CT_*</code>、<code>DEFAULT_TRIAGE_*</code>，並對齊 Kim, J.-K. (2024). <em>Applied Sciences</em>.
      </p>
    </section>
  );
}

export default MedicalExamReference;
