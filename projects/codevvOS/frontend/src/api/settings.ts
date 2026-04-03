import { getStoredToken } from './auth'

function authHeaders(): Record<string, string> {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function fetchSchema(): Promise<object> {
  const res = await fetch('/api/settings/schema', { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed to fetch schema: ${res.status}`)
  return res.json() as Promise<object>
}

export async function fetchUserSettings(): Promise<unknown> {
  const res = await fetch('/api/settings/user', { headers: authHeaders() })
  if (!res.ok) throw new Error(`Failed to fetch settings: ${res.status}`)
  return res.json()
}

export async function saveUserSettings(data: unknown): Promise<unknown> {
  const res = await fetch('/api/settings/user', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`Failed to save settings: ${res.status}`)
  return res.json()
}
