import type { AnalyzeRequest, AnalyzeResultV2 } from './types'

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

