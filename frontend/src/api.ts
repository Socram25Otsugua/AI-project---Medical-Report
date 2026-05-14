import type { AnalyzeRequest, AnalyzeResultV2, ChatTurnRequest, ChatTurnResult } from './types'
import type { HistoryItem } from './history'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
const HISTORY_KEY = 'rmr_summary_history_v1'

export async function analyzeReport(payload: AnalyzeRequest): Promise<AnalyzeResultV2> {
  const r = await fetch(`${API_BASE}/api/v1/reports/analyze`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }

  return (await r.json()) as AnalyzeResultV2
}

export async function analyzeReportWithAgent(payload: AnalyzeRequest): Promise<AnalyzeResultV2> {
  const r = await fetch(`${API_BASE}/api/v1/reports/analyze-agent`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }

  return (await r.json()) as AnalyzeResultV2
}

export async function chatDoctorTurn(payload: ChatTurnRequest): Promise<ChatTurnResult> {
  const r = await fetch(`${API_BASE}/api/v1/reports/chat-turn`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as ChatTurnResult
}

export async function finalizeSummary(payload: AnalyzeRequest): Promise<AnalyzeResultV2> {
  const r = await fetch(`${API_BASE}/api/v1/reports/finalize-summary`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as AnalyzeResultV2
}

function readLocalHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as HistoryItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeLocalHistory(items: HistoryItem[]): void {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items))
}

export async function listHistory(limit = 50): Promise<HistoryItem[]> {
  return readLocalHistory()
    .sort((a, b) => b.createdAt - a.createdAt)
    .slice(0, limit)
}

export async function createHistory(item: Omit<HistoryItem, 'id'>): Promise<HistoryItem> {
  const created: HistoryItem = { ...item, id: crypto.randomUUID() }
  const next = [created, ...readLocalHistory()].slice(0, 50)
  writeLocalHistory(next)
  return created
}

export async function deleteHistory(reportId: string): Promise<{ deleted: boolean }> {
  const prev = readLocalHistory()
  const next = prev.filter((item) => item.id !== reportId)
  writeLocalHistory(next)
  return { deleted: next.length !== prev.length }
}

export async function clearHistory(): Promise<{ deleted: number }> {
  const deleted = readLocalHistory().length
  writeLocalHistory([])
  return { deleted }
}

