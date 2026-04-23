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
