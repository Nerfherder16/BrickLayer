import { useEffect, useState } from 'react'
import type { IDockviewPanelProps } from 'dockview-react'
import { Plus, Search } from 'lucide-react'
import { useGraphStore } from '../../stores/graphStore'
import { GraphCanvas } from '../Graph/GraphCanvas'
import { NodeDetail } from '../Graph/NodeDetail'
import { AddDecisionForm } from '../Graph/AddDecisionForm'

const NODE_TYPES = ['Decision', 'Assumption', 'Evidence', 'CodeFile'] as const

const TYPE_BADGE_COLORS: Record<string, string> = {
  Decision: 'var(--color-blue-500)',
  Assumption: 'var(--color-amber-500)',
  Evidence: 'var(--color-green-500)',
  CodeFile: 'var(--color-gray-500)',
}

/** Knowledge graph panel — force-directed Sigma canvas with type filters and search. */
export default function KnowledgeGraphPanel(_props: IDockviewPanelProps): JSX.Element {
  const fetchNodes = useGraphStore((s) => s.fetchNodes)
  const typeFilter = useGraphStore((s) => s.typeFilter)
  const searchQuery = useGraphStore((s) => s.searchQuery)
  const setSearchQuery = useGraphStore((s) => s.setSearchQuery)
  const toggleTypeFilter = useGraphStore((s) => s.toggleTypeFilter)
  const selectedNodeId = useGraphStore((s) => s.selectedNodeId)
  const nodes = useGraphStore((s) => s.nodes)
  const [showAddForm, setShowAddForm] = useState(false)

  useEffect(() => {
    void fetchNodes()
  }, [fetchNodes])

  const selectedNode = selectedNodeId ? nodes.find((n) => n.id === selectedNodeId) ?? null : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.5rem 0.75rem',
          borderBottom: '1px solid var(--color-gray-200)',
          flexShrink: 0,
          flexWrap: 'wrap',
        }}
      >
        {/* Search */}
        <div style={{ position: 'relative', flexGrow: 1, minWidth: '140px' }}>
          <Search
            size={14}
            style={{ position: 'absolute', left: '0.5rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-gray-400)' }}
          />
          <input
            type="search"
            aria-label="Search nodes"
            placeholder="Search…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.25rem 0.5rem 0.25rem 1.75rem',
              border: '1px solid var(--color-gray-300)',
              borderRadius: '0.375rem',
              fontSize: '0.8125rem',
            }}
          />
        </div>

        {/* Type filter toggles */}
        {NODE_TYPES.map((type) => (
          <button
            key={type}
            aria-pressed={!typeFilter.has(type)}
            onClick={() => toggleTypeFilter(type)}
            style={{
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              border: `1px solid ${TYPE_BADGE_COLORS[type]}`,
              background: typeFilter.has(type) ? 'transparent' : TYPE_BADGE_COLORS[type],
              color: typeFilter.has(type) ? TYPE_BADGE_COLORS[type] : 'white',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            {type}
          </button>
        ))}

        {/* Add Decision */}
        <button
          onClick={() => setShowAddForm(true)}
          aria-label="Add Decision node"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            padding: '0.25rem 0.625rem',
            border: '1px solid var(--color-blue-500)',
            borderRadius: '0.375rem',
            background: 'var(--color-blue-500)',
            color: 'white',
            fontSize: '0.8125rem',
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          <Plus size={14} />
          Add Decision
        </button>
      </div>

      {/* Add Decision form overlay */}
      {showAddForm && (
        <div
          style={{
            position: 'absolute',
            top: '3.5rem',
            right: '1rem',
            zIndex: 10,
            background: 'white',
            border: '1px solid var(--color-gray-200)',
            borderRadius: '0.5rem',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            padding: '1rem',
            width: '280px',
          }}
        >
          <AddDecisionForm onClose={() => setShowAddForm(false)} />
        </div>
      )}

      {/* Canvas + detail pane */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <GraphCanvas />
        </div>

        {selectedNode && <NodeDetail node={selectedNode} />}
      </div>
    </div>
  )
}
