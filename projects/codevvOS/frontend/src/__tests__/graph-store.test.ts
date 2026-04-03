import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useGraphStore } from '../stores/graphStore'
import type { GraphNode } from '../stores/graphStore'

const makeNode = (overrides: Partial<GraphNode> = {}): GraphNode => ({
  id: 'node-1',
  node_type: 'Decision',
  title: 'Test Decision',
  properties: {},
  ...overrides,
})

beforeEach(() => {
  useGraphStore.setState({
    nodes: [],
    edges: [],
    selectedNodeId: null,
    typeFilter: new Set<string>(),
    searchQuery: '',
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('graphStore', () => {
  describe('initial state', () => {
    it('should have empty nodes array', () => {
      expect(useGraphStore.getState().nodes).toEqual([])
    })

    it('should have null selectedNodeId', () => {
      expect(useGraphStore.getState().selectedNodeId).toBeNull()
    })

    it('should have empty typeFilter', () => {
      expect(useGraphStore.getState().typeFilter.size).toBe(0)
    })

    it('should have empty searchQuery', () => {
      expect(useGraphStore.getState().searchQuery).toBe('')
    })
  })

  describe('fetchNodes', () => {
    it('should GET /api/graph/nodes and populate nodes', async () => {
      const mockNodes: GraphNode[] = [makeNode()]
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockNodes,
      } as Response)

      await useGraphStore.getState().fetchNodes()

      expect(useGraphStore.getState().nodes).toEqual(mockNodes)
    })

    it('should fetch from /api/graph/nodes', async () => {
      const mockFetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)

      await useGraphStore.getState().fetchNodes()

      expect(mockFetch).toHaveBeenCalledWith('/api/graph/nodes')
    })

    it('should not throw when fetch fails', async () => {
      vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'))

      await expect(useGraphStore.getState().fetchNodes()).resolves.toBeUndefined()
    })

    it('should leave nodes unchanged when response is not ok', async () => {
      useGraphStore.setState({ nodes: [makeNode()] })
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        json: async () => [],
      } as Response)

      await useGraphStore.getState().fetchNodes()

      expect(useGraphStore.getState().nodes).toHaveLength(1)
    })
  })

  describe('setSelectedNode', () => {
    it('should set selectedNodeId', () => {
      useGraphStore.getState().setSelectedNode('node-42')
      expect(useGraphStore.getState().selectedNodeId).toBe('node-42')
    })

    it('should clear selectedNodeId when null is passed', () => {
      useGraphStore.setState({ selectedNodeId: 'node-1' })
      useGraphStore.getState().setSelectedNode(null)
      expect(useGraphStore.getState().selectedNodeId).toBeNull()
    })
  })

  describe('toggleTypeFilter', () => {
    it('should add a type to typeFilter', () => {
      useGraphStore.getState().toggleTypeFilter('Decision')
      expect(useGraphStore.getState().typeFilter.has('Decision')).toBe(true)
    })

    it('should remove a type that is already in typeFilter', () => {
      useGraphStore.setState({ typeFilter: new Set(['Decision']) })
      useGraphStore.getState().toggleTypeFilter('Decision')
      expect(useGraphStore.getState().typeFilter.has('Decision')).toBe(false)
    })

    it('should not affect other types when toggling one', () => {
      useGraphStore.setState({ typeFilter: new Set(['Decision', 'Evidence']) })
      useGraphStore.getState().toggleTypeFilter('Decision')
      expect(useGraphStore.getState().typeFilter.has('Evidence')).toBe(true)
    })
  })

  describe('setSearchQuery', () => {
    it('should update searchQuery', () => {
      useGraphStore.getState().setSearchQuery('auth')
      expect(useGraphStore.getState().searchQuery).toBe('auth')
    })
  })

  describe('addNode', () => {
    it('should append a node to the nodes array', () => {
      const node = makeNode({ id: 'node-99' })
      useGraphStore.getState().addNode(node)
      expect(useGraphStore.getState().nodes).toContainEqual(node)
    })
  })

  describe('visibleNodes', () => {
    it('should return all nodes when no filter or query is set', () => {
      const nodes = [makeNode({ id: 'a' }), makeNode({ id: 'b', node_type: 'Evidence' })]
      useGraphStore.setState({ nodes })
      expect(useGraphStore.getState().visibleNodes()).toHaveLength(2)
    })

    it('should hide nodes of filtered type', () => {
      const nodes = [
        makeNode({ id: 'a', node_type: 'Decision' }),
        makeNode({ id: 'b', node_type: 'Evidence' }),
      ]
      useGraphStore.setState({ nodes, typeFilter: new Set(['Decision']) })
      const visible = useGraphStore.getState().visibleNodes()
      expect(visible.some((n) => n.node_type === 'Decision')).toBe(false)
      expect(visible.some((n) => n.node_type === 'Evidence')).toBe(true)
    })

    it('should filter nodes by title substring (case insensitive)', () => {
      const nodes = [
        makeNode({ id: 'a', title: 'Auth decision' }),
        makeNode({ id: 'b', title: 'Database schema' }),
      ]
      useGraphStore.setState({ nodes, searchQuery: 'auth' })
      const visible = useGraphStore.getState().visibleNodes()
      expect(visible).toHaveLength(1)
      expect(visible[0].id).toBe('a')
    })

    it('should apply both type filter and search query together', () => {
      const nodes = [
        makeNode({ id: 'a', node_type: 'Decision', title: 'Auth decision' }),
        makeNode({ id: 'b', node_type: 'Evidence', title: 'Auth evidence' }),
        makeNode({ id: 'c', node_type: 'Decision', title: 'DB schema' }),
      ]
      useGraphStore.setState({ nodes, typeFilter: new Set(['Decision']), searchQuery: 'auth' })
      const visible = useGraphStore.getState().visibleNodes()
      expect(visible).toHaveLength(1)
      expect(visible[0].id).toBe('b')
    })
  })
})
