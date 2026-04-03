import { useState, useRef, useCallback } from 'react'
import { streamChat } from '../api/ai'
import type { ChatMessage } from '../api/ai'

interface UseAIChatReturn {
  messages: ChatMessage[]
  isStreaming: boolean
  currentResponse: string
  sendMessage: (text: string) => Promise<void>
  cancelStream: () => void
}

/** Manages AI chat state: message history, streaming response, and cancellation. */
export function useAIChat(): UseAIChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')
  const abortControllerRef = useRef<AbortController | null>(null)
  const cancelledRef = useRef(false)

  const sendMessage = useCallback(async (text: string): Promise<void> => {
    const userMessage: ChatMessage = { role: 'user', content: text }

    setMessages((prev) => [...prev, userMessage])
    setIsStreaming(true)
    setCurrentResponse('')

    const controller = new AbortController()
    abortControllerRef.current = controller
    cancelledRef.current = false

    let accumulated = ''

    try {
      const generator = streamChat(text, messages)
      for await (const chunk of generator) {
        if (cancelledRef.current) break

        if (chunk.done) {
          if (accumulated) {
            const assistantMessage: ChatMessage = { role: 'assistant', content: accumulated }
            setMessages((prev) => [...prev, assistantMessage])
          }
          setCurrentResponse('')
          setIsStreaming(false)
          return
        }

        if (chunk.token !== undefined) {
          accumulated += chunk.token
          setCurrentResponse(accumulated)
        }
      }
    } catch {
      // Swallow errors — stream already ended or was cancelled
    } finally {
      setIsStreaming(false)
    }
  }, [messages])

  const cancelStream = useCallback((): void => {
    cancelledRef.current = true
    abortControllerRef.current?.abort()
    setIsStreaming(false)
  }, [])

  return { messages, isStreaming, currentResponse, sendMessage, cancelStream }
}
