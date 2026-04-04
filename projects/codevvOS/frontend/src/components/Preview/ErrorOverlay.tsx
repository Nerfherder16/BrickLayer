import React from 'react'

interface ErrorOverlayProps {
  visible: boolean
  onRetry: () => void
}

/** Absolute-positioned error overlay for the preview iframe. */
export function ErrorOverlay({ visible, onRetry }: ErrorOverlayProps): JSX.Element | null {
  if (!visible) return null

  return (
    <div
      data-testid="preview-error-overlay"
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        background: 'var(--color-surface)',
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-sm)',
        zIndex: 10,
      }}
    >
      <span>Failed to load preview</span>
      <button
        data-testid="error-retry-button"
        onClick={onRetry}
        style={{
          padding: '0.375rem 0.875rem',
          background: 'var(--color-accent)',
          color: 'var(--color-text)',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: 'var(--text-sm)',
        }}
      >
        Retry
      </button>
    </div>
  )
}
