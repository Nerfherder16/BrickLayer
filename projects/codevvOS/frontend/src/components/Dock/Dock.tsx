import { useContext, useEffect, useState } from 'react'
import { LayoutContext } from '../../contexts/LayoutContext'
import { APP_REGISTRY } from './appRegistry'

export default function Dock(): JSX.Element {
  const { dockviewApi } = useContext(LayoutContext)
  const [activePanelId, setActivePanelId] = useState<string | null>(null)
  const [openPanelIds, setOpenPanelIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (dockviewApi === null) return

    const activeDisposable = dockviewApi.onDidActivePanelChange((panel) => {
      setActivePanelId(panel?.id ?? null)
    })

    const layoutDisposable = dockviewApi.onDidLayoutChange(() => {
      setOpenPanelIds(new Set(dockviewApi.panels.map((p) => p.id)))
    })

    return () => {
      activeDisposable.dispose()
      layoutDisposable.dispose()
    }
  }, [dockviewApi])

  function handleAppClick(appId: string, componentKey: string, label: string): void {
    if (dockviewApi === null) return

    if (activePanelId === appId) {
      // Already active — no-op
      return
    }

    const existing = dockviewApi.getPanel(appId)
    if (existing !== null && existing !== undefined) {
      existing.focus()
    } else {
      dockviewApi.addPanel({ id: appId, component: componentKey, title: label })
    }
  }

  return (
    <div
      data-testid="dock"
      style={{
        height: '48px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 8px',
        gap: '4px',
      }}
    >
      {APP_REGISTRY.map((app) => {
        const Icon = app.icon
        const isActive = activePanelId === app.id
        const isOpen = openPanelIds.has(app.id)

        return (
          <div
            key={app.id}
            style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
          >
            <button
              type="button"
              aria-label={app.label}
              title={app.label}
              data-testid={`dock-btn-${app.id}`}
              data-active={isActive ? 'true' : undefined}
              data-open={isOpen ? 'true' : undefined}
              onClick={() => { handleAppClick(app.id, app.componentKey, app.label) }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '8px',
                display: 'flex',
                alignItems: 'center',
                opacity: isActive ? 1 : 0.7,
              }}
            >
              <Icon size={20} />
            </button>
            {isActive && (
              <span
                aria-hidden="true"
                style={{
                  position: 'absolute',
                  bottom: 0,
                  width: '3px',
                  height: '3px',
                  borderRadius: '50%',
                  background: 'var(--color-accent, #6b66f8)',
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
