import { observationChartToReportText, parseObservationChart } from './observationChart'
import type { IndicatorsState, SectionDef } from './schema'
import { OBSERVATION_CHART_STATE_KEY } from './schema'

const BOOLEAN_FIELDS_TO_KEEP_WHEN_NO = new Set(['has_medicine', 'has_allergies'])

function valToString(v: string | number | boolean): string {
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  return String(v ?? '').trim()
}

export function indicatorsToReportText(sections: SectionDef[], state: IndicatorsState): string {
  const lines: string[] = []
  lines.push('Radio Medical Record (structured entry)')
  lines.push('')

  for (const s of sections) {
    if (s.id === 'observation') continue
    lines.push(`## ${s.title}`)
    if (s.description) lines.push(s.description)
    for (const f of s.fields) {
      const v = state[f.key]
      const vs = valToString(v)
      if (vs === '') {
        continue
      }
      if (vs === 'No' && !BOOLEAN_FIELDS_TO_KEEP_WHEN_NO.has(f.key)) {
        // keep most false checkboxes out; preserve clinically important negatives
        continue
      }
      const unit = f.unit ? ` ${f.unit}` : ''
      lines.push(`- ${f.label}: ${vs}${unit}`)
    }
    lines.push('')
  }

  const observationText = observationChartToReportText(parseObservationChart(state[OBSERVATION_CHART_STATE_KEY]))
  if (observationText.trim()) {
    lines.push(observationText)
    lines.push('')
  }

  return lines.join('\n').trim() + '\n'
}

