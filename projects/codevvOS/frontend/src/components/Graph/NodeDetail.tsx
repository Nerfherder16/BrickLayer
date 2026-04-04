import { X } from 'lucide-react'
import { useGraphStore } from '../../stores/graphStore'
import type { GraphNode } from '../../stores/graphStore'

interface NodeDetailProps {
  node: GraphNode
}

/** Side pane showing details for the selected graph node. */
export function NodeDetail({ node }: NodeDetailProps): JSX.Element {
  const setSelectedNode = useGraphStore((s) => s.setSelectedNode)

  return (
    <aside
      data-testid="node-detail"
      style={{
        width: '280px',
        flexShrink: 0,
        borderLeft: '1px solid var(--color-gray-200)',
        padding: '1rem',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            color: 'var(--color-gray-500)',
          }}
        >
          {node.node_type}
        </span>
        <button
          aria-label="Close node detail"
          onClick={() => setSelectedNode(null)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem' }}
        >
          <X size={16} />
        </button>
      </div>

      <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>{node.title}</h3>

      {node.properties && Object.keys(node.properties).length > 0 && (
        <dl style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {Object.entries(node.properties).map(([key, value]) => (
            <div key={key}>
              <dt style={{ fontSize: '0.75rem', color: 'var(--color-gray-500)' }}>{key}</dt>
              <dd style={{ margin: 0, fontSize: '0.875rem' }}>{String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </aside>
  )
}
