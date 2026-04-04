import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'

// ---------------------------------------------------------------------------
// Mock @codemirror/* packages — EditorView requires a real DOM layout engine
// that jsdom cannot provide. We stub at the module level.
// ---------------------------------------------------------------------------

const mockDestroy = vi.fn()
const mockDispatch = vi.fn()

// Track the latest updateListener callback so tests can fire it
let capturedUpdateListener: ((update: { docChanged: boolean; state: { doc: { toString: () => string } } }) => void) | null = null

vi.mock('@codemirror/view', () => {
  const mockEditable = { of: vi.fn(() => 'editable-ext') }

  class MockEditorView {
    dom = document.createElement('div')
    state = { doc: { toString: () => '' } }
    destroy = mockDestroy
    dispatch = mockDispatch

    static updateListener = {
      of: (fn: (update: { docChanged: boolean; state: { doc: { toString: () => string } } }) => void) => {
        capturedUpdateListener = fn
        return { extension: 'updateListener' }
      },
    }

    static editable = mockEditable
  }

  return {
    EditorView: MockEditorView,
    keymap: { of: () => [] },
  }
})

vi.mock('@codemirror/state', () => ({
  EditorState: {
    create: vi.fn(({ doc }: { doc: string }) => ({
      doc: { toString: () => doc ?? '' },
    })),
  },
  Compartment: vi.fn(() => ({
    of: (ext: unknown) => ext,
    reconfigure: (ext: unknown) => ext,
  })),
}))

vi.mock('@codemirror/lang-javascript', () => ({
  javascript: vi.fn(() => ({ extension: 'javascript' })),
}))

vi.mock('@codemirror/lang-python', () => ({
  python: vi.fn(() => ({ extension: 'python' })),
}))

vi.mock('@codemirror/theme-one-dark', () => ({
  oneDark: { extension: 'oneDark' },
}))

// Import component AFTER mocks are in place
import CodeMirrorEditor from '../components/Editor/CodeMirrorEditor'

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('CodeMirrorEditor', () => {
  beforeEach(() => {
    mockDestroy.mockClear()
    mockDispatch.mockClear()
    capturedUpdateListener = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders wrapper div with data-testid="codemirror-editor"', () => {
    const onChange = vi.fn()
    render(<CodeMirrorEditor value="" onChange={onChange} />)
    expect(screen.getByTestId('codemirror-editor')).toBeDefined()
  })

  it('calls onChange when updateListener fires with docChanged=true', () => {
    const onChange = vi.fn()
    render(<CodeMirrorEditor value="hello" onChange={onChange} />)

    act(() => {
      if (capturedUpdateListener) {
        capturedUpdateListener({
          docChanged: true,
          state: { doc: { toString: () => 'hello world' } },
        })
      }
    })

    expect(onChange).toHaveBeenCalledWith('hello world')
  })

  it('does not call onChange when docChanged is false', () => {
    const onChange = vi.fn()
    render(<CodeMirrorEditor value="hello" onChange={onChange} />)

    act(() => {
      if (capturedUpdateListener) {
        capturedUpdateListener({
          docChanged: false,
          state: { doc: { toString: () => 'hello' } },
        })
      }
    })

    expect(onChange).not.toHaveBeenCalled()
  })

  it('destroys EditorView on unmount (no memory leak)', () => {
    const onChange = vi.fn()
    const { unmount } = render(<CodeMirrorEditor value="" onChange={onChange} />)
    unmount()
    expect(mockDestroy).toHaveBeenCalledTimes(1)
  })

  it('accepts language prop without crashing (javascript)', () => {
    const onChange = vi.fn()
    expect(() =>
      render(<CodeMirrorEditor value="" onChange={onChange} language="javascript" />),
    ).not.toThrow()
  })

  it('accepts language prop without crashing (python)', () => {
    const onChange = vi.fn()
    expect(() =>
      render(<CodeMirrorEditor value="" onChange={onChange} language="python" />),
    ).not.toThrow()
  })

  it('accepts readOnly prop without crashing', () => {
    const onChange = vi.fn()
    expect(() =>
      render(<CodeMirrorEditor value="" onChange={onChange} readOnly />),
    ).not.toThrow()
  })
})

// ---------------------------------------------------------------------------
// Feature flag test — EditorPanel renders CodeMirrorEditor when flag is true
// ---------------------------------------------------------------------------
describe('EditorPanel feature flag', () => {
  it('renders codemirror-editor when useCodeMirror flag is true (default)', async () => {
    const { default: EditorPanel } = await import('../components/Panels/EditorPanel')
    render(<EditorPanel />)
    expect(screen.getByTestId('codemirror-editor')).toBeDefined()
  })
})
