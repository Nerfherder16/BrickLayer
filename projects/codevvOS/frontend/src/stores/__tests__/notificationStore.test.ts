import { describe, it, expect, beforeAll, afterEach, afterAll, vi, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

const TOKEN_KEY = 'codevvos_token'
const TEST_TOKEN = 'test.eyJleHAiOjk5OTk5OTk5OTl9.sig'

const mockNotifications = [
  {
    id: '1',
    tenant_id: 'tenant-1',
    user_id: 'user-1',
    type: 'info',
    title: 'Test Notification',
    body: 'Test body',
    read: false,
    created_at: '2026-04-03T10:00:00Z',
  },
]

const server = setupServer(
  http.get('/api/notifications', () =>
    HttpResponse.json({ items: mockNotifications, has_more: false }),
  ),
  http.patch('/api/notifications/:id/read', () =>
    new HttpResponse(null, { status: 204 }),
  ),
)

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  vi.clearAllMocks()
  sessionStorage.clear()
})
afterAll(() => server.close())

describe('notificationStore', () => {
  beforeEach(async () => {
    sessionStorage.setItem(TOKEN_KEY, TEST_TOKEN)
    // Reset store between tests by re-importing fresh
    vi.resetModules()
  })

  it('should start with empty items and zero unread_count', async () => {
    const { useNotificationStore } = await import('../notificationStore')
    const state = useNotificationStore.getState()
    expect(state.items).toEqual([])
    expect(state.unread_count).toBe(0)
    expect(state.loading).toBe(false)
  })

  it('fetchRecent() should populate items from GET /api/notifications', async () => {
    const { useNotificationStore } = await import('../notificationStore')
    await useNotificationStore.getState().fetchRecent()
    const state = useNotificationStore.getState()
    expect(state.items).toHaveLength(1)
    expect(state.items[0].id).toBe('1')
    expect(state.items[0].title).toBe('Test Notification')
  })

  it('fetchRecent() should set unread_count to 1 when 1 unread notification', async () => {
    const { useNotificationStore } = await import('../notificationStore')
    await useNotificationStore.getState().fetchRecent()
    expect(useNotificationStore.getState().unread_count).toBe(1)
  })

  it('markRead() should call PATCH and flip item.read to true', async () => {
    const { useNotificationStore } = await import('../notificationStore')
    await useNotificationStore.getState().fetchRecent()
    await useNotificationStore.getState().markRead('1')
    const state = useNotificationStore.getState()
    expect(state.items[0].read).toBe(true)
    expect(state.unread_count).toBe(0)
  })
})
