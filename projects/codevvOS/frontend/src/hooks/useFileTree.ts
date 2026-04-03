import { useState, useEffect, useCallback } from 'react'
import { fetchTree, fetchFileContent } from '../api/files'
import type { TreeNode } from '../api/files'

interface SelectedFile {
  path: string
  content: string
}

interface UseFileTreeReturn {
  tree: TreeNode | null
  loading: boolean
  error: string | null
  expandedPaths: Set<string>
  selectedFile: SelectedFile | null
  expandDir: (path: string) => Promise<void>
  selectFile: (path: string) => Promise<void>
}

function mergeChildren(tree: TreeNode, targetPath: string, children: TreeNode[]): TreeNode {
  if (tree.type !== 'dir') return tree

  // Build the path for the current node by matching name against path segments.
  // Walk by comparing the last segment of targetPath to tree.name at each level.
  const mergeAt = (node: TreeNode, remainingSegments: string[]): TreeNode => {
    if (remainingSegments.length === 0) {
      return { ...node, children }
    }
    const [next, ...rest] = remainingSegments
    if (!node.children) return node
    return {
      ...node,
      children: node.children.map((child) =>
        child.name === next ? mergeAt(child, rest) : child,
      ),
    }
  }

  // The targetPath is absolute, e.g. "/workspace/src".
  // The root node has name = last segment of rootPath (e.g. "workspace").
  // Extract segments after the root name.
  const segments = targetPath.split('/').filter(Boolean)
  // Find the root node name's index in the path to get relative segments
  const rootIdx = segments.indexOf(tree.name)
  const relativeSegments = rootIdx >= 0 ? segments.slice(rootIdx + 1) : segments

  return mergeAt(tree, relativeSegments)
}

/** Manages file tree state: loading, expanding/collapsing dirs, previewing files. */
export function useFileTree(rootPath = '/workspace'): UseFileTreeReturn {
  const [tree, setTree] = useState<TreeNode | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchTree(rootPath)
      .then((data) => {
        if (!cancelled) {
          setTree(data)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err))
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [rootPath])

  const expandDir = useCallback(
    async (path: string) => {
      if (expandedPaths.has(path)) {
        setExpandedPaths((prev) => {
          const next = new Set(prev)
          next.delete(path)
          return next
        })
        return
      }
      const children = await fetchTree(path)
      setTree((prev) =>
        prev ? mergeChildren(prev, path, children.children ?? []) : prev,
      )
      setExpandedPaths((prev) => new Set([...prev, path]))
    },
    [expandedPaths],
  )

  const selectFile = useCallback(async (path: string) => {
    const content = await fetchFileContent(path)
    setSelectedFile({ path, content })
  }, [])

  return { tree, loading, error, expandedPaths, selectedFile, expandDir, selectFile }
}
