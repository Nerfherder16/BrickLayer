import { getStoredToken } from './auth'

export type ChatMessage = { role: 'user' | 'assistant'; content: string; artifact?: { id: string; title: string } }

/** Stream an AI chat response via SSE from POST /api/ai/chat. */
export async function* streamChat(
  message: string,
  history: ChatMessage[],
): AsyncGenerator<{ token?: string; error?: string; done?: boolean }> {
  const token = getStoredToken()

  let response: Response
  try {
    response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, history }),
    })
  } catch (err) {
    yield { error: err instanceof Error ? err.message : String(err) }
    return
  }

  if (!response.ok || !response.body) {
    yield { error: `Request failed: ${response.status}` }
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      // Keep the last potentially incomplete line in the buffer
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data:')) continue

        const data = trimmed.slice('data:'.length).trim()
        if (data === '[DONE]') {
          yield { done: true }
          return
        }

        try {
          const parsed = JSON.parse(data) as { token?: string; error?: string }
          if (parsed.token !== undefined) {
            yield { token: parsed.token }
          } else if (parsed.error !== undefined) {
            yield { error: parsed.error }
          }
        } catch {
          // skip unparseable line
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
