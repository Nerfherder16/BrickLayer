import { useArtifactStore } from '../../stores/artifactStore'

export interface RenderChipProps {
  artifactId: string
  title: string
}

/** Inline chip rendered below chat messages that have an associated artifact. */
export function RenderChip({ artifactId, title }: RenderChipProps): JSX.Element {
  const setActiveArtifact = useArtifactStore((s) => s.setActiveArtifact)

  return (
    <button
      data-testid="render-chip"
      type="button"
      className="render-chip"
      onClick={() => setActiveArtifact(artifactId)}
      aria-label={`Open artifact: ${title}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        padding: '0.25rem 0.625rem',
        borderRadius: '9999px',
        border: '1px solid var(--color-border, #334155)',
        background: 'var(--color-surface, #1e293b)',
        color: 'var(--color-text, #e2e8f0)',
        fontSize: '0.75rem',
        cursor: 'pointer',
        marginTop: '0.5rem',
      }}
    >
      <span aria-hidden="true">▶</span>
      {title}
    </button>
  )
}
