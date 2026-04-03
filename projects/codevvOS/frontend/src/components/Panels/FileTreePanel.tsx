import type { IDockviewPanelProps } from 'dockview-react'
import { ChevronRight, FolderTree, FileText } from 'lucide-react'
import { useFileTree } from '../../hooks/useFileTree'
import type { TreeNode } from '../../api/files'
import './FileTreePanel.css'

interface TreeItemProps {
  node: TreeNode
  path: string
  depth: number
  expandedPaths: Set<string>
  selectedFilePath: string | null
  onExpandDir: (path: string) => void
  onSelectFile: (path: string) => void
}

function TreeItem({
  node,
  path,
  depth,
  expandedPaths,
  selectedFilePath,
  onExpandDir,
  onSelectFile,
}: TreeItemProps): JSX.Element {
  const isExpanded = expandedPaths.has(path)
  const isSelected = selectedFilePath === path

  if (node.type === 'dir') {
    return (
      <>
        <div
          className="file-tree-item"
          style={{ paddingLeft: `calc(var(--space-4) * ${depth})` }}
          onClick={() => onExpandDir(path)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onExpandDir(path)}
          aria-expanded={isExpanded}
        >
          <ChevronRight
            className="file-tree-icon"
            style={{ transform: isExpanded ? 'rotate(90deg)' : undefined }}
          />
          <FolderTree className="file-tree-icon" />
          <span className="file-tree-item-text">{node.name}</span>
        </div>
        {isExpanded && node.children?.map((child) => (
          <TreeItem
            key={child.name}
            node={child}
            path={`${path}/${child.name}`}
            depth={depth + 1}
            expandedPaths={expandedPaths}
            selectedFilePath={selectedFilePath}
            onExpandDir={onExpandDir}
            onSelectFile={onSelectFile}
          />
        ))}
      </>
    )
  }

  return (
    <div
      className={`file-tree-item${isSelected ? ' file-tree-item--selected' : ''}`}
      style={{ paddingLeft: `calc(var(--space-4) * ${depth})` }}
      onClick={() => onSelectFile(path)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelectFile(path)}
    >
      <FileText className="file-tree-icon" />
      <span className="file-tree-item-text">{node.name}</span>
    </div>
  )
}

/** File tree panel with split tree/preview layout for the dockview shell. */
export default function FileTreePanel(_props: IDockviewPanelProps): JSX.Element {
  const { tree, loading, error, expandedPaths, selectedFile, expandDir, selectFile } =
    useFileTree()

  return (
    <div className="file-tree-panel" data-testid="file-tree-panel">
      <div className="file-tree-zone">
        {loading && (
          <div className="file-tree-status">Loading...</div>
        )}
        {error && (
          <div className="file-tree-status file-tree-status--error">{error}</div>
        )}
        {!loading && !error && tree && (
          <>
            {tree.children?.map((child) => (
              <TreeItem
                key={child.name}
                node={child}
                path={`/${tree.name}/${child.name}`}
                depth={1}
                expandedPaths={expandedPaths}
                selectedFilePath={selectedFile?.path ?? null}
                onExpandDir={expandDir}
                onSelectFile={selectFile}
              />
            ))}
          </>
        )}
      </div>

      <div className="file-tree-preview">
        {selectedFile ? (
          <>
            <div className="file-tree-preview-header">
              <span>{selectedFile.path.split('/').pop()}</span>
            </div>
            <pre className="file-tree-preview-code">{selectedFile.content}</pre>
          </>
        ) : (
          <div className="file-tree-preview-empty">Select a file to preview</div>
        )}
      </div>
    </div>
  )
}
