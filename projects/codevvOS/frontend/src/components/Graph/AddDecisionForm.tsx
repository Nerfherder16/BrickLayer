import { useState, useCallback } from 'react'
import { useGraphStore } from '../../stores/graphStore'
import type { GraphNode } from '../../stores/graphStore'

interface AddDecisionFormProps {
  onClose: () => void
}

/** Form to add a new Decision node to the knowledge graph. */
export function AddDecisionForm({ onClose }: AddDecisionFormProps): JSX.Element {
  const [title, setTitle] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const addNode = useGraphStore((s) => s.addNode)

  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
      e.preventDefault()
      const trimmed = title.trim()
      if (!trimmed) return

      setSubmitting(true)
      setError(null)

      try {
        const resp = await fetch('/api/graph/nodes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ node_type: 'Decision', title: trimmed, properties: {} }),
        })

        if (!resp.ok) {
          setError('Failed to create node')
          return
        }

        const responseNode = (await resp.json()) as GraphNode
        addNode(responseNode)
        onClose()
      } catch {
        setError('Network error')
      } finally {
        setSubmitting(false)
      }
    },
    [title, addNode, onClose],
  )

  return (
    <form
      data-testid="add-decision-form"
      onSubmit={(e) => void handleSubmit(e)}
      style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
    >
      <label htmlFor="decision-title" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
        Decision title
      </label>
      <input
        id="decision-title"
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Describe the decision…"
        required
        style={{
          padding: '0.5rem 0.75rem',
          border: '1px solid var(--color-gray-300)',
          borderRadius: '0.375rem',
          fontSize: '0.875rem',
        }}
      />

      {error && (
        <p style={{ color: 'var(--color-red-500)', fontSize: '0.875rem', margin: 0 }}>{error}</p>
      )}

      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
        <button type="button" onClick={onClose} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" disabled={submitting || !title.trim()}>
          {submitting ? 'Adding…' : 'Add Decision'}
        </button>
      </div>
    </form>
  )
}
