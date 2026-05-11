import { useId, useState, type KeyboardEventHandler } from 'react'

import { runMcpBridge, uploadSubmission } from '../api/client'
import type { MCPBridgeResponse, RubricCriterion } from '../types/feedback'

type ChatMessage = {
  role: 'user' | 'assistant'
  text: string
}

type Props = {
  rubric: RubricCriterion[]
}

export default function ChatbotPanel({ rubric }: Props) {
  const fileInputId = useId()
  const [sessionId, setSessionId] = useState<string>('')
  const [fileId, setFileId] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const uploadIfNeeded = async (): Promise<string | undefined> => {
    if (!selectedFile || fileId) {
      return fileId || undefined
    }
    const uploaded = await uploadSubmission(selectedFile)
    setFileId(uploaded.file_id)
    return uploaded.file_id
  }

  const sendPrompt = async () => {
    const trimmed = prompt.trim()
    if (!trimmed || isLoading) return

    setError('')
    setIsLoading(true)
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])

    try {
      const uploadedFileId = await uploadIfNeeded()
      const payload: {
        user_prompt: string
        session_id?: string
        file_id?: string
        rubric?: RubricCriterion[]
      } = {
        user_prompt: trimmed,
      }

      if (sessionId) {
        payload.session_id = sessionId
      }
      if (uploadedFileId) {
        payload.file_id = uploadedFileId
      }
      if (rubric.length > 0) {
        payload.rubric = rubric
      }

      const res: MCPBridgeResponse = await runMcpBridge(payload)
      setSessionId(res.session_id)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: res.assistant_message,
        },
      ])
      setPrompt('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bridge request failed.')
    } finally {
      setIsLoading(false)
    }
  }

  const onPromptKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = async (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      await sendPrompt()
    }
  }

  const fileStatus = selectedFile?.name ?? (fileId ? 'File attached' : 'No file attached')

  return (
    <section className="panel chat-shell">
      <div className="chat-head">
        <span className="chat-head-label">Chat Assistant</span>
        {sessionId && <span className="chat-session">Session {sessionId.slice(0, 8)}</span>}
      </div>

      <div className="chat-log">
        {messages.map((m, idx) => (
          <div key={`${m.role}-${idx}`} className={`chat-row chat-row-${m.role}`}>
            <article className={`chat-msg chat-${m.role}`}>
              <p>{m.text}</p>
            </article>
          </div>
        ))}
        {messages.length === 0 && <p className="chat-empty">Attach a file and ask your first question.</p>}
      </div>

      <div className="chat-controls">
        <div className="attach-row">
          <label htmlFor={fileInputId} className="attach-btn">Attach File</label>
          <span className="attach-name">{fileStatus}</span>
          <input
            id={fileInputId}
            className="chat-file-input"
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={(e) => {
              setSelectedFile(e.target.files?.[0] ?? null)
              setFileId('')
            }}
          />
        </div>

        <textarea
          placeholder="Ask for analysis, rubric scoring, or full feedback"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={onPromptKeyDown}
          rows={2}
        />

        <div className="chat-actions">
          <button type="button" className="primary-btn" onClick={sendPrompt} disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Running...' : 'Send'}
          </button>
          {error && <p className="error">{error}</p>}
        </div>
      </div>
    </section>
  )
}
