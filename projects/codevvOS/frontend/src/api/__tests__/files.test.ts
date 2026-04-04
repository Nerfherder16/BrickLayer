import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { fetchTree, fetchFileContent } from '../files'

const TOKEN_KEY = 'codevvos_token'
const TEST_TOKEN = 'test.eyJleHAiOjk5OTk5OTk5OTl9.sig'

const server = setupServer(
  http.get('/api/files/tree', ({ request }) => {
    const url = new URL(request.url)
    const path = url.searchParams.get('path')
    if (path === '/workspace') {
      return HttpResponse.json({
        name: 'workspace',
        type: 'dir',
        children: [
          { name: 'src', type: 'dir' },
          { name: 'readme.md', type: 'file', size: 100 },
        ],
      })
    }
    return HttpResponse.json({ name: 'unknown', type: 'dir' })
  }),
  http.patch('/api/files/workspace/readme.md', () =>
    HttpResponse.json({ content: '# Hello' }),
  ),
)

beforeAll(() => {
  sessionStorage.setItem(TOKEN_KEY, TEST_TOKEN)
  server.listen({ onUnhandledRequest: 'error' })
})
afterEach(() => server.resetHandlers())
afterAll(() => {
  server.close()
  sessionStorage.clear()
})

describe('fetchTree', () => {
  it('should return tree structure for /workspace', async () => {
    const result = await fetchTree('/workspace')
    expect(result.name).toBe('workspace')
    expect(result.type).toBe('dir')
    expect(result.children).toHaveLength(2)
    expect(result.children![0]).toEqual({ name: 'src', type: 'dir' })
    expect(result.children![1]).toEqual({ name: 'readme.md', type: 'file', size: 100 })
  })
})

describe('fetchFileContent', () => {
  it('should return file content string for /workspace/readme.md', async () => {
    const content = await fetchFileContent('/workspace/readme.md')
    expect(content).toBe('# Hello')
  })
})
