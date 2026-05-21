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
  /** 0–100: coverage of key vitals from structured extraction (MCP). */
  vitals_score?: number
  vitals_feedback?: string[]
}

export type ResponseResult = {
  immediate_actions?: string[]
  monitoring_parameters?: string[]
  escalation_criteria?: string[]
  /** Legacy field from older saved reports. */
  next_step_message?: string
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

export type ChatTurnRequest = AnalyzeRequest & {
  user_message?: string
}

export type ChatTurnResult = {
  assistant_message: string
  questions_for_participants: string[]
  pending_questions: string[]
  can_finalize_summary: boolean
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

