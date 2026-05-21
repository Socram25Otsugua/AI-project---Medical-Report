import {
  OBSERVATION_COLUMN_COUNT,
  OBSERVATION_ROWS,
  type ObservationChartData,
  type ObservationColumn,
  type ObservationRowDef,
} from '../indicators/observationChart'

type ObservationChartProps = {
  chart: ObservationChartData
  onChange: (chart: ObservationChartData) => void
  lockedColumnIndexes?: number[]
  missingMandatoryLabels?: string[]
  showValidation?: boolean
}

function renderCellInput(
  row: ObservationRowDef,
  columnIndex: number,
  value: string,
  disabled: boolean,
  onCellChange: (columnIndex: number, rowKey: string, nextValue: string) => void,
) {
  const id = `obs_${columnIndex}_${row.key}`
  const isMissing = row.mandatory && value.trim() === ''

  if (row.type === 'select') {
    return (
      <select
        id={id}
        className={`obsChartInput ${isMissing ? 'obsChartInputMissing' : ''}`}
        value={value}
        disabled={disabled}
        onChange={(e) => onCellChange(columnIndex, row.key, e.target.value)}
      >
        <option value="">—</option>
        {(row.options ?? []).map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    )
  }

  return (
    <input
      id={id}
      className={`obsChartInput ${isMissing ? 'obsChartInputMissing' : ''}`}
      type={row.type === 'number' ? 'number' : 'text'}
      value={value}
      placeholder={row.placeholder}
      disabled={disabled}
      onChange={(e) => onCellChange(columnIndex, row.key, e.target.value)}
    />
  )
}

export function ObservationChart({
  chart,
  onChange,
  lockedColumnIndexes = [],
  missingMandatoryLabels = [],
  showValidation = false,
}: ObservationChartProps) {
  const lockedSet = new Set(lockedColumnIndexes)

  const onCellChange = (columnIndex: number, rowKey: string, nextValue: string) => {
    if (lockedSet.has(columnIndex)) return
    const nextColumns = chart.columns.map((column, index) => {
      if (index !== columnIndex) return column
      return { ...column, [rowKey]: nextValue }
    }) as ObservationColumn[]
    onChange({ columns: nextColumns })
  }

  return (
    <div className="obsChart">
      <div className="obsChartHeaderBar">Radio Medical Record — Observation Chart</div>

      {showValidation && missingMandatoryLabels.length > 0 && (
        <div className="obsChartNotice" role="alert">
          <div className="obsChartNoticeTitle">Observation chart incomplete</div>
          <div>
            Fill the first column through <strong>Temperature</strong> before sending to the AI doctor. Missing:{' '}
            {missingMandatoryLabels.join(', ')}.
          </div>
        </div>
      )}

      <div className="obsChartScroll">
        <table className="obsChartTable">
          <thead>
            <tr>
              <th className="obsChartLabelCol">Parameter</th>
              {Array.from({ length: OBSERVATION_COLUMN_COUNT }, (_, index) => (
                <th key={index} className="obsChartDataCol">
                  <span className="obsChartColTitle">Col {index + 1}</span>
                  {lockedSet.has(index) && <span className="obsChartLockedTag">Locked</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {OBSERVATION_ROWS.map((row) => (
              <tr key={row.key} className={row.mandatory ? 'obsChartRowMandatory' : 'obsChartRowOptional'}>
                <th scope="row" className="obsChartRowLabel">
                  {row.label}
                  {row.mandatory && <span className="obsChartRequiredMark">*</span>}
                </th>
                {chart.columns.map((column, columnIndex) => (
                  <td key={`${row.key}_${columnIndex}`} className="obsChartCell">
                    {renderCellInput(row, columnIndex, String(column[row.key] ?? ''), lockedSet.has(columnIndex), onCellChange)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="obsChartLegend">
        <div className="obsChartLegendTitle">How to code</div>
        <div className="obsChartLegendGrid">
          <div>
            <strong>General condition</strong>
            <ul>
              <li>1 = Generally unaffected</li>
              <li>2 = Slightly ill / not completely well</li>
              <li>3 = Ill and generally affected</li>
              <li>4 = Very ill and heavily affected</li>
            </ul>
          </div>
          <div>
            <strong>Level of consciousness</strong>
            <ul>
              <li>1 = Awake, alert and well orientated</li>
              <li>2 = Unclear, but responds to questions</li>
              <li>3 = Responds to pain stimuli only</li>
              <li>4 = Unconscious, unresponsive to pain</li>
            </ul>
          </div>
          <div>
            <strong>Pupil reaction</strong>
            <ul>
              <li>Normal reaction: + / +</li>
              <li>Abnormal: describe findings (e.g. right pupil large, no light reaction)</li>
            </ul>
          </div>
        </div>
        <p className="obsChartLegendNote">
          Fields marked with * are required in column 1 before sending to the AI doctor. After the first send, locked
          columns stay read-only; add progress in the next empty column during chat.
        </p>
      </div>
    </div>
  )
}
