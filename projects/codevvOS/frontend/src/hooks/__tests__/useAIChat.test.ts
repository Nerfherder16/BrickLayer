import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAIChat } from '../useAIChat'
import * as aiApi from '../../api/ai'

vi.mock('../../api/ai')

const mockStreamChat = vi.mocked(aiApi.streamChat)

async function* makeStream(
  items: Array<{ token?: string; error?: string; done?: boolean }>,
): AsyncGenerator<{ token?: string; error?: string; done?: boolean }> {
  for (const item of items) {
    yield item
  }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useAIChat', () => {
  it('should have empty messages and isStreaming false on initial render', () => {
    const { result } = renderHook(() => useAIChat())
    expect(result.current.messages).toEqual([])
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.currentResponse).toBe('')
  })

  it('should add user message and set isStreaming true when sendMessage is called', async () => {
    mockStreamChat.mockReturnValue(makeStream([{ done: true }]))

    const { result } = renderHook(() => useAIChat())

    act(() => {
      void result.current.sendMessage('hello')
    })

    // User message added synchronously
    expect(result.current.messages).toContainEqual({ role: 'user', content: 'hello' })
    expect(result.current.isStreaming).toBe(true)
  })

  it('should append assistant message and clear isStreaming after stream completes', async () => {
    mockStreamChat.mockReturnValue(makeStream([{ token: 'World' }, { done: true }]))

    const { result } = renderHook(() => useAIChat())

    await act(async () => {
      await result.current.sendMessage('hello')
    })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))

    expect(result.current.messages).toContainEqual({ role: 'assistant', content: 'World' })
    expect(result.current.isStreaming).toBe(false)
  })

  it('should set isStreaming false on error from stream', async () => {
    mockStreamChat.mockReturnValue(makeStream([{ error: 'oops' }, { done: true }]))

    const { result } = renderHook(() => useAIChat())

    await act(async () => {
      await result.current.sendMessage('hello')
    })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))
    expect(result.current.isStreaming).toBe(false)
  })

  it('should set isStreaming false when cancelStream is called', async () => {
    // Simulate a slow stream that never resolves (we'll cancel before it finishes)
    let resolve!: () => void
    const neverEnds = async function* () {
      yield { token: 'partial' }
      // hang until aborted
      await new Promise<void>((r) => { resolve = r })
      yield { done: true as const }
    }
    mockStreamChat.mockReturnValue(neverEnds())

    const { result } = renderHook(() => useAIChat())

    act(() => {
      void result.current.sendMessage('hello')
    })

    await waitFor(() => expect(result.current.isStreaming).toBe(true))

    act(() => {
      result.current.cancelStream()
      resolve() // unblock generator so it doesn't leak
    })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))
  })
})
