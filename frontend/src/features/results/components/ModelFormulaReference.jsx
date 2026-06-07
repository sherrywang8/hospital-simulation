const RESOURCE_CAPACITY_EQUATIONS = [
  { label: 'CT 容量', left: 'C', sub: 'CT', right: 'n_CT', defaultValue: 1 },
  { label: 'Xray 容量', left: 'C', sub: 'XR', right: 'n_XR', defaultValue: 1 },
  { label: 'Lab 容量', left: 'C', sub: 'Lab', right: 'n_Lab', defaultValue: 1 },
  { label: 'Ultrasound 容量', left: 'C', sub: 'US', right: 'n_US', defaultValue: 1 },
];

const EXAM_ROWS = [
  {
    name: 'Lab（檢驗）',
    capacity: 1,
    probability: 0.92,
    duration: 1.19,
    reportDelay: 20.0,
    note: '抽血/檢體；報告約 20 分鐘後可用',
  },
  {
    name: 'X-ray（X 光）',
    capacity: 1,
    probability: 0.29,
    duration: 3.99,
    reportDelay: 30.0,
    note: '影像檢查；報告約 30 分鐘後可用',
  },
  {
    name: 'Ultrasound（超音波）',
    capacity: 1,
    probability: 0.22,
    duration: 6.58,
    reportDelay: 0.0,
    note: '即時判讀，無報告等待時間',
  },
  {
    name: 'CT（電腦斷層）',
    capacity: 1,
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

const STOCHASTIC_DISTRIBUTIONS = [
  {
    label: '檢傷時間',
    expression: 'T_triage ~ Triangular(a = 3, m = 7, b = 10)',
    note: 'Kim (2024) 建議的三角分配，現由「共用護理師池」接單執行檢傷流程。',
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

const DEFAULT_INDIRECT_NURSING_MULTIPLIER = 1.0;

const INDIRECT_NURSING_REFERENCE = {
  title: 'Impact of Emergency Department Volume on Registered Nurse Time at the Bedside',
  authors: 'Hobgood, C., Villani, J., & Quattlebaum, R.',
  journal: 'Annals of Emergency Medicine',
  year: 2005,
  directCarePercent: 25.6,
  indirectCarePercent: 48.4,
  note: '文獻指出急診護理師的 indirect patient care 約為 direct patient care 的 1.89 倍；本系統採保守校正值 1.0。',
};

const NURSING_TASK_ROWS = [
  { name: '心肺復甦術 (CPR)',           mean: 40.1, std: 14.3, applyIndirect: false, sourceType: 'Expected' },
  { name: '呼吸道置入與固定 (Airway)',       mean:  6.7, std:  5.0, applyIndirect: true,  sourceType: 'Measured' },
  { name: '靜脈留置針置入 (IV insertion)',   mean:  2.5, std:  0.5, applyIndirect: true,  sourceType: 'Measured' },
  { name: '靜脈抽血 (Venous blood sample)', mean:  1.7, std:  1.3, applyIndirect: true,  sourceType: 'Measured' },
  { name: '導尿管置入 (Foley insertion)',    mean:  5.7, std:  4.9, applyIndirect: true,  sourceType: 'Measured' },
  { name: '傷口護理 (Wound care)',           mean:  3.7, std:  3.1, applyIndirect: true,  sourceType: 'Measured' },
  { name: '協助侵入性處置 (CVC/LP)',           mean:  7.7, std:  4.4, applyIndirect: false, sourceType: 'Expected/Procedure support' },
  { name: '給藥/打針 (Medication/IM)',        mean:  2.0, std:  1.0, applyIndirect: true,  sourceType: 'Measured' },
  { name: '衛生教育 (Health education)',     mean:  1.0, std:  0.5, applyIndirect: true,  sourceType: 'Measured' },
  { name: '護理紀錄 (Documentation)',        mean: 16.0, std: 15.3, applyIndirect: false, sourceType: 'Expected' },
];

// 🌟 新增：病患動向與住院機率常數
const DISPOSITION_ROWS = [
  { level: 'Level I (急救)', prob: '92%', note: '幾乎全數轉入 ICU 或病房。若執行 CPR 或插管，系統強制 100% 住院。' },
  { level: 'Level II (危急)', prob: '61%', note: '高危險群，多數需住院。若執行 CVC 或插管，系統強制 100% 住院。' },
  { level: 'Level III (緊急)', prob: '36%', note: '消耗多項檢驗資源。若病情評估需放置導尿管 (Foley)，系統強制 100% 住院。' },
  { level: 'Level IV (次緊急)', prob: '10%', note: '輕症，極少數因特殊狀況留院，多數離院。' },
  { level: 'Level V (非緊急)', prob: '0%', note: '僅需簡單理學檢查或衛教，100% 離院。' },
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
        <span className="reference-chip">分段排班函數</span>
        <span className="reference-chip">NHPP 到診模型</span>
        <span className="reference-chip">檢傷與看診分布</span>
        <span className="reference-chip">醫師職級差異</span>
        {/* 🌟 新增 Chip 標籤 */}
        <span className="reference-chip">終點動向邏輯</span>
        <span className="reference-chip">間接護理補正</span> 
      </div>

      <div className="formula-grid">
        <article className="formula-card">
          <p className="formula-tag">Exam Resources</p>
          <h3 className="formula-title">檢查 / 檢驗資源明細</h3>
          <p className="formula-copy">
            四種檢查資源目前皆以固定容量搭配固定執行時間與報告延遲實作；檢查機率則代表病人在初診後被開立該項檢查的條件機率。
          </p>

          <div className="table-wrap">
            <table className="log-table reference-table">
              <thead>
                <tr>
                  <th>項目</th>
                  <th>固定容量</th>
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
                    <td className="mono-cell">{row.capacity}</td>
                    <td className="mono-cell">{row.probability.toFixed(2)}</td>
                    <td className="mono-cell">{row.duration.toFixed(2)}</td>
                    <td className="mono-cell">{row.reportDelay.toFixed(1)}</td>
                    <td>{row.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="formula-note">
            固定容量分別對應前端可調參數 <code>num_lab</code>、<code>num_xray</code>、<code>num_ultrasound</code>、<code>num_ct</code>，目前預設皆為 1。
          </p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Nursing Flow</p>
          <h3 className="formula-title">護理人員流程參數</h3>
          <p className="formula-copy">
            目前檢傷流程由共用護理師池執行，檢傷時間分布與期望值如下。
          </p>

          <div className="table-wrap">
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

          <p className="formula-note">
            目前檢傷護理時間對應 <code>DEFAULT_TRIAGE_MIN</code>、<code>DEFAULT_TRIAGE_MODE</code>、<code>DEFAULT_TRIAGE_MAX</code>。
          </p>
        </article>

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
              <span className="formula-note formula-note-inline">
                預設容量 = {item.defaultValue}
              </span>
            </FormulaRow>
          ))}

          <p className="formula-note">
            其中 <code>n_CT</code>、<code>n_XR</code>、<code>n_Lab</code>、<code>n_US</code> 分別代表各設備可同時服務的最大數量。
          </p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Shift Function</p>
          <h3 className="formula-title">人力容量 (動態分段班表)</h3>
          <p className="formula-copy">
            醫師與護理師皆採分段函數，會依模擬時間落點自動切換為對應班別的編制人力。
          </p>

          <FormulaRow label="醫師容量 (兩班制)">
            <div className="piecewise-block">
              <div className="piecewise-head">
                D(t) =
              </div>
              <div className="piecewise-body">
                <div className="piecewise-line">
                  <span>
                    n<sub>doc</sub>
                    <sup>day</sup>
                  </span>
                  <span>if 07:00 &lt;= (t mod 1440) &lt; 22:00</span>
                </div>
                <div className="piecewise-line">
                  <span>
                    n<sub>doc</sub>
                    <sup>night</sup>
                  </span>
                  <span>otherwise</span>
                </div>
              </div>
            </div>
          </FormulaRow>

          <FormulaRow label="護理師容量 (三班制)">
            <div className="piecewise-block">
              <div className="piecewise-head">
                N(t) =
              </div>
              <div className="piecewise-body">
                <div className="piecewise-line">
                  <span>
                    n<sub>nurse</sub>
                    <sup>day</sup>
                  </span>
                  <span>if 07:00 &lt;= (t mod 1440) &lt; 15:00</span>
                </div>
                <div className="piecewise-line">
                  <span>
                    n<sub>nurse</sub>
                    <sup>evening</sup>
                  </span>
                  <span>if 15:00 &lt;= (t mod 1440) &lt; 22:00</span>
                </div>
                <div className="piecewise-line">
                  <span>
                    n<sub>nurse</sub>
                    <sup>night</sup>
                  </span>
                  <span>otherwise</span>
                </div>
              </div>
            </div>
          </FormulaRow>

          <p className="formula-note">
            目前系統預設為醫師日/夜兩班 (5人/3人)，護理師採標準白班/小夜/大夜三班制 (16/16/8人)。
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
            這些分布會直接影響病患的檢傷、初診與複診服務時間，也是目前模擬核心的重要隨機來源。
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
            初診服務時間依醫師職級（一般 / 資深）與病患 KTAS 檢傷級別採三角分配抽樣。論文將 KTAS 等級分組為 (1,2) / (3) / (4,5) 三段，本系統將 Level I/II 對應 KTAS 1,2、Level III 對應 KTAS 3、Level IV/V 對應 KTAS 4,5。
          </p>

          <FormulaRow label="General — KTAS 1, 2 (Level I, II)">
            <span className="equation-symbol">
              S ~ Triangular(min = 8, mode = 20, max = 30)
            </span>
          </FormulaRow>
          <FormulaRow label="Senior — KTAS 1, 2 (Level I, II)">
            <span className="equation-symbol">
              S ~ Triangular(min = 5, mode = 15, max = 25)
            </span>
          </FormulaRow>
          <FormulaRow label="General — KTAS 3 (Level III)">
            <span className="equation-symbol">
              S ~ Triangular(min = 10, mode = 25, max = 35)
            </span>
          </FormulaRow>
          <FormulaRow label="Senior — KTAS 3 (Level III)">
            <span className="equation-symbol">
              S ~ Triangular(min = 5, mode = 20, max = 30)
            </span>
          </FormulaRow>
          <FormulaRow label="General — KTAS 4, 5 (Level IV, V)">
            <span className="equation-symbol">
              S ~ Triangular(min = 20, mode = 35, max = 45)
            </span>
          </FormulaRow>
          <FormulaRow label="Senior — KTAS 4, 5 (Level IV, V)">
            <span className="equation-symbol">
              S ~ Triangular(min = 15, mode = 30, max = 40)
            </span>
          </FormulaRow>

          <p className="reference-cite">* 參數引用自：Kim, J.-K. (2024). Enhancing Patient Flow in Emergency Departments. <em>Applied Sciences</em>. Table 4.</p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Nursing Care</p>
          <h3 className="formula-title">護理處置時間參數 (Nursing Care Time Parameters)</h3>
          <p className="formula-copy">
            時間參數參考自 Wen-Chih Fann 等人 (2019) 於台灣急診室之實證研究
            (Do Emergency Nurses Spend Enough Time on Nursing Activities?)。多數 measured-time 床邊任務會再套用間接護理補正；
            已採 expected nursing time 的 CPR 與護理紀錄不重複補正。
          </p>

          <div className="table-wrap">
            <table className="log-table reference-table">
              <thead>
                <tr>
                  <th>處置項目</th>
                  <th>來源類型</th>
                  <th>原始 Mean (分鐘)</th>
                  <th>SD (分鐘)</th>
                  <th>間接補正</th>
                  <th>模型使用 Mean (分鐘)</th>
                </tr>
              </thead>
              <tbody>
                {NURSING_TASK_ROWS.map((row) => {
                  const adjustedMean = row.applyIndirect
                    ? row.mean * (1 + DEFAULT_INDIRECT_NURSING_MULTIPLIER)
                    : row.mean;

                  return (
                    <tr key={row.name}>
                      <td>{row.name}</td>
                      <td className="mono-cell">{row.sourceType}</td>
                      <td className="mono-cell">{row.mean.toFixed(1)}</td>
                      <td className="mono-cell">{row.std.toFixed(1)}</td>
                      <td>{row.applyIndirect ? `是 × (1 + ${DEFAULT_INDIRECT_NURSING_MULTIPLIER})` : '否'}</td>
                      <td className="mono-cell">{adjustedMean.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="reference-cite">
            * 參數引用自：Fann, W.-C. et al. (2019). Do Emergency Nurses Spend Enough Time on Nursing Activities?{' '}
            <em>Journal of Emergency Nursing</em>.
          </p>
        </article>

        <article className="formula-card">
          <p className="formula-tag">Indirect Nursing Workload</p>
          <h3 className="formula-title">間接護理補正參數</h3>
          <p className="formula-copy">
            為避免只用 measured nursing time 低估急診護理師工作量，本系統參考 Hobgood 等人的急診護理 time-motion study，
            對 measured-time 床邊任務加入間接護理工作補正。
          </p>

          <FormulaRow label="補正係數">
            <span className="equation-symbol">
              k<sub>indirect</sub>
            </span>
            <span className="equation-operator">=</span>
            <span className="equation-symbol">{DEFAULT_INDIRECT_NURSING_MULTIPLIER.toFixed(1)}</span>
          </FormulaRow>

          <FormulaRow label="模型使用時間">
            <span className="equation-symbol">
              T<sub>nursing, model</sub>
            </span>
            <span className="equation-operator">=</span>
            <span className="equation-symbol">
              T<sub>measured</sub> × (1 + k<sub>indirect</sub>)
            </span>
          </FormulaRow>

          <div className="table-wrap">
            <table className="log-table reference-table">
              <thead>
                <tr>
                  <th>文獻指標</th>
                  <th>比例</th>
                  <th>模型解讀</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Direct patient care</td>
                  <td className="mono-cell">{INDIRECT_NURSING_REFERENCE.directCarePercent.toFixed(1)}%</td>
                  <td>可被病人流程直接觀察到的床邊護理任務。</td>
                </tr>
                <tr>
                  <td>Indirect patient care</td>
                  <td className="mono-cell">{INDIRECT_NURSING_REFERENCE.indirectCarePercent.toFixed(1)}%</td>
                  <td>醫囑確認、紀錄、溝通、標本處理、流程協調等背景工作。</td>
                </tr>
                <tr>
                  <td>Indirect / Direct</td>
                  <td className="mono-cell">
                    {(INDIRECT_NURSING_REFERENCE.indirectCarePercent / INDIRECT_NURSING_REFERENCE.directCarePercent).toFixed(2)} ×
                  </td>
                  <td>本系統暫採保守值 1.0，而非直接使用 1.89。</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="reference-cite">
            * 參數概念參考自：{INDIRECT_NURSING_REFERENCE.authors} ({INDIRECT_NURSING_REFERENCE.year}).{' '}
            <em>{INDIRECT_NURSING_REFERENCE.title}</em>. {INDIRECT_NURSING_REFERENCE.journal}.
          </p>
        </article>

        {/* 🌟 新增：病患動向與住院邏輯卡片 */}
        <article className="formula-card">
          <p className="formula-tag">Disposition</p>
          <h3 className="formula-title">病患終點動向 (Disposition & Admission Probabilities)</h3>
          <p className="formula-copy">
            基礎住院機率參考自 ESI 創始實證文獻。若病患於模擬中觸發特定重症處置，系統將啟動強制覆寫邏輯，直接辦理住院 (轉病房/ICU)。
          </p>

          <div className="table-wrap">
            <table className="log-table reference-table">
              <thead>
                <tr>
                  <th>檢傷級別 (Triage Level)</th>
                  <th>基礎住院率</th>
                  <th>臨床意義與系統強制覆寫邏輯</th>
                </tr>
              </thead>
              <tbody>
                {DISPOSITION_ROWS.map((row) => (
                  <tr key={row.level}>
                    <td>{row.level}</td>
                    <td className="mono-cell">{row.prob}</td>
                    <td>{row.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="reference-cite">
            * 參數引用自：Wuerz, R. C., et al. (2000). <em>Reliability and Validity of a New Five-level Triage Instrument.</em> Academic Emergency Medicine.
          </p>
        </article>
      </div>
    </section>
  );
}

export default ModelFormulaReference;