import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useAuth } from '../useAuth'

const TOKEN_KEY = 'codevvos_token'

function makeJWT(exp: number): string {
  const payload = Buffer.from(JSON.stringify({ exp })).toString('base64')
  return `header.${payload}.sig`
}

describe('useAuth', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  afterEach(() => {
    sessionStorage.clear()
  })

  it('should have isAuthenticated false with no token in sessionStorage', () => {
    const { result } = renderHook(() => useAuth())
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.token).toBeNull()
  })

  it('should set isAuthenticated true after login with valid future-expiry JWT', async () => {
    const validToken = makeJWT(9999999999)
    const { result } = renderHook(() => useAuth())
    await act(async () => {
      result.current.login(validToken)
    })
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.token).toBe(validToken)
  })

  it('should set isAuthenticated false after logout and clear sessionStorage', async () => {
    const validToken = makeJWT(9999999999)
    const { result } = renderHook(() => useAuth())
    await act(async () => {
      result.current.login(validToken)
    })
    await act(async () => {
      result.current.logout()
    })
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.token).toBeNull()
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('should set isAuthenticated false when sessionStorage has expired token on mount', () => {
    const expiredToken = makeJWT(1)
    sessionStorage.setItem(TOKEN_KEY, expiredToken)
    const { result } = renderHook(() => useAuth())
    expect(result.current.isAuthenticated).toBe(false)
  })
})
