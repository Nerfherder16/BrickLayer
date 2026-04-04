import { useEffect, useMemo } from 'react'
import { SigmaContainer, useLoadGraph, useRegisterEvents } from '@react-sigma/core'
import { MultiGraph } from 'graphology'
import { useGraphStore } from '../../stores/graphStore'
import type { GraphNode, GraphEdge } from '../../stores/graphStore'
import '@react-sigma/core/lib/style.css'

const NODE_COLORS: Record<string, string> = {
  Decision: 'var(--color-blue-500)',
  Assumption: 'var(--color-amber-500)',
  Evidence: 'var(--color-green-500)',
  CodeFile: 'var(--color-gray-500)',
}

interface GraphLoaderProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

/** Inner component that uses Sigma hooks — must be a child of SigmaContainer. */
function GraphLoader({ nodes, edges }: GraphLoaderProps): null {
  const loadGraph = useLoadGraph()
  const registerEvents = useRegisterEvents()
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)

  useEffect(() => {
    const graph = new MultiGraph()

    nodes.forEach((node: GraphNode) => {
      graph.addNode(node.id, {
        label: node.title,
        size: 10,
        color: NODE_COLORS[node.node_type] ?? NODE_COLORS['CodeFile'],
        x: Math.random(),
        y: Math.random(),
      })
    })

    const nodeIds = new Set(nodes.map((n) => n.id))
    edges.forEach((edge) => {
      if (nodeIds.has(edge.from_id) && nodeIds.has(edge.to_id)) {
        try {
          graph.addEdge(edge.from_id, edge.to_id, { type: edge.edge_type })
        } catch {
          // duplicate edge — skip
        }
      }
    })

    loadGraph(graph)

    registerEvents({
      clickNode: (event: { node: string }) => {
        setSelectedNode(event.node)
      },
    })
  }, [nodes, edges, loadGraph, registerEvents, setSelectedNode])

  return null
}

/** Force-directed sigma graph canvas. */
export function GraphCanvas(): JSX.Element {
  const allNodes = useGraphStore((s) => s.nodes)
  const typeFilter = useGraphStore((s) => s.typeFilter)
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const edges = useGraphStore((s) => s.edges)

  const visibleNodes = useMemo(() => {
    const query = searchQuery.toLowerCase()
    return allNodes.filter((n) => {
      if (typeFilter.has(n.node_type)) return false
      if (query && !n.title.toLowerCase().includes(query)) return false
      return true
    })
  }, [allNodes, typeFilter, searchQuery])

  return (
    <div data-testid="graph-canvas" style={{ width: '100%', height: '100%' }}>
      <SigmaContainer style={{ width: '100%', height: '100%' }}>
        <GraphLoader nodes={visibleNodes} edges={edges} />
      </SigmaContainer>
    </div>
  )
}
