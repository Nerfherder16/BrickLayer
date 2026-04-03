import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSidecarStore } from '../stores/sidecarStore'

// Helper to encode a single SSE data line
function sseChunk(data: string): Uint8Array {
  return new TextEncoder().encode(`data: ${data}\n\n`)
}

function makeReadableStream(chunks: Uint8Array[]): ReadableStream<Uint8Array> {
  let i = 0
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) {
        controller.enqueue(chunks[i++])
      } else {
        controller.close()
      }
    },
  })
}

beforeEach(() => {
  // Reset store to initial state before each test
  useSidecarStore.setState({
    output: [],
    isRunning: false,
    currentCommand: null,
    connectionState: 'idle',
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('sidecarStore', () => {
  describe('initial state', () => {
    it('should have empty output array', () => {
      expect(useSidecarStore.getState().output).toEqual([])
    })

    it('should have isRunning false', () => {
      expect(useSidecarStore.getState().isRunning).toBe(false)
    })

    it('should have connectionState idle', () => {
      expect(useSidecarStore.getState().connectionState).toBe('idle')
    })

    it('should have null currentCommand', () => {
      expect(useSidecarStore.getState().currentCommand).toBeNull()
    })
  })

  describe('runCommand', () => {
    it('should POST to /bl-sidecar/run with command and args', async () => {
      const mockFetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        body: makeReadableStream([]),
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('ls', ['-la'])

      expect(mockFetch).toHaveBeenCalledWith('/bl-sidecar/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'ls', args: ['-la'] }),
      })
    })

    it('should default args to empty array when not provided', async () => {
      const mockFetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        body: makeReadableStream([]),
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('whoami')

      expect(mockFetch).toHaveBeenCalledWith('/bl-sidecar/run', expect.objectContaining({
        body: JSON.stringify({ command: 'whoami', args: [] }),
      }))
    })

    it('should set connectionState to connecting before first event', async () => {
      let capturedState: string | null = null

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async () => {
        capturedState = useSidecarStore.getState().connectionState
        return {
          ok: true,
          body: makeReadableStream([]),
        } as unknown as Response
      })

      await useSidecarStore.getState().runCommand('echo', ['hello'])
      expect(capturedState).toBe('connecting')
    })

    it('should accumulate SSE data lines in output array', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        body: makeReadableStream([
          sseChunk('line one'),
          sseChunk('line two'),
          sseChunk('line three'),
        ]),
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('echo', ['test'])

      expect(useSidecarStore.getState().output).toEqual(['line one', 'line two', 'line three'])
    })

    it('should set isRunning to false after stream completes', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        body: makeReadableStream([sseChunk('done')]),
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('ls')

      expect(useSidecarStore.getState().isRunning).toBe(false)
    })

    it('should set connectionState to done after stream completes', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        body: makeReadableStream([]),
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('ls')

      expect(useSidecarStore.getState().connectionState).toBe('done')
    })

    it('should set connectionState to error when fetch response is not ok', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        body: null,
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('badcmd')

      expect(useSidecarStore.getState().connectionState).toBe('error')
      expect(useSidecarStore.getState().isRunning).toBe(false)
    })

    it('should set connectionState to error when fetch throws', async () => {
      vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))

      await useSidecarStore.getState().runCommand('ls')

      expect(useSidecarStore.getState().connectionState).toBe('error')
      expect(useSidecarStore.getState().isRunning).toBe(false)
    })

    it('should store currentCommand', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        body: makeReadableStream([]),
      } as unknown as Response)

      await useSidecarStore.getState().runCommand('pytest')

      expect(useSidecarStore.getState().currentCommand).toBe('pytest')
    })
  })

  describe('interrupt', () => {
    it('should POST to /bl-sidecar/interrupt', async () => {
      const mockFetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as unknown as Response)

      await useSidecarStore.getState().interrupt()

      expect(mockFetch).toHaveBeenCalledWith('/bl-sidecar/interrupt', { method: 'POST' })
    })

    it('should set isRunning to false after interrupt', async () => {
      useSidecarStore.setState({ isRunning: true })
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: true } as Response)

      await useSidecarStore.getState().interrupt()

      expect(useSidecarStore.getState().isRunning).toBe(false)
    })

    it('should set connectionState to idle after interrupt', async () => {
      useSidecarStore.setState({ connectionState: 'running' })
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: true } as Response)

      await useSidecarStore.getState().interrupt()

      expect(useSidecarStore.getState().connectionState).toBe('idle')
    })
  })

  describe('getStatus', () => {
    it('should GET /bl-sidecar/status and return result', async () => {
      const mockStatus = { active: true, command: 'pytest' }
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus,
      } as unknown as Response)

      const result = await useSidecarStore.getState().getStatus()

      expect(result).toEqual(mockStatus)
    })

    it('should return inactive state when fetch fails', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        json: async () => ({}),
      } as unknown as Response)

      const result = await useSidecarStore.getState().getStatus()

      expect(result).toEqual({ active: false, command: null })
    })
  })

  describe('clearOutput', () => {
    it('should clear the output array', () => {
      useSidecarStore.setState({ output: ['line1', 'line2'] })
      useSidecarStore.getState().clearOutput()
      expect(useSidecarStore.getState().output).toEqual([])
    })
  })
})
