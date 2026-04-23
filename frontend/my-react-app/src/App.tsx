import { useState } from 'react'
import FeedbackReportView from './components/FeedbackReport'
import LoadingState from './components/LoadingState'
import RubricBuilder from './components/RubricBuilder'
import UploadForm from './components/UploadForm'
import { runFeedback, saveRubric, uploadSubmission } from './api/client'
import type { FeedbackReport, RubricCriterion } from './types/feedback'
import './App.css'

function App() {
  const [fileId, setFileId] = useState<string>('')
  const [rubric, setRubric] = useState<RubricCriterion[]>([])
  const [report, setReport] = useState<FeedbackReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    if (!fileId || rubric.length === 0) {
      setError('Upload a file and add at least one rubric criterion.')
      return
    }
    setError('')
    setIsLoading(true)
    try {
      const rubricRes = await saveRubric({ criteria: rubric })
      const feedback = await runFeedback({ file_id: fileId, rubric_id: rubricRes.rubric_id })
      setReport(feedback.report)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate feedback.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app">
      <h1>AI Assignment Feedback System</h1>
      <UploadForm
        onUpload={async (file) => {
          const res = await uploadSubmission(file)
          setFileId(res.file_id)
          return res.file_id
        }}
      />
      <RubricBuilder rubric={rubric} onChange={setRubric} />
      <button type="button" className="primary-btn" onClick={handleGenerate} disabled={isLoading}>
        Generate Feedback
      </button>
      {isLoading && <LoadingState message="Running multi-agent feedback pipeline..." />}
      {error && <p className="error">{error}</p>}
      {report && <FeedbackReportView report={report} />}
    </main>
  )
}

export default App
