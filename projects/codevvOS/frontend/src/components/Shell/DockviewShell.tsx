import { useCallback, useContext, useEffect, useRef } from 'react'
import {
  DockviewReact,
  type DockviewApi,
  type DockviewReadyEvent,
  type IDockviewPanelProps,
} from 'dockview-react'
import { LayoutContext } from '../../contexts/LayoutContext'
import { getStoredToken } from '../../api/auth'
import { APP_REGISTRY } from '../Dock/appRegistry'
import WelcomePanel from './WelcomePanel'
import TerminalPanel from '../Panels/TerminalPanel'
import FileTreePanel from '../Panels/FileTreePanel'
import AIChatPanel from '../Panels/AIChatPanel'
import SettingsPanel from '../Panels/SettingsPanel'
import '../../styles/dockview-theme.css'

// Panel component registry — DockviewReact requires FunctionComponent (not ComponentType)
export const COMPONENTS: Record<string, React.FunctionComponent<IDockviewPanelProps>> = {
  WelcomePanel: WelcomePanel as React.FunctionComponent<IDockviewPanelProps>,
  TerminalPanel: TerminalPanel as React.FunctionComponent<IDockviewPanelProps>,
  FileTreePanel: FileTreePanel as React.FunctionComponent<IDockviewPanelProps>,
  AIChatPanel: AIChatPanel as React.FunctionComponent<IDockviewPanelProps>,
  SettingsPanel: SettingsPanel as React.FunctionComponent<IDockviewPanelProps>,
}

// Dev-mode assertion: warn if any APP_REGISTRY componentKey is missing from COMPONENTS
if (import.meta.env.DEV) {
  APP_REGISTRY.forEach(app => {
    if (!(app.componentKey in COMPONENTS)) {
      console.warn(`[DockviewShell] Missing COMPONENTS entry for componentKey: "${app.componentKey}"`)
    }
  })
}

// Default layout applied when no saved layout exists or fromJSON fails
const DEFAULT_PANEL_OPTS = {
  id: 'welcome',
  component: 'WelcomePanel',
  title: 'Welcome',
} as const

function applyDefaultLayout(api: DockviewApi): void {
  api.addPanel(DEFAULT_PANEL_OPTS)
}

export default function DockviewShell(): JSX.Element {
  const { setDockviewApi } = useContext(LayoutContext)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const disposableRef = useRef<{ dispose: () => void } | null>(null)

  // Cleanup subscription and pending save timer on unmount
  useEffect(() => {
    return () => {
      disposableRef.current?.dispose()
      if (saveTimerRef.current !== null) {
        clearTimeout(saveTimerRef.current)
      }
    }
  }, [])

  const loadLayout = useCallback(
    async (api: DockviewApi) => {
      try {
        const token = getStoredToken()
        const res = await fetch('/api/layout', {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        })
        const data = (await res.json()) as { layout_version: number | null; layout: unknown }

        if (data.layout && typeof data.layout === 'object') {
          try {
            api.fromJSON(data.layout as Parameters<DockviewApi['fromJSON']>[0])
          } catch {
            applyDefaultLayout(api)
          }
        } else {
          applyDefaultLayout(api)
        }
      } catch {
        applyDefaultLayout(api)
      }
    },
    [],
  )

  const handleReady = useCallback(
    (event: DockviewReadyEvent) => {
      const api = event.api
      setDockviewApi(api)

      // Subscribe to layout changes with 1000ms debounce
      disposableRef.current = api.onDidLayoutChange(() => {
        if (saveTimerRef.current !== null) {
          clearTimeout(saveTimerRef.current)
        }
        saveTimerRef.current = setTimeout(() => {
          saveTimerRef.current = null
          const token = getStoredToken()
          fetch('/api/layout', {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ version: 1, layout: api.toJSON() }),
          }).catch(() => {
            // Non-fatal: layout save failure is silent
          })
        }, 1000)
      })

      // Load saved layout (async, non-blocking)
      void loadLayout(api)
    },
    [setDockviewApi, loadLayout],
  )

  return (
    <div style={{ height: 'calc(100vh - 48px)', width: '100%' }}>
      <DockviewReact components={COMPONENTS} onReady={handleReady} />
    </div>
  )
}
