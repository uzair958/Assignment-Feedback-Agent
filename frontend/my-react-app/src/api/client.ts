import type { FeedbackReport, RubricCriterion, RubricResponse, UploadResponse } from '../types/feedback'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? 'GET'
  const url = `${API_BASE}${path}`
  const startedAt = performance.now()

  console.log('[api] request', { method, url })

  const response = await fetch(url, init)
  const durationMs = Math.round(performance.now() - startedAt)

  console.log('[api] response', {
    method,
    url,
    status: response.status,
    ok: response.ok,
    durationMs,
  })

  if (!response.ok) {
    const message = await response.text()
    console.error('[api] error', {
      method,
      url,
      status: response.status,
      body: message,
    })
    throw new Error(message || `Request failed: ${response.status}`)
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.toLowerCase().includes('application/json')) {
    const textBody = await response.text()
    throw new Error(`Expected JSON response but got: ${textBody.slice(0, 200)}`)
  }

  return response.json() as Promise<T>
}

export const uploadSubmission = async (file: File): Promise<UploadResponse> => {
  const form = new FormData()
  form.append('file', file)

  const raw = await request<Record<string, unknown>>('/upload', { method: 'POST', body: form })
  const fileIdCandidate =
    raw.file_id ??
    raw.fileId ??
    (typeof raw.data === 'object' && raw.data !== null ? (raw.data as Record<string, unknown>).file_id : undefined)

  if (typeof fileIdCandidate !== 'string' || !fileIdCandidate.trim()) {
    console.error('[api] upload payload missing file id', raw)
    throw new Error('Upload succeeded but no file id was returned by backend.')
  }

  const normalized: UploadResponse = {
    file_id: fileIdCandidate,
    filename: String(raw.filename ?? ''),
    file_path: String(raw.file_path ?? ''),
    file_type: String(raw.file_type ?? ''),
    size_bytes: Number(raw.size_bytes ?? 0),
  }

  console.log('[api] upload normalized', normalized)
  return normalized
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
