import { create } from 'zustand'
import { toast } from 'sonner'

const TOKEN_KEY = 'codevvos_token'

export interface NotificationItem {
  id: string
  tenant_id: string
  user_id: string
  type: string
  title: string
  body?: string
  read: boolean
  created_at: string
}

interface NotificationState {
  items: NotificationItem[]
  unread_count: number
  loading: boolean
  fetchRecent: () => Promise<void>
  markRead: (id: string) => Promise<void>
  addToast: (notification: NotificationItem) => void
}

function getAuthHeader(): Record<string, string> {
  const token = sessionStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  items: [],
  unread_count: 0,
  loading: false,

  async fetchRecent(): Promise<void> {
    set({ loading: true })
    try {
      const res = await fetch('/api/notifications?limit=20', {
        headers: getAuthHeader(),
      })
      if (!res.ok) return
      const data = (await res.json()) as { items: NotificationItem[]; has_more: boolean }
      const existing = get().items
      const existingIds = new Set(existing.map((n) => n.id))
      const merged = [
        ...data.items.filter((n) => !existingIds.has(n.id)),
        ...existing,
      ]
      // Keep only the most recent 50, de-duped by id
      const seen = new Set<string>()
      const deduped = merged.filter((n) => {
        if (seen.has(n.id)) return false
        seen.add(n.id)
        return true
      })
      set({
        items: deduped,
        unread_count: deduped.filter((n) => !n.read).length,
      })
    } finally {
      set({ loading: false })
    }
  },

  async markRead(id: string): Promise<void> {
    await fetch(`/api/notifications/${id}/read`, {
      method: 'PATCH',
      headers: getAuthHeader(),
    })
    set((state) => {
      const items = state.items.map((n) => (n.id === id ? { ...n, read: true } : n))
      return { items, unread_count: items.filter((n) => !n.read).length }
    })
  },

  addToast(notification: NotificationItem): void {
    toast(notification.title, { description: notification.body })
  },
}))
