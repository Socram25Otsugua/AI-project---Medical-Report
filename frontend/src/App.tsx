import { useMemo, useState } from 'react'
import './App.css'
import { analyzeReport } from './api'
import type { AnalyzeResult } from './types'

function App() {
  const [reportText, setReportText] = useState('')
  const [sessionId] = useState(() => crypto.randomUUID())
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResult | null>(null)

  const completeness = useMemo(() => result?.review.completeness_score ?? null, [result])

  return (
    <>
      <div className="container">
        <header className="header">
          <div>
            <div className="badge">Offline • Ollama • LangChain • RAG • MCP</div>
            <h1>Radio Medical Report Reviewer</h1>
            <p className="subtitle">
              Paste the report (or transcription) to get structured feedback plus a situation-adapted next-step response.
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
                  onClick={() => {
                    setReportText('')
                    setResult(null)
                    setError(null)
                  }}
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
                      const res = await analyzeReport({ session_id: sessionId, report_text: reportText, locale: 'en-UK' })
                      setResult(res)
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Unknown error')
                    } finally {
                      setBusy(false)
                    }
                  }}
                  disabled={busy || reportText.trim().length < 20}
                >
                  {busy ? 'Analyzing…' : 'Analyze'}
                </button>
              </div>
            </div>

            <textarea
              className="textarea"
              placeholder="Paste the Radio Medical Record text here…"
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
            />

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
              </div>
            )}
          </section>
        </main>
      </div>
    </>
  )
}

export default App
