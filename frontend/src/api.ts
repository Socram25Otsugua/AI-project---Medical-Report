import type { AnalyzeRequest, AnalyzeResultV2 } from './types'
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

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, init)
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`Backend error (${r.status}): ${text || r.statusText}`)
  }
  return (await r.json()) as T
}

export async function listHistory(limit = 50): Promise<HistoryItem[]> {
  return await api<HistoryItem[]>(`/api/v1/reports/history?limit=${encodeURIComponent(String(limit))}`)
}

export async function createHistory(item: Omit<HistoryItem, 'id'>): Promise<HistoryItem> {
  return await api<HistoryItem>(`/api/v1/reports/history`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(item),
  })
}

export async function deleteHistory(reportId: string): Promise<{ deleted: boolean }> {
  return await api<{ deleted: boolean }>(`/api/v1/reports/history/${encodeURIComponent(reportId)}`, { method: 'DELETE' })
}

export async function clearHistory(): Promise<{ deleted: number }> {
  return await api<{ deleted: number }>(`/api/v1/reports/history`, { method: 'DELETE' })
}

