import type { AnalyzeRequest, AnalyzeResultV2, ChatTurnRequest, ChatTurnResult } from './types'
import type { HistoryItem } from './history'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function postJson<T>(path: string, payload?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    ...(payload !== undefined ? { body: JSON.stringify(payload) } : {}),
  })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as T
}

async function fetchJson<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`)
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as T
}

export async function chatDoctorTurn(payload: ChatTurnRequest): Promise<ChatTurnResult> {
  return postJson('/api/v1/reports/chat-turn', payload)
}

export async function finalizeSummary(payload: AnalyzeRequest): Promise<AnalyzeResultV2> {
  return postJson('/api/v1/reports/finalize-summary', payload)
}

export async function listHistory(limit = 50): Promise<HistoryItem[]> {
  return fetchJson(`/api/v1/reports/history?limit=${encodeURIComponent(String(limit))}`)
}

export async function createHistory(item: Omit<HistoryItem, 'id'>): Promise<HistoryItem> {
  return postJson('/api/v1/reports/history', item)
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
