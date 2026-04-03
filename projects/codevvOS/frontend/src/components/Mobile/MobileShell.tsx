import { useState } from 'react'
import { LayoutDashboard, FolderOpen, Terminal, MessageSquare, MoreHorizontal } from 'lucide-react'
import WelcomePanel from '@/components/Panels/WelcomePanel'
import ComingSoonPanel from '@/components/Mobile/ComingSoonPanel'

type TabId = 'dashboard' | 'files' | 'terminal' | 'ai-chat' | 'more'

interface Tab {
  id: TabId
  label: string
  Icon: React.ComponentType<{ size?: number; 'aria-hidden'?: string }>
}

const TABS: Tab[] = [
  { id: 'dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { id: 'files', label: 'Files', Icon: FolderOpen },
  { id: 'terminal', label: 'Terminal', Icon: Terminal },
  { id: 'ai-chat', label: 'AI Chat', Icon: MessageSquare },
  { id: 'more', label: 'More', Icon: MoreHorizontal },
]

function ActivePanel({ activeTab }: { activeTab: TabId }): JSX.Element {
  if (activeTab === 'dashboard') return <WelcomePanel />
  const tab = TABS.find(t => t.id === activeTab)
  return <ComingSoonPanel label={tab?.label ?? activeTab} />
}

export default function MobileShell(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard')

  return (
    <div
      style={{
        height: '100vh',
        overflow: 'hidden',
        backgroundColor: 'var(--color-base)',
        position: 'relative',
      }}
    >
      <div
        data-testid="panel-content"
        style={{
          height: 'calc(100vh - 56px - env(safe-area-inset-bottom))',
          overflow: 'auto',
        }}
      >
        <ActivePanel activeTab={activeTab} />
      </div>

      <nav
        role="tablist"
        aria-label="Mobile navigation"
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: '56px',
          display: 'flex',
          backgroundColor: 'var(--color-surface-2)',
          borderTop: '1px solid var(--color-border-muted)',
        }}
      >
        {TABS.map(({ id, label, Icon }) => {
          const isActive = activeTab === id
          return (
            <button
              key={id}
              role="tab"
              onClick={() => setActiveTab(id)}
              aria-selected={isActive}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.25rem',
                background: 'none',
                border: 'none',
                borderTop: isActive
                  ? '2px solid var(--color-accent)'
                  : '2px solid transparent',
                color: isActive ? 'var(--color-accent)' : 'var(--color-text-tertiary)',
                cursor: 'pointer',
                fontSize: 'var(--text-xs)',
                padding: 0,
              }}
            >
              <Icon size={20} aria-hidden="true" />
              {label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
