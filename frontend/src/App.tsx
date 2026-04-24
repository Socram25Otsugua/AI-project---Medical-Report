import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { analyzeReport } from './api'
import type { AnalyzeResultV2 } from './types'
import type { HistoryItem } from './history'
import { loadHistory, saveHistory } from './history'
import { defaultIndicatorsState, sections, type IndicatorsState } from './indicators/schema'
import { indicatorsToReportText } from './indicators/render'

function App() {
  const [sessionId] = useState(() => crypto.randomUUID())
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResultV2 | null>(null)
  const [sourceLabel] = useState<string>('Form entry')
  const [history, setHistory] = useState<HistoryItem[]>(() => loadHistory())
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null)
  const [indicators, setIndicators] = useState<IndicatorsState>(() => defaultIndicatorsState())

  const completeness = useMemo(() => result?.review.completeness_score ?? null, [result])

  const canAnalyze = useMemo(() => {
    if (busy) return false
    const name = String(indicators.patient_name ?? '').trim()
    const problem = String(indicators.problem_description ?? '').trim()
    const anyVital =
      String(indicators.spo2_percent ?? '').trim() !== '' ||
      String(indicators.pulse_bpm ?? '').trim() !== '' ||
      String(indicators.bp_systolic ?? '').trim() !== '' ||
      String(indicators.breathing_frequency ?? '').trim() !== ''
    return (name.length >= 2 && problem.length >= 10) || anyVital
  }, [busy, indicators])

  useEffect(() => {
    saveHistory(history)
  }, [history])

  const handleClear = () => {
    setResult(null)
    setError(null)
    setSelectedHistoryId(null)
    setIndicators(defaultIndicatorsState())
  }

  return (
    <>
      <div className="appShell">
        <aside className="sidebar">
          <div className="sidebarTop">
            <div className="brand">
              <div className="brandDot" />
              <div>
                <div className="brandName">RMR Reviewer</div>
                <div className="brandSub">Offline • Ollama</div>
              </div>
            </div>

            <button className="button sidebarBtn" onClick={handleClear} disabled={busy}>
              New report
            </button>
          </div>

          <div className="sidebarSectionTitle">History</div>
          {history.length === 0 ? (
            <div className="sidebarEmpty">No saved reports yet.</div>
          ) : (
            <div className="historyList">
              {history.map((h) => {
                const score = h.result.review.completeness_score
                const when = new Date(h.createdAt).toLocaleString()
                const active = h.id === selectedHistoryId
                return (
                  <button
                    key={h.id}
                    className={`historyItem ${active ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedHistoryId(h.id)
                      setResult(h.result)
                      setError(null)
                      if (h.indicators) setIndicators(h.indicators)
                    }}
                    disabled={busy}
                  >
                    <div className="historyTop">
                      <div className="historyTitle">{h.sourceLabel || 'Form entry'}</div>
                      <div className={`historyScore s-${score >= 85 ? 'g' : score >= 60 ? 'y' : 'r'}`}>{score}</div>
                    </div>
                    <div className="historyMeta">{when}</div>
                  </button>
                )
              })}
            </div>
          )}

          {history.length > 0 && (
            <div className="sidebarFooter">
              <button
                className="button ghost sidebarBtn"
                onClick={() => {
                  setHistory([])
                  setSelectedHistoryId(null)
                }}
                disabled={busy}
              >
                Clear history
              </button>
            </div>
          )}
        </aside>

        <div className="container">
          <header className="header">
            <div>
              <div className="badge">Offline • Ollama • LangChain • RAG • MCP</div>
              <h1>Radio Medical Report Reviewer</h1>
              <p className="subtitle">
                Fill in the form below and click Analyze. Get structured feedback plus a situation-adapted next-step response.
              </p>
            </div>
            <div className="meta">
              <div className="metaLabel">Session</div>
              <div className="metaValue">{sessionId}</div>
            </div>
          </header>

          <main className="grid">
          <section className="card">
            <div className="cardHeader">
              <h2>Report</h2>
              <div className="actions">
                <button
                  className="button ghost"
                  onClick={handleClear}
                  disabled={busy}
                >
                  Clear
                </button>
                <button
                  className="button"
                  onClick={async () => {
                    setBusy(true)
                    setError(null)
                    try {
                      const finalText = indicatorsToReportText(sections, indicators)
                      const res = await analyzeReport({ session_id: sessionId, report_text: finalText, locale: 'en-UK' })
                      setResult(res)
                      const item: HistoryItem = {
                        id: crypto.randomUUID(),
                        createdAt: Date.now(),
                        sourceLabel: sourceLabel === 'No file selected' ? 'Form entry' : sourceLabel,
                        reportText: finalText,
                        result: res,
                        mode: 'form',
                        indicators,
                      }
                      setHistory((prev) => [item, ...prev].slice(0, 50))
                      setSelectedHistoryId(item.id)
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Unknown error')
                    } finally {
                      setBusy(false)
                    }
                  }}
                  disabled={!canAnalyze}
                >
                  {busy ? 'Analyzing…' : 'Analyze'}
                </button>
              </div>
            </div>

            <div className="formGrid">
                {sections.map((sec) => (
                  <div key={sec.id} className="formSection">
                    <div className="formSectionHeader">
                      <div className="formSectionTitle">{sec.title}</div>
                      {sec.description && <div className="formSectionDesc">{sec.description}</div>}
                    </div>
                    <div className="fields">
                      {sec.fields.map((f) => {
                        const v = indicators[f.key]
                        const id = `f_${sec.id}_${f.key}`
                        if (f.type === 'textarea') {
                          return (
                            <label key={f.key} className="field">
                              <span className="fieldLabel">{f.label}</span>
                              <textarea
                                id={id}
                                className="fieldInput textareaSmall"
                                placeholder={f.placeholder}
                                value={typeof v === 'string' ? v : String(v ?? '')}
                                onChange={(e) => setIndicators((p) => ({ ...p, [f.key]: e.target.value }))}
                              />
                            </label>
                          )
                        }
                        if (f.type === 'checkbox') {
                          return (
                            <label key={f.key} className="field checkRow">
                              <input
                                id={id}
                                type="checkbox"
                                checked={Boolean(v)}
                                onChange={(e) => setIndicators((p) => ({ ...p, [f.key]: e.target.checked }))}
                              />
                              <span className="fieldLabel">{f.label}</span>
                            </label>
                          )
                        }
                        if (f.type === 'select') {
                          return (
                            <label key={f.key} className="field">
                              <span className="fieldLabel">{f.label}</span>
                              <select
                                id={id}
                                className="fieldInput"
                                value={typeof v === 'string' ? v : String(v ?? '')}
                                onChange={(e) => setIndicators((p) => ({ ...p, [f.key]: e.target.value }))}
                              >
                                {(f.options ?? []).map((o) => (
                                  <option key={o.value} value={o.value}>
                                    {o.label}
                                  </option>
                                ))}
                              </select>
                            </label>
                          )
                        }
                        return (
                          <label key={f.key} className="field">
                            <span className="fieldLabel">
                              {f.label}
                              {f.unit ? <span className="unit">{f.unit}</span> : null}
                            </span>
                            <input
                              id={id}
                              className="fieldInput"
                              type={f.type === 'number' ? 'number' : 'text'}
                              placeholder={f.placeholder}
                              value={typeof v === 'string' ? v : String(v ?? '')}
                              onChange={(e) =>
                                setIndicators((p) => ({
                                  ...p,
                                  [f.key]: f.type === 'number' ? e.target.value : e.target.value,
                                }))
                              }
                            />
                          </label>
                        )
                      })}
                    </div>
                  </div>
                ))}
            </div>

            {error && <div className="error">Error: {error}</div>}
          </section>

          <section className="card">
            <div className="cardHeader">
              <h2>Results</h2>
              {completeness !== null && (
                <div className="score">
                  <div className="scoreLabel">Completeness</div>
                  <div className="scoreValue">{completeness}/100</div>
                </div>
              )}
            </div>

            {!result ? (
              <div className="empty">
                Submit a report to see checklist-based deficiencies and a situation-adapted next-step response.
              </div>
            ) : (
              <div className="result">
                <div className="panel">
                  <div className="panelTitle">Deficiencies</div>
                  {result.review.deficiencies.length === 0 ? (
                    <div className="muted">No deficiencies detected (or the report is already very complete).</div>
                  ) : (
                    <ul className="list">
                      {result.review.deficiencies.map((d, idx) => (
                        <li key={idx} className={`item sev-${d.severity}`}>
                          <div className="itemTop">
                            <div className="pill">{d.area}</div>
                            <div className="sev">{d.severity}</div>
                          </div>
                          <div className="itemIssue">{d.issue}</div>
                          <div className="itemSuggestion">{d.suggestion}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="panel">
                  <div className="panelTitle">Safety flags</div>
                  {result.review.safety_flags.length === 0 ? (
                    <div className="muted">No red flags detected.</div>
                  ) : (
                    <ul className="bullets">
                      {result.review.safety_flags.map((f, idx) => (
                        <li key={idx}>{f}</li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="panel">
                  <div className="panelTitle">Recommended response (next step)</div>
                  <div className="message">{result.response.next_step_message}</div>
                  {result.response.rationale_bullets.length > 0 && (
                    <>
                      <div className="subTitle">Rationale</div>
                      <ul className="bullets">
                        {result.response.rationale_bullets.map((b, idx) => (
                          <li key={idx}>{b}</li>
                        ))}
                      </ul>
                    </>
                  )}
                  {result.response.questions_for_participants.length > 0 && (
                    <>
                      <div className="subTitle">Targeted questions</div>
                      <ul className="bullets">
                        {result.response.questions_for_participants.map((q, idx) => (
                          <li key={idx}>{q}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>

                {result.patient_evaluation && (
                  <div className="panel">
                    <div className="panelTitle">Patient evaluation</div>
                    <div className="pillRow">
                      <div className={`statusPill st-${result.patient_evaluation.status}`}>
                        {result.patient_evaluation.status.toUpperCase()}
                      </div>
                    </div>
                    <div className="message">{result.patient_evaluation.summary}</div>
                    {result.patient_evaluation.suspected_problems.length > 0 && (
                      <>
                        <div className="subTitle">Suspected problems</div>
                        <ul className="bullets">
                          {result.patient_evaluation.suspected_problems.map((p, idx) => (
                            <li key={idx}>{p}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {result.patient_evaluation.red_flags.length > 0 && (
                      <>
                        <div className="subTitle">Red flags</div>
                        <ul className="bullets">
                          {result.patient_evaluation.red_flags.map((p, idx) => (
                            <li key={idx}>{p}</li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>
          </main>
        </div>
      </div>
    </>
  )
}

export default App
