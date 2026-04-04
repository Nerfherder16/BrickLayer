import React from 'react'

const VIEWPORT_OPTIONS = [
  { label: 'Desktop', width: 1440, testId: 'viewport-1440' },
  { label: 'Tablet', width: 768, testId: 'viewport-768' },
  { label: 'Mobile', width: 375, testId: 'viewport-375' },
] as const

interface ViewportToolbarProps {
  onRefresh: () => void
  viewport: number
  onViewportChange: (width: number) => void
  url: string
}

/** Toolbar for the live preview panel — viewport selector, refresh, URL bar. */
export function ViewportToolbar({
  onRefresh,
  viewport,
  onViewportChange,
  url,
}: ViewportToolbarProps): JSX.Element {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.375rem 0.75rem',
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        flexShrink: 0,
      }}
    >
      <button
        data-testid="refresh-button"
        onClick={onRefresh}
        aria-label="Refresh preview"
        style={{
          padding: '0.25rem 0.5rem',
          background: 'transparent',
          border: '1px solid var(--color-border)',
          borderRadius: '4px',
          cursor: 'pointer',
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--text-sm)',
        }}
      >
        ↺
      </button>

      <div style={{ display: 'flex', gap: '0.25rem' }}>
        {VIEWPORT_OPTIONS.map(({ label, width, testId }) => (
          <button
            key={width}
            data-testid={testId}
            onClick={() => onViewportChange(width)}
            aria-pressed={viewport === width}
            style={{
              padding: '0.25rem 0.5rem',
              background: viewport === width ? 'var(--color-accent)' : 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: '4px',
              cursor: 'pointer',
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--text-xs)',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <input
        readOnly
        value={url}
        aria-label="Preview URL"
        style={{
          flex: 1,
          padding: '0.25rem 0.5rem',
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: '4px',
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--text-sm)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      />
    </div>
  )
}
