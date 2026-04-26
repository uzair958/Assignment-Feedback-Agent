export interface RubricCriterion {
  name: string
  max_points: number
  description: string
}

export interface CriterionScore {
  criterion: string
  max_points: number
  awarded_points: number
  justification: string
  strengths: string[]
  improvements: string[]
  evidence_quotes?: string[]
}

export interface FeedbackReport {
  overall_summary: string
  total_score: number
  total_possible: number
  grade_breakdown: CriterionScore[]
  top_strengths: string[]
  priority_improvements: string[]
  suggested_next_steps: string[]
}

export interface RubricResponse {
  rubric_id: string
  criteria: RubricCriterion[]
}

export interface UploadResponse {
  file_id: string
  filename: string
  file_path: string
  file_type: string
  size_bytes: number
}

export interface MCPToolExecution {
  tool_name: string
  payload: Record<string, unknown>
  result: Record<string, unknown>
}

export interface MCPBridgeRequest {
  user_prompt: string
  session_id?: string
  file_id?: string
  rubric_id?: string
  raw_text?: string
  rubric?: RubricCriterion[]
  max_steps?: number
}

export interface MCPBridgeResponse {
  session_id: string
  assistant_message: string
  intent: 'analyze_text' | 'score_rubric' | 'full_feedback'
  planned_tools: string[]
  executed_steps: MCPToolExecution[]
  artifacts: Record<string, unknown>
}
