import { useState, useEffect, useRef, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { listUsers, login, storeToken } from '@/api/auth'
import type { UserSummary } from '@/api/auth'
import './LoginScreen.css'

type Phase = 'loading' | 'picker' | 'password' | 'admin-create'
type ErrorKind = 'wrong-password' | 'locked' | 'network' | null

interface LoginScreenProps {
  onLoginSuccess: (token: string) => void
}

function Clock() {
  const fmt = () =>
    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  const [time, setTime] = useState(fmt)

  useEffect(() => {
    const id = setInterval(() => setTime(fmt()), 1000)
    return () => clearInterval(id)
  }, [])

  return <span>{time}</span>
}

function AdminCreateForm() {
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch('/api/auth/register-admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: displayName, email, password }),
      })
      if (!res.ok) throw new Error('Failed')
      window.location.reload()
    } catch {
      setError('Failed to create account. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="admin-form" onSubmit={handleSubmit}>
      <div className="admin-form-field">
        <label className="admin-form-label" htmlFor="admin-display-name">
          Display Name
        </label>
        <input
          id="admin-display-name"
          className="admin-form-input"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          required
        />
      </div>
      <div className="admin-form-field">
        <label className="admin-form-label" htmlFor="admin-email">
          Email
        </label>
        <input
          id="admin-email"
          type="email"
          className="admin-form-input"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="admin-form-field">
        <label className="admin-form-label" htmlFor="admin-password">
          Password
        </label>
        <input
          id="admin-password"
          type="password"
          className="admin-form-input"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      {error && <p className="error-message">{error}</p>}
      <button type="submit" className="btn-primary" disabled={submitting}>
        Create Account
      </button>
    </form>
  )
}

export function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const [phase, setPhase] = useState<Phase>('loading')
  const [users, setUsers] = useState<UserSummary[]>([])
  const [selectedUser, setSelectedUser] = useState<UserSummary | null>(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<ErrorKind>(null)
  const [shaking, setShaking] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [networkError, setNetworkError] = useState(false)
  const passwordRef = useRef<HTMLInputElement>(null)

  const loadUsers = useCallback(async () => {
    setPhase('loading')
    setNetworkError(false)
    try {
      const list = await listUsers()
      setUsers(list)
      if (list.length === 0) {
        setPhase('admin-create')
      } else if (list.length === 1) {
        setSelectedUser(list[0])
        setPhase('password')
      } else {
        setPhase('picker')
      }
    } catch {
      setNetworkError(true)
      setPhase('picker')
    }
  }, [])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  useEffect(() => {
    if (phase === 'password') {
      const id = setTimeout(() => passwordRef.current?.focus(), 50)
      return () => clearTimeout(id)
    }
  }, [phase])

  function selectUser(user: UserSummary) {
    setSelectedUser(user)
    setPassword('')
    setError(null)
    setPhase('password')
  }

  function goBack() {
    setPhase('picker')
    setSelectedUser(null)
    setPassword('')
    setError(null)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedUser || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await login(selectedUser.id, password)
      storeToken(result.token)
      onLoginSuccess(result.token)
    } catch (err) {
      if (err instanceof Response) {
        if (err.status === 401) {
          let body: { detail?: string } = {}
          try {
            body = await err.json()
          } catch {
            /* ignore */
          }
          if (body.detail?.toLowerCase().includes('locked')) {
            setError('locked')
          } else {
            setError('wrong-password')
            setPassword('')
            setShaking(true)
            setTimeout(() => setShaking(false), 400)
            setTimeout(() => passwordRef.current?.focus(), 10)
          }
        } else {
          setError('network')
        }
      } else {
        setError('network')
      }
    } finally {
      setSubmitting(false)
    }
  }

  // Network error on initial load (before any users fetched)
  if (networkError && phase === 'picker') {
    return (
      <div className="login-screen" data-testid="login-screen">
        <div className="login-gradient" aria-hidden="true" />
        <div className="login-center">
          <div className="login-card">
            <div className="network-error-content">
              <p className="error-message">
                Unable to reach CodeVV. Check that services are running.
              </p>
              <button className="btn-primary" onClick={loadUsers} style={{ width: 'auto', padding: '0 1.5rem' }}>
                Retry
              </button>
            </div>
          </div>
        </div>
        <footer className="login-footer">
          <span>CodeVV OS</span>
          <Clock />
        </footer>
      </div>
    )
  }

  return (
    <div className="login-screen" data-testid="login-screen">
      <div className="login-gradient" aria-hidden="true" />

      <div className="login-center">
        <div className={`login-card${shaking ? ' shake' : ''}`}>
          <AnimatePresence mode="wait">
            {phase === 'loading' && (
              <motion.div
                key="loading"
                className="login-spinner-wrapper"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="spinner" role="status" aria-label="Loading users" />
              </motion.div>
            )}

            {phase === 'picker' && !networkError && (
              <motion.div
                key="picker"
                className="user-picker"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                <div className={`user-picker-grid${users.length >= 5 ? ' grid-2col' : ''}`}>
                  {users.map((user) => (
                    <button
                      key={user.id}
                      className="user-card"
                      onClick={() => selectUser(user)}
                      type="button"
                    >
                      <div className="user-avatar">{user.avatar_initials}</div>
                      <span className="user-name">{user.display_name}</span>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {phase === 'password' && selectedUser && (
              <motion.div
                key="password"
                className="password-phase"
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -40 }}
                transition={{ duration: 0.2, ease: [0.2, 0, 0, 1] }}
              >
                <div className="user-avatar-lg">{selectedUser.avatar_initials}</div>
                <p className="user-name" style={{ fontSize: 'var(--text-base)', textAlign: 'center' }}>
                  {selectedUser.display_name}
                </p>

                <form className="password-form" onSubmit={handleSubmit}>
                  <input
                    ref={passwordRef}
                    type="password"
                    className={`password-input${error === 'wrong-password' ? ' error' : ''}`}
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={error === 'locked' || submitting}
                    aria-label="Password"
                  />

                  {error === 'wrong-password' && (
                    <p className="error-message">Incorrect password</p>
                  )}
                  {error === 'locked' && (
                    <p className="warning-message">Account locked. Contact your admin.</p>
                  )}
                  {error === 'network' && (
                    <p className="error-message">
                      Unable to reach CodeVV. Check that services are running.
                    </p>
                  )}

                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={submitting || error === 'locked'}
                  >
                    Sign in
                  </button>

                  {users.length > 1 && (
                    <button type="button" className="btn-ghost" onClick={goBack}>
                      ← Other user
                    </button>
                  )}
                </form>
              </motion.div>
            )}

            {phase === 'admin-create' && (
              <motion.div
                key="admin-create"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <h2 className="login-title">Create admin account</h2>
                <AdminCreateForm />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <footer className="login-footer">
        <span>CodeVV OS</span>
        <Clock />
      </footer>
    </div>
  )
}

export default LoginScreen
