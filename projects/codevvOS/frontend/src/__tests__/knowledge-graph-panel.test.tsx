import React from 'react'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ---- Mocks (must be before any imports that use them) ----------------------

vi.mock('@react-sigma/core', () => ({
  SigmaContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="sigma-container">{children}</div>
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
  return {
    default: MockMultiGraph,
    MultiGraph: MockMultiGraph,
  }
})

vi.mock('graphology-layout-forceatlas2', () => ({ default: vi.fn() }))

// ---- Import after mocks ----------------------------------------------------

import KnowledgeGraphPanel from '../components/Panels/KnowledgeGraphPanel'
import type { IDockviewPanelProps } from 'dockview-react'
import { useGraphStore } from '../stores/graphStore'
import type { GraphNode } from '../stores/graphStore'

// ---- Helpers ----------------------------------------------------------------

function makePanelProps(): IDockviewPanelProps {
  return {} as IDockviewPanelProps
}

function makeNode(overrides: Partial<GraphNode> = {}): GraphNode {
  return {
    id: 'node-1',
    node_type: 'Decision',
    title: 'Test Decision',
    properties: {},
    ...overrides,
  }
}

// ---- Setup ------------------------------------------------------------------

beforeEach(() => {
  useGraphStore.setState({
    nodes: [],
    edges: [],
    selectedNodeId: null,
    typeFilter: new Set<string>(),
    searchQuery: '',
  })
  vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: true,
    json: async () => [],
  } as Response)
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ---- Tests ------------------------------------------------------------------

describe('KnowledgeGraphPanel', () => {
  it('renders graph-canvas testid without crashing with empty data', () => {
    render(<KnowledgeGraphPanel {...makePanelProps()} />)
    expect(screen.getByTestId('graph-canvas')).toBeDefined()
  })

  it('calls GET /api/graph/nodes on mount', async () => {
    const mockFetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response)

    await act(async () => {
      render(<KnowledgeGraphPanel {...makePanelProps()} />)
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/graph/nodes')
  })

  it('shows node-detail when a node is selected', () => {
    const node = makeNode()
    useGraphStore.setState({ nodes: [node], selectedNodeId: 'node-1' })

    render(<KnowledgeGraphPanel {...makePanelProps()} />)

    expect(screen.getByTestId('node-detail')).toBeDefined()
  })

  it('does not show node-detail when no node is selected', () => {
    render(<KnowledgeGraphPanel {...makePanelProps()} />)
    expect(screen.queryByTestId('node-detail')).toBeNull()
  })

  it('type filter button toggles Decision type in store', async () => {
    render(<KnowledgeGraphPanel {...makePanelProps()} />)

    const decisionBtn = screen.getByRole('button', { name: 'Decision' })
    fireEvent.click(decisionBtn)

    expect(useGraphStore.getState().typeFilter.has('Decision')).toBe(true)
  })

  it('search input updates searchQuery in store', () => {
    render(<KnowledgeGraphPanel {...makePanelProps()} />)

    const search = screen.getByRole('searchbox')
    fireEvent.change(search, { target: { value: 'auth' } })

    expect(useGraphStore.getState().searchQuery).toBe('auth')
  })

  it('clicking Add Decision button shows add-decision-form', () => {
    render(<KnowledgeGraphPanel {...makePanelProps()} />)

    const addBtn = screen.getByRole('button', { name: /add decision/i })
    fireEvent.click(addBtn)

    expect(screen.getByTestId('add-decision-form')).toBeDefined()
  })
})

describe('AddDecisionForm', () => {
  it('submits POST /api/graph/nodes with Decision type', async () => {
    const returnedNode: GraphNode = {
      id: 'new-id',
      node_type: 'Decision',
      title: 'My Decision',
      properties: {},
    }
    const mockFetch = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({ ok: true, json: async () => [] } as Response)  // fetchNodes on mount
      .mockResolvedValueOnce({ ok: true, json: async () => returnedNode } as Response)  // POST

    await act(async () => {
      render(<KnowledgeGraphPanel {...makePanelProps()} />)
    })

    // Open the form
    fireEvent.click(screen.getByRole('button', { name: /add decision/i }))

    const titleInput = screen.getByRole('textbox', { name: /decision title/i })
    fireEvent.change(titleInput, { target: { value: 'My Decision' } })

    await act(async () => {
      fireEvent.submit(screen.getByTestId('add-decision-form'))
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/graph/nodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_type: 'Decision', title: 'My Decision', properties: {} }),
    })
  })
})

describe('GraphCanvas', () => {
  it('renders data-testid="graph-canvas"', () => {
    render(<KnowledgeGraphPanel {...makePanelProps()} />)
    expect(screen.getByTestId('graph-canvas')).toBeDefined()
  })
})

describe('visibleNodes filtering', () => {
  it('type filter hides Decision nodes from the store visible set', () => {
    useGraphStore.setState({
      nodes: [
        makeNode({ id: 'a', node_type: 'Decision' }),
        makeNode({ id: 'b', node_type: 'Evidence' }),
      ],
      typeFilter: new Set(['Decision']),
    })

    const visible = useGraphStore.getState().visibleNodes()
    expect(visible.some((n) => n.node_type === 'Decision')).toBe(false)
  })

  it('search filters by title substring', () => {
    useGraphStore.setState({
      nodes: [
        makeNode({ id: 'a', title: 'Use PostgreSQL' }),
        makeNode({ id: 'b', title: 'Auth service' }),
      ],
      searchQuery: 'postgres',
    })

    const visible = useGraphStore.getState().visibleNodes()
    expect(visible).toHaveLength(1)
    expect(visible[0].id).toBe('a')
  })
})
