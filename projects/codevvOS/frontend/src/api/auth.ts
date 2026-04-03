const TOKEN_KEY = 'codevvos_token'

export interface UserSummary {
  id: string
  display_name: string
  avatar_initials: string
}

export interface User {
  id: string
  display_name: string
  avatar_initials: string
}

/** Fetch all users for the login screen picker. */
export async function listUsers(): Promise<UserSummary[]> {
  const res = await fetch('/api/auth/users')
  if (!res.ok) throw new Error('Network error')
  return res.json()
}

/** Authenticate a user by ID and password, returning a JWT. */
export async function login(userId: string, password: string): Promise<{ token: string; user: User }> {
  const res = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, password }),
  })
  if (!res.ok) throw res
  return res.json()
}

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function storeToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}
