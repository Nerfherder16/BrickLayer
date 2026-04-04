import type { IDockviewPanelProps } from 'dockview-react'
import { useSidecarStore } from '@/stores/sidecarStore'
import { CommandToolbar } from '@/components/Sidecar/CommandToolbar'
import { AnsiOutput } from '@/components/Sidecar/AnsiOutput'

/** Dockview panel that streams BL sidecar command output with ANSI color rendering. */
export default function SidecarOutputPanel(_props: IDockviewPanelProps): JSX.Element {
  const { output, connectionState } = useSidecarStore()

  return (
    <div
      data-testid="sidecar-output-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'var(--color-bg, #0f172a)',
        color: 'var(--color-text, #e2e8f0)',
        overflow: 'hidden',
      }}
    >
      <CommandToolbar />
      {connectionState === 'connecting' && (
        <div
          data-testid="sidecar-connecting"
          style={{
            padding: '8px',
            color: 'var(--color-text-muted, #64748b)',
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: '13px',
          }}
        >
          Connecting…
        </div>
      )}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px',
        }}
      >
        <AnsiOutput lines={output} />
      </div>
    </div>
  )
}
