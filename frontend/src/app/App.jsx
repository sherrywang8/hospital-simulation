import { startTransition, useEffect, useState } from 'react';
import './App.css';
import MetricCard from '../components/MetricCard.jsx';
import StatusBanner from '../components/StatusBanner.jsx';
import ArrivalRateReferenceTable from '../features/results/components/ArrivalRateReferenceTable.jsx';
import ComparisonSummary from '../features/results/components/ComparisonSummary.jsx';
import MedicalExamReference from '../features/results/components/MedicalExamReference.jsx';
import ModelFormulaReference from '../features/results/components/ModelFormulaReference.jsx';
import ResultSummary from '../features/results/components/ResultSummary.jsx';
import EventLogTable from '../features/results/components/EventLogTable.jsx';
import ScenarioSelector from '../features/simulation/components/ScenarioSelector.jsx';
import SimulationForm from '../features/simulation/components/SimulationForm.jsx';
import { fetchSampleResult, fetchScenarios, isRemoteApiConfigured, runSimulation } from '../lib/api.js';
import { formatInteger } from '../lib/formatters.js';

const EMPTY_FORM = {
  scheduling_strategy: 'SBP',
  num_general_doctors: 5,
  num_senior_doctors: 3,
  num_doctors_night: 5,
  num_senior_doctors_night: 2,
  num_nurses_day: 16,
  num_nurses_evening: 16,
  num_nurses_night: 8,
  medication_probability: 0.5, // 給藥機率
  num_ct: 1,
  num_xray: 1,
  num_lab: 1,
  num_ultrasound: 1,
  simulation_time: 10080,
  exam_probability: 0.6,
  arrival_rate_multiplier: 1.0,
  use_taiwan_ttas: false,
  random_seed: 7,
};

const VIEW_OVERVIEW = 'overview';
const VIEW_PAPER_REFERENCE = 'paper-reference';
const VIEW_MODEL_FORMULA = 'model-formula';

function App() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioSlug, setSelectedScenarioSlug] = useState('');
  const [formValues, setFormValues] = useState(EMPTY_FORM);
  const [baselineResult, setBaselineResult] = useState(null);
  const [customBaseline, setCustomBaseline] = useState(null);
  const [result, setResult] = useState(null);
  const [activeView, setActiveView] = useState(VIEW_OVERVIEW);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [apiAvailable, setApiAvailable] = useState(false);
  const [dataSource, setDataSource] = useState('sample');
  const [status, setStatus] = useState({
    tone: 'info',
    message: '正在載入情境與樣本資料。',
  });

  const selectedScenario = scenarios.find((scenario) => scenario.slug === selectedScenarioSlug) || null;

  const commitScenarioResult = (scenario, sampleResult) => {
    startTransition(() => {
      setBaselineResult(sampleResult);
      setResult(sampleResult);
      setFormValues({ ...scenario.parameters });
      setDataSource('sample');
    });
  };

  useEffect(() => {
    const controller = new AbortController();

    const initialize = async () => {
      try {
        const scenarioResponse = await fetchScenarios(controller.signal);
        if (controller.signal.aborted) {
          return;
        }

        const nextScenarios = scenarioResponse.data;
        const defaultScenario = nextScenarios[0];
        setScenarios(nextScenarios);
        setSelectedScenarioSlug(defaultScenario.slug);
        setApiAvailable(scenarioResponse.source === 'api' || isRemoteApiConfigured());
        const sampleResult = await fetchSampleResult(defaultScenario.sample_result_slug, controller.signal);
        commitScenarioResult(defaultScenario, sampleResult);
        setStatus({
          tone: scenarioResponse.source === 'api' ? 'success' : 'warning',
          message:
            scenarioResponse.source === 'api'
              ? '已載入後端提供的情境設定。'
              : '目前未連到 API，畫面已切換到樣本資料模式。',
        });
      } catch (error) {
        setStatus({
          tone: 'error',
          message: `初始化失敗：${error.message}`,
        });
      } finally {
        setLoading(false);
      }
    };

    initialize();
    return () => controller.abort();
  }, []);

  const handleScenarioChange = async (slug) => {
    const scenario = scenarios.find((item) => item.slug === slug);
    if (!scenario) {
      return;
    }

    setSelectedScenarioSlug(slug);
    setBusy(true);
    try {
      const sampleResult = await fetchSampleResult(scenario.sample_result_slug);
      commitScenarioResult(scenario, sampleResult);
      setStatus({
        tone: 'info',
        message: `已切換到 ${scenario.title} 樣本情境。`,
      });
    } catch (error) {
      setStatus({
        tone: 'error',
        message: `載入情境失敗：${error.message}`,
      });
    } finally {
      setBusy(false);
    }
  };

  const handleRunSimulation = async () => {
    setBusy(true);
    try {
      const response = await runSimulation(formValues);
      startTransition(() => {
        setResult(response);
        setDataSource('live');
      });
      setApiAvailable(true);
      setStatus({
        tone: 'success',
        message: '即時模擬完成，畫面已載入最新結果。',
      });
    } catch (error) {
      if (selectedScenario) {
        try {
          const sampleResult = await fetchSampleResult(selectedScenario.sample_result_slug);
          commitScenarioResult(selectedScenario, sampleResult);
          setStatus({
            tone: 'warning',
            message: `未能連到 API，已退回 ${selectedScenario.title} 樣本結果。`,
          });
        } catch (sampleError) {
          setStatus({
            tone: 'error',
            message: `即時模擬與樣本載入都失敗：${sampleError.message}`,
          });
        }
      } else {
        setStatus({
          tone: 'error',
          message: `即時模擬失敗：${error.message}`,
        });
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="dashboard-shell">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">React + SimPy + FastAPI</p>
          <h1 className="hero-title">急診模擬系統控制台</h1>
          <p className="hero-subtitle">
            目前預設情境已對齊論文版本的 NHPP 到診、SBP 排程、5/5/3 醫師班表與四種檢查流程。
            當 API 尚未部署時，頁面會自動退回 `public/data` 內的樣本結果，方便先檢視整體行為。
          </p>
        </div>

        <div className="hero-metrics">
          <MetricCard label="情境數量" value={formatInteger(scenarios.length)} />
          <MetricCard label="結果來源" value={dataSource === 'live' ? 'Live API' : 'Sample Data'} />
          <MetricCard
            label="事件筆數"
            value={formatInteger(result?.summary?.total_events || result?.event_log?.length || 0)}
          />
          <MetricCard
            label="病人數"
            value={formatInteger(result?.summary?.total_patients || result?.patient_summary?.length || 0)}
          />
        </div>
      </section>

      <StatusBanner tone={status.tone}>{status.message}</StatusBanner>

      <section className="view-switch" aria-label="頁面切換">
        <button
          type="button"
          className={`view-tab ${activeView === VIEW_OVERVIEW ? 'is-active' : ''}`}
          onClick={() => setActiveView(VIEW_OVERVIEW)}
        >
          模擬總覽
        </button>
        <button
          type="button"
          className={`view-tab ${activeView === VIEW_PAPER_REFERENCE ? 'is-active' : ''}`}
          onClick={() => setActiveView(VIEW_PAPER_REFERENCE)}
        >
          論文參考
        </button>
        <button
          type="button"
          className={`view-tab ${activeView === VIEW_MODEL_FORMULA ? 'is-active' : ''}`}
          onClick={() => setActiveView(VIEW_MODEL_FORMULA)}
        >
          模型公式
        </button>
      </section>

      {activeView === VIEW_OVERVIEW ? (
        <>
          <section className="layout-grid">
            <div className="layout-column">
              <ScenarioSelector
                scenarios={scenarios}
                selectedSlug={selectedScenarioSlug}
                onChange={handleScenarioChange}
                disabled={loading || busy}
              />
              <SimulationForm
                values={formValues}
                onFieldChange={(key, value) =>
                  setFormValues((current) => ({
                    ...current,
                    [key]: value,
                  }))
                }
                onSubmit={handleRunSimulation}
                disabled={loading || busy}
                apiAvailable={apiAvailable}
              />
            </div>

            <div className="layout-column">
              {result ? <ResultSummary result={result} sourceLabel={dataSource === 'live' ? '即時 API' : '本地樣本'} /> : null}

              {result ? (
                <div className="baseline-actions">
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => {
                      setCustomBaseline({
                        result,
                        parameters: { ...formValues },
                        strategy: formValues.scheduling_strategy,
                        source: dataSource,
                        capturedAt: new Date().toISOString(),
                      });
                      setStatus({
                        tone: 'success',
                        message: `已將目前 ${formValues.scheduling_strategy} 策略結果鎖定為比較基準。`,
                      });
                    }}
                    disabled={busy}
                  >
                    🔒 將目前結果設為比較基準
                  </button>
                  {customBaseline ? (
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => {
                        setCustomBaseline(null);
                        setStatus({
                          tone: 'info',
                          message: '已清除自訂比較基準，將回到情境樣本作為 Baseline。',
                        });
                      }}
                    >
                      清除自訂基準
                    </button>
                  ) : null}
                </div>
              ) : null}

              {result && (customBaseline || (dataSource === 'live' && baselineResult)) ? (
                <ComparisonSummary
                  currentResult={result}
                  currentParameters={formValues}
                  baselineResult={customBaseline ? customBaseline.result : baselineResult}
                  baselineParameters={customBaseline ? customBaseline.parameters : null}
                  baselineLabel={
                    customBaseline
                      ? `自訂基準 (${customBaseline.strategy})`
                      : selectedScenario?.title || '情境樣本'
                  }
                  isCustomBaseline={Boolean(customBaseline)}
                />
              ) : null}
            </div>
          </section>

          {result?.event_log ? <EventLogTable logs={result.event_log} /> : null}
        </>
      ) : activeView === VIEW_PAPER_REFERENCE ? (
        <section className="reference-page">
          <ArrivalRateReferenceTable />
          <MedicalExamReference />
        </section>
      ) : (
        <section className="reference-page">
          <ModelFormulaReference />
        </section>
      )}
    </main>
  );
}

export default App;
