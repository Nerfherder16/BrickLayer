import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import FileTreePanel from '../FileTreePanel'
import * as useFileTreeModule from '../../../hooks/useFileTree'
import type { TreeNode } from '../../../api/files'

vi.mock('../../../hooks/useFileTree')

const mockExpandDir = vi.fn()
const mockSelectFile = vi.fn()

const populatedTree: TreeNode = {
  name: 'workspace',
  type: 'dir',
  children: [
    { name: 'src', type: 'dir' },
    { name: 'readme.md', type: 'file', size: 100 },
  ],
}

function renderPanel() {
  const AnyPanel = FileTreePanel as React.FC
  return render(<AnyPanel />)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('FileTreePanel', () => {
  it('should render a container with data-testid="file-tree-panel"', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: null,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByTestId('file-tree-panel')).toBeDefined()
  })

  it('should render "src" directory item when tree is populated', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: populatedTree,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByText('src')).toBeDefined()
  })

  it('should render "readme.md" file item when tree is populated', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: populatedTree,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByText('readme.md')).toBeDefined()
  })

  it('should call expandDir when clicking on a directory item', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: populatedTree,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    fireEvent.click(screen.getByText('src'))
    expect(mockExpandDir).toHaveBeenCalledWith('/workspace/src')
  })

  it('should call selectFile when clicking on a file item', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: populatedTree,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    fireEvent.click(screen.getByText('readme.md'))
    expect(mockSelectFile).toHaveBeenCalledWith('/workspace/readme.md')
  })

  it('should show file content in preview zone when selectedFile is set', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: populatedTree,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: { path: '/workspace/readme.md', content: '# Hello' },
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByText('# Hello')).toBeDefined()
  })

  it('should show "Select a file to preview" when selectedFile is null', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: populatedTree,
      loading: false,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByText('Select a file to preview')).toBeDefined()
  })

  it('should show loading state when loading is true', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: null,
      loading: true,
      error: null,
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByText('Loading...')).toBeDefined()
  })

  it('should show error message when error is set', () => {
    vi.mocked(useFileTreeModule.useFileTree).mockReturnValue({
      tree: null,
      loading: false,
      error: 'Network failure',
      expandedPaths: new Set(),
      selectedFile: null,
      expandDir: mockExpandDir,
      selectFile: mockSelectFile,
    })
    renderPanel()
    expect(screen.getByText('Network failure')).toBeDefined()
  })
})
