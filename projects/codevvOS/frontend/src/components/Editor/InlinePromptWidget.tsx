import { useState, useRef, useCallback, KeyboardEvent } from 'react'

export interface InlinePromptWidgetProps {
  /** Full document text passed to the API. */
  document: string
  /** Language identifier (typescript, python, etc.) */
  language: string
  /** Called with the streamed new document text when SSE completes. */
  onSubmit: (newDoc: string) => void
  /** Called when the widget should be dismissed (Escape, cancel). */
  onDismiss: () => void
}

/** Floating prompt input widget for Cmd+K inline AI edits. */
export default function InlinePromptWidget({
  document,
  language,
  onSubmit,
  onDismiss,
}: InlinePromptWidgetProps): JSX.Element {
  const [prompt, setPrompt] = useState('')
  const [streaming, setStreaming] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Escape') {
        onDismiss()
      }
    },
    [onDismiss],
  )

  const submit = useCallback(
    async (promptText: string) => {
      if (!promptText.trim() || streaming) return
      setStreaming(true)

      try {
        const response = await fetch('/api/ai/inline-edit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: promptText, document, language }),
        })

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let accumulated = ''
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Split on SSE event boundaries (double newline)
          const events = buffer.split('\n\n')
          // Keep last potentially incomplete event in buffer
          buffer = events.pop() ?? ''

          for (const event of events) {
            if (event.includes('event: done')) {
              setStreaming(false)
              onSubmit(accumulated)
              return
            }
            // Collect data: lines from event and join with newline
            const dataLines = event.split('\n').filter((l) => l.startsWith('data: '))
            for (const dataLine of dataLines) {
              const value = dataLine.slice('data: '.length)
              accumulated = accumulated ? accumulated + '\n' + value : value
            }
          }
        }

        // Fallback if stream ended without explicit done event
        setStreaming(false)
        onSubmit(accumulated)
      } catch {
        setStreaming(false)
      }
    },
    [document, language, onSubmit, streaming],
  )

  const handleSubmit = useCallback(() => {
    void submit(prompt)
  }, [prompt, submit])

  const handleFormKeyDown = useCallback(
    (e: KeyboardEvent<HTMLFormElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        void submit(prompt)
      }
    },
    [prompt, submit],
  )

  return (
    <form
      onKeyDown={handleFormKeyDown}
      onSubmit={(e) => {
        e.preventDefault()
        void submit(prompt)
      }}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.375rem 0.5rem',
        background: 'var(--color-surface, #1e293b)',
        border: '1px solid var(--color-accent, #6366f1)',
        borderRadius: '4px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      }}
    >
      {streaming && (
        <span
          data-testid="inline-prompt-spinner"
          aria-label="Generating…"
          style={{
            display: 'inline-block',
            width: '12px',
            height: '12px',
            border: '2px solid var(--color-muted, #475569)',
            borderTopColor: 'var(--color-accent, #6366f1)',
            borderRadius: '50%',
            animation: 'spin 0.6s linear infinite',
            flexShrink: 0,
          }}
        />
      )}
      <input
        ref={inputRef}
        data-testid="inline-prompt-input"
        type="text"
        placeholder="AI prompt (↵ submit, Esc dismiss)"
        aria-label="Inline AI prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={streaming}
        autoFocus
        style={{
          flex: 1,
          minWidth: '240px',
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: 'var(--color-text, #e2e8f0)',
          fontSize: '0.8125rem',
        }}
      />
      <button
        type="submit"
        aria-label="Submit prompt"
        disabled={streaming || !prompt.trim()}
        style={{
          padding: '0.2rem 0.5rem',
          fontSize: '0.75rem',
          background: 'var(--color-accent, #6366f1)',
          color: '#fff',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
        }}
      >
        Submit
      </button>
    </form>
  )
}
