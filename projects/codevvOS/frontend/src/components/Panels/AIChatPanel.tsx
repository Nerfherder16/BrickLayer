import { useRef, useEffect, useCallback } from 'react'
import type { IDockviewPanelProps } from 'dockview-react'
import { Send, Square, MessageSquare } from 'lucide-react'
import { useAIChat } from '../../hooks/useAIChat'
import './AIChatPanel.css'

/** AI chat panel for dockview — streams responses from POST /api/ai/chat. */
export default function AIChatPanel(_props: IDockviewPanelProps): JSX.Element {
  const { messages, isStreaming, currentResponse, sendMessage, cancelStream } = useAIChat()
  const messageListRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new content arrives if near bottom
  useEffect(() => {
    const list = messageListRef.current
    if (!list) return
    const nearBottom = list.scrollHeight - list.scrollTop - list.clientHeight <= 50
    if (nearBottom || isStreaming) {
      list.scrollTop = list.scrollHeight
    }
  }, [messages, currentResponse, isStreaming])

  const handleSend = useCallback((): void => {
    const textarea = textareaRef.current
    if (!textarea) return
    const text = textarea.value.trim()
    if (!text || isStreaming) return
    textarea.value = ''
    resizeTextarea(textarea)
    void sendMessage(text)
  }, [isStreaming, sendMessage])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const handleInput = useCallback((e: React.FormEvent<HTMLTextAreaElement>): void => {
    resizeTextarea(e.currentTarget)
  }, [])

  const hasMessages = messages.length > 0 || isStreaming

  return (
    <div className="ai-chat-panel" data-testid="ai-chat-panel">
      {hasMessages ? (
        <div className="ai-chat-message-list" ref={messageListRef}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message-bubble message-${msg.role}`}
              data-align={msg.role === 'user' ? 'right' : 'left'}
            >
              <div className="message-text">{msg.content}</div>
              <div className="message-timestamp">{new Date().toLocaleTimeString()}</div>
            </div>
          ))}

          {isStreaming && currentResponse === '' && (
            <div className="ai-chat-thinking" data-testid="thinking-indicator">
              <div className="ai-chat-thinking-dots">
                <span className="ai-chat-thinking-dot" />
                <span className="ai-chat-thinking-dot" />
                <span className="ai-chat-thinking-dot" />
              </div>
              <span>Thinking...</span>
            </div>
          )}

          {isStreaming && currentResponse !== '' && (
            <div
              className="ai-chat-streaming"
              data-testid="streaming-response"
              data-align="left"
            >
              <span className="message-text ai-chat-streaming-cursor">{currentResponse}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="ai-chat-empty-state" data-testid="empty-state">
          <MessageSquare className="ai-chat-empty-icon" aria-hidden="true" />
          <span className="ai-chat-empty-text">Start a conversation</span>
        </div>
      )}

      <div className="ai-chat-input-area">
        <textarea
          ref={textareaRef}
          className="ai-chat-textarea"
          data-testid="chat-input"
          placeholder="Ask AI..."
          rows={1}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          aria-label="Chat message input"
        />
        {isStreaming ? (
          <button
            className="ai-chat-action-button"
            data-testid="stop-button"
            onClick={cancelStream}
            aria-label="Stop streaming"
            type="button"
          >
            <Square size={18} />
          </button>
        ) : (
          <button
            className="ai-chat-action-button"
            data-testid="send-button"
            onClick={handleSend}
            aria-label="Send message"
            type="button"
          >
            <Send size={18} />
          </button>
        )}
      </div>
    </div>
  )
}

function resizeTextarea(el: HTMLTextAreaElement): void {
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}
