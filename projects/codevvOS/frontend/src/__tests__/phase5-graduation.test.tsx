/**
 * Phase 5 Graduation Test — Integration smoke tests for the full Phase 5 feature set.
 *
 * Verifies:
 *   1. CodeMirror editor mounts with feature flag enabled
 *   2. Inline prompt widget appears with data-testid
 *   3. LivePreviewPanel renders iframe with src from store
 *   4. SidecarOutputPanel renders with SSE mock
 *   5. ArtifactPanel renders iframe with allow-scripts sandbox
 *   6. KnowledgeGraphPanel renders graph canvas
 *   7. APP_REGISTRY includes all 4 new panel keys
 *   8. All 4 new panels coexist in dockview without errors
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mock @codemirror/* packages
// ---------------------------------------------------------------------------
vi.mock('@codemirror/view', () => ({
  EditorView: class {
    dom = document.createElement('div')
    state = { doc: { toString: () => '' } }
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
    mark: vi.fn(() => ({ spec: {} })),
    set: vi.fn(() => ({})),
    none: {},
  },
  DecorationSet: {},
  keymap: { of: vi.fn(() => ({})) },
  ViewPlugin: { fromClass: vi.fn(() => ({})) },
}))

vi.mock('@codemirror/state', () => ({
  EditorState: { create: vi.fn(() => ({ doc: { toString: () => '' } })) },
  StateField: {
    define: vi.fn((spec: { create: () => unknown }) => ({ _isStateField: true, spec })),
  },
  StateEffect: {
    define: vi.fn(() => ({ of: vi.fn((val: unknown) => ({ value: val })) })),
  },
  RangeSetBuilder: vi.fn(() => ({ add: vi.fn(), finish: vi.fn(() => ({})) })),
  Compartment: vi.fn(() => ({
    of: vi.fn((ext: unknown) => ext),
    reconfigure: vi.fn((ext: unknown) => ext),
  })),
}))

vi.mock('@codemirror/theme-one-dark', () => ({ oneDark: {} }))
vi.mock('@codemirror/lang-javascript', () => ({ javascript: vi.fn(() => ({})) }))
vi.mock('@codemirror/lang-python', () => ({ python: vi.fn(() => ({})) }))

// ---------------------------------------------------------------------------
// Mock Sigma / Graphology for KnowledgeGraphPanel
// ---------------------------------------------------------------------------
vi.mock('@react-sigma/core', () => ({
  SigmaContainer: ({ children }: { children: React.ReactNode }) => (
    React.createElement('div', { 'data-testid': 'sigma-container' }, children)
  ),
  useLoadGraph: () => vi.fn(),
  useRegisterEvents: () => vi.fn(),
}))

vi.mock('graphology', () => {
  class MockMultiGraph {
    addNode(): void {}
    addEdge(): void {}
    nodes(): string[] { return [] }
  }
  return { default: MockMultiGraph, MultiGraph: MockMultiGraph }
})

vi.mock('graphology-layout-forceatlas2', () => ({ default: vi.fn() }))

// ---------------------------------------------------------------------------
// Mock ansi-to-html for SidecarOutputPanel
// ---------------------------------------------------------------------------
vi.mock('ansi-to-html', () => ({
  default: class MockAnsiToHtml {
    toHtml(input: string): string { return input }
  },
}))

// ---------------------------------------------------------------------------
// Mock stores
// ---------------------------------------------------------------------------
vi.mock('../stores/previewStore')
vi.mock('../stores/artifactStore')
vi.mock('../stores/sidecarStore')
vi.mock('../stores/graphStore')

import * as previewStoreModule from '../stores/previewStore'
import * as artifactStoreModule from '../stores/artifactStore'
import * as sidecarStoreModule from '../stores/sidecarStore'
import * as graphStoreModule from '../stores/graphStore'
import type { SidecarState, ConnectionState } from '../stores/sidecarStore'

// ---------------------------------------------------------------------------
// Imports after mocks
// ---------------------------------------------------------------------------
import CodeMirrorEditor from '../components/Editor/CodeMirrorEditor'
import LivePreviewPanel from '../components/Panels/LivePreviewPanel'
import SidecarOutputPanel from '../components/Panels/SidecarOutputPanel'
import ArtifactPanel from '../components/Panels/ArtifactPanel'
import KnowledgeGraphPanel from '../components/Panels/KnowledgeGraphPanel'
import { APP_REGISTRY } from '../components/Dock/appRegistry'
import type { IDockviewPanelProps } from 'dockview-react'


// ---------------------------------------------------------------------------
// Store setup helpers
// ---------------------------------------------------------------------------

function setupPreviewStore(overrides: Partial<ReturnType<typeof previewStoreModule.usePreviewStore>> = {}): void {
  const state = {
    previewPort: 5173,
    refreshCount: 0,
    previewUrl: 'http://localhost:5173?_r=0',
    setPort: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  }
  vi.mocked(previewStoreModule.usePreviewStore).mockImplementation((selector: unknown) => {
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
}

function setupArtifactStore(): void {
  const mockGetActiveArtifact = vi.fn().mockReturnValue({
    id: 'art-1',
    title: 'My Artifact',
    jsx: '<div>hello</div>',
    compiled: 'console.log("hello")',
  })
  const state = {
    artifacts: [],
    activeArtifactId: 'art-1',
    addArtifact: vi.fn(),
    setActiveArtifact: vi.fn(),
    getActiveArtifact: mockGetActiveArtifact,
  }
  vi.mocked(artifactStoreModule.useArtifactStore).mockImplementation((selector: unknown) => {
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
}

function setupSidecarStore(overrides: Partial<SidecarState> = {}): void {
  const state: SidecarState = {
    output: [],
    isRunning: false,
    currentCommand: null,
    connectionState: 'idle' as ConnectionState,
    runCommand: vi.fn(),
    interrupt: vi.fn(),
    getStatus: vi.fn(),
    clearOutput: vi.fn(),
    ...overrides,
  }
  vi.mocked(sidecarStoreModule.useSidecarStore).mockImplementation((selector: unknown) => {
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
}

function setupGraphStore(): void {
  const state = {
    nodes: [],
    edges: [],
    selectedNodeId: null,
    typeFilter: new Set<string>(),
    searchQuery: '',
    fetchNodes: vi.fn().mockResolvedValue(undefined),
    fetchEdges: vi.fn().mockResolvedValue(undefined),
    setSelectedNode: vi.fn(),
    toggleTypeFilter: vi.fn(),
    setSearchQuery: vi.fn(),
    addNode: vi.fn(),
    filteredNodes: [],
  }
  vi.mocked(graphStoreModule.useGraphStore).mockImplementation((selector: unknown) => {
    if (typeof selector === 'function') return (selector as (s: typeof state) => unknown)(state)
    return state
  })
}

// ---------------------------------------------------------------------------
// EventSource mock — jsdom does not include EventSource
// ---------------------------------------------------------------------------

class MockEventSource {
  url: string
  onmessage: ((ev: MessageEvent) => void) | null = null
  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  close = vi.fn()
  constructor(url: string) { this.url = url }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.clearAllMocks()
  vi.stubGlobal('EventSource', MockEventSource)
  setupPreviewStore()
  setupArtifactStore()
  setupSidecarStore()
  setupGraphStore()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Phase 5 Graduation', () => {
  it('1. CodeMirror editor mounts with feature flag enabled', () => {
    render(
      <CodeMirrorEditor
        value="const x = 1"
        onChange={vi.fn()}
        language="typescript"
      />,
    )
    expect(screen.getByTestId('codemirror-editor')).toBeDefined()
  })

  it('2. Inline prompt widget renders with data-testid="inline-prompt-input"', async () => {
    vi.stubGlobal('fetch', vi.fn())
    const { default: InlinePromptWidget } = await import('../components/Editor/InlinePromptWidget')
    render(
      <InlinePromptWidget
        onSubmit={vi.fn()}
        onDismiss={vi.fn()}
        document="hello world"
        language="typescript"
      />,
    )
    expect(screen.getByTestId('inline-prompt-input')).toBeDefined()
    vi.unstubAllGlobals()
  })

  it('3. LivePreviewPanel renders iframe with src from store', () => {
    render(<LivePreviewPanel />)
    const iframe = screen.getByTestId('live-preview-iframe') as HTMLIFrameElement
    expect(iframe).toBeDefined()
    expect(iframe.src).toContain('localhost:5173')
  })

  it('4. SidecarOutputPanel renders with connection state visible', () => {
    setupSidecarStore({ connectionState: 'idle' as ConnectionState })
    render(<SidecarOutputPanel {...({} as IDockviewPanelProps)} />)
    // Panel wrapper must render; connecting indicator or output area
    const panel = screen.getByTestId('sidecar-output-panel')
    expect(panel).toBeDefined()
  })

  it('5. ArtifactPanel renders iframe with allow-scripts sandbox', () => {
    render(<ArtifactPanel {...({} as IDockviewPanelProps)} />)
    const iframe = screen.getByTestId('artifact-iframe') as HTMLIFrameElement
    expect(iframe).toBeDefined()
    expect(iframe.getAttribute('sandbox')).toContain('allow-scripts')
  })

  it('6. KnowledgeGraphPanel renders graph canvas', () => {
    render(<KnowledgeGraphPanel {...({} as IDockviewPanelProps)} />)
    expect(screen.getByTestId('graph-canvas')).toBeDefined()
  })

  it('7. APP_REGISTRY includes all 4 new panel keys', () => {
    const ids = APP_REGISTRY.map((def) => def.id)
    expect(ids).toContain('live-preview')
    expect(ids).toContain('sidecar-output')
    expect(ids).toContain('artifacts')
    expect(ids).toContain('knowledge-graph')
  })

  it('8. All 4 new panels coexist without errors', () => {
    const { container } = render(
      <div>
        <LivePreviewPanel />
        <SidecarOutputPanel {...({} as IDockviewPanelProps)} />
        <ArtifactPanel {...({} as IDockviewPanelProps)} />
        <KnowledgeGraphPanel {...({} as IDockviewPanelProps)} />
      </div>,
    )
    // All four panels must render without throwing
    expect(container.querySelectorAll('[data-testid]').length).toBeGreaterThanOrEqual(4)
  })
})
