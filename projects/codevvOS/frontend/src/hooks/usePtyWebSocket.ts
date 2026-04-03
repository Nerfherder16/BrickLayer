import { useEffect, useRef, useState, useCallback } from 'react'
import { getStoredToken } from '@/api/auth'

const MAX_RETRIES = 10
const BASE_DELAY_MS = 1000
const MAX_DELAY_MS = 30000

export interface PtyWebSocketResult {
  ws: WebSocket | null
  readyState: number
  send: (data: string) => void
  sendResize: (cols: number, rows: number) => void
}

/** Open and manage a WebSocket connection to the PTY host for a given session. */
export function usePtyWebSocket(sessionId: string, onData?: (data: string) => void): PtyWebSocketResult {
  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)
  const onDataRef = useRef(onData)
  useEffect(() => { onDataRef.current = onData }, [onData])
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING)

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    const ws = new WebSocket(`/pty/${sessionId}`)
    wsRef.current = ws
    setReadyState(WebSocket.CONNECTING)

    ws.onopen = () => {
      if (!mountedRef.current) {
        ws.close()
        return
      }
      retryCountRef.current = 0
      setReadyState(WebSocket.OPEN)

      const token = getStoredToken()
      ws.send(JSON.stringify({ type: 'auth', token }))
    }

    ws.onmessage = (event: MessageEvent<string>) => {
      if (!mountedRef.current) return
      try {
        const message = JSON.parse(event.data) as { type: string; id?: number; data?: string }
        if (message.type === 'data' && message.id !== undefined) {
          ws.send(JSON.stringify({ type: 'ack', id: message.id }))
          if (message.data !== undefined) {
            onDataRef.current?.(message.data)
          }
        } else if (message.type === 'replay' && message.data !== undefined) {
          onDataRef.current?.(message.data)
        }
      } catch {
        // Ignore malformed messages
      }
    }

    ws.onclose = () => {
      if (!mountedRef.current) return
      setReadyState(WebSocket.CLOSED)
      scheduleReconnect()
    }

    ws.onerror = () => {
      if (!mountedRef.current) return
      // onerror is always followed by onclose, so reconnection is handled there
    }
  }, [sessionId])

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return
    if (retryCountRef.current >= MAX_RETRIES) return

    const delay = Math.min(BASE_DELAY_MS * Math.pow(2, retryCountRef.current), MAX_DELAY_MS)
    retryCountRef.current += 1

    retryTimerRef.current = setTimeout(() => {
      if (mountedRef.current) {
        connect()
      }
    }, delay)
  }, [connect])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      if (retryTimerRef.current !== null) {
        clearTimeout(retryTimerRef.current)
        retryTimerRef.current = null
      }
      if (wsRef.current !== null) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  const send = useCallback((data: string) => {
    const ws = wsRef.current
    if (ws !== null && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'data', data }))
    }
  }, [])

  const sendResize = useCallback((cols: number, rows: number) => {
    const ws = wsRef.current
    if (ws !== null && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'resize', cols, rows }))
    }
  }, [])

  return { ws: wsRef.current, readyState, send, sendResize }
}
