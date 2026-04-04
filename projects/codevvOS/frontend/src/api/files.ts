import { getStoredToken } from './auth'

export interface TreeNode {
  name: string
  type: 'file' | 'dir'
  size?: number
  modified?: string
  children?: TreeNode[]
}

/** Fetch a directory tree listing for the given path. */
export async function fetchTree(path: string): Promise<TreeNode> {
  const token = getStoredToken()
  const res = await fetch(`/api/files/tree?path=${encodeURIComponent(path)}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Failed to fetch tree: ${res.status}`)
  return res.json() as Promise<TreeNode>
}

/** Fetch the content of a file at the given path. */
export async function fetchFileContent(path: string): Promise<string> {
  const token = getStoredToken()
  // Strip leading slash for URL construction
  const urlPath = path.startsWith('/') ? path.slice(1) : path
  const res = await fetch(`/api/files/${urlPath}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ action: 'read' }),
  })
  if (!res.ok) throw new Error(`Failed to fetch file: ${res.status}`)
  const data = (await res.json()) as { content: string }
  return data.content
}
