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

export type PatientEvaluation = {
  status: 'ok' | 'concerning' | 'critical' | 'unknown'
  summary: string
  suspected_problems: string[]
  red_flags: string[]
}

export type AnalyzeResultV2 = AnalyzeResult & {
  patient_evaluation?: PatientEvaluation
}

