import 'dockview-react/dist/styles/dockview.css'
import './styles/dockview-theme.css'
import { useAuth } from '@/hooks/useAuth'
import { LayoutContextProvider } from '@/contexts/LayoutContext'
import DockviewShell from '@/components/Shell/DockviewShell'
import Dock from '@/components/Dock/Dock'
import LoginScreen from '@/components/Login/LoginScreen'

export default function App(): JSX.Element {
  const { isAuthenticated, login } = useAuth()

  if (!isAuthenticated) {
    return <LoginScreen onLoginSuccess={login} />
  }

  return (
    <LayoutContextProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <DockviewShell />
        <Dock />
      </div>
    </LayoutContextProvider>
  )
}
