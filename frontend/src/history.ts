import type { AnalyzeResultV2 } from './types'
import type { IndicatorsState } from './indicators/schema'

export type HistoryItem = {
  id: string
  createdAt: number
  sourceLabel: string
  reportText: string
  result: AnalyzeResultV2
  mode?: 'form' | 'text'
  indicators?: IndicatorsState
}
