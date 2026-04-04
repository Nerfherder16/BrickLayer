import { describe, it, expect, beforeAll, afterEach, afterAll, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { streamChat } from '../ai'

const TOKEN_KEY = 'codevvos_token'
const TEST_TOKEN = 'test.eyJleHAiOjk5OTk5OTk5OTl9.sig'

function makeSseStream(lines: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const line of lines) {
        controller.enqueue(encoder.encode(line))
      }
      controller.close()
    },
  })
}

const server = setupServer(
  http.post('/api/ai/chat', ({ request }) => {
    const url = new URL(request.url)
    const search = url.searchParams.get('scenario')
    if (search === 'error') {
      return new HttpResponse(
        makeSseStream([
          'data: {"error":"fail"}\n\n',
          'data: [DONE]\n\n',
        ]),
        { headers: { 'Content-Type': 'text/event-stream' } },
      )
    }
    return new HttpResponse(
      makeSseStream([
        'data: {"token":"Hi"}\n\n',
        'data: [DONE]\n\n',
      ]),
      { headers: { 'Content-Type': 'text/event-stream' } },
    )
  }),
)

beforeAll(() => {
  sessionStorage.setItem(TOKEN_KEY, TEST_TOKEN)
  server.listen({ onUnhandledRequest: 'error' })
})
afterEach(() => server.resetHandlers())
afterAll(() => {
  server.close()
  sessionStorage.clear()
})

describe('streamChat', () => {
  it('should yield token and done for a normal SSE stream', async () => {
    const results: Array<{ token?: string; error?: string; done?: boolean }> = []
    for await (const chunk of streamChat('hello', [])) {
      results.push(chunk)
    }
    expect(results).toContainEqual({ token: 'Hi' })
    expect(results[results.length - 1]).toEqual({ done: true })
  })

  it('should yield error event from SSE stream', async () => {
    // Override handler with error scenario via custom handler
    server.use(
      http.post('/api/ai/chat', () => {
        return new HttpResponse(
          makeSseStream([
            'data: {"error":"fail"}\n\n',
            'data: [DONE]\n\n',
          ]),
          { headers: { 'Content-Type': 'text/event-stream' } },
        )
      }),
    )

    const results: Array<{ token?: string; error?: string; done?: boolean }> = []
    for await (const chunk of streamChat('hello', [])) {
      results.push(chunk)
    }
    expect(results).toContainEqual({ error: 'fail' })
    expect(results[results.length - 1]).toEqual({ done: true })
  })

  it('should call fetch with correct URL, method POST, and Authorization header', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    // consume the generator
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    for await (const _ of streamChat('hello', [])) {
      // drain
    }
    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/ai/chat',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: `Bearer ${TEST_TOKEN}`,
        }),
      }),
    )
    fetchSpy.mockRestore()
  })
})
