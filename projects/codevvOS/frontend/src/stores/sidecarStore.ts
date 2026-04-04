import { create } from 'zustand'

export type ConnectionState = 'idle' | 'connecting' | 'running' | 'done' | 'error'

export interface SidecarState {
  output: string[]
  isRunning: boolean
  currentCommand: string | null
  connectionState: ConnectionState

  runCommand: (command: string, args?: string[]) => Promise<void>
  interrupt: () => Promise<void>
  getStatus: () => Promise<{ active: boolean; command: string | null }>
  clearOutput: () => void
}

export const useSidecarStore = create<SidecarState>((set) => ({
  output: [],
  isRunning: false,
  currentCommand: null,
  connectionState: 'idle',

  async runCommand(command: string, args: string[] = []): Promise<void> {
    set({ output: [], isRunning: true, currentCommand: command, connectionState: 'connecting' })

    try {
      const response = await fetch('/bl-sidecar/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, args }),
      })

      if (!response.ok || response.body === null) {
        set({ isRunning: false, connectionState: 'error' })
        return
      }

      set({ connectionState: 'running' })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            set((state) => ({ output: [...state.output, data] }))
          }
        }
      }

      set({ isRunning: false, connectionState: 'done' })
    } catch {
      set({ isRunning: false, connectionState: 'error' })
    }
  },

  async interrupt(): Promise<void> {
    await fetch('/bl-sidecar/interrupt', { method: 'POST' })
    set({ isRunning: false, connectionState: 'idle' })
  },

  async getStatus(): Promise<{ active: boolean; command: string | null }> {
    const res = await fetch('/bl-sidecar/status')
    if (!res.ok) return { active: false, command: null }
    return (await res.json()) as { active: boolean; command: string | null }
  },

  clearOutput(): void {
    set({ output: [] })
  },
}))
