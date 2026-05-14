import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react'
import './App.css'
import { chatDoctorTurn, clearHistory, createHistory, deleteHistory, finalizeSummary, listHistory } from './api'
import type { AnalyzeResultV2 } from './types'
import type { HistoryItem } from './history'
import { defaultIndicatorsState, sections, type FieldDef, type IndicatorsState, type SectionDef } from './indicators/schema'
import { indicatorsToReportText } from './indicators/render'

type UiTab = 'form' | 'chat' | 'summary'

type ChatMessage = {
  id: string
  role: 'assistant' | 'user'
  text: string
  createdAt: number
}

type VitalsQuality = 'green' | 'yellow' | 'orange' | 'red' | 'unknown'

type FormStep = {
  id: string
  title: string
  description: string
  sectionIds: string[]
}

const FORM_STEPS: FormStep[] = [
  {
    id: 'patient',
    title: 'Patient details',
    description: 'Identity, contacts, allergies and medicines',
    sectionIds: ['identity', 'ship', 'allergies_meds'],
  },
  { id: 'airway', title: 'A — Airway', description: 'Airway and immediate support', sectionIds: ['airway'] },
  { id: 'breathing', title: 'B — Breathing', description: 'Respiratory observation', sectionIds: ['breathing'] },
  {
    id: 'circulation',
    title: 'C — Circulation',
    description: 'Perfusion and hemodynamics',
    sectionIds: ['circulation'],
  },
  { id: 'disability', title: 'D — Disability', description: 'Neurologic status', sectionIds: ['disability'] },
  { id: 'exposure', title: 'E — Exposure', description: 'Full-body and temperature findings', sectionIds: ['exposure'] },
  { id: 'problem', title: 'Problem', description: 'Chief complaint and context', sectionIds: ['problem'] },
  { id: 'actions', title: 'Actions', description: 'Treatments and timeline', sectionIds: ['actions', 'observation'] },
]

function scoreTier(score: number): 'g' | 'y' | 'r' {
  if (score >= 85) return 'g'
  if (score >= 60) return 'y'
  return 'r'
}

function patientNameFromIndicators(indicators?: IndicatorsState): string | null {
  const name = String(indicators?.patient_name ?? '').trim()
  return name.length > 0 ? name : null
}

function historyTitle(item: HistoryItem): string {
  const fallback = item.sourceLabel && item.sourceLabel !== 'Form entry' ? item.sourceLabel : 'Unnamed patient'
  return patientNameFromIndicators(item.indicators) ?? fallback
}

function fieldValue(v: string | number | boolean | undefined): string {
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  return String(v ?? '').trim()
}

function toNumber(value: string | number | boolean | undefined): number | null {
  const parsed = Number(String(value ?? '').trim())
  if (Number.isNaN(parsed)) return null
  return parsed
}

function renderField(field: FieldDef, sectionId: string, indicators: IndicatorsState, setIndicators: Dispatch<SetStateAction<IndicatorsState>>) {
  const v = indicators[field.key]
  const id = `f_${sectionId}_${field.key}`
  if (field.type === 'textarea') {
    return (
      <label key={field.key} className="field">
        <span className="fieldLabel">{field.label}</span>
        <textarea
          id={id}
          className="fieldInput textareaSmall"
          placeholder={field.placeholder}
          value={typeof v === 'string' ? v : String(v ?? '')}
          onChange={(e) => setIndicators((p) => ({ ...p, [field.key]: e.target.value }))}
        />
      </label>
    )
  }
  if (field.type === 'checkbox') {
    return (
      <label key={field.key} className="field checkRow">
        <input
          id={id}
          type="checkbox"
          checked={Boolean(v)}
          onChange={(e) => setIndicators((p) => ({ ...p, [field.key]: e.target.checked }))}
        />
        <span className="fieldLabel">{field.label}</span>
      </label>
    )
  }
  if (field.type === 'select') {
    return (
      <label key={field.key} className="field">
        <span className="fieldLabel">{field.label}</span>
        <select
          id={id}
          className="fieldInput"
          value={typeof v === 'string' ? v : String(v ?? '')}
          onChange={(e) => setIndicators((p) => ({ ...p, [field.key]: e.target.value }))}
        >
          {(field.options ?? []).map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
    )
  }
  return (
    <label key={field.key} className="field">
      <span className="fieldLabel">
        {field.label}
        {field.unit ? <span className="unit">{field.unit}</span> : null}
      </span>
      <input
        id={id}
        className="fieldInput"
        type={field.type === 'number' ? 'number' : 'text'}
        placeholder={field.placeholder}
        value={typeof v === 'string' ? v : String(v ?? '')}
        onChange={(e) => setIndicators((p) => ({ ...p, [field.key]: e.target.value }))}
      />
    </label>
  )
}

function App() {
  const [sessionId] = useState(() => crypto.randomUUID())
  const [activeTab, setActiveTab] = useState<UiTab>('form')
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [activeStepId, setActiveStepId] = useState<string>(FORM_STEPS[0].id)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResultV2 | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [pendingQuestions, setPendingQuestions] = useState<string[]>([])
  const [summarySaved, setSummarySaved] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [indicators, setIndicators] = useState<IndicatorsState>(() => defaultIndicatorsState())

  const completeness = useMemo(() => result?.review.completeness_score ?? null, [result])
  const hasAllRequiredVitals = useMemo(() => {
    const hr = toNumber(indicators.pulse_bpm)
    const rr = toNumber(indicators.breathing_frequency)
    const spo2 = toNumber(indicators.spo2_percent)
    const sys = toNumber(indicators.bp_systolic)
    const dia = toNumber(indicators.bp_diastolic)
    const temp = toNumber(indicators.temp_mouth_c) ?? toNumber(indicators.temp_alt_c)
    return [hr, rr, spo2, sys, dia, temp].every((v) => v !== null)
  }, [indicators])

  const vitalsQuality = useMemo((): { level: VitalsQuality; label: string; feedback: string[] } => {
    if (!hasAllRequiredVitals) {
      return {
        level: 'unknown',
        label: 'Incomplete',
        feedback: ['Summary is locked until all vitals are provided (HR, RR, SpO2, BP systolic/diastolic, temperature).'],
      }
    }
    const hr = toNumber(indicators.pulse_bpm) ?? 0
    const rr = toNumber(indicators.breathing_frequency) ?? 0
    const spo2 = toNumber(indicators.spo2_percent) ?? 0
    const sys = toNumber(indicators.bp_systolic) ?? 0
    const dia = toNumber(indicators.bp_diastolic) ?? 0
    const temp = (toNumber(indicators.temp_mouth_c) ?? toNumber(indicators.temp_alt_c)) ?? 0

    let severityPoints = 0
    const feedback: string[] = []

    if (hr < 50 || hr > 120) {
      severityPoints += 2
      feedback.push(`Heart rate is concerning (${hr} bpm).`)
    } else if (hr < 50 || hr > 80) {
      severityPoints += 1
      feedback.push(`Heart rate is outside typical range (${hr} bpm).`)
    }

    if (rr < 10 || rr > 25) {
      severityPoints += 2
      feedback.push(`Respiratory rate is concerning (${rr}/min).`)
    } else if (rr < 12 || rr > 20) {
      severityPoints += 1
      feedback.push(`Respiratory rate is outside typical range (${rr}/min).`)
    }

    if (spo2 <= 90) {
      severityPoints += 3
      feedback.push(`SpO2 is critical (${spo2}%).`)
    } else if (spo2 < 92) {
      severityPoints += 2
      feedback.push(`SpO2 is low (${spo2}%).`)
    } else if (spo2 < 95) {
      severityPoints += 1
      feedback.push(`SpO2 is mildly below target (${spo2}%).`)
    }

    if (sys < 90) {
      severityPoints += 2
      feedback.push(`Systolic blood pressure suggests shock risk (${sys} mmHg).`)
    } else if (sys > 140 || dia > 90 || dia < 60) {
      severityPoints += 1
      feedback.push(`Blood pressure is outside typical range (${sys}/${dia} mmHg).`)
    }

    if (temp < 35 || temp >= 39) {
      severityPoints += 2
      feedback.push(`Temperature is high risk (${temp}°C).`)
    } else if (temp < 36 || temp >= 38) {
      severityPoints += 1
      feedback.push(`Temperature is outside typical range (${temp}°C).`)
    }

    if (severityPoints === 0) {
      return { level: 'green', label: 'Good', feedback: ['Vitals are currently stable and within typical ranges.'] }
    }
    if (severityPoints <= 2) return { level: 'yellow', label: 'Watch', feedback }
    if (severityPoints <= 4) return { level: 'orange', label: 'Concerning', feedback }
    return { level: 'red', label: 'Critical', feedback }
  }, [hasAllRequiredVitals, indicators])

  const summaryReady = useMemo(
    () => Boolean(result) && pendingQuestions.length === 0 && hasAllRequiredVitals,
    [result, pendingQuestions.length, hasAllRequiredVitals],
  )
  const canFinalizeNow = useMemo(() => pendingQuestions.length === 0 && hasAllRequiredVitals, [pendingQuestions.length, hasAllRequiredVitals])

  const canAskDoctor = useMemo(() => {
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

  const activeStepIndex = useMemo(() => FORM_STEPS.findIndex((step) => step.id === activeStepId), [activeStepId])
  const currentStep = activeStepIndex >= 0 ? FORM_STEPS[activeStepIndex] : FORM_STEPS[0]
  const currentStepSections = useMemo<SectionDef[]>(
    () =>
      currentStep.sectionIds
        .map((sectionId) => sections.find((section) => section.id === sectionId))
        .filter((section): section is SectionDef => Boolean(section)),
    [currentStep],
  )

  const patientFacts = useMemo(
    () => [
      { label: 'Name', value: fieldValue(indicators.patient_name) || 'Not provided' },
      { label: 'Birthdate / CPR', value: fieldValue(indicators.birthdate_cpr) || 'Not provided' },
      { label: 'Gender', value: fieldValue(indicators.gender) || 'Not provided' },
      { label: 'Nationality', value: fieldValue(indicators.nationality) || 'Not provided' },
      { label: 'Ship', value: fieldValue(indicators.ship_name) || 'Not provided' },
      { label: 'Position', value: fieldValue(indicators.coordinates) || 'Not provided' },
    ],
    [indicators],
  )

  const vitalsFacts = useMemo(
    () => [
      { label: 'Heart rate', value: fieldValue(indicators.pulse_bpm), unit: 'bpm' },
      { label: 'SpO2', value: fieldValue(indicators.spo2_percent), unit: '%' },
      { label: 'Respiratory rate', value: fieldValue(indicators.breathing_frequency), unit: '/min' },
      { label: 'Blood pressure', value: `${fieldValue(indicators.bp_systolic)}/${fieldValue(indicators.bp_diastolic)}`, unit: 'mmHg' },
      { label: 'Temperature', value: fieldValue(indicators.temp_mouth_c) || fieldValue(indicators.temp_alt_c), unit: '°C' },
    ],
    [indicators],
  )

  useEffect(() => {
    ;(async () => {
      try {
        const items = await listHistory(50)
        setHistory(items)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load history')
      }
    })()
  }, [])

  useEffect(() => {
    const onEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsMenuOpen(false)
    }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [])

  const handleClear = () => {
    setResult(null)
    setError(null)
    setSelectedHistoryId(null)
    setChatMessages([])
    setPendingQuestions([])
    setSummarySaved(false)
    setChatInput('')
    setIndicators(defaultIndicatorsState())
    setActiveTab('form')
    setActiveStepId(FORM_STEPS[0].id)
  }

  const buildReportText = (messages: ChatMessage[]) => {
    const base = indicatorsToReportText(sections, indicators)
    const transcript = messages
      .map((m) => `${m.role === 'user' ? 'Crew' : 'Doctor'}: ${m.text}`)
      .join('\n')
      .trim()

    if (!transcript) return base
    return `${base}\n\nConversation updates:\n${transcript}`
  }

  const buildAssistantMessage = (assistantMessage: string, questionsToShow: string[]) => {
    const parts: string[] = [assistantMessage]
    if (questionsToShow.length > 0) {
      parts.push(
        ['Important follow-up questions:', ...questionsToShow.map((q) => `- ${q}`)].join('\n'),
      )
    }
    return parts.join('\n\n').trim()
  }

  const saveSummaryToHistory = async (res: AnalyzeResultV2, messages: ChatMessage[]) => {
    if (summarySaved) return
    const reportText = buildReportText(messages)
    const itemNoId: Omit<HistoryItem, 'id'> = {
      createdAt: Date.now(),
      sourceLabel: patientNameFromIndicators(indicators) ?? 'Unnamed patient',
      reportText,
      result: res,
      mode: 'form',
      indicators,
    }
    const saved = await createHistory(itemNoId)
    setHistory((prev) => [saved, ...prev].slice(0, 50))
    setSelectedHistoryId(saved.id)
    setSummarySaved(true)
  }

  const finalizeCase = async (messages: ChatMessage[]) => {
    if (summarySaved || !canFinalizeNow) return
    const reportText = buildReportText(messages)
    const res = await finalizeSummary({ session_id: sessionId, report_text: reportText, locale: 'en-UK' })
    setResult(res)
    await saveSummaryToHistory(res, messages)
    setActiveTab('summary')
  }

  const askDoctor = async (userMessage?: string) => {
    if (!canAskDoctor) return
    setActiveTab('chat')
    setIsMenuOpen(false)
    setBusy(true)
    setError(null)

    const trimmed = (userMessage ?? '').trim()
    const nextMessages = trimmed
      ? [...chatMessages, { id: crypto.randomUUID(), role: 'user' as const, text: trimmed, createdAt: Date.now() }]
      : [...chatMessages]
    if (trimmed) setChatMessages(nextMessages)

    try {
      const reportText = buildReportText(nextMessages)
      const turn = await chatDoctorTurn({
        session_id: sessionId,
        report_text: reportText,
        locale: 'en-UK',
        user_message: trimmed,
      })
      setPendingQuestions(turn.pending_questions)
      const questionsToShow = turn.pending_questions.slice(0, 3)
      const doctorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: buildAssistantMessage(turn.assistant_message, questionsToShow),
        createdAt: Date.now(),
      }
      const allMessages = [...nextMessages, doctorMessage]
      setChatMessages(allMessages)
      const readyNow = turn.can_finalize_summary && hasAllRequiredVitals
      if (readyNow) {
        await finalizeCase(allMessages)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="appShell">
      {isMenuOpen && <button type="button" className="menuBackdrop" aria-label="Close menu" onClick={() => setIsMenuOpen(false)} />}
      <aside className={`sidebar ${isMenuOpen ? 'open' : ''}`}>
        <div className="sidebarTop">
          <div className="logoCard">
            <div className="logoCrown">♛</div>
            <div className="logoArc" />
            <div className="logoText">DANISH MARITIME AUTHORITY</div>
          </div>

          <div className="brand">
            <div className="brandAvatar">{String(indicators.patient_name || 'P').trim().slice(0, 1).toUpperCase()}</div>
            <div className="brandCopy">
              <div className="brandName">{patientNameFromIndicators(indicators) ?? 'Draft patient'}</div>
              <div className="brandSub">{new Date().toLocaleDateString()}</div>
            </div>
          </div>

          <button
            className="button sidebarBtn"
            onClick={() => {
              handleClear()
              setIsMenuOpen(false)
            }}
            disabled={busy}
          >
            New report
          </button>

          <div className="menuQuickLinks">
            <button
              type="button"
              className={`quickLink ${activeTab === 'form' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('form')
                setIsMenuOpen(false)
              }}
            >
              Form
            </button>
            <button
              type="button"
              className={`quickLink ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('chat')
                setIsMenuOpen(false)
              }}
            >
              Chat
            </button>
            <button
              type="button"
              className={`quickLink ${activeTab === 'summary' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('summary')
                setIsMenuOpen(false)
              }}
            >
              Summary
            </button>
          </div>
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
                    setChatMessages([])
                    setPendingQuestions([])
                    setSummarySaved(true)
                    if (h.indicators) setIndicators(h.indicators)
                    setActiveTab('summary')
                    setIsMenuOpen(false)
                  }}
                  disabled={busy}
                >
                  <div className="historyTop">
                    <div className="historyTitle">{historyTitle(h)}</div>
                    <div className={`historyScore s-${scoreTier(score)}`}>{score}</div>
                  </div>
                  <div className="historyMeta">{when}</div>
                  <button
                    type="button"
                    className="iconBtn"
                    title="Delete report"
                    aria-label="Delete report"
                    onClick={async (e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      try {
                        await deleteHistory(h.id)
                        setHistory((prev) => prev.filter((x) => x.id !== h.id))
                        if (selectedHistoryId === h.id) {
                          setSelectedHistoryId(null)
                          setResult(null)
                          setActiveTab('form')
                        }
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Failed to delete report')
                      }
                    }}
                    disabled={busy}
                  >
                    ✕
                  </button>
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
                ;(async () => {
                  try {
                    await clearHistory()
                    setHistory([])
                    setSelectedHistoryId(null)
                    setResult(null)
                    setPendingQuestions([])
                    setSummarySaved(false)
                    setActiveTab('form')
                    setIsMenuOpen(false)
                  } catch (e) {
                    setError(e instanceof Error ? e.message : 'Failed to clear history')
                  }
                })()
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
          <button type="button" className="menuToggle" aria-label="Open menu" onClick={() => setIsMenuOpen(true)}>
            <span className="menuIcon" />
          </button>
          <div>
            <h1>Radio Medical Assistant</h1>
            <p className="subtitle">
              Structured workflow: complete the form by section, collaborate with the AI doctor in chat, and review a final
              clinical summary.
            </p>
          </div>
          <div className="meta">
            <div className="metaLabel">Session</div>
            <div className="metaValue">{sessionId}</div>
          </div>
        </header>

        <main className="workspace card">
          <div className="tabsRow">
            <button type="button" className={`tabBtn ${activeTab === 'form' ? 'active' : ''}`} onClick={() => setActiveTab('form')}>
              Form
            </button>
            <button type="button" className={`tabBtn ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
              Chat
            </button>
            <button
              type="button"
              className={`tabBtn ${activeTab === 'summary' ? 'active' : ''}`}
              onClick={async () => {
                if (!result && canFinalizeNow && chatMessages.length > 0) {
                  setBusy(true)
                  setError(null)
                  try {
                    await finalizeCase(chatMessages)
                  } catch (e) {
                    setError(e instanceof Error ? e.message : 'Unknown error')
                  } finally {
                    setBusy(false)
                  }
                  return
                }
                if (summaryReady || summarySaved || Boolean(selectedHistoryId)) setActiveTab('summary')
              }}
              disabled={!summaryReady && !summarySaved && !selectedHistoryId && !canFinalizeNow}
            >
              Summary
            </button>
          </div>

          {activeTab === 'form' && (
            <section className="tabPanel">
              <div className="stepper">
                {FORM_STEPS.map((step, index) => (
                  <button
                    type="button"
                    key={step.id}
                    className={`stepBtn ${step.id === currentStep.id ? 'active' : ''}`}
                    onClick={() => setActiveStepId(step.id)}
                  >
                    <span className="stepIndex">{index + 1}</span>
                    <span className="stepText">{step.title}</span>
                  </button>
                ))}
              </div>

              <div className="formSectionCard">
                <div className="formSectionHeader">
                  <div className="formSectionTitle">{currentStep.title}</div>
                  <div className="formSectionDesc">{currentStep.description}</div>
                </div>

                <div className="formGrid">
                  {currentStepSections.map((sec) => (
                    <div key={sec.id} className="formSection">
                      {currentStepSections.length > 1 && <div className="nestedSectionTitle">{sec.title}</div>}
                      {sec.description && <div className="formSectionDesc">{sec.description}</div>}
                      <div className="fields">{sec.fields.map((f) => renderField(f, sec.id, indicators, setIndicators))}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="cardFooter">
                <button
                  className="button ghost"
                  onClick={() => setActiveStepId(FORM_STEPS[Math.max(0, activeStepIndex - 1)].id)}
                  disabled={activeStepIndex <= 0 || busy}
                >
                  ← Previous section
                </button>
                <div className="footerActions">
                  <button
                    className="button ghost"
                    onClick={() => setActiveStepId(FORM_STEPS[Math.min(FORM_STEPS.length - 1, activeStepIndex + 1)].id)}
                    disabled={activeStepIndex >= FORM_STEPS.length - 1 || busy}
                  >
                    Next section →
                  </button>
                  <button className="button" onClick={() => void askDoctor()} disabled={!canAskDoctor}>
                    {busy ? 'Analyzing…' : 'Send to AI doctor'}
                  </button>
                </div>
              </div>
            </section>
          )}

          {activeTab === 'chat' && (
            <section className="tabPanel chatPanel">
              <div className="chatStream">
                {(pendingQuestions.length > 0 || !hasAllRequiredVitals) && (
                  <div className="chatGateNotice">
                    <div className="chatGateTitle">Summary locked</div>
                    {!hasAllRequiredVitals && <div>Complete all required vitals before the final summary can be generated.</div>}
                    {pendingQuestions.length > 0 && (
                      <div>{pendingQuestions.length} follow-up question(s) still need to be answered in chat.</div>
                    )}
                  </div>
                )}
                {chatMessages.length === 0 ? (
                  <div className="empty">Send the current form to start the doctor conversation.</div>
                ) : (
                  chatMessages.map((message) => (
                    <div key={message.id} className={`chatBubble ${message.role === 'user' ? 'user' : 'assistant'}`}>
                      <div className="chatText">{message.text}</div>
                      <div className="chatTime">{new Date(message.createdAt).toLocaleTimeString()}</div>
                    </div>
                  ))
                )}
                {busy && (
                  <div className="chatBubble assistant thinkingBubble">
                    <span className="thinkingSpinner" aria-hidden="true" />
                    AI doctor is reviewing the case...
                  </div>
                )}
              </div>

              <div className="chatComposer">
                <input
                  className="fieldInput"
                  placeholder="Type additional findings, answers, or updates…"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      const msg = chatInput.trim()
                      if (!msg) return
                      setChatInput('')
                      void askDoctor(msg)
                    }
                  }}
                />
                <button
                  className="button"
                  onClick={() => {
                    const msg = chatInput.trim()
                    if (!msg) return
                    setChatInput('')
                    void askDoctor(msg)
                  }}
                  disabled={busy || chatInput.trim().length === 0}
                >
                  Send
                </button>
                <button
                  className="button ghost"
                  onClick={async () => {
                    if (!result && canFinalizeNow && chatMessages.length > 0) {
                      setBusy(true)
                      setError(null)
                      try {
                        await finalizeCase(chatMessages)
                      } catch (e) {
                        setError(e instanceof Error ? e.message : 'Unknown error')
                      } finally {
                        setBusy(false)
                      }
                      return
                    }
                    setActiveTab('summary')
                  }}
                  disabled={!summaryReady && !summarySaved && !selectedHistoryId && !canFinalizeNow}
                >
                  View summary
                </button>
              </div>
            </section>
          )}

          {activeTab === 'summary' && (
            <section className="tabPanel summaryPanel">
              {!result ? (
                <div className="empty">No summary yet. Complete the form and start a chat with the AI doctor first.</div>
              ) : (
                <>
                  <div className="summaryCard">
                    <div className="summaryTitle">Patient details</div>
                    <div className="factsGrid">
                      {patientFacts.map((fact) => (
                        <div key={fact.label} className="factItem">
                          <div className="factLabel">{fact.label}</div>
                          <div className="factValue">{fact.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="summaryCard">
                    <div className="summaryTitle">Clinical picture and vitals</div>
                    <div className="clinicalBody">
                      <div className="vitalsDialWrap">
                        <div className={`vitalsDial vitals-${vitalsQuality.level}`}>
                          <div className="vitalsDialInner">
                            <div className="vitalsDialValue">{vitalsQuality.label}</div>
                            <div className="vitalsDialLabel">Vitals quality</div>
                          </div>
                        </div>
                      </div>
                      <div className="factsGrid">
                        <div className="factItem wide">
                          <div className="factLabel">Chief complaint</div>
                          <div className="factValue">{fieldValue(indicators.problem_description) || 'Not provided'}</div>
                        </div>
                        {vitalsFacts.map((v) => (
                          <div key={v.label} className="factItem">
                            <div className="factLabel">{v.label}</div>
                            <div className="factValue">
                              {v.value && v.value !== '/' ? `${v.value}${v.unit ? ` ${v.unit}` : ''}` : 'Not provided'}
                            </div>
                          </div>
                        ))}
                        <div className="factItem wide">
                          <div className="factLabel">Vitals feedback</div>
                          <ul className="bullets">
                            {vitalsQuality.feedback.map((line, idx) => (
                              <li key={idx}>{line}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="summaryCard">
                    <div className="summaryTitle">AI assessment</div>
                    <div className="scoreChips">
                      {completeness !== null && (
                        <div className={`score score-tier-${scoreTier(completeness)}`}>
                          <div className="scoreLabel">Completeness</div>
                          <div className="scoreValue">{completeness}/100</div>
                        </div>
                      )}
                      <div className={`qualityPill q-${vitalsQuality.level}`}>Vitals quality: {vitalsQuality.label}</div>
                      {result.patient_evaluation && (
                        <div className={`statusPill st-${result.patient_evaluation.status}`}>
                          {result.patient_evaluation.status.toUpperCase()}
                        </div>
                      )}
                    </div>
                    <div className="summaryBody">
                      <div className="subTitle">Recommended next step</div>
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
                          <div className="subTitle">Pending questions from AI doctor</div>
                          <ul className="bullets">
                            {result.response.questions_for_participants.map((q, idx) => (
                              <li key={idx}>{q}</li>
                            ))}
                          </ul>
                        </>
                      )}
                      {result.patient_evaluation?.suspected_problems?.length ? (
                        <>
                          <div className="subTitle">Suspected problems</div>
                          <ul className="bullets">
                            {result.patient_evaluation.suspected_problems.map((p, idx) => (
                              <li key={idx}>{p}</li>
                            ))}
                          </ul>
                        </>
                      ) : null}
                      {result.patient_evaluation?.red_flags?.length ? (
                        <>
                          <div className="subTitle">Red flags</div>
                          <ul className="bullets">
                            {result.patient_evaluation.red_flags.map((flag, idx) => (
                              <li key={idx}>{flag}</li>
                            ))}
                          </ul>
                        </>
                      ) : null}
                    </div>
                  </div>
                </>
              )}
            </section>
          )}

          {error && <div className="error">Error: {error}</div>}
        </main>
      </div>
    </div>
  )
}

export default App
