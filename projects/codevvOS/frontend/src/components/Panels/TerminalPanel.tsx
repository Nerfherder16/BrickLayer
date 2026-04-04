import { useCallback, useEffect, useRef } from 'react'
import type { IDockviewPanelProps } from 'dockview-react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebglAddon } from '@xterm/addon-webgl'
import { WebLinksAddon } from '@xterm/addon-web-links'
import { SearchAddon } from '@xterm/addon-search'
import { usePtyWebSocket } from '@/hooks/usePtyWebSocket'
import './TerminalPanel.css'

function getCssVar(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value !== '' ? value : fallback
}

export default function TerminalPanel(_props: IDockviewPanelProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null)
  const terminalRef = useRef<Terminal | null>(null)
  const sessionId = useRef(crypto.randomUUID()).current

  const handleData = useCallback((data: string) => {
    terminalRef.current?.write(data)
  }, [])

  const { send, sendResize } = usePtyWebSocket(sessionId, handleData)

  useEffect(() => {
    if (containerRef.current === null) return

    const background = getCssVar('--terminal-background', '#0A0A0D')
    const foreground = getCssVar('--terminal-foreground', '#CCCCCC')
    const cursor = getCssVar('--terminal-cursor', '#CCCCCC')
    const fontFamily = getCssVar('--font-mono', 'monospace')

    // Step 1: Create Terminal instance
    const terminal = new Terminal({
      theme: {
        background,
        foreground,
        cursor,
        cursorAccent: '#0A0A0D',
        selectionBackground: 'rgba(107, 102, 248, 0.3)',
      },
      fontFamily,
      fontSize: 13,
      lineHeight: 1.4,
      cursorBlink: true,
    })

    // Step 2: Attach to DOM (MUST happen before loading addons)
    terminal.open(containerRef.current)
    terminalRef.current = terminal

    // Step 3–6: Load addons in order
    const webglAddon = new WebglAddon()
    const fitAddon = new FitAddon()
    const webLinksAddon = new WebLinksAddon()
    const searchAddon = new SearchAddon()

    webglAddon.onContextLoss(() => {
      webglAddon.dispose()
    })

    terminal.loadAddon(webglAddon)
    terminal.loadAddon(fitAddon)
    terminal.loadAddon(webLinksAddon)
    terminal.loadAddon(searchAddon)

    // Step 7: Initial fit
    fitAddon.fit()

    // Wire user keystrokes → ptyHost
    const dataDisposable = terminal.onData((data: string) => {
      send(data)
    })

    // Wire terminal resize → ptyHost
    const resizeDisposable = terminal.onResize(({ cols, rows }: { cols: number; rows: number }) => {
      sendResize(cols, rows)
    })

    // Debounced ResizeObserver for container size changes
    let resizeTimer: ReturnType<typeof setTimeout> | null = null
    const resizeObserver = new ResizeObserver(() => {
      if (resizeTimer !== null) clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => {
        fitAddon.fit()
      }, 150)
    })
    resizeObserver.observe(containerRef.current)

    return () => {
      terminalRef.current = null
      if (resizeTimer !== null) clearTimeout(resizeTimer)
      resizeObserver.disconnect()
      dataDisposable.dispose()
      resizeDisposable.dispose()
      fitAddon.dispose()
      webglAddon.dispose()
      webLinksAddon.dispose()
      searchAddon.dispose()
      terminal.dispose()
    }
  }, [send, sendResize])

  return <div ref={containerRef} className="terminal-panel" data-testid="terminal-panel" />
}
