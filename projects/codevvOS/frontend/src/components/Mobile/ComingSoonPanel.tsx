import { LayoutDashboard } from 'lucide-react'

interface ComingSoonPanelProps {
  label: string
}

export default function ComingSoonPanel({ label }: ComingSoonPanelProps): JSX.Element {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        gap: '0.75rem',
        color: 'var(--color-text-tertiary)',
      }}
    >
      <LayoutDashboard size={32} aria-hidden="true" />
      <span style={{ fontSize: 'var(--text-sm)' }}>Coming in Phase 3</span>
      <span style={{ fontSize: 'var(--text-xs)', opacity: 0.7 }}>{label}</span>
    </div>
  )
}
