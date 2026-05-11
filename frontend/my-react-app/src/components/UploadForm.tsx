import { useState } from 'react'

type Props = {
  onUpload: (file: File) => Promise<string>
}

export default function UploadForm({ onUpload }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const uploadFile = async (file: File) => {
    if (isUploading) return
    setError('')
    setIsUploading(true)
    try {
      const fileId = await onUpload(file)
      setStatus(`Uploaded. File ID: ${fileId}`)
    } catch (err) {
      setStatus('')
      setError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  const submit = async () => {
    if (!selectedFile) return
    await uploadFile(selectedFile)
  }

  return (
    <section className="panel">
      <h2>Upload Assignment</h2>
      <div className="field">
        <input
          type="file"
          accept=".txt,.pdf,.docx"
          onChange={(e) => {
            const file = e.target.files?.[0] ?? null
            setSelectedFile(file)
            setStatus('')
            setError('')
          }}
        />
      </div>
      <button className="primary-btn" type="button" onClick={submit} disabled={!selectedFile || isUploading}>
        {isUploading ? 'Uploading...' : 'Upload'}
      </button>
      {status && <p>{status}</p>}
      {error && <p className="error">{error}</p>}
    </section>
  )
}
