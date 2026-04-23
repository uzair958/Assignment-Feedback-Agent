import { useState } from 'react'

type Props = {
  onUpload: (file: File) => Promise<string>
}

export default function UploadForm({ onUpload }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [status, setStatus] = useState('')

  const submit = async () => {
    if (!selectedFile) return
    const fileId = await onUpload(selectedFile)
    setStatus(`Uploaded. File ID: ${fileId}`)
  }

  return (
    <section className="panel">
      <h2>1) Upload Assignment</h2>
      <div className="field">
        <input
          type="file"
          accept=".txt,.pdf,.docx"
          onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
        />
      </div>
      <button className="primary-btn" type="button" onClick={submit} disabled={!selectedFile}>
        Upload
      </button>
      {status && <p>{status}</p>}
    </section>
  )
}
