import { useState } from 'react'
import type { IDockviewPanelProps } from 'dockview-react'
import { useArtifactStore } from '../../stores/artifactStore'
import { IframeSandbox } from '../Artifacts/IframeSandbox'
import { ArtifactHistory } from '../Artifacts/ArtifactHistory'
import type { ArtifactHistoryItem } from '../Artifacts/ArtifactHistory'

/** Dockview panel that renders the active artifact in a sandboxed iframe. */
export default function ArtifactPanel(_props: IDockviewPanelProps): JSX.Element {
  const getActiveArtifact = useArtifactStore((s) => s.getActiveArtifact)
  const addArtifact = useArtifactStore((s) => s.addArtifact)
  const setActiveArtifact = useArtifactStore((s) => s.setActiveArtifact)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const artifact = getActiveArtifact()

  function handleHistorySelect(item: ArtifactHistoryItem): void {
    addArtifact({
      id: item.metadata.artifact_id,
      title: item.metadata.title,
      jsx: item.metadata.jsx,
      compiled: item.metadata.compiled,
    })
    setActiveArtifact(item.metadata.artifact_id)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.375rem 0.75rem',
          borderBottom: '1px solid var(--color-border, #334155)',
          background: 'var(--color-surface, #1e293b)',
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted, #64748b)' }}>
          History:
        </span>
        <ArtifactHistory onSelect={handleHistorySelect} />
      </div>

      {!artifact ? (
        <div
          data-testid="artifact-panel-empty"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 1,
            color: 'var(--color-text-muted, #64748b)',
            fontSize: '0.875rem',
          }}
        >
          No artifact selected
        </div>
      ) : !artifact.compiled ? (
        <div
          data-testid="artifact-panel-empty"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flex: 1,
            color: 'var(--color-text-muted, #64748b)',
            fontSize: '0.875rem',
          }}
        >
          Artifact not compiled yet
        </div>
      ) : (
        <div style={{ position: 'relative', flex: 1 }}>
          <IframeSandbox
            compiled={artifact.compiled}
            title={artifact.title}
            onError={(msg) => setErrorMessage(msg)}
          />
          {errorMessage !== null && (
            <div
              data-testid="artifact-error-overlay"
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'rgba(15, 23, 42, 0.85)',
                color: 'var(--color-text, #e2e8f0)',
                gap: '0.75rem',
                padding: '1rem',
              }}
            >
              <span style={{ color: 'var(--color-error, #f87171)', fontWeight: 600 }}>
                Artifact error
              </span>
              <span style={{ fontSize: '0.875rem', textAlign: 'center' }}>{errorMessage}</span>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                style={{
                  padding: '0.375rem 0.875rem',
                  border: '1px solid var(--color-border, #334155)',
                  borderRadius: '0.375rem',
                  background: 'var(--color-surface, #1e293b)',
                  color: 'var(--color-text, #e2e8f0)',
                  cursor: 'pointer',
                  fontSize: '0.8125rem',
                }}
              >
                Dismiss
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
