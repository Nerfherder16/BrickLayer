import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { usePtyWebSocket } from '../usePtyWebSocket'

// WebSocket mock
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  url: string
  readyState: number = MockWebSocket.CONNECTING
  sentMessages: string[] = []
  onopen: (() => void) | null = null
  onclose: ((event: { code: number; reason: string }) => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: ((event: unknown) => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
    // Simulate async open
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      this.onopen?.()
    }, 0)
  }

  send(data: string): void {
    this.sentMessages.push(data)
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({ code: 1000, reason: 'normal' })
  }

  // Helper to simulate receiving a message
  simulateMessage(data: unknown): void {
    this.onmessage?.({ data: JSON.stringify(data) })
  }

  // Helper to simulate connection close (server-side)
  simulateClose(code = 1006): void {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({ code, reason: '' })
  }

  static instances: MockWebSocket[] = []

  static reset(): void {
    MockWebSocket.instances = []
  }

  static latest(): MockWebSocket {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1]
  }
}

describe('usePtyWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.reset()
    vi.useFakeTimers()
    vi.stubGlobal('WebSocket', MockWebSocket)
    // Clear sessionStorage token
    sessionStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    sessionStorage.clear()
  })

  it('should open WebSocket with URL containing sessionId', async () => {
    const { unmount } = renderHook(() => usePtyWebSocket('test-session'))

    // Let the async open happen
    await act(async () => {
      await vi.runAllTimersAsync()
    })

    expect(MockWebSocket.instances.length).toBeGreaterThan(0)
    expect(MockWebSocket.latest().url).toContain('/pty/test-session')
    unmount()
  })

  it('should send auth message as first message on open', async () => {
    const testToken = 'test-jwt-token'
    sessionStorage.setItem('codevvos_token', testToken)

    const { unmount } = renderHook(() => usePtyWebSocket('test-session'))

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const ws = MockWebSocket.latest()
    expect(ws.sentMessages.length).toBeGreaterThan(0)

    const firstMessage = JSON.parse(ws.sentMessages[0])
    expect(firstMessage.type).toBe('auth')
    expect(firstMessage.token).toBe(testToken)
    unmount()
  })

  it('should send ACK when receiving a data message', async () => {
    const { unmount } = renderHook(() => usePtyWebSocket('test-session'))

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const ws = MockWebSocket.latest()

    act(() => {
      ws.simulateMessage({ type: 'data', id: 1, data: 'hello' })
    })

    // Find the ACK message (after the auth message)
    const ackMessage = ws.sentMessages
      .map((m) => JSON.parse(m))
      .find((m) => m.type === 'ack' && m.id === 1)

    expect(ackMessage).toBeDefined()
    expect(ackMessage?.type).toBe('ack')
    expect(ackMessage?.id).toBe(1)
    unmount()
  })

  it('should send resize message when sendResize is called', async () => {
    const { result, unmount } = renderHook(() => usePtyWebSocket('test-session'))

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const ws = MockWebSocket.latest()
    const initialCount = ws.sentMessages.length

    act(() => {
      result.current.sendResize(80, 24)
    })

    expect(ws.sentMessages.length).toBe(initialCount + 1)
    const resizeMsg = JSON.parse(ws.sentMessages[ws.sentMessages.length - 1])
    expect(resizeMsg).toEqual({ type: 'resize', cols: 80, rows: 24 })
    unmount()
  })

  it('should attempt reconnection after close with 1s initial delay', async () => {
    const { unmount } = renderHook(() => usePtyWebSocket('test-session'))

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const firstWs = MockWebSocket.latest()
    const initialCount = MockWebSocket.instances.length

    // Simulate unexpected server close
    act(() => {
      firstWs.simulateClose(1006)
    })

    // Should not reconnect immediately
    expect(MockWebSocket.instances.length).toBe(initialCount)

    // Advance by 1s — should reconnect
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000)
    })

    expect(MockWebSocket.instances.length).toBe(initialCount + 1)
    unmount()
  })

  it('should call WebSocket.close() on unmount', async () => {
    const { unmount } = renderHook(() => usePtyWebSocket('test-session'))

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const ws = MockWebSocket.latest()
    const closeSpy = vi.spyOn(ws, 'close')

    unmount()

    expect(closeSpy).toHaveBeenCalled()
  })

  it('should return send function that sends data messages', async () => {
    const { result, unmount } = renderHook(() => usePtyWebSocket('test-session'))

    await act(async () => {
      await vi.runAllTimersAsync()
    })

    const ws = MockWebSocket.latest()
    const initialCount = ws.sentMessages.length

    act(() => {
      result.current.send('ls -la\r')
    })

    expect(ws.sentMessages.length).toBe(initialCount + 1)
    const dataMsg = JSON.parse(ws.sentMessages[ws.sentMessages.length - 1])
    expect(dataMsg).toEqual({ type: 'data', data: 'ls -la\r' })
    unmount()
  })
})
