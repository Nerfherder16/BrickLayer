/** Action bar shown below diff decorations: Accept, Reject, Regenerate. */

export interface DiffActionBarProps {
  onAccept: () => void
  onReject: () => void
  onRegenerate: () => void
}

export default function DiffActionBar({
  onAccept,
  onReject,
  onRegenerate,
}: DiffActionBarProps): JSX.Element {
  return (
    <div
      data-testid="diff-action-bar"
      style={{
        display: 'flex',
        gap: '0.5rem',
        padding: '0.375rem 0.5rem',
        background: 'var(--color-surface, #1e293b)',
        borderTop: '1px solid var(--color-border, #334155)',
        borderRadius: '0 0 4px 4px',
      }}
    >
      <button
        aria-label="Accept changes"
        onClick={onAccept}
        style={{
          padding: '0.25rem 0.625rem',
          fontSize: '0.75rem',
          fontWeight: 600,
          background: 'var(--color-success, #22c55e)',
          color: 'var(--color-on-success, #fff)',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
        }}
      >
        Accept
      </button>
      <button
        aria-label="Reject changes"
        onClick={onReject}
        style={{
          padding: '0.25rem 0.625rem',
          fontSize: '0.75rem',
          fontWeight: 600,
          background: 'var(--color-danger, #ef4444)',
          color: 'var(--color-on-danger, #fff)',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
        }}
      >
        Reject
      </button>
      <button
        aria-label="Regenerate"
        onClick={onRegenerate}
        style={{
          padding: '0.25rem 0.625rem',
          fontSize: '0.75rem',
          fontWeight: 600,
          background: 'var(--color-muted, #475569)',
          color: 'var(--color-text, #e2e8f0)',
          border: 'none',
          borderRadius: '3px',
          cursor: 'pointer',
        }}
      >
        Regenerate
      </button>
    </div>
  )
}
