import { create } from 'zustand'

export interface GraphNode {
  id: string
  node_type: 'Decision' | 'Assumption' | 'Evidence' | 'CodeFile'
  title: string
  properties?: Record<string, unknown>
}

export interface GraphEdge {
  from_id: string
  to_id: string
  edge_type: string
}

interface GraphState {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNodeId: string | null
  typeFilter: Set<string>
  searchQuery: string

  fetchNodes: () => Promise<void>
  setSelectedNode: (id: string | null) => void
  toggleTypeFilter: (nodeType: string) => void
  setSearchQuery: (q: string) => void
  addNode: (node: GraphNode) => void

  visibleNodes: () => GraphNode[]
}

export const useGraphStore = create<GraphState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  typeFilter: new Set<string>(),
  searchQuery: '',

  async fetchNodes(): Promise<void> {
    try {
      const resp = await fetch('/api/graph/nodes')
      if (!resp.ok) return
      const data = (await resp.json()) as GraphNode[]
      set({ nodes: data })
    } catch {
      // network error — leave state as-is
    }
  },

  setSelectedNode(id: string | null): void {
    set({ selectedNodeId: id })
  },

  toggleTypeFilter(nodeType: string): void {
    set((state) => {
      const next = new Set(state.typeFilter)
      if (next.has(nodeType)) {
        next.delete(nodeType)
      } else {
        next.add(nodeType)
      }
      return { typeFilter: next }
    })
  },

  setSearchQuery(q: string): void {
    set({ searchQuery: q })
  },

  addNode(node: GraphNode): void {
    set((state) => ({ nodes: [...state.nodes, node] }))
  },

  visibleNodes(): GraphNode[] {
    const { nodes, typeFilter, searchQuery } = get()
    const query = searchQuery.toLowerCase()
    return nodes.filter((n) => {
      if (typeFilter.has(n.node_type)) return false
      if (query && !n.title.toLowerCase().includes(query)) return false
      return true
    })
  },
}))
