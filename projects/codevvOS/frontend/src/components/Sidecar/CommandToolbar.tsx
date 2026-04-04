import { useState } from 'react'
import { useSidecarStore } from '@/stores/sidecarStore'

/** Toolbar with command input, run button, and stop button for the sidecar panel. */
export function CommandToolbar(): JSX.Element {
  const [commandInput, setCommandInput] = useState('')
  const { isRunning, runCommand, interrupt, clearOutput } = useSidecarStore()

  function handleRun(): void {
    const trimmed = commandInput.trim()
    if (!trimmed || isRunning) return
    const parts = trimmed.split(' ')
    const cmd = parts[0]
    const args = parts.slice(1)
    clearOutput()
    void runCommand(cmd, args)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>): void {
    if (e.key === 'Enter') handleRun()
  }

  return (
    <div
      data-testid="command-toolbar"
      style={{
        display: 'flex',
        gap: '8px',
        padding: '8px',
        borderBottom: '1px solid var(--color-border, #334155)',
        background: 'var(--color-surface, #1e293b)',
      }}
    >
      <input
        data-testid="command-input"
        type="text"
        value={commandInput}
        onChange={(e) => setCommandInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="command args..."
        disabled={isRunning}
        aria-label="Command input"
        style={{
          flex: 1,
          background: 'var(--color-bg, #0f172a)',
          color: 'var(--color-text, #e2e8f0)',
          border: '1px solid var(--color-border, #334155)',
          borderRadius: '4px',
          padding: '4px 8px',
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: '13px',
        }}
      />
      <button
        data-testid="run-button"
        onClick={handleRun}
        disabled={isRunning || commandInput.trim() === ''}
        aria-label="Run command"
        style={{
          background: 'var(--color-primary, #6366f1)',
          color: 'var(--color-text-inverse, #fff)',
          border: 'none',
          borderRadius: '4px',
          padding: '4px 12px',
          cursor: isRunning ? 'not-allowed' : 'pointer',
        }}
      >
        Run
      </button>
      <button
        data-testid="stop-button"
        onClick={() => void interrupt()}
        disabled={!isRunning}
        aria-label="Stop command"
        style={{
          background: 'var(--color-danger, #ef4444)',
          color: 'var(--color-text-inverse, #fff)',
          border: 'none',
          borderRadius: '4px',
          padding: '4px 12px',
          cursor: !isRunning ? 'not-allowed' : 'pointer',
          opacity: isRunning ? 1 : 0.5,
        }}
      >
        Stop
      </button>
    </div>
  )
}
