import { useEffect, useState } from 'react'

export interface ArtifactHistoryItem {
  id: string
  title: string
  timestamp: string
  metadata: {
    artifact_id: string
    title: string
    jsx: string
    compiled: string | null
  }
}

export interface ArtifactHistoryProps {
  onSelect: (item: ArtifactHistoryItem) => void
}

/** Dropdown list of past artifacts fetched from GET /api/artifacts/history. */
export function ArtifactHistory({ onSelect }: ArtifactHistoryProps): JSX.Element {
  const [items, setItems] = useState<ArtifactHistoryItem[]>([])

  useEffect(() => {
    fetch('/api/artifacts/history')
      .then((r) => r.json())
      .then((data: ArtifactHistoryItem[]) => setItems(data))
      .catch(() => setItems([]))
  }, [])

  return (
    <div data-testid="artifact-history" style={{ minWidth: '12rem' }}>
      {items.length === 0 ? (
        <span style={{ color: 'var(--color-text-muted, #64748b)', fontSize: '0.8125rem' }}>
          No saved artifacts
        </span>
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {items.map((item) => (
            <li
              key={item.id}
              data-testid="artifact-history-item"
              onClick={() => onSelect(item)}
              style={{
                padding: '0.375rem 0.75rem',
                cursor: 'pointer',
                fontSize: '0.8125rem',
                color: 'var(--color-text, #e2e8f0)',
                borderRadius: '0.25rem',
              }}
            >
              {item.title || item.metadata?.title || item.id}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
