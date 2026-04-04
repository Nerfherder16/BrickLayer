import { useState, useEffect } from 'react'
import { getStoredToken, storeToken, clearToken } from '@/api/auth'

interface AuthState {
  token: string | null
  isAuthenticated: boolean
}

const isExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.exp < Math.floor(Date.now() / 1000)
  } catch {
    return true
  }
}

function resolveInitialState(): AuthState {
  const stored = getStoredToken()
  if (stored !== null && !isExpired(stored)) {
    return { token: stored, isAuthenticated: true }
  }
  return { token: null, isAuthenticated: false }
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(resolveInitialState)

  useEffect(() => {
    const stored = getStoredToken()
    if (stored !== null && isExpired(stored)) {
      clearToken()
      setState({ token: null, isAuthenticated: false })
    }
  }, [])

  const login = (token: string) => {
    storeToken(token)
    setState({ token, isAuthenticated: true })
  }

  const logout = () => {
    clearToken()
    setState({ token: null, isAuthenticated: false })
  }

  return { ...state, login, logout }
}
