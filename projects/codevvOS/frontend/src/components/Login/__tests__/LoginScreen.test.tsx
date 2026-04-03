import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { LoginScreen } from '../LoginScreen'

const singleUser = [{ id: 'u1', display_name: 'Tim', avatar_initials: 'T' }]
const twoUsers = [
  { id: 'u1', display_name: 'Tim', avatar_initials: 'T' },
  { id: 'u2', display_name: 'Alice', avatar_initials: 'A' },
]

const server = setupServer(
  http.get('/api/auth/users', () => HttpResponse.json(singleUser)),
  http.post('/auth/login', () =>
    HttpResponse.json({ token: 'test-jwt', user: { id: 'u1', display_name: 'Tim', avatar_initials: 'T' } }),
  ),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  sessionStorage.clear()
})
afterAll(() => server.close())

describe('LoginScreen', () => {
  it('should show spinner then Tim name after loading single user', async () => {
    render(<LoginScreen onLoginSuccess={vi.fn()} />)
    expect(screen.getByRole('status')).toBeDefined()
    // Single user → goes to Phase B where display name is shown
    expect(await screen.findByText('Tim')).toBeDefined()
  })

  it('should show password input directly and auto-focus with single user', async () => {
    render(<LoginScreen onLoginSuccess={vi.fn()} />)
    const input = await screen.findByPlaceholderText('Password')
    expect(input).toBeDefined()
    await waitFor(() => {
      expect(document.activeElement?.getAttribute('placeholder')).toBe('Password')
    })
  })

  it('should show user picker cards with two users then password input after click', async () => {
    server.use(http.get('/api/auth/users', () => HttpResponse.json(twoUsers)))
    render(<LoginScreen onLoginSuccess={vi.fn()} />)

    expect(await screen.findByText('Tim')).toBeDefined()
    expect(screen.getByText('Alice')).toBeDefined()

    fireEvent.click(screen.getByText('Tim'))

    expect(await screen.findByPlaceholderText('Password')).toBeDefined()
  })

  it('should call onLoginSuccess with token and store in sessionStorage on success', async () => {
    const mockFn = vi.fn()
    render(<LoginScreen onLoginSuccess={mockFn} />)

    const input = await screen.findByPlaceholderText('Password')
    fireEvent.change(input, { target: { value: 'correct' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => expect(mockFn).toHaveBeenCalledWith('test-jwt'))
    expect(sessionStorage.getItem('codevvos_token')).toBe('test-jwt')
  })

  it('should show Incorrect password error and shake card on 401', async () => {
    server.use(
      http.post('/auth/login', () =>
        new HttpResponse(JSON.stringify({ detail: 'Invalid credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
    render(<LoginScreen onLoginSuccess={vi.fn()} />)

    const input = await screen.findByPlaceholderText('Password')
    fireEvent.change(input, { target: { value: 'wrong' } })
    fireEvent.submit(input.closest('form')!)

    expect(await screen.findByText('Incorrect password')).toBeDefined()
    const card = document.querySelector('.login-card')
    expect(card?.classList.contains('shake')).toBe(true)
  })

  it('should show Unable to reach CodeVV on network error', async () => {
    server.use(http.get('/api/auth/users', () => HttpResponse.error()))
    render(<LoginScreen onLoginSuccess={vi.fn()} />)
    expect(await screen.findByText(/Unable to reach CodeVV/)).toBeDefined()
  })
})
