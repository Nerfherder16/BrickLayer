import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useFileTree } from '../useFileTree'
import * as filesApi from '../../api/files'
import type { TreeNode } from '../../api/files'

vi.mock('../../api/files')

const mockFetchTree = vi.mocked(filesApi.fetchTree)
const mockFetchFileContent = vi.mocked(filesApi.fetchFileContent)

const rootTree: TreeNode = {
  name: 'workspace',
  type: 'dir',
  children: [
    { name: 'src', type: 'dir' },
    { name: 'readme.md', type: 'file', size: 100 },
  ],
}

const srcTree: TreeNode = {
  name: 'src',
  type: 'dir',
  children: [{ name: 'index.ts', type: 'file', size: 50 }],
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useFileTree', () => {
  it('should have loading true and tree null on initial render', () => {
    mockFetchTree.mockResolvedValue(rootTree)
    const { result } = renderHook(() => useFileTree())
    expect(result.current.loading).toBe(true)
    expect(result.current.tree).toBeNull()
  })

  it('should populate tree and set loading false after fetch resolves', async () => {
    mockFetchTree.mockResolvedValue(rootTree)
    const { result } = renderHook(() => useFileTree())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.tree).toEqual(rootTree)
    expect(result.current.error).toBeNull()
  })

  it('should set error state when fetchTree throws', async () => {
    mockFetchTree.mockRejectedValue(new Error('Network failure'))
    const { result } = renderHook(() => useFileTree())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Network failure')
    expect(result.current.tree).toBeNull()
  })

  it('should expand a directory and add its path to expandedPaths', async () => {
    mockFetchTree
      .mockResolvedValueOnce(rootTree)
      .mockResolvedValueOnce(srcTree)
    const { result } = renderHook(() => useFileTree())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => {
      await result.current.expandDir('/workspace/src')
    })

    expect(mockFetchTree).toHaveBeenCalledWith('/workspace/src')
    expect(result.current.expandedPaths.has('/workspace/src')).toBe(true)
  })

  it('should collapse (remove from expandedPaths) when expandDir called on already-expanded path', async () => {
    mockFetchTree
      .mockResolvedValueOnce(rootTree)
      .mockResolvedValueOnce(srcTree)
    const { result } = renderHook(() => useFileTree())
    await waitFor(() => expect(result.current.loading).toBe(false))

    // Expand first
    await act(async () => {
      await result.current.expandDir('/workspace/src')
    })
    expect(result.current.expandedPaths.has('/workspace/src')).toBe(true)

    const fetchCallsAfterFirstExpand = mockFetchTree.mock.calls.length

    // Collapse — should not call fetchTree again
    await act(async () => {
      await result.current.expandDir('/workspace/src')
    })
    expect(result.current.expandedPaths.has('/workspace/src')).toBe(false)
    expect(mockFetchTree).toHaveBeenCalledTimes(fetchCallsAfterFirstExpand)
  })

  it('should set selectedFile with path and content after selectFile', async () => {
    mockFetchTree.mockResolvedValue(rootTree)
    mockFetchFileContent.mockResolvedValue('# Hello')
    const { result } = renderHook(() => useFileTree())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => {
      await result.current.selectFile('/workspace/readme.md')
    })

    expect(mockFetchFileContent).toHaveBeenCalledWith('/workspace/readme.md')
    expect(result.current.selectedFile).toEqual({
      path: '/workspace/readme.md',
      content: '# Hello',
    })
  })
})
