export type Deficiency = {
  area: string
  issue: string
  severity: 'low' | 'medium' | 'high'
  suggestion: string
}

export type ReviewResult = {
  extracted: Record<string, unknown>
  deficiencies: Deficiency[]
  safety_flags: string[]
  completeness_score: number
}

export type ResponseResult = {
  next_step_message: string
  rationale_bullets: string[]
  questions_for_participants: string[]
}

export type AnalyzeResult = {
  review: ReviewResult
  response: ResponseResult
}

export type AnalyzeRequest = {
  session_id: string
  report_text: string
  locale: 'en-UK' | 'pt-PT'
}

