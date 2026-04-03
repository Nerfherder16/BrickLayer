import type { IDockviewPanelProps } from 'dockview-react'
import { Settings } from 'lucide-react'

export default function SettingsPanel(_props: IDockviewPanelProps): JSX.Element {
  return (
    <div
      data-testid="settings-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        gap: '12px',
      }}
    >
      <Settings size="var(--icon-3xl)" color="var(--color-text-tertiary)" />
      <span
        style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--color-text-tertiary)',
        }}
      >
        Settings — Coming in Phase 3c
      </span>
    </div>
  )
}
