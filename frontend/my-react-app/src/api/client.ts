import type { FeedbackReport, RubricCriterion, RubricResponse, UploadResponse } from '../types/feedback'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const uploadSubmission = async (file: File): Promise<UploadResponse> => {
  const form = new FormData()
  form.append('file', file)
  return request<UploadResponse>('/upload', { method: 'POST', body: form })
}

export const saveRubric = async (payload: { criteria: RubricCriterion[] }): Promise<RubricResponse> =>
  request<RubricResponse>('/rubric', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

export const runFeedback = async (payload: {
  file_id: string
  rubric_id: string
}): Promise<{ report: FeedbackReport }> =>
  request<{ report: FeedbackReport }>('/feedback/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
