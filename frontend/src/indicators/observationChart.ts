export type ObservationRowType = 'text' | 'number' | 'select'

export type ObservationRowDef = {
  key: string
  label: string
  type: ObservationRowType
  options?: string[]
  mandatory: boolean
  placeholder?: string
}

export const OBSERVATION_COLUMN_COUNT = 8

export const OBSERVATION_ROWS: ObservationRowDef[] = [
  { key: 'date', label: 'Date', type: 'text', mandatory: true, placeholder: 'YYYY-MM-DD' },
  { key: 'time', label: 'Time', type: 'text', mandatory: true, placeholder: 'HH:MM' },
  {
    key: 'general_condition',
    label: 'General condition (1–4)',
    type: 'select',
    options: ['1', '2', '3', '4'],
    mandatory: true,
  },
  {
    key: 'consciousness',
    label: 'Level of consciousness (1–4)',
    type: 'select',
    options: ['1', '2', '3', '4'],
    mandatory: true,
  },
  { key: 'oxygen_l_min', label: 'Oxygen liters/min', type: 'number', mandatory: true },
  { key: 'breathing_frequency', label: 'Breathing frequency /min. (12–16)', type: 'number', mandatory: true },
  { key: 'spo2', label: 'Oxygen saturation in % (95–100)', type: 'number', mandatory: true },
  { key: 'capillary_response', label: 'Capillary response in sec. (< 2 sek.)', type: 'number', mandatory: true },
  { key: 'heart_rate', label: 'Heart rate / min. (60–80)', type: 'number', mandatory: true },
  {
    key: 'blood_pressure',
    label: 'Blood pressure (120–140 / 60–90)',
    type: 'text',
    mandatory: true,
    placeholder: '120/80',
  },
  {
    key: 'pupil_reaction',
    label: 'Pupil reaction (Normal + / +)',
    type: 'text',
    mandatory: true,
    placeholder: '+ / +',
  },
  { key: 'temperature', label: 'Temp. measured in the mouth/rectal', type: 'number', mandatory: true },
  {
    key: 'venous_cannula',
    label: 'Venous cannula inserted (yes / no)',
    type: 'select',
    options: ['yes', 'no'],
    mandatory: false,
  },
  { key: 'iv_fluid', label: 'Intravenous fluid, drops / min.', type: 'number', mandatory: false },
  { key: 'fluid_intake', label: 'Fluid intake / drink', type: 'text', mandatory: false },
  { key: 'urine_24h', label: '24-hour urine', type: 'text', mandatory: false },
  { key: 'urine_sticks', label: 'Urine sticks', type: 'text', mandatory: false },
  { key: 'blood_sugar', label: 'Blood sugar (4–7 mmol / liter)', type: 'number', mandatory: false },
  { key: 'malaria_test', label: 'Malaria test', type: 'text', mandatory: false },
  { key: 'crp_test', label: 'CRP Test', type: 'text', mandatory: false },
]

export type ObservationColumn = Record<string, string>

export type ObservationChartData = {
  columns: ObservationColumn[]
}

export const OBSERVATION_CHART_KEY = 'observation_chart'

export function createEmptyObservationChart(): ObservationChartData {
  return {
    columns: Array.from({ length: OBSERVATION_COLUMN_COUNT }, () => ({})),
  }
}

export function parseObservationChart(raw: string | number | boolean | undefined): ObservationChartData {
  if (typeof raw !== 'string' || raw.trim() === '') {
    return createEmptyObservationChart()
  }
  try {
    const parsed = JSON.parse(raw) as Partial<ObservationChartData>
    if (!parsed || !Array.isArray(parsed.columns)) {
      return createEmptyObservationChart()
    }
    const columns = parsed.columns.slice(0, OBSERVATION_COLUMN_COUNT).map((column) => ({ ...(column ?? {}) }))
    while (columns.length < OBSERVATION_COLUMN_COUNT) {
      columns.push({})
    }
    return { columns }
  } catch {
    return createEmptyObservationChart()
  }
}

export function serializeObservationChart(chart: ObservationChartData): string {
  return JSON.stringify(chart)
}

function cellValue(column: ObservationColumn, key: string): string {
  return String(column[key] ?? '').trim()
}

export function columnHasAnyValue(column: ObservationColumn): boolean {
  return OBSERVATION_ROWS.some((row) => cellValue(column, row.key) !== '')
}

export function getMissingMandatoryFields(column: ObservationColumn): string[] {
  return OBSERVATION_ROWS.filter((row) => row.mandatory && cellValue(column, row.key) === '').map((row) => row.label)
}

export function isColumnReadyForSend(column: ObservationColumn): boolean {
  return getMissingMandatoryFields(column).length === 0
}

export function getFirstColumnMissingFields(chart: ObservationChartData): string[] {
  return getMissingMandatoryFields(chart.columns[0] ?? {})
}

export function isObservationChartReadyForSend(chart: ObservationChartData): boolean {
  return isColumnReadyForSend(chart.columns[0] ?? {})
}

export function observationChartToReportText(chart: ObservationChartData): string {
  const filledCount = chart.columns.filter((column) => columnHasAnyValue(column)).length
  const lines: string[] = ['## Observation chart']
  lines.push(
    'Serial vitals chart: up to 8 columns (left to right = earlier to later readings). ' +
      'During telemedicine chat the crew may add new readings in the next empty column — use all filled columns and trends when evaluating the patient.',
  )
  if (filledCount > 0 && filledCount < OBSERVATION_COLUMN_COUNT) {
    lines.push(
      `Filled columns: ${filledCount} of ${OBSERVATION_COLUMN_COUNT}. ` +
        `Columns ${filledCount + 1}–${OBSERVATION_COLUMN_COUNT} are available for repeat observations.`,
    )
  }
  lines.push('')

  chart.columns.forEach((column, index) => {
    if (!columnHasAnyValue(column)) return
    lines.push(`### Observation column ${index + 1}`)
    for (const row of OBSERVATION_ROWS) {
      const value = cellValue(column, row.key)
      if (value === '') continue
      lines.push(`- ${row.label}: ${value}`)
    }
    lines.push('')
  })

  return lines.join('\n').trim()
}
