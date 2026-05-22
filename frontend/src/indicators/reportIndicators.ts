import type { HistoryItem } from '../history'
import { getFirstColumnMissingFields, OBSERVATION_ROWS, parseObservationChart } from './observationChart'
import { OBSERVATION_CHART_STATE_KEY, sections, type IndicatorsState } from './schema'

export type CompletenessTier = 'r' | 'y' | 'g'
export type ClinicalTier = 'critical' | 'bad' | 'concerning' | 'ok' | 'excellent' | 'unknown'
export type VitalsQualityLevel = 'red' | 'orange' | 'yellow' | 'green' | 'unknown'

function toNumber(value: string | number | boolean | undefined): number | null {
  const parsed = Number(String(value ?? '').trim())
  if (Number.isNaN(parsed)) return null
  return parsed
}

function isFieldFilled(value: string | number | boolean | undefined, type: string): boolean {
  if (type === 'checkbox') return Boolean(value)
  return String(value ?? '').trim() !== ''
}

export function completenessTierFromIndicators(indicators?: IndicatorsState): CompletenessTier {
  if (!indicators) return 'r'

  let filled = 0
  let total = 0

  for (const section of sections) {
    for (const field of section.fields) {
      total += 1
      if (isFieldFilled(indicators[field.key], field.type)) filled += 1
    }
  }

  const chart = parseObservationChart(indicators[OBSERVATION_CHART_STATE_KEY])
  const mandatoryCount = OBSERVATION_ROWS.filter((row) => row.mandatory).length
  const missingMandatory = getFirstColumnMissingFields(chart).length
  total += mandatoryCount
  filled += mandatoryCount - missingMandatory

  if (total === 0) return 'r'

  const ratio = filled / total
  if (ratio >= 0.7) return 'g'
  if (ratio >= 0.35) return 'y'
  return 'r'
}

export function vitalsQualityLevel(indicators?: IndicatorsState): VitalsQualityLevel {
  if (!indicators) return 'unknown'

  const hr = toNumber(indicators.pulse_bpm)
  const rr = toNumber(indicators.breathing_frequency)
  const spo2 = toNumber(indicators.spo2_percent)
  const sys = toNumber(indicators.bp_systolic)
  const dia = toNumber(indicators.bp_diastolic)
  const temp = toNumber(indicators.temp_mouth_c) ?? toNumber(indicators.temp_alt_c)

  if ([hr, rr, spo2, sys, dia, temp].some((value) => value === null)) {
    return 'unknown'
  }

  let severityPoints = 0

  if (hr! < 50 || hr! > 120) severityPoints += 2
  else if (hr! < 50 || hr! > 80) severityPoints += 1

  if (rr! < 10 || rr! > 25) severityPoints += 2
  else if (rr! < 12 || rr! > 20) severityPoints += 1

  if (spo2! <= 90) severityPoints += 3
  else if (spo2! < 92) severityPoints += 2
  else if (spo2! < 95) severityPoints += 1

  if (sys! < 90) severityPoints += 2
  else if (sys! > 140 || dia! > 90 || dia! < 60) severityPoints += 1

  if (temp! < 35 || temp! >= 39) severityPoints += 2
  else if (temp! < 36 || temp! >= 38) severityPoints += 1

  if (severityPoints === 0) return 'green'
  if (severityPoints <= 2) return 'yellow'
  if (severityPoints <= 3) return 'orange'
  return 'red'
}

export function clinicalTierFromHistory(item: HistoryItem): ClinicalTier {
  const evaluation = item.result.patient_evaluation
  const vitalsLevel = vitalsQualityLevel(item.indicators)

  if (evaluation?.status === 'critical') return 'critical'

  if (evaluation?.status === 'concerning') {
    if (evaluation.red_flags?.length || vitalsLevel === 'red' || vitalsLevel === 'orange') return 'bad'
    return 'concerning'
  }

  if (evaluation?.status === 'ok') {
    return vitalsLevel === 'green' ? 'excellent' : 'ok'
  }

  if (vitalsLevel === 'red') return 'critical'
  if (vitalsLevel === 'orange') return 'bad'
  if (vitalsLevel === 'yellow') return 'concerning'
  if (vitalsLevel === 'green') return 'excellent'
  return 'unknown'
}
