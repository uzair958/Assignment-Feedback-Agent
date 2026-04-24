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

  const isReadyToGenerate = Boolean(fileId) && rubric.length > 0

  const handleGenerate = async () => {
    if (!isReadyToGenerate) {
      if (!fileId && rubric.length === 0) {
        setError('Please upload the file (click Upload) and add at least one rubric criterion.')
      } else if (!fileId) {
        setError('Please upload the file first by selecting it and clicking Upload.')
      } else {
        setError('Please add at least one rubric criterion, then click Add Criterion.')
      }
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
          setError('')
          return res.file_id
        }}
      />
      <RubricBuilder
        rubric={rubric}
        onChange={(criteria) => {
          setRubric(criteria)
          if (criteria.length > 0) {
            setError('')
          }
        }}
      />
      <button
        type="button"
        className="primary-btn"
        onClick={handleGenerate}
        disabled={isLoading}
      >
        Generate Feedback
      </button>
      {!isReadyToGenerate && (
        <p>
          Complete both steps first: upload your file and add at least one rubric criterion.
        </p>
      )}
      <p>
        Status: File {fileId ? 'uploaded' : 'not uploaded'} | Criteria {rubric.length}
      </p>
      {isLoading && <LoadingState message="Running multi-agent feedback pipeline..." />}
      {error && <p className="error">{error}</p>}
      {report && <FeedbackReportView report={report} />}
    </main>
  )
}

export default App
