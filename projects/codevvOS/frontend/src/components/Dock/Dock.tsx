import { MonitorDot } from 'lucide-react'

export default function Dock() {
  return (
    <div
      data-testid="dock"
      style={{ height: '48px', display: 'flex', alignItems: 'center', padding: '0 8px', gap: '4px' }}
    >
      <button
        aria-label="Welcome"
        type="button"
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '8px', display: 'flex', alignItems: 'center' }}
      >
        <MonitorDot size={20} />
      </button>
    </div>
  )
}
