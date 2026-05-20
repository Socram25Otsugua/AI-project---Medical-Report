import type { AnalyzeRequest, AnalyzeResultV2, ChatTurnRequest, ChatTurnResult } from './types'
import type { HistoryItem } from './history'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

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

export async function listHistory(limit = 50): Promise<HistoryItem[]> {
  const r = await fetch(`${API_BASE}/api/v1/reports/history?limit=${encodeURIComponent(String(limit))}`)
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as HistoryItem[]
}

export async function createHistory(item: Omit<HistoryItem, 'id'>): Promise<HistoryItem> {
  const r = await fetch(`${API_BASE}/api/v1/reports/history`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(item),
  })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as HistoryItem
}

export async function deleteHistory(reportId: string): Promise<{ deleted: boolean }> {
  const r = await fetch(`${API_BASE}/api/v1/reports/history/${encodeURIComponent(reportId)}`, { method: 'DELETE' })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as { deleted: boolean }
}

export async function clearHistory(): Promise<{ deleted: number }> {
  const r = await fetch(`${API_BASE}/api/v1/reports/history`, { method: 'DELETE' })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as { deleted: number }
}

