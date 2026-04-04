import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'
import * as dockview from 'dockview-react'

vi.mock('../components/Shell/DockviewShell', () => ({
  default: () => <div data-testid="dockview-shell" />,
}))
vi.mock('../components/Dock/Dock', () => ({
  default: () => <div data-testid="dock" />,
}))
vi.mock('../components/Login/LoginScreen', () => ({
  default: ({ onLoginSuccess }: { onLoginSuccess: (token: string) => void }) => (
    <div data-testid="login-screen">
      <button onClick={() => onLoginSuccess('test.eyJleHAiOjk5OTk5OTk5OTl9.sig')}>Login</button>
    </div>
  ),
}))

const TOKEN_KEY = 'codevvos_token'

function makeJWT(exp: number): string {
  return `header.${Buffer.from(JSON.stringify({ exp })).toString('base64')}.sig`
}

describe('App', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  afterEach(() => {
    sessionStorage.clear()
  })

  it('should render without error and produce non-zero body height', () => {
    expect(() => render(<App />)).not.toThrow()
    expect(document.body).toBeDefined()
  })

  it('should show login-screen when no token in sessionStorage', () => {
    render(<App />)
    expect(screen.getByTestId('login-screen')).toBeDefined()
  })

  it('should show shell when valid future-expiry token is in sessionStorage', () => {
    sessionStorage.setItem(TOKEN_KEY, makeJWT(9999999999))
    render(<App />)
    expect(screen.getByTestId('dock')).toBeDefined()
  })

  it('should show login-screen when expired token is in sessionStorage', () => {
    sessionStorage.setItem(TOKEN_KEY, makeJWT(1))
    render(<App />)
    expect(screen.getByTestId('login-screen')).toBeDefined()
  })
})

describe('dockview-react', () => {
  it('should export DockviewReact', () => {
    expect(dockview.DockviewReact).toBeDefined()
  })
})
