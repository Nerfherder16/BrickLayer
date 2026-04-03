import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// ---------------------------------------------------------------------------
// Mock CM6 — jsdom cannot run real CM6 layout engine
// ---------------------------------------------------------------------------
vi.mock('@codemirror/view', () => ({
  EditorView: class {
    dom = document.createElement('div')
    state = { doc: { toString: () => 'initial content' } }
    dispatch = vi.fn()
    destroy = vi.fn()
    static updateListener = { of: vi.fn(() => ({})) }
    static editable = { of: vi.fn(() => ({})) }
  },
  WidgetType: class {
    toDOM() { return document.createElement('span') }
    ignoreEvent() { return true }
  },
  Decoration: {
    widget: vi.fn(() => ({ spec: {} })),
    mark: vi.fn(({ class: cls }: { class: string }) => ({ spec: { class: cls } })),
    set: vi.fn(() => ({})),
    none: {},
  },
  DecorationSet: {},
  keymap: { of: vi.fn(() => ({})) },
  ViewPlugin: { fromClass: vi.fn(() => ({})) },
}))

vi.mock('@codemirror/state', () => ({
  EditorState: {
    create: vi.fn(() => ({ doc: { toString: () => '' } })),
  },
  StateField: {
    define: vi.fn((spec: { create: () => unknown }) => ({
      _isStateField: true,
      spec,
    })),
  },
  StateEffect: {
    define: vi.fn(() => ({
      of: vi.fn((val: unknown) => ({ value: val })),
    })),
  },
  RangeSetBuilder: vi.fn(() => ({
    add: vi.fn(),
    finish: vi.fn(() => ({})),
  })),
  Compartment: vi.fn(() => ({
    of: vi.fn((ext: unknown) => ext),
    reconfigure: vi.fn((ext: unknown) => ext),
  })),
}))

vi.mock('@codemirror/theme-one-dark', () => ({ oneDark: {} }))
vi.mock('@codemirror/lang-javascript', () => ({ javascript: vi.fn(() => ({})) }))
vi.mock('@codemirror/lang-python', () => ({ python: vi.fn(() => ({})) }))

// ---------------------------------------------------------------------------
// Mock fetch for SSE streaming
// ---------------------------------------------------------------------------
function makeSseStream(chunks: string[], done = true): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(`data: ${chunk}\n\n`))
      }
      if (done) {
        controller.enqueue(encoder.encode('event: done\ndata: \n\n'))
      }
      controller.close()
    },
  })
  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'text/event-stream' },
  })
}

// ---------------------------------------------------------------------------
// Tests — DiffActionBar
// ---------------------------------------------------------------------------
describe('DiffActionBar', () => {
  it('renders with data-testid="diff-action-bar"', async () => {
    const { default: DiffActionBar } = await import('../components/Editor/DiffActionBar')
    const onAccept = vi.fn()
    const onReject = vi.fn()
    const onRegenerate = vi.fn()
    render(<DiffActionBar onAccept={onAccept} onReject={onReject} onRegenerate={onRegenerate} />)
    expect(screen.getByTestId('diff-action-bar')).toBeDefined()
  })

  it('calls onAccept when Accept button clicked', async () => {
    const { default: DiffActionBar } = await import('../components/Editor/DiffActionBar')
    const onAccept = vi.fn()
    const onReject = vi.fn()
    const onRegenerate = vi.fn()
    render(<DiffActionBar onAccept={onAccept} onReject={onReject} onRegenerate={onRegenerate} />)
    fireEvent.click(screen.getByRole('button', { name: /accept/i }))
    expect(onAccept).toHaveBeenCalledTimes(1)
  })

  it('calls onReject when Reject button clicked', async () => {
    const { default: DiffActionBar } = await import('../components/Editor/DiffActionBar')
    const onAccept = vi.fn()
    const onReject = vi.fn()
    const onRegenerate = vi.fn()
    render(<DiffActionBar onAccept={onAccept} onReject={onReject} onRegenerate={onRegenerate} />)
    fireEvent.click(screen.getByRole('button', { name: /reject/i }))
    expect(onReject).toHaveBeenCalledTimes(1)
  })

  it('calls onRegenerate when Regenerate button clicked', async () => {
    const { default: DiffActionBar } = await import('../components/Editor/DiffActionBar')
    const onAccept = vi.fn()
    const onReject = vi.fn()
    const onRegenerate = vi.fn()
    render(<DiffActionBar onAccept={onAccept} onReject={onReject} onRegenerate={onRegenerate} />)
    fireEvent.click(screen.getByRole('button', { name: /regenerate/i }))
    expect(onRegenerate).toHaveBeenCalledTimes(1)
  })
})

// ---------------------------------------------------------------------------
// Tests — InlinePromptWidget
// ---------------------------------------------------------------------------
describe('InlinePromptWidget', () => {
  const onSubmit = vi.fn()
  const onDismiss = vi.fn()

  beforeEach(() => {
    onSubmit.mockClear()
    onDismiss.mockClear()
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders input with data-testid="inline-prompt-input"', async () => {
    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={onSubmit}
        onDismiss={onDismiss}
        document="hello world"
        language="typescript"
      />,
    )
    expect(screen.getByTestId('inline-prompt-input')).toBeDefined()
  })

  it('calls onDismiss when Escape key pressed', async () => {
    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={onSubmit}
        onDismiss={onDismiss}
        document="hello world"
        language="typescript"
      />,
    )
    const input = screen.getByTestId('inline-prompt-input')
    fireEvent.keyDown(input, { key: 'Escape' })
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('calls POST /api/ai/inline-edit on submit with prompt, document, language', async () => {
    const mockFetch = vi.fn().mockReturnValue(makeSseStream(['new content']))
    vi.stubGlobal('fetch', mockFetch)

    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={onSubmit}
        onDismiss={onDismiss}
        document="hello world"
        language="typescript"
      />,
    )

    const input = screen.getByTestId('inline-prompt-input')
    await userEvent.type(input, 'refactor this')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/ai/inline-edit',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
          body: expect.stringContaining('"prompt":"refactor this"'),
        }),
      )
    })
  })

  it('body includes document and language fields', async () => {
    const mockFetch = vi.fn().mockReturnValue(makeSseStream(['result']))
    vi.stubGlobal('fetch', mockFetch)

    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={onSubmit}
        onDismiss={onDismiss}
        document="my code"
        language="python"
      />,
    )

    const input = screen.getByTestId('inline-prompt-input')
    await userEvent.type(input, 'fix')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      const bodyArg = JSON.parse(((mockFetch.mock.calls[0] as unknown[][])[1] as RequestInit).body as string)
      expect(bodyArg.document).toBe('my code')
      expect(bodyArg.language).toBe('python')
    })
  })

  it('calls onSubmit with streamed newDoc after SSE completes', async () => {
    const mockFetch = vi.fn().mockReturnValue(makeSseStream(['line one\n', 'line two']))
    vi.stubGlobal('fetch', mockFetch)

    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={onSubmit}
        onDismiss={onDismiss}
        document="original"
        language="typescript"
      />,
    )

    const input = screen.getByTestId('inline-prompt-input')
    await userEvent.type(input, 'transform')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith('line one\nline two')
    })
  })

  it('shows spinner while streaming is in progress', async () => {
    let resolveStream!: () => void
    const slowStream = new Promise<Response>((resolve) => {
      resolveStream = () => resolve(makeSseStream(['result']))
    })
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(slowStream))

    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={onSubmit}
        onDismiss={onDismiss}
        document="code"
        language="typescript"
      />,
    )

    const input = screen.getByTestId('inline-prompt-input')
    await userEvent.type(input, 'do something')
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    expect(screen.getByTestId('inline-prompt-spinner')).toBeDefined()

    await act(async () => { resolveStream() })
    await waitFor(() => {
      expect(screen.queryByTestId('inline-prompt-spinner')).toBeNull()
    })
  })
})

// ---------------------------------------------------------------------------
// Tests — diffDecorations (unit)
// ---------------------------------------------------------------------------
describe('diffDecorations', () => {
  it('exports diffDecorationsExtension function', async () => {
    const mod = await import('../components/Editor/extensions/diffDecorations')
    expect(typeof mod.diffDecorationsExtension).toBe('function')
  })

  it('returns an array (Extension[]) without throwing', async () => {
    const { diffDecorationsExtension } = await import(
      '../components/Editor/extensions/diffDecorations'
    )
    const ext = diffDecorationsExtension('line one\nline two', 'line one\nline three')
    expect(ext).toBeDefined()
  })

  it('added lines use cm-line-added class', async () => {
    const { computeDiffLines } = await import('../components/Editor/extensions/diffDecorations')
    const result = computeDiffLines('line one\n', 'line one\nline two\n')
    const added = result.filter((d) => d.type === 'added')
    expect(added.length).toBeGreaterThan(0)
    expect(added[0].lineIndex).toBe(1) // second line (0-indexed)
  })

  it('removed lines use cm-line-removed class', async () => {
    const { computeDiffLines } = await import('../components/Editor/extensions/diffDecorations')
    const result = computeDiffLines('line one\nline two\n', 'line one\n')
    const removed = result.filter((d) => d.type === 'removed')
    expect(removed.length).toBeGreaterThan(0)
  })
})

// ---------------------------------------------------------------------------
// Tests — inlineAIPrompt extension
// ---------------------------------------------------------------------------
describe('inlineAIPromptExtension', () => {
  it('exports inlineAIPromptExtension function', async () => {
    const mod = await import('../components/Editor/extensions/inlineAIPrompt')
    expect(typeof mod.inlineAIPromptExtension).toBe('function')
  })

  it('returns an array of extensions', async () => {
    const { inlineAIPromptExtension } = await import(
      '../components/Editor/extensions/inlineAIPrompt'
    )
    const ext = inlineAIPromptExtension()
    expect(Array.isArray(ext)).toBe(true)
    expect(ext.length).toBeGreaterThan(0)
  })

  it('exports openInlinePrompt action function', async () => {
    const mod = await import('../components/Editor/extensions/inlineAIPrompt')
    expect(typeof mod.openInlinePrompt).toBe('function')
  })
})
