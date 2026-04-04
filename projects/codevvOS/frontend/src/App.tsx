import 'dockview-react/dist/styles/dockview.css'
import './styles/dockview-theme.css'
import { useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useBreakpoint } from '@/hooks/useBreakpoint'
import { LayoutContextProvider } from '@/contexts/LayoutContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { KeyboardProvider } from '@/contexts/KeyboardContext'
import { registerShortcut, unregisterShortcut } from '@/hooks/useKeyboardShortcuts'
import DockviewShell from '@/components/Shell/DockviewShell'
import Dock from '@/components/Dock/Dock'
import LoginScreen from '@/components/Login/LoginScreen'
import MobileShell from '@/components/Mobile/MobileShell'

function DefaultShortcuts(): null {
  useEffect(() => {
    // CommandPalette (Task 4.5) will wire the real handler
    registerShortcut('cmd-palette-cmd', 'cmd+shift+k', () => undefined, 'global')
    registerShortcut('cmd-palette-ctrl', 'ctrl+shift+k', () => undefined, 'global')
    // Settings panel — handler wired when SettingsPanel component exists
    registerShortcut('settings-cmd', 'cmd+,', () => undefined, 'global')
    registerShortcut('settings-ctrl', 'ctrl+,', () => undefined, 'global')
    // Terminal focus
    registerShortcut('terminal-focus', 'ctrl+`', () => undefined, 'global')
    // New panel shortcuts (Task 5.14)
    registerShortcut('live-preview-cmd', 'cmd+shift+p', () => undefined, 'global')
    registerShortcut('sidecar-output-cmd', 'cmd+shift+b', () => undefined, 'global')
    registerShortcut('artifacts-cmd', 'cmd+shift+a', () => undefined, 'global')
    registerShortcut('knowledge-graph-cmd', 'cmd+shift+g', () => undefined, 'global')

    return () => {
      unregisterShortcut('cmd-palette-cmd')
      unregisterShortcut('cmd-palette-ctrl')
      unregisterShortcut('settings-cmd')
      unregisterShortcut('settings-ctrl')
      unregisterShortcut('terminal-focus')
      unregisterShortcut('live-preview-cmd')
      unregisterShortcut('sidecar-output-cmd')
      unregisterShortcut('artifacts-cmd')
      unregisterShortcut('knowledge-graph-cmd')
    }
  }, [])

  return null
}

export default function App(): JSX.Element {
  const { isAuthenticated, login } = useAuth()
  const { isMobile } = useBreakpoint()

  if (!isAuthenticated) {
    return (
      <KeyboardProvider>
        <ThemeProvider>
          <LoginScreen onLoginSuccess={login} />
        </ThemeProvider>
      </KeyboardProvider>
    )
  }

  if (isMobile) {
    return (
      <KeyboardProvider>
        <ThemeProvider>
          <MobileShell />
        </ThemeProvider>
      </KeyboardProvider>
    )
  }

  return (
    <KeyboardProvider>
      <ThemeProvider>
        <LayoutContextProvider>
          <DefaultShortcuts />
          <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
            <DockviewShell />
            <Dock />
          </div>
        </LayoutContextProvider>
      </ThemeProvider>
    </KeyboardProvider>
  )
}
