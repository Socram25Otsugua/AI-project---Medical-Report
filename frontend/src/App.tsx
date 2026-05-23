import { useEffect, useMemo, useState, type Dispatch, type ReactNode, type SetStateAction } from 'react'
import './App.css'
import { chatDoctorTurn, createHistory, deleteHistory, finalizeSummary, listHistory } from './api'
import type { AnalyzeResultV2 } from './types'
import type { HistoryItem } from './history'
import { defaultIndicatorsState, OBSERVATION_CHART_STATE_KEY, sections, type FieldDef, type IndicatorsState, type SectionDef } from './indicators/schema'
import { indicatorsToReportText } from './indicators/render'
import { ObservationChart } from './components/ObservationChart'
import { ClinicalSummary } from './components/ClinicalSummary'
import {
  columnHasAnyValue,
  createEmptyObservationChart,
  getFirstColumnMissingFields,
  isObservationChartReadyForSend,
  parseObservationChart,
  serializeObservationChart,
  type ObservationChartData,
} from './indicators/observationChart'
import { clinicalTierFromHistory, completenessTierFromIndicators, vitalsQualityLevel } from './indicators/reportIndicators'

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
  shortLabel: string
  description: string
  sectionIds: string[]
}

const FORM_STEPS: FormStep[] = [
  {
    id: 'patient',
    title: 'Patient & vessel',
    shortLabel: 'P — Patient',
    description: 'Identity, vessel contact details, allergies and medicines',
    sectionIds: ['identity', 'ship', 'allergies_meds'],
  },
  {
    id: 'airway',
    title: 'A — Airway',
    shortLabel: 'A — Airway',
    description: 'Airway and immediate support',
    sectionIds: ['airway'],
  },
  {
    id: 'breathing',
    title: 'B — Breathing',
    shortLabel: 'B — Breathing',
    description: 'Respiratory observation',
    sectionIds: ['breathing'],
  },
  {
    id: 'circulation',
    title: 'C — Circulation',
    shortLabel: 'C — Circulation',
    description: 'Perfusion and hemodynamics',
    sectionIds: ['circulation'],
  },
  {
    id: 'disability',
    title: 'D — Disability',
    shortLabel: 'D — Disability',
    description: 'Neurologic status',
    sectionIds: ['disability'],
  },
  {
    id: 'exposure',
    title: 'E — Exposure',
    shortLabel: 'E — Exposure',
    description: 'Full-body and temperature findings',
    sectionIds: ['exposure'],
  },
  {
    id: 'problem',
    title: 'Problem',
    shortLabel: 'Problem',
    description: 'Chief complaint and context',
    sectionIds: ['problem'],
  },
  {
    id: 'actions',
    title: 'Actions',
    shortLabel: 'Actions',
    description: 'Treatments and timeline',
    sectionIds: ['actions', 'observation'],
  },
]

function fieldFromSections(sectionId: string, key: string): FieldDef | undefined {
  return sections.find((section) => section.id === sectionId)?.fields.find((field) => field.key === key)
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

function createInitialIndicators(): IndicatorsState {
  return {
    ...defaultIndicatorsState(),
    [OBSERVATION_CHART_STATE_KEY]: serializeObservationChart(createEmptyObservationChart()),
  }
}

function renderField(
  field: FieldDef,
  sectionId: string,
  indicators: IndicatorsState,
  setIndicators: Dispatch<SetStateAction<IndicatorsState>>,
  disabled = false,
  options?: { labelOverride?: string; hint?: string },
) {
  const v = indicators[field.key]
  const id = `f_${sectionId}_${field.key}`
  const label = options?.labelOverride ?? field.label
  const inputWrap = (control: ReactNode) =>
    options?.hint ? (
      <div className="fieldWithHint">
        {control}
        <span className="fieldHint">{options.hint}</span>
      </div>
    ) : (
      control
    )
  if (field.type === 'textarea') {
    return (
      <label key={field.key} className="field">
        <span className="fieldLabel">{label}</span>
        <textarea
          id={id}
          className="fieldInput textareaSmall"
          placeholder={field.placeholder}
          value={typeof v === 'string' ? v : String(v ?? '')}
          disabled={disabled}
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
          disabled={disabled}
          onChange={(e) => setIndicators((p) => ({ ...p, [field.key]: e.target.checked }))}
        />
        <span className="fieldLabel">{label}</span>
      </label>
    )
  }
  if (field.type === 'select') {
    return (
      <label key={field.key} className="field">
        <span className="fieldLabel">{label}</span>
        <select
          id={id}
          className="fieldInput"
          value={typeof v === 'string' ? v : String(v ?? '')}
          disabled={disabled}
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
        {label}
        {field.unit ? <span className="unit">{field.unit}</span> : null}
      </span>
      {inputWrap(
        <input
          id={id}
          className="fieldInput"
          type={field.type === 'number' ? 'number' : 'text'}
          placeholder={field.placeholder}
          value={typeof v === 'string' ? v : String(v ?? '')}
          disabled={disabled}
          onChange={(e) => setIndicators((p) => ({ ...p, [field.key]: e.target.value }))}
        />,
      )}
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
  const [indicators, setIndicators] = useState<IndicatorsState>(() => createInitialIndicators())
  const [formLockedToDoctor, setFormLockedToDoctor] = useState(false)
  const [lockedObservationColumnIndexes, setLockedObservationColumnIndexes] = useState<number[]>([])
  const [sendAttempted, setSendAttempted] = useState(false)
  const [historySearch, setHistorySearch] = useState('')
  const [lastAutosaveAt, setLastAutosaveAt] = useState<number | null>(null)
  const [autosaveTick, setAutosaveTick] = useState(0)

  const observationChart = useMemo(
    () => parseObservationChart(indicators[OBSERVATION_CHART_STATE_KEY]),
    [indicators],
  )
  const missingObservationFields = useMemo(
    () => getFirstColumnMissingFields(observationChart),
    [observationChart],
  )
  const observationChartReady = useMemo(
    () => isObservationChartReadyForSend(observationChart),
    [observationChart],
  )

  const hasAllRequiredVitals = useMemo(() => {
    const hr = toNumber(indicators.pulse_bpm)
    const rr = toNumber(indicators.breathing_frequency)
    const spo2 = toNumber(indicators.spo2_percent)
    const sys = toNumber(indicators.bp_systolic)
    const dia = toNumber(indicators.bp_diastolic)
    const temp = toNumber(indicators.temp_mouth_c) ?? toNumber(indicators.temp_alt_c)
    if ([hr, rr, spo2, sys, dia, temp].every((v) => v !== null)) return true

    const col = observationChart.columns[0] ?? {}
    const chartHr = toNumber(col.heart_rate)
    const chartRr = toNumber(col.breathing_frequency)
    const chartSpo2 = toNumber(col.spo2)
    const bpMatch = String(col.blood_pressure ?? '').trim().match(/(\d+)\s*\/\s*(\d+)/)
    const chartSys = bpMatch ? Number(bpMatch[1]) : null
    const chartDia = bpMatch ? Number(bpMatch[2]) : null
    const chartTemp = toNumber(col.temperature)
    return [chartHr, chartRr, chartSpo2, chartSys, chartDia, chartTemp].every((v) => v !== null)
  }, [indicators, observationChart])

  const vitalsQuality = useMemo((): { level: VitalsQuality; label: string; feedback: string[] } => {
    const level = vitalsQualityLevel(indicators)
    if (level === 'unknown') {
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

    const feedback: string[] = []

    if (hr < 50 || hr > 120) feedback.push(`Heart rate is concerning (${hr} bpm).`)
    else if (hr < 50 || hr > 80) feedback.push(`Heart rate is outside typical range (${hr} bpm).`)

    if (rr < 10 || rr > 25) feedback.push(`Respiratory rate is concerning (${rr}/min).`)
    else if (rr < 12 || rr > 20) feedback.push(`Respiratory rate is outside typical range (${rr}/min).`)

    if (spo2 <= 90) feedback.push(`SpO2 is critical (${spo2}%).`)
    else if (spo2 < 92) feedback.push(`SpO2 is low (${spo2}%).`)
    else if (spo2 < 95) feedback.push(`SpO2 is mildly below target (${spo2}%).`)

    if (sys < 90) feedback.push(`Systolic blood pressure suggests shock risk (${sys} mmHg).`)
    else if (sys > 140 || dia > 90 || dia < 60) feedback.push(`Blood pressure is outside typical range (${sys}/${dia} mmHg).`)

    if (temp < 35 || temp >= 39) feedback.push(`Temperature is high risk (${temp}°C).`)
    else if (temp < 36 || temp >= 38) feedback.push(`Temperature is outside typical range (${temp}°C).`)

    if (level === 'green') {
      return { level: 'green', label: 'Good', feedback: ['Vitals are currently stable and within typical ranges.'] }
    }
    if (level === 'yellow') return { level: 'yellow', label: 'Watch', feedback }
    if (level === 'orange') return { level: 'orange', label: 'Concerning', feedback }
    return { level: 'red', label: 'Critical', feedback }
  }, [indicators])

  const summaryReady = useMemo(
    () => Boolean(result) && pendingQuestions.length === 0 && hasAllRequiredVitals,
    [result, pendingQuestions.length, hasAllRequiredVitals],
  )
  const canFinalizeNow = useMemo(() => pendingQuestions.length === 0 && hasAllRequiredVitals, [pendingQuestions.length, hasAllRequiredVitals])
  const summaryBlockReason = useMemo(() => {
    if (!hasAllRequiredVitals) return 'Complete all required vitals first.'
    if (pendingQuestions.length > 0) return 'Answer all follow-up chat questions first.'
    if (chatMessages.length === 0) return 'Start chat at least once before generating summary.'
    return null
  }, [hasAllRequiredVitals, pendingQuestions.length, chatMessages.length])

  const canAskDoctor = useMemo(() => {
    if (busy) return false
    if (!observationChartReady) return false
    const name = String(indicators.patient_name ?? '').trim()
    const problem = String(indicators.problem_description ?? '').trim()
    const anyVital =
      String(indicators.spo2_percent ?? '').trim() !== '' ||
      String(indicators.pulse_bpm ?? '').trim() !== '' ||
      String(indicators.bp_systolic ?? '').trim() !== '' ||
      String(indicators.breathing_frequency ?? '').trim() !== ''
    return (name.length >= 2 && problem.length >= 10) || anyVital
  }, [busy, indicators, observationChartReady])

  const showChatTab = formLockedToDoctor || chatMessages.length > 0
  const showSummaryTab =
    Boolean(result) ||
    summarySaved ||
    Boolean(selectedHistoryId) ||
    (showChatTab && chatMessages.length > 0 && (canFinalizeNow || pendingQuestions.length === 0))

  const updateObservationChart = (chart: ObservationChartData) => {
    setIndicators((prev) => ({
      ...prev,
      [OBSERVATION_CHART_STATE_KEY]: serializeObservationChart(chart),
    }))
  }

  const filteredHistory = useMemo(() => {
    const query = historySearch.trim().toLowerCase()
    if (!query) return history
    return history.filter((item) => historyTitle(item).toLowerCase().includes(query))
  }, [history, historySearch])

  const autosaveLabel = useMemo(() => {
    if (!lastAutosaveAt) return 'Draft autosaved · just now'
    const seconds = Math.max(0, Math.floor((Date.now() - lastAutosaveAt) / 1000))
    if (seconds < 5) return 'Draft autosaved · just now'
    if (seconds < 60) return `Draft autosaved · ${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    return `Draft autosaved · ${minutes}m ago`
  }, [lastAutosaveAt, autosaveTick])

  const activeStepIndex = useMemo(() => FORM_STEPS.findIndex((step) => step.id === activeStepId), [activeStepId])
  const currentStep = activeStepIndex >= 0 ? FORM_STEPS[activeStepIndex] : FORM_STEPS[0]
  const progressPercent = useMemo(
    () => Math.round(((activeStepIndex + 1) / FORM_STEPS.length) * 100),
    [activeStepIndex],
  )
  const currentStepSections = useMemo<SectionDef[]>(
    () =>
      currentStep.sectionIds
        .map((sectionId) => sections.find((section) => section.id === sectionId))
        .filter((section): section is SectionDef => Boolean(section)),
    [currentStep],
  )

  useEffect(() => {
    const timer = window.setTimeout(() => {
      localStorage.setItem(`draft_${sessionId}`, JSON.stringify(indicators))
      setLastAutosaveAt(Date.now())
    }, 800)
    return () => window.clearTimeout(timer)
  }, [indicators, sessionId])

  useEffect(() => {
    const timer = window.setInterval(() => setAutosaveTick((value) => value + 1), 1000)
    return () => window.clearInterval(timer)
  }, [])

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

  useEffect(() => {
    if (activeTab === 'chat') setActiveTab('form')
    if (activeTab === 'summary' && !showSummaryTab) setActiveTab('form')
  }, [activeTab, showSummaryTab])

  const handleClear = () => {
    setResult(null)
    setError(null)
    setSelectedHistoryId(null)
    setChatMessages([])
    setPendingQuestions([])
    setSummarySaved(false)
    setChatInput('')
    setFormLockedToDoctor(false)
    setLockedObservationColumnIndexes([])
    setSendAttempted(false)
    setIndicators(createInitialIndicators())
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

  const finalizeCase = async (messages: ChatMessage[], options?: { switchToSummary?: boolean }) => {
    if (!canFinalizeNow) return
    const reportText = buildReportText(messages)
    const res = await finalizeSummary({ session_id: sessionId, report_text: reportText, locale: 'en-UK' })
    setResult(res)
    if (!summarySaved) {
      await saveSummaryToHistory(res, messages)
    }
    if (options?.switchToSummary !== false) {
      setActiveTab('summary')
    }
  }

  const askDoctor = async (userMessage?: string) => {
    if (busy) return
    if (!canAskDoctor) {
      setSendAttempted(true)
      if (!observationChartReady) {
        setError(null)
        setActiveStepId('actions')
        setActiveTab('form')
        return
      }
      setError('Add patient name and problem description, or at least one ABCDE vital, before sending to the AI doctor.')
      return
    }
    setActiveTab('form')
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
      if (!formLockedToDoctor) {
        setFormLockedToDoctor(true)
        setActiveStepId('actions')
        setLockedObservationColumnIndexes(
          observationChart.columns
            .map((column, index) => (columnHasAnyValue(column) ? index : -1))
            .filter((index) => index >= 0),
        )
      }
      setPendingQuestions(turn.pending_questions ?? [])
      const questionsToShow = (turn.pending_questions ?? []).slice(0, 3)
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
        await finalizeCase(allMessages, { switchToSummary: !result })
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setBusy(false)
    }
  }

  const openSummaryView = async () => {
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
    if (summaryReady || summarySaved || Boolean(selectedHistoryId)) {
      setActiveTab('summary')
      return
    }
    setError(summaryBlockReason ?? 'Summary is not ready yet.')
  }

  const renderStepFormContent = () => {
    if (currentStep.id === 'patient') {
      const nameField = fieldFromSections('identity', 'patient_name')
      const birthField = fieldFromSections('identity', 'birthdate_cpr')
      const nationalityField = fieldFromSections('identity', 'nationality')
      const utcField = fieldFromSections('identity', 'utc_time')
      const shipNameField = fieldFromSections('ship', 'ship_name')
      const satelliteField = fieldFromSections('ship', 'satellite_call_no')
      const extraIdentityFields =
        sections
          .find((section) => section.id === 'identity')
          ?.fields.filter((field) => !['patient_name', 'birthdate_cpr', 'nationality', 'utc_time'].includes(field.key)) ?? []
      const extraShipFields =
        sections
          .find((section) => section.id === 'ship')
          ?.fields.filter((field) => !['ship_name', 'satellite_call_no'].includes(field.key)) ?? []
      const allergiesSection = sections.find((section) => section.id === 'allergies_meds')

      return (
        <div className="formGrid">
          <div className="fields">
            {nameField
              ? renderField(nameField, 'identity', indicators, setIndicators, formLockedToDoctor, {
                  labelOverride: 'Full name',
                })
              : null}
            {birthField ? renderField(birthField, 'identity', indicators, setIndicators, formLockedToDoctor) : null}
            {nationalityField
              ? renderField(nationalityField, 'identity', indicators, setIndicators, formLockedToDoctor)
              : null}
            {utcField
              ? renderField(utcField, 'identity', indicators, setIndicators, formLockedToDoctor, { hint: '24h' })
              : null}
          </div>

          <div className="sectionDivider">Vessel</div>

          <div className="fields">
            {shipNameField ? renderField(shipNameField, 'ship', indicators, setIndicators, formLockedToDoctor) : null}
            {satelliteField ? renderField(satelliteField, 'ship', indicators, setIndicators, formLockedToDoctor) : null}
          </div>

          {(extraIdentityFields.length > 0 || extraShipFields.length > 0 || allergiesSection) && (
            <>
              <div className="nestedSectionTitle">Additional details</div>
              {extraIdentityFields.length > 0 && (
                <div className="fields">
                  {extraIdentityFields.map((field) =>
                    renderField(field, 'identity', indicators, setIndicators, formLockedToDoctor),
                  )}
                </div>
              )}
              {extraShipFields.length > 0 && (
                <div className="fields">
                  {extraShipFields.map((field) =>
                    renderField(field, 'ship', indicators, setIndicators, formLockedToDoctor),
                  )}
                </div>
              )}
              {allergiesSection && (
                <div className="fields">
                  {allergiesSection.fields.map((field) =>
                    renderField(field, allergiesSection.id, indicators, setIndicators, formLockedToDoctor),
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )
    }

    return (
      <div className="formGrid">
        {currentStepSections.map((sec) => (
          <div key={sec.id} className="formSection">
            {currentStepSections.length > 1 && <div className="nestedSectionTitle">{sec.title}</div>}
            {sec.description && <div className="formSectionDesc">{sec.description}</div>}
            {sec.id === 'observation' ? (
              <ObservationChart
                chart={observationChart}
                onChange={updateObservationChart}
                lockedColumnIndexes={lockedObservationColumnIndexes}
                missingMandatoryLabels={missingObservationFields}
                showValidation={sendAttempted && !observationChartReady}
              />
            ) : (
              <div className="fields">
                {sec.fields.map((f) => renderField(f, sec.id, indicators, setIndicators, formLockedToDoctor))}
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const chatPanel = (
    <aside className="chatCard">
      <div className="chatCardHeader">
        <div className="chatDoctorIcon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path
              d="M9 3h6a2 2 0 0 1 2 2v1h2a2 2 0 0 1 2 2v3a6 6 0 0 1-6 6h-1.2l-2.3 2.3a1 1 0 0 1-1.7-.7V17H9a6 6 0 0 1-6-6V8a2 2 0 0 1 2-2h2V5a2 2 0 0 1 2-2Z"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinejoin="round"
            />
            <path d="M8 10h8M8 13h5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <div className="chatDoctorTitle">AI Doctor</div>
          <div className="chatDoctorStatus">Online — responds in seconds</div>
        </div>
      </div>

      <div className="chatStream">
        {!hasAllRequiredVitals && chatMessages.length > 0 && (
          <div className="chatGateNotice">
            <div className="chatGateTitle">Summary locked</div>
            <div>Complete all required vitals before the clinical summary can be generated.</div>
          </div>
        )}
        {hasAllRequiredVitals && pendingQuestions.length > 0 && (
          <div className="chatGateNotice">
            <div className="chatGateTitle">Clinical question pending</div>
            <div>Answer the follow-up question below, then open the summary.</div>
          </div>
        )}
        {chatMessages.length === 0 ? (
          <div className="chatWelcome">
            I&apos;m your radio medical doctor for this session. Complete the form on the left, then send me the case when
            you&apos;re ready — I&apos;ll ask focused follow-up questions and help you reach a safe clinical summary.
          </div>
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
          className="fieldInput chatComposerInput"
          placeholder="Message the AI doctor..."
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
          type="button"
          className="chatSendBtn"
          aria-label="Send message"
          onClick={() => {
            const msg = chatInput.trim()
            if (!msg) return
            setChatInput('')
            void askDoctor(msg)
          }}
          disabled={busy || chatInput.trim().length === 0}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="m5 12 14-7-4 7 4 7-14-7Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    </aside>
  )

  return (
    <div className="appShell">
      {isMenuOpen && <button type="button" className="menuBackdrop" aria-label="Close menu" onClick={() => setIsMenuOpen(false)} />}
      <aside className={`sidebar ${isMenuOpen ? 'open' : ''}`}>
        <div className="sidebarTop">
          <div className="sidebarBrand">
            <div className="sidebarBrandIcon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 3c-3.2 0-5.8 2.1-6.8 5.1-.4 1.2-.2 2.5.5 3.6l1.3 2.1v4.7c0 .8.7 1.5 1.5 1.5h6.9c.8 0 1.5-.7 1.5-1.5v-4.7l1.3-2.1c.7-1.1.9-2.4.5-3.6C17.8 5.1 15.2 3 12 3Z"
                  stroke="currentColor"
                  strokeWidth="1.6"
                />
                <circle cx="12" cy="9.5" r="1.2" fill="currentColor" />
                <path d="M8.5 20.5h7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </div>
            <div className="sidebarBrandText">
              <div className="sidebarBrandTitle">Danish Maritime</div>
              <div className="sidebarBrandSub">Authority · Radio Medical</div>
            </div>
          </div>

          <button
            type="button"
            className="newReportBtn"
            onClick={() => {
              handleClear()
              setIsMenuOpen(false)
            }}
            disabled={busy}
          >
            <span className="newReportIcon" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <span className="newReportCopy">
              <span className="newReportTitle">New report</span>
              <span className="newReportHint">Start a fresh assessment</span>
            </span>
            <span className="newReportChevron" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="m9 6 6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </button>

          <div className="sidebarSearchWrap">
            <span className="sidebarSearchIcon" aria-hidden="true">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
                <circle cx="11" cy="11" r="6.5" stroke="currentColor" strokeWidth="1.8" />
                <path d="m16.5 16.5 4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </span>
            <input
              className="sidebarSearch"
              placeholder="Search reports..."
              value={historySearch}
              onChange={(e) => setHistorySearch(e.target.value)}
            />
          </div>
        </div>

        <div className="sidebarSectionHead">
          <div className="sidebarSectionTitle">History</div>
          <div className="sidebarSectionCount">{filteredHistory.length}</div>
        </div>

        {filteredHistory.length === 0 ? (
          <div className="sidebarEmpty">{history.length === 0 ? 'No saved reports yet.' : 'No matching reports.'}</div>
        ) : (
          <div className="historyList">
            {filteredHistory.map((h) => {
              const when = new Date(h.createdAt).toLocaleString()
              const active = h.id === selectedHistoryId
              const completenessTier = completenessTierFromIndicators(h.indicators)
              const clinicalTier = clinicalTierFromHistory(h)
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
                    setFormLockedToDoctor(true)
                    if (h.indicators) {
                      setIndicators(h.indicators)
                      const chart = parseObservationChart(h.indicators[OBSERVATION_CHART_STATE_KEY])
                      setLockedObservationColumnIndexes(
                        chart.columns
                          .map((column, index) => (columnHasAnyValue(column) ? index : -1))
                          .filter((index) => index >= 0),
                      )
                    }
                    setActiveTab('summary')
                    setIsMenuOpen(false)
                  }}
                  disabled={busy}
                >
                  <div className="historyItemMain">
                    <div className="historyFileIcon" aria-hidden="true">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path
                          d="M8 4h8l4 4v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"
                          stroke="currentColor"
                          strokeWidth="1.6"
                          strokeLinejoin="round"
                        />
                        <path d="M14 4v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <div className="historyItemBody">
                      <div className="historyTop">
                        <div className="historyTitle">{historyTitle(h)}</div>
                        <div className="historyIndicators">
                          <div className={`historyBadge v-${clinicalTier}`} title="Clinical situation">
                            V
                          </div>
                          <div className={`historyBadge c-${completenessTier}`} title="Report completeness">
                            C
                          </div>
                        </div>
                      </div>
                      <div className="historyMeta">{when}</div>
                    </div>
                  </div>
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

        <div className="sidebarProfile">
          <div className="sidebarProfileAvatar">DM</div>
          <div className="sidebarProfileCopy">
            <div className="sidebarProfileName">Dr. M. Sørensen</div>
            <div className="sidebarProfileSub">On-duty · Esbjerg</div>
          </div>
          <button type="button" className="sidebarHelpBtn" aria-label="Help">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
              <path d="M9.5 9.5a2.7 2.7 0 0 1 5 1.4c0 2-2.5 2.2-2.5 4.1" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              <circle cx="12" cy="17.2" r="1" fill="currentColor" />
            </svg>
          </button>
        </div>
      </aside>

      <div className="mainArea">
        <header className="pageHeader">
          <button type="button" className="menuToggle" aria-label="Open menu" onClick={() => setIsMenuOpen(true)}>
            <span className="menuIcon" />
          </button>
          <div className="pageHeaderMain">
            <div className="liveBadge">Live session</div>
            <h1>Radio Medical Assistant</h1>
            <p className="subtitle">
              Structured workflow: complete the form by section, collaborate with the AI doctor in chat, and review a
              final clinical summary.
            </p>
          </div>
          <div className="headerActions">
            {showSummaryTab && (
              <button
                type="button"
                className={activeTab === 'summary' ? 'button ghost summaryNavBtn' : 'viewSummaryBtn'}
                onClick={() => {
                  if (activeTab === 'summary') {
                    setActiveTab('form')
                    return
                  }
                  void openSummaryView()
                }}
                disabled={busy}
              >
                {activeTab === 'summary' ? (
                  'Back to form'
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path
                        d="M8 4h8l4 4v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinejoin="round"
                      />
                      <path d="M14 4v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                      <path d="M9 12h6M9 15h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                    </svg>
                    View clinical summary
                  </>
                )}
              </button>
            )}
            {activeTab !== 'summary' && (
              <div className="progressCard">
                <div className="progressLabel">Progress</div>
                <div className="progressTrack">
                  <div className="progressFill" style={{ width: `${progressPercent}%` }} />
                </div>
                <div className="progressValue">
                  {activeStepIndex + 1} / {FORM_STEPS.length}
                </div>
              </div>
            )}
          </div>
        </header>

        {activeTab === 'summary' ? (
          <section className="summaryShell">
            {!result ? (
              <div className="empty">No summary yet. Complete the form and start a chat with the AI doctor first.</div>
            ) : (
              <ClinicalSummary
                indicators={indicators}
                result={result}
                vitalsQualityLabel={vitalsQuality.label}
                vitalsQualityLevel={vitalsQuality.level}
              />
            )}
          </section>
        ) : (
          <>
            <div className="stepper">
              {FORM_STEPS.map((step, index) => (
                <button
                  type="button"
                  key={step.id}
                  className={`stepBtn ${step.id === currentStep.id ? 'active' : ''}`}
                  onClick={() => setActiveStepId(step.id)}
                >
                  <span className="stepIndex">{index + 1}</span>
                  <span className="stepText">{step.shortLabel}</span>
                </button>
              ))}
            </div>

            <div className="contentGrid">
              <section className="formCard">
                {formLockedToDoctor && (
                  <div className="formLockedNotice" role="status">
                    Form locked after first send to the AI doctor. Update the observation chart here while you continue
                    the conversation in the chat panel.
                  </div>
                )}

                <div className="formCardHeader">
                  <div className="formCardHeaderMain">
                    <div className="stepOfBadge">
                      Step {activeStepIndex + 1} of {FORM_STEPS.length}
                    </div>
                    <div className="formSectionTitle">{currentStep.title}</div>
                    <div className="formSectionDesc">{currentStep.description}</div>
                  </div>
                  <div className="autosavePill">
                    <span className="autosaveDot" aria-hidden="true" />
                    {autosaveLabel}
                  </div>
                </div>

                {renderStepFormContent()}

                <div className="cardFooter">
                  <button
                    type="button"
                    className="button ghost"
                    onClick={() => setActiveStepId(FORM_STEPS[Math.max(0, activeStepIndex - 1)].id)}
                    disabled={activeStepIndex <= 0 || busy}
                  >
                    ← Previous section
                  </button>
                  <div className="footerActions">
                    <button
                      type="button"
                      className="button ghost"
                      onClick={() => setActiveStepId(FORM_STEPS[Math.min(FORM_STEPS.length - 1, activeStepIndex + 1)].id)}
                      disabled={activeStepIndex >= FORM_STEPS.length - 1 || busy}
                    >
                      Next section →
                    </button>
                    <button
                      type="button"
                      className={`button ${!canAskDoctor ? 'buttonAttention' : ''}`}
                      onClick={() => void askDoctor()}
                      disabled={busy}
                    >
                      {busy ? 'Analyzing…' : 'Send to AI doctor'}
                    </button>
                  </div>
                </div>
              </section>

              {chatPanel}
            </div>
          </>
        )}

        {error && <div className="error">Error: {error}</div>}
      </div>
    </div>
  )
}

export default App
