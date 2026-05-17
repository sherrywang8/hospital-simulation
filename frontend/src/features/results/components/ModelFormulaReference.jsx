const RESOURCE_CAPACITY_EQUATIONS = [
  { label: 'CT 容量', left: 'C', sub: 'CT', right: 'n_CT' },
  { label: 'Xray 容量', left: 'C', sub: 'XR', right: 'n_XR' },
  { label: 'Lab 容量', left: 'C', sub: 'Lab', right: 'n_Lab' },
  { label: 'Ultrasound 容量', left: 'C', sub: 'US', right: 'n_US' },
];

const STOCHASTIC_DISTRIBUTIONS = [
  {
    label: '檢傷時間',
    expression: 'T_triage ~ Triangular(a = 3, m = 7, b = 10)',
    note: 'Kim (2024) 建議的三角分配，對應目前檢傷護理師流程。',
  },
  {
    label: '初診服務時間',
    expression: 'S_initial ~ Triangular(min, mode, max)，依醫師職級與檢傷級別而定',
    note: '初診看診時間依醫師職級與病患檢傷級別採三角分配，詳見下方 Doctor Experience Levels 卡片。',
  },
  {
    label: '複診服務時間',
    expression: 'S_followup ~ TruncatedExponential(mean = 15, min = 5, max = 25)',
    note: '病人做完檢查後回診的服務時間採另一組截尾指數分配。',
  },
];

function FormulaRow({ label, children }) {
  return (
    <div className="formula-row">
      <span className="formula-label">{label}</span>
      <div className="equation-block">{children}</div>
    </div>
  );
}

function ModelFormulaReference() {
  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="panel-eyebrow">Model Formula</p>
          <h2 className="panel-title">模型公式與機率分布</h2>
        </div>
        <p className="panel-copy">
          這個分頁整理目前系統用到的主要數學表示法，方便對照簡報、論文與程式實作。
        </p>
      </div>

      <div className="reference-summary">
        <span className="reference-chip">固定容量函數</span>
        <span className="reference-chip">分段醫師班表</span>
        <span className="reference-chip">NHPP 到診模型</span>
        <span className="reference-chip">檢傷與看診分布</span>
        <span className="reference-chip">醫師職級差異</span>
      </div>

      <div className="formula-grid">
        <article className="formula-card">
          <p className="formula-tag">Capacity</p>
          <h3 className="formula-title">固定容量資源</h3>
          <p className="formula-copy">
            CT、Xray、Lab、Ultrasound 在目前模型中視為固定容量資源。它們不是機率密度函數，而是隨時間固定不變的容量函數。
          </p>

          {RESOURCE_CAPACITY_EQUATIONS.map((item) => (
            <FormulaRow key={item.label} label={item.label}>
              <span className="equation-symbol">
                {item.left}
                <sub>{item.sub}</sub>(t)
              </span>
              <span className="equation-operator">=</span>
              <span className="equation-symbol">{item.right}</span>
            </FormulaRow>
          ))}

          <p className="formula-note">
            其中 <code>n_CT</code>、<code>n_XR</code>、<code>n_Lab</code>、<code>n_US</code> 分別代表各設備可同時服務的最大數量。
          </p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Shift Function</p>
          <h3 className="formula-title">醫師容量</h3>
          <p className="formula-copy">
            醫師白天與夜班採分段函數，會依模擬時間落點切換為白班或夜班容量。
          </p>

          <FormulaRow label="醫師容量">
            <div className="piecewise-block">
              <div className="piecewise-head">
                D(t) =
              </div>
              <div className="piecewise-body">
                <div className="piecewise-line">
                  <span>
                    n<sub>d</sub>
                    <sup>day</sup>
                  </span>
                  <span>if 07:00 &lt;= (t mod 1440) &lt; 22:00</span>
                </div>
                <div className="piecewise-line">
                  <span>
                    n<sub>d</sub>
                    <sup>night</sup>
                  </span>
                  <span>otherwise</span>
                </div>
              </div>
            </div>
          </FormulaRow>

          <p className="formula-note">
            目前系統預設為白班 <code>5</code> 位醫師、夜班 <code>3</code> 位醫師；你也可以在前端表單手動調整。
          </p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Arrival Rate</p>
          <h3 className="formula-title">到診率與 NHPP</h3>
          <p className="formula-copy">
            到診率依星期與小時變動，使用論文 Table 2 的基準值，再乘上情境調整倍率。
          </p>

          <FormulaRow label="到診率">
            <span className="equation-symbol">
              λ<sub>d,h</sub>
            </span>
            <span className="equation-operator">=</span>
            <span className="equation-symbol">
              λ
              <sup>paper</sup>
              <sub>d,h</sub> · α
            </span>
          </FormulaRow>

          <FormulaRow label="每小時到診人數">
            <span className="equation-symbol">
              N<sub>d,h</sub>
            </span>
            <span className="equation-operator">~</span>
            <span className="equation-symbol">
              Poisson(λ<sub>d,h</sub>)
            </span>
          </FormulaRow>

          <p className="formula-note">
            這裡的 <code>α</code> 是前端可調的 <code>arrival_rate_multiplier</code>。整體概念屬於 NHPP
            （Non-Homogeneous Poisson Process，非齊次卜瓦松過程）。
          </p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Distributions</p>
          <h3 className="formula-title">其他已實作的隨機分布</h3>
          <p className="formula-copy">
            這些分布會直接影響病人的檢傷、初診與複診服務時間，也是目前模擬核心的重要隨機來源。
          </p>

          {STOCHASTIC_DISTRIBUTIONS.map((item) => (
            <FormulaRow key={item.label} label={item.label}>
              <div className="distribution-block">
                <span className="equation-symbol">{item.expression}</span>
                <span className="formula-note formula-note-inline">{item.note}</span>
              </div>
            </FormulaRow>
          ))}
        </article>

        <article className="formula-card">
          <p className="formula-tag">Doctor Experience Levels</p>
          <h3 className="formula-title">醫師職級差異看診時間</h3>
          <p className="formula-copy">
            初診服務時間依醫師職級（一般 / 資深）與病患檢傷級別（Level III / Level IV）採三角分配抽樣，反映資深醫師效率較高的臨床現實。
          </p>

          <FormulaRow label="General — Level III">
            <span className="equation-symbol">
              S ~ Triangular(min = 10, mode = 25, max = 35)
            </span>
          </FormulaRow>
          <FormulaRow label="General — Level IV">
            <span className="equation-symbol">
              S ~ Triangular(min = 20, mode = 35, max = 45)
            </span>
          </FormulaRow>
          <FormulaRow label="Senior — Level III">
            <span className="equation-symbol">
              S ~ Triangular(min = 5, mode = 20, max = 30)
            </span>
          </FormulaRow>
          <FormulaRow label="Senior — Level IV">
            <span className="equation-symbol">
              S ~ Triangular(min = 15, mode = 30, max = 40)
            </span>
          </FormulaRow>

          <p className="reference-cite">* 參數引用自：Kim, J.-K. (2024). Enhancing Patient Flow in Emergency Departments. <em>Applied Sciences</em>. Table 4.</p>
        </article>
      </div>
    </section>
  );
}

export default ModelFormulaReference;
