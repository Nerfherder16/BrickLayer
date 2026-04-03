import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AIChatPanel from '../AIChatPanel'
import * as useAIChatModule from '../../../hooks/useAIChat'
import type { ChatMessage } from '../../../api/ai'

vi.mock('../../../hooks/useAIChat')

const mockSendMessage = vi.fn()
const mockCancelStream = vi.fn()

function makeHookReturn(overrides: Partial<ReturnType<typeof useAIChatModule.useAIChat>> = {}) {
  return {
    messages: [] as ChatMessage[],
    isStreaming: false,
    currentResponse: '',
    sendMessage: mockSendMessage,
    cancelStream: mockCancelStream,
    ...overrides,
  }
}

function renderPanel() {
  const AnyPanel = AIChatPanel as React.FC
  return render(<AnyPanel />)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('AIChatPanel', () => {
  it('should render container with data-testid="ai-chat-panel"', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(makeHookReturn())
    renderPanel()
    expect(screen.getByTestId('ai-chat-panel')).toBeDefined()
  })

  it('should show empty state when there are no messages', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(makeHookReturn())
    renderPanel()
    expect(screen.getByTestId('empty-state')).toBeDefined()
    expect(screen.getByText('Start a conversation')).toBeDefined()
  })

  it('should render user and assistant message bubbles when messages exist', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({
        messages: [
          { role: 'user', content: 'Hello there' },
          { role: 'assistant', content: 'Hi back' },
        ],
      }),
    )
    renderPanel()
    expect(screen.getByText('Hello there')).toBeDefined()
    expect(screen.getByText('Hi back')).toBeDefined()
  })

  it('should render user message bubble with data-align="right"', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({
        messages: [{ role: 'user', content: 'Hello there' }],
      }),
    )
    renderPanel()
    const bubble = screen.getByText('Hello there').closest('[data-align]')
    expect(bubble?.getAttribute('data-align')).toBe('right')
  })

  it('should render assistant message bubble with data-align="left"', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({
        messages: [{ role: 'assistant', content: 'Hi back' }],
      }),
    )
    renderPanel()
    const bubble = screen.getByText('Hi back').closest('[data-align]')
    expect(bubble?.getAttribute('data-align')).toBe('left')
  })

  it('should show thinking indicator when isStreaming and currentResponse is empty', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({ isStreaming: true, currentResponse: '' }),
    )
    renderPanel()
    expect(screen.getByTestId('thinking-indicator')).toBeDefined()
    expect(screen.getByText('Thinking...')).toBeDefined()
  })

  it('should show streaming response when isStreaming and currentResponse is non-empty', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({ isStreaming: true, currentResponse: 'partial response' }),
    )
    renderPanel()
    expect(screen.getByTestId('streaming-response')).toBeDefined()
    expect(screen.getByText(/partial response/)).toBeDefined()
  })

  it('should call sendMessage with input text when Enter is pressed', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(makeHookReturn())
    renderPanel()
    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'test' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    expect(mockSendMessage).toHaveBeenCalledWith('test')
  })

  it('should NOT send when Shift+Enter is pressed (newline instead)', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(makeHookReturn())
    renderPanel()
    const input = screen.getByTestId('chat-input')
    fireEvent.change(input, { target: { value: 'test' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  it('should show send button when not streaming', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(makeHookReturn({ isStreaming: false }))
    renderPanel()
    expect(screen.getByTestId('send-button')).toBeDefined()
  })

  it('should show stop button when streaming', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({ isStreaming: true, currentResponse: 'partial' }),
    )
    renderPanel()
    expect(screen.getByTestId('stop-button')).toBeDefined()
  })

  it('should call cancelStream when stop button is clicked', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({ isStreaming: true, currentResponse: 'partial' }),
    )
    renderPanel()
    fireEvent.click(screen.getByTestId('stop-button'))
    expect(mockCancelStream).toHaveBeenCalled()
  })

  it('should not show empty state when messages exist', () => {
    vi.mocked(useAIChatModule.useAIChat).mockReturnValue(
      makeHookReturn({
        messages: [{ role: 'user', content: 'hi' }],
      }),
    )
    renderPanel()
    expect(screen.queryByTestId('empty-state')).toBeNull()
  })
})
