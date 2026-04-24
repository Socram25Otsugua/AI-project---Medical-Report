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

const KEY = 'rmrr.history.v1'

export function loadHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as HistoryItem[]
    if (!Array.isArray(parsed)) return []
    // basic sanity filtering to avoid breaking older data
    return parsed
      .filter((x) => x && typeof x === 'object' && typeof (x as any).id === 'string')
      .slice(0, 50)
  } catch {
    return []
  }
}

export function saveHistory(items: HistoryItem[]) {
  localStorage.setItem(KEY, JSON.stringify(items.slice(0, 50)))
}

